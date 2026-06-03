# =============================================================
# Python + Requests 14天学习计划 - Day 13
# 主题：项目实战 Day 3 — 安全测试 + Mock + 并发 + 报告生成
# 日期：2026-05-28
# =============================================================

"""
Day 13 学习大纲
===============
Part 1：接口安全测试
    - Token 过期 / 无效 / 篡改
    - 权限越权（水平越权、垂直越权）
    - 注入攻击（SQL / NoSQL / XSS / SSRF）
    - 敏感信息泄露检查

Part 2：unittest.mock / pytest monkeypatch
    - Mock 外部HTTP依赖（requests.get 打桩）
    - Mock 数据库返回值
    - monkeypatch 修改环境变量
    - side_effect 模拟网络异常

Part 3：接口幂等性 + 简单并发测试
    - 重复请求验证（POST 幂等性）
    - 并发场景（threading 同时发起 N 个请求）
    - 竞态条件检测

Part 4：自定义测试报告生成器
    - 收集 pytest 结果 → 生成 Markdown 报告
    - 测试摘要：通过数 / 失败数 / 跳过数 / 耗时

Part 5：综合回归实战（山海之巅全模块覆盖）
    - Login + Player + Combat 三模块串联回归
    - 断言完整性检查（状态码 + 字段 + 响应时间）
"""

import requests
import pytest
import json
import time
import threading
import hashlib
import re
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime
from collections import defaultdict


# =========================================================
# 复用 Day 11/12 的基础工具类（简化版内联）
# =========================================================

BASE_URL = "https://httpbin.org"

# 模拟山海之巅 API 根地址（测试环境）
GAME_API_BASE = "https://httpbin.org"  # 用 httpbin 模拟真实接口


class BaseAPI:
    """统一请求封装（复用自 Day 11）"""

    def __init__(self, base_url: str = BASE_URL, timeout: int = 20):
        self.session = requests.Session()
        self.base_url = base_url
        self.timeout = timeout
        self._default_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self.session.headers.update(self._default_headers)

    def set_token(self, token: str):
        self.session.headers["Authorization"] = f"Bearer {token}"

    def clear_token(self):
        self.session.headers.pop("Authorization", None)

    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{path}"
        kwargs.setdefault("timeout", self.timeout)
        max_retry = 3
        for attempt in range(max_retry):
            try:
                resp = self.session.request(method, url, **kwargs)
                return resp
            except requests.exceptions.ConnectionError as e:
                if attempt == max_retry - 1:
                    raise
                time.sleep(1)

    def get(self, path, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path, **kwargs):
        return self.request("POST", path, **kwargs)

    def put(self, path, **kwargs):
        return self.request("PUT", path, **kwargs)

    def delete(self, path, **kwargs):
        return self.request("DELETE", path, **kwargs)


class AssertHelper:
    """断言工具（复用自 Day 11）"""

    @staticmethod
    def status_code(resp, expected: int):
        assert resp.status_code == expected, (
            f"状态码期望 {expected}，实际 {resp.status_code}，响应: {resp.text[:200]}"
        )

    @staticmethod
    def json_field_exists(resp, field_path: str):
        data = resp.json()
        keys = field_path.split(".")
        cur = data
        for key in keys:
            assert isinstance(cur, dict) and key in cur, (
                f"字段 '{field_path}' 不存在于响应中"
            )
            cur = cur[key]

    @staticmethod
    def response_time_ok(resp, max_seconds: float = 3.0):
        elapsed = resp.elapsed.total_seconds()
        assert elapsed <= max_seconds, (
            f"响应时间 {elapsed:.2f}s 超过上限 {max_seconds}s"
        )

    @staticmethod
    def no_sensitive_info(resp, keywords=None):
        """检查响应中无敏感信息泄露"""
        if keywords is None:
            keywords = ["password", "passwd", "secret", "private_key", "token_secret"]
        text = resp.text.lower()
        leaked = [kw for kw in keywords if kw in text]
        assert not leaked, f"响应中发现敏感字段: {leaked}"


# =============================================================
# Part 1：接口安全测试
# =============================================================

print("\n" + "=" * 60)
print("  Day 13 - Part 1：接口安全测试")
print("=" * 60)
print("""
📌 接口安全测试 4 大类

1. 鉴权安全（Authentication）
   - 无 token 访问受保护接口 → 期望 401
   - 伪造/篡改 token → 期望 401 / 403
   - Token 格式错误 → 期望 400 / 401

2. 权限控制（Authorization）
   - 水平越权：用 A 用户 token 访问 B 用户数据 → 期望 403
   - 垂直越权：用普通用户 token 调管理员接口 → 期望 403

3. 注入防护（Injection）
   - SQL 注入、NoSQL 注入、XSS、SSRF → 期望接口返回错误而非执行
   - 测试点：返回 5xx 证明未过滤，200 但数据正常证明有防护

4. 信息安全（Information Security）
   - 响应中不应包含明文密码、secret、token_secret
   - 错误信息不应暴露数据库类型、栈跟踪等内部信息
""")


# 测试类：Token 安全
class TestTokenSecurity:
    """Token 安全测试套件"""

    def setup_method(self):
        self.api = BaseAPI()

    # ---- 1. 无 token 访问（期望接口拒绝，此处用 httpbin 模拟） ----
    def test_no_token_request(self):
        """无 token 时请求受保护接口"""
        # httpbin /bearer 端点：无 Authorization 头返回 401
        resp = self.api.get("/bearer")
        # httpbin 的 /bearer 在无有效 Bearer token 时返回 401
        assert resp.status_code == 401, (
            f"无token应返回401，实际: {resp.status_code}"
        )
        print("    ✅ 无 token → 401 Unauthorized")

    def test_valid_bearer_token(self):
        """携带合法 Bearer token"""
        self.api.set_token("valid_game_token_abc123")
        resp = self.api.get("/bearer")
        AssertHelper.status_code(resp, 200)
        data = resp.json()
        assert data.get("authenticated") is True
        assert "token" in data
        print(f"    ✅ 合法 token → 200, authenticated={data['authenticated']}")

    def test_malformed_token(self):
        """格式错误的 token（非 Bearer 格式）"""
        # 直接设置一个非 Bearer 格式的 Authorization 头
        self.api.session.headers["Authorization"] = "NotBearer!!!corrupted"
        resp = self.api.get("/bearer")
        # httpbin /bearer 对非 Bearer 格式返回 401
        assert resp.status_code == 401
        print(f"    ✅ 畸形 token → {resp.status_code}")

    def test_tampered_token_payload(self):
        """篡改 token payload（JWT 结构破坏）"""
        fake_jwt = "eyJhbGciOiJIUzI1NiJ9.TAMPERED_PAYLOAD.fake_signature"
        self.api.set_token(fake_jwt)
        resp = self.api.get("/bearer")
        # JWT 格式但 payload 被篡改 → httpbin 仍返回 200（因为 httpbin 只检查 Bearer 前缀）
        # 真实游戏服务器会返回 401/403，这里记录真实行为
        print(f"    ℹ️  篡改 JWT → httpbin 返回 {resp.status_code}（真实服务器应为 401）")
        assert resp.status_code in (200, 401, 403)

    def test_empty_token(self):
        """空字符串 token"""
        self.api.set_token("")
        resp = self.api.get("/bearer")
        assert resp.status_code == 401
        print(f"    ✅ 空 token → 401")


# 测试类：越权测试
class TestPrivilegeEscalation:
    """越权测试套件"""

    def setup_method(self):
        self.api = BaseAPI()
        self.api.set_token("normal_user_token")

    def test_horizontal_privilege_escalation(self):
        """
        水平越权：模拟用 A 用户 token 请求 B 用户的数据
        场景：GET /player/{other_user_id}/info
        期望：403 Forbidden
        实际（httpbin模拟）：通过 JSON 响应模拟越权检查逻辑
        """
        # httpbin /get 会回显我们发送的参数
        resp = self.api.get("/get", params={
            "user_id": "attacker_uid_999",
            "target_uid": "victim_uid_123",
            "action": "steal_data"
        })
        AssertHelper.status_code(resp, 200)
        # 验证：请求中带了越权参数，响应中我们能识别到这是需要拦截的场景
        data = resp.json()
        args = data.get("args", {})
        # 在真实系统中，uid != target_uid 时应返回 403
        # 这里记录此场景的测试骨架
        assert "target_uid" in args
        print(f"    ✅ 水平越权测试骨架通过（真实服务器需拦截 uid≠target_uid 场景）")

    def test_vertical_privilege_escalation(self):
        """
        垂直越权：普通用户尝试调用管理员接口
        场景：POST /admin/ban_user（普通 token）
        期望：403 Forbidden
        """
        resp = self.api.post("/post", json={
            "action": "admin_ban_user",
            "target_user": "player_123",
            "operator_token": "normal_user_token",  # 普通 token
            "role": "user"  # 非 admin
        })
        AssertHelper.status_code(resp, 200)  # httpbin 总是200
        data = resp.json()
        # 真实系统中 role=user 调用 admin 接口应被拒绝
        payload = data.get("json", {})
        assert payload.get("role") == "user"
        print(f"    ✅ 垂直越权测试骨架通过（真实服务器需拦截 role=user 调用 admin 接口）")


# 测试类：注入攻击防护
class TestInjectionProtection:
    """注入攻击防护测试"""

    def setup_method(self):
        self.api = BaseAPI()
        self.api.set_token("test_token_day13")

    SQL_PAYLOADS = [
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "1 UNION SELECT username, password FROM users",
        "' OR 1=1 --",
        "admin'--",
    ]

    XSS_PAYLOADS = [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert(1)>",
        "javascript:alert(document.cookie)",
        "<svg onload=alert('XSS')>",
    ]

    @pytest.mark.parametrize("payload", SQL_PAYLOADS)
    def test_sql_injection_in_username(self, payload):
        """SQL 注入：用户名字段注入测试"""
        resp = self.api.post("/post", json={
            "username": payload,
            "password": "normal_password"
        })
        # 1. 接口不应因注入崩溃（500）
        assert resp.status_code != 500, f"SQL注入导致服务器500错误！payload: {payload}"
        # 2. 接口应拒绝（400/401/403）或正常处理（200但无危险操作）
        assert resp.status_code in (200, 400, 401, 403), (
            f"异常状态码 {resp.status_code}，payload: {payload}"
        )
        # 3. 响应中不应出现数据库错误信息
        db_error_keywords = ["syntax error", "mysql_", "ora-", "pg_query", "sqlite"]
        assert not any(kw in resp.text.lower() for kw in db_error_keywords), (
            f"响应中出现数据库错误信息！payload: {payload}"
        )
        print(f"    ✅ SQL注入防护: {payload[:30]}... → {resp.status_code}")

    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    def test_xss_injection_in_nickname(self, payload):
        """XSS 注入：昵称字段 XSS 测试"""
        resp = self.api.put("/put", json={
            "player_id": "pid_001",
            "nickname": payload
        })
        assert resp.status_code != 500, f"XSS注入导致服务器500！payload: {payload}"
        # 理想情况：响应中的用户输入应被转义，不含原始 <script> 等标签
        # httpbin 会原样回显，这里只验证不崩溃
        data = resp.json()
        assert data is not None
        print(f"    ✅ XSS防护骨架: {payload[:30]}... → {resp.status_code}")

    def test_ssrf_prevention(self):
        """SSRF：服务端请求伪造（传入内网地址）"""
        resp = self.api.post("/post", json={
            "callback_url": "http://169.254.169.254/latest/meta-data/",  # AWS 元数据地址
            "action": "fetch_url"
        })
        # 真实系统应拦截内网/本地回环地址
        assert resp.status_code != 500
        print(f"    ✅ SSRF防护骨架: 内网地址 → {resp.status_code}")

    def test_no_sensitive_info_in_response(self):
        """响应不含敏感信息"""
        resp = self.api.get("/get", params={"query": "user_info"})
        # 检查响应中无明文密码/secret
        AssertHelper.no_sensitive_info(resp)
        print(f"    ✅ 响应无敏感信息泄露")


# =============================================================
# Part 2：unittest.mock + pytest monkeypatch
# =============================================================

print("\n" + "=" * 60)
print("  Day 13 - Part 2：Mock 模拟外部依赖")
print("=" * 60)
print("""
📌 为什么要 Mock？

真实测试中常遇到：
  - 第三方API不稳定（httpbin.org 偶发502）
  - 数据库操作慢（每次测试都读写DB不现实）
  - 需要模拟网络超时、断网等特殊场景

Mock 的核心：用"假对象"替换"真实依赖"，让测试可控且快速。

3 种 Mock 用法：
  ① unittest.mock.patch   → 装饰器/上下文管理器，替换对象
  ② MagicMock             → 自动生成属性的魔法 Mock 对象
  ③ pytest monkeypatch    → pytest 内置，测试结束自动还原
""")


# 模拟"山海之巅"客户端（被测对象）
class ShanHaiApiClient:
    """山海之巅游戏 API 客户端（被测模块）"""

    def __init__(self, base_url: str = GAME_API_BASE):
        self.base_url = base_url
        self.token = None

    def login(self, username: str, password: str) -> dict:
        """登录接口"""
        resp = requests.post(
            f"{self.base_url}/post",
            json={"username": username, "password": password},
            timeout=10
        )
        if resp.status_code == 200:
            # 真实项目中这里解析 token
            self.token = hashlib.md5(f"{username}:{password}".encode()).hexdigest()
            return {"success": True, "token": self.token}
        return {"success": False, "error": "login_failed"}

    def get_player_info(self, player_id: str) -> dict:
        """获取玩家信息"""
        if not self.token:
            raise ValueError("未登录，请先调用 login()")
        resp = requests.get(
            f"{self.base_url}/get",
            params={"player_id": player_id},
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=10
        )
        return resp.json()

    def send_notification(self, player_id: str, message: str) -> bool:
        """发送通知（依赖外部推送服务）"""
        # 假设这里调用了第三方推送服务
        resp = requests.post(
            "https://push.shanhai-game.com/notify",
            json={"player_id": player_id, "msg": message},
            timeout=5
        )
        return resp.status_code == 200


class TestMockUsage:
    """Mock 技术测试套件"""

    # ---- ① 用 patch 替换真实 HTTP 请求 ----
    @patch("requests.post")
    def test_mock_login_success(self, mock_post):
        """Mock login：伪造服务器返回成功"""
        # 配置 mock 返回值
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "json": {"username": "hero_001", "password": "xxx"},
            "url": "https://httpbin.org/post"
        }
        mock_post.return_value = mock_response

        client = ShanHaiApiClient()
        result = client.login("hero_001", "secret123")

        # 验证返回值
        assert result["success"] is True
        assert "token" in result
        # 验证 requests.post 被调用了一次
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert "hero_001" in str(call_kwargs)
        print(f"    ✅ Mock 登录成功: token={result['token'][:16]}...")

    @patch("requests.post")
    def test_mock_login_failure(self, mock_post):
        """Mock login：伪造服务器返回 500 错误"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        client = ShanHaiApiClient()
        result = client.login("hero_001", "wrong_password")

        assert result["success"] is False
        assert result["error"] == "login_failed"
        print(f"    ✅ Mock 登录失败处理正确: {result}")

    @patch("requests.post")
    def test_mock_network_timeout(self, mock_post):
        """Mock 网络超时：伪造 Timeout 异常"""
        mock_post.side_effect = requests.exceptions.Timeout("连接超时")

        client = ShanHaiApiClient()
        with pytest.raises(requests.exceptions.Timeout) as exc_info:
            client.login("hero_001", "pass")

        assert "超时" in str(exc_info.value)
        print(f"    ✅ Mock 超时异常捕获正确: {exc_info.value}")

    @patch("requests.post")
    def test_mock_notification_service(self, mock_post):
        """Mock 第三方推送服务（不依赖真实外部服务）"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        client = ShanHaiApiClient()
        client.token = "fake_token_for_test"
        result = client.send_notification("player_001", "你的装备已强化完成！")

        assert result is True
        # 验证调用参数
        call_args = mock_post.call_args
        sent_json = call_args.kwargs.get("json") or call_args.args[1] if len(call_args.args) > 1 else {}
        if not sent_json and call_args.kwargs.get("json"):
            sent_json = call_args.kwargs["json"]
        print(f"    ✅ Mock 推送服务调用成功，result={result}")

    # ---- ② monkeypatch 修改环境变量 ----
    def test_monkeypatch_env_variable(self, monkeypatch):
        """monkeypatch：临时修改环境变量"""
        import os
        monkeypatch.setenv("GAME_ENV", "staging")
        monkeypatch.setenv("GAME_BASE_URL", "https://staging-api.shanhai.com")

        env = os.environ.get("GAME_ENV")
        base_url = os.environ.get("GAME_BASE_URL")

        assert env == "staging"
        assert "staging" in base_url
        print(f"    ✅ monkeypatch 环境变量: GAME_ENV={env}, URL={base_url}")
        # 测试结束后 monkeypatch 自动还原

    # ---- ③ Mock + side_effect 模拟多次调用不同结果 ----
    @patch("requests.get")
    def test_mock_side_effect_retry(self, mock_get):
        """side_effect 模拟第1、2次超时，第3次成功（retry场景）"""
        success_resp = MagicMock()
        success_resp.status_code = 200
        success_resp.json.return_value = {"player_id": "p001", "level": 88}

        mock_get.side_effect = [
            requests.exceptions.ConnectionError("第1次连接失败"),
            requests.exceptions.ConnectionError("第2次连接失败"),
            success_resp  # 第3次成功
        ]

        def get_with_retry(url, max_retry=3, **kwargs):
            for i in range(max_retry):
                try:
                    return requests.get(url, **kwargs)
                except requests.exceptions.ConnectionError:
                    if i == max_retry - 1:
                        raise
                    time.sleep(0.01)  # 测试中用极短间隔

        resp = get_with_retry(f"{GAME_API_BASE}/get")
        assert resp.status_code == 200
        assert resp.json()["level"] == 88
        assert mock_get.call_count == 3  # 被调用了3次
        print(f"    ✅ side_effect retry：第3次成功，共调用 {mock_get.call_count} 次")


# =============================================================
# Part 3：接口幂等性 + 并发测试
# =============================================================

print("\n" + "=" * 60)
print("  Day 13 - Part 3：幂等性 + 并发测试")
print("=" * 60)
print("""
📌 幂等性（Idempotency）

含义：同一请求执行 N 次，结果与执行 1 次相同。

方法对应规则：
  GET    → 天然幂等（读操作，不改变状态）
  PUT    → 幂等（覆盖更新，结果相同）
  DELETE → 幂等（多次删除同一资源，最终状态相同）
  POST   → 非幂等（每次创建新资源）
  PATCH  → 视情况而定

📌 并发测试

场景：多玩家同时登录、抢购道具、同时结算等。
工具：threading.Thread 并发发起请求，收集结果统计。
""")


class TestIdempotency:
    """幂等性测试"""

    def setup_method(self):
        self.api = BaseAPI()

    def test_get_is_idempotent(self):
        """GET 请求幂等性验证：多次请求结果一致"""
        results = []
        for i in range(3):
            resp = self.api.get("/get", params={"player_id": "p001"})
            AssertHelper.status_code(resp, 200)
            results.append(resp.json().get("args", {}))
            time.sleep(0.2)

        # 所有结果的 player_id 参数应一致
        player_ids = [r.get("player_id") for r in results]
        assert all(pid == "p001" for pid in player_ids), (
            f"GET 幂等性失败：{player_ids}"
        )
        print(f"    ✅ GET 幂等性: 3次请求结果一致，player_id 均为 p001")

    def test_put_is_idempotent(self):
        """PUT 请求幂等性：同样的数据更新 3 次，最终状态相同"""
        update_data = {"player_id": "p001", "nickname": "铁血战神", "level": 99}
        responses = []
        for i in range(3):
            resp = self.api.put("/put", json=update_data)
            AssertHelper.status_code(resp, 200)
            responses.append(resp.json().get("json", {}))
            time.sleep(0.2)

        # 每次 PUT 的 payload 相同
        for r in responses:
            assert r.get("nickname") == "铁血战神"
            assert r.get("level") == 99
        print(f"    ✅ PUT 幂等性: 3次更新，昵称和等级一致")

    def test_delete_is_idempotent(self):
        """DELETE 幂等性：删除同一资源 N 次，均为成功或 404（不会出现 5xx）"""
        results = []
        for i in range(3):
            resp = self.api.delete("/delete")
            # 第1次: 200（成功删除），后续: 可能 404（已删除）或 200
            assert resp.status_code in (200, 404), (
                f"DELETE 幂等性测试：期望 200/404，实际 {resp.status_code}"
            )
            results.append(resp.status_code)
            time.sleep(0.2)

        print(f"    ✅ DELETE 幂等性: {results}（均为200或404，无5xx）")

    def test_post_non_idempotent_note(self):
        """POST 非幂等：每次 POST 创建新资源（观察行为差异）"""
        created_ids = []
        for i in range(3):
            resp = self.api.post("/post", json={
                "action": "create_character",
                "name": f"英雄_{i}"
            })
            AssertHelper.status_code(resp, 200)
            data = resp.json()
            # httpbin 返回 url 固定，但真实系统每次 POST 会生成新 ID
            created_ids.append(data.get("json", {}).get("name"))
            time.sleep(0.2)

        # 每次创建的名字不同（模拟不同资源）
        assert len(set(created_ids)) == 3, "POST 应创建不同资源"
        print(f"    ✅ POST 非幂等（观察）: 创建了 {created_ids}")


class TestConcurrency:
    """并发测试"""

    def setup_method(self):
        self.results = []
        self.lock = threading.Lock()
        self.errors = []

    def _concurrent_request(self, thread_id: int, api: BaseAPI, path: str, data: dict):
        """线程任务：发起请求并记录结果"""
        try:
            start = time.time()
            resp = api.post(path, json=data)
            elapsed = time.time() - start
            with self.lock:
                self.results.append({
                    "thread_id": thread_id,
                    "status_code": resp.status_code,
                    "elapsed": round(elapsed, 3)
                })
        except Exception as e:
            with self.lock:
                self.errors.append(f"线程{thread_id}: {e}")

    def test_concurrent_login(self):
        """并发登录：5个玩家同时登录"""
        threads = []
        thread_count = 5

        for i in range(thread_count):
            api = BaseAPI()  # 每个线程用独立 Session
            t = threading.Thread(
                target=self._concurrent_request,
                args=(i, api, "/post", {
                    "action": "login",
                    "username": f"player_{i:03d}",
                    "password": "game_pass_123"
                })
            )
            threads.append(t)

        # 同时启动所有线程
        for t in threads:
            t.start()

        # 等待所有线程完成
        for t in threads:
            t.join(timeout=30)

        # 断言：无线程出错
        assert not self.errors, f"并发请求出错: {self.errors}"
        # 断言：所有请求都得到了响应
        assert len(self.results) == thread_count, (
            f"期望 {thread_count} 个响应，实际 {len(self.results)} 个"
        )
        # 断言：所有响应状态码为 200
        success_count = sum(1 for r in self.results if r["status_code"] == 200)
        assert success_count == thread_count, (
            f"并发登录失败，成功数: {success_count}/{thread_count}"
        )
        avg_time = sum(r["elapsed"] for r in self.results) / len(self.results)
        print(f"    ✅ 并发登录 {thread_count} 人: 全部成功，平均响应 {avg_time:.2f}s")

    def test_concurrent_item_purchase(self):
        """并发抢购：10个玩家同时购买同一道具（检查无数据异常）"""
        threads = []
        thread_count = 10

        for i in range(thread_count):
            api = BaseAPI()
            api.set_token(f"player_token_{i}")
            t = threading.Thread(
                target=self._concurrent_request,
                args=(i, api, "/post", {
                    "action": "buy_item",
                    "item_id": "dragon_sword_001",
                    "player_id": f"p{i:04d}",
                    "price": 9999
                })
            )
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        assert not self.errors, f"并发购买出错: {self.errors}"
        status_codes = [r["status_code"] for r in self.results]
        success = sum(1 for s in status_codes if s == 200)
        print(
            f"    ✅ 并发购买 {thread_count} 人: "
            f"成功 {success}/{thread_count}，"
            f"响应时间 min={min(r['elapsed'] for r in self.results):.2f}s "
            f"max={max(r['elapsed'] for r in self.results):.2f}s"
        )
        # 不要求全部 200，但不能有 500
        assert all(s != 500 for s in status_codes), "并发购买出现 500 错误！"


# =============================================================
# Part 4：自定义测试报告生成器
# =============================================================

print("\n" + "=" * 60)
print("  Day 13 - Part 4：自定义 Markdown 报告生成器")
print("=" * 60)
print("""
📌 Markdown 测试报告

目的：把 pytest 的执行结果整理成可读性更强的报告
格式：Markdown（可直接粘贴到 TAPD/飞书/Confluence）
内容：总通过/失败数、每条用例状态、耗时统计
""")


class TestReportGenerator:
    """测试报告生成器"""

    def setup_method(self):
        self.report_data = {
            "title": "山海之巅 — 接口测试报告 Day 13",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "cases": [],
            "start_time": time.time()
        }

    def _add_case(self, name: str, status: str, desc: str = "", elapsed: float = 0.0):
        self.report_data["cases"].append({
            "name": name,
            "status": status,  # PASS / FAIL / SKIP
            "desc": desc,
            "elapsed": elapsed
        })

    def _generate_report(self) -> str:
        data = self.report_data
        total = len(data["cases"])
        passed = sum(1 for c in data["cases"] if c["status"] == "PASS")
        failed = sum(1 for c in data["cases"] if c["status"] == "FAIL")
        skipped = sum(1 for c in data["cases"] if c["status"] == "SKIP")
        total_elapsed = time.time() - data["start_time"]

        lines = [
            f"# {data['title']}",
            f"",
            f"> 报告生成时间：{data['date']}",
            f"",
            f"## 执行摘要",
            f"",
            f"| 指标 | 数值 |",
            f"|------|------|",
            f"| 总用例数 | {total} |",
            f"| ✅ 通过 | {passed} |",
            f"| ❌ 失败 | {failed} |",
            f"| ⏭️ 跳过 | {skipped} |",
            f"| 通过率 | {passed/total*100:.1f}% |" if total > 0 else "| 通过率 | N/A |",
            f"| 总耗时 | {total_elapsed:.2f}s |",
            f"",
            f"## 用例详情",
            f"",
            f"| # | 用例名称 | 状态 | 耗时(s) | 描述 |",
            f"|---|---------|------|---------|------|",
        ]

        status_icon = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭️"}
        for i, case in enumerate(data["cases"], 1):
            icon = status_icon.get(case["status"], "❓")
            lines.append(
                f"| {i} | {case['name']} | {icon} {case['status']} "
                f"| {case['elapsed']:.2f} | {case['desc']} |"
            )

        lines += [
            f"",
            f"---",
            f"*报告由 Day 13 自动化测试框架生成*",
        ]
        return "\n".join(lines)

    def test_generate_markdown_report(self):
        """生成 Markdown 格式测试报告"""
        # 模拟收集测试结果
        test_cases = [
            ("test_login_normal", "PASS", "正常登录流程", 0.32),
            ("test_login_wrong_password", "PASS", "错误密码返回401", 0.28),
            ("test_login_sql_injection", "PASS", "SQL注入防护", 0.41),
            ("test_player_info", "PASS", "获取玩家信息", 0.35),
            ("test_player_update_nickname", "PASS", "更新昵称", 0.29),
            ("test_combat_start", "PASS", "开始战斗", 0.38),
            ("test_combat_skill", "PASS", "使用技能", 0.31),
            ("test_combat_settlement", "PASS", "战斗结算", 0.44),
            ("test_admin_ban_user", "SKIP", "管理员封号（权限不足，跳过）", 0.0),
            ("test_server_maintenance", "SKIP", "维护期测试（环境限制）", 0.0),
        ]

        for name, status, desc, elapsed in test_cases:
            self._add_case(name, status, desc, elapsed)

        report = self._generate_report()

        # 验证报告格式
        assert "# 山海之巅" in report
        assert "执行摘要" in report
        assert "用例详情" in report
        assert "✅ PASS" in report
        assert "⏭️ SKIP" in report

        # 写入文件
        report_path = "c:/Users/Administrator/WorkBuddy/Claw/test_report_day13.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"    ✅ Markdown 报告生成成功: {report_path}")
        print(f"    📊 共 {len(test_cases)} 条用例，8 PASS / 2 SKIP")

        # 打印报告摘要到控制台
        lines = report.split("\n")
        for line in lines[:20]:
            print(f"       {line}")


# =============================================================
# Part 5：综合回归实战（全模块串联）
# =============================================================

print("\n" + "=" * 60)
print("  Day 13 - Part 5：综合回归实战")
print("=" * 60)
print("""
📌 回归测试目标

覆盖山海之巅 3 大核心模块：
  ① Login  → 登录/注销/鉴权
  ② Player → 玩家信息/背包/战力
  ③ Combat → 战斗/技能/结算

串联依赖链：
  Login → token → Player(get_info) → character_id
       → Player(get_inventory) → item_id
       → Combat(start_battle) → battle_id
       → Combat(use_skill)
       → Combat(settlement)
""")


class TestRegressionSuite:
    """综合回归测试套件"""

    @pytest.fixture(scope="class")
    def game_session(self):
        """class 级别 fixture：整个测试类共用一个 session"""
        api = BaseAPI()
        api.set_token("regression_token_day13_xyz")
        yield api
        api.clear_token()

    @pytest.fixture(scope="class")
    def test_context(self):
        """共享测试上下文（存储跨用例依赖数据）"""
        ctx = {
            "token": None,
            "player_id": "test_player_day13",
            "character_id": "char_day13_001",
            "item_id": None,
            "battle_id": None,
        }
        yield ctx

    # ---- Login 模块回归 ----
    def test_01_login_success(self, game_session, test_context):
        """[回归-Login-01] 正常登录"""
        t0 = time.time()
        resp = game_session.post("/post", json={
            "username": "regression_tester",
            "password": "pass_day13",
            "platform": "PC"
        })
        elapsed = time.time() - t0

        AssertHelper.status_code(resp, 200)
        AssertHelper.response_time_ok(resp, 3.0)
        data = resp.json()
        assert "json" in data

        # 保存 token 到上下文
        test_context["token"] = "mocked_token_" + hashlib.md5(b"regression").hexdigest()[:8]
        print(f"    ✅ [Login-01] 登录成功，耗时 {elapsed:.2f}s，token已存储")

    def test_02_login_wrong_password(self, game_session):
        """[回归-Login-02] 错误密码"""
        resp = game_session.post("/post", json={
            "username": "regression_tester",
            "password": "WRONG_PASSWORD",
            "expected_result": "401"
        })
        # httpbin 总是200，真实测试需断言 401
        assert resp.status_code in (200, 401)
        print(f"    ✅ [Login-02] 错误密码场景验证，status={resp.status_code}")

    def test_03_login_sql_injection(self, game_session):
        """[回归-Login-03] SQL 注入防护"""
        resp = game_session.post("/post", json={
            "username": "' OR '1'='1",
            "password": "anything"
        })
        assert resp.status_code not in (500,), "SQL 注入导致服务器崩溃！"
        print(f"    ✅ [Login-03] SQL 注入防护，status={resp.status_code}")

    # ---- Player 模块回归 ----
    def test_04_get_player_info(self, game_session, test_context):
        """[回归-Player-04] 获取玩家信息"""
        t0 = time.time()
        resp = game_session.get("/get", params={
            "player_id": test_context["player_id"],
            "include_stats": "true"
        })
        elapsed = time.time() - t0

        AssertHelper.status_code(resp, 200)
        AssertHelper.response_time_ok(resp, 3.0)
        data = resp.json()
        assert "args" in data
        assert data["args"].get("player_id") == test_context["player_id"]
        print(f"    ✅ [Player-04] 获取玩家信息，耗时 {elapsed:.2f}s")

    def test_05_update_player_nickname(self, game_session, test_context):
        """[回归-Player-05] 更新玩家昵称"""
        new_name = "回归测试英雄"
        resp = game_session.put("/put", json={
            "player_id": test_context["player_id"],
            "nickname": new_name,
            "character_id": test_context["character_id"]
        })
        AssertHelper.status_code(resp, 200)
        data = resp.json()
        assert data.get("json", {}).get("nickname") == new_name
        print(f"    ✅ [Player-05] 昵称更新为 '{new_name}'")

    def test_06_get_inventory(self, game_session, test_context):
        """[回归-Player-06] 获取背包列表"""
        resp = game_session.get("/get", params={
            "character_id": test_context["character_id"],
            "page": 1,
            "limit": 20
        })
        AssertHelper.status_code(resp, 200)
        data = resp.json()
        assert data["args"]["character_id"] == test_context["character_id"]

        # 存储第一个道具 ID 供 Combat 模块使用
        test_context["item_id"] = "item_sword_golden_001"
        print(f"    ✅ [Player-06] 背包查询成功，item_id={test_context['item_id']}")

    def test_07_player_invalid_token(self):
        """[回归-Player-07] 无效 token 访问"""
        bad_api = BaseAPI()
        bad_api.set_token("totally_invalid_token_xyz")
        resp = bad_api.get("/bearer")
        # /bearer 端点对非 Bearer 格式 token 返回 401
        # 对我们的格式它实际上认可 Bearer 前缀，返回200
        assert resp.status_code in (200, 401, 403)
        print(f"    ✅ [Player-07] 无效 token 处理，status={resp.status_code}")

    # ---- Combat 模块回归 ----
    def test_08_start_battle(self, game_session, test_context):
        """[回归-Combat-08] 开始战斗"""
        resp = game_session.post("/post", json={
            "action": "start_battle",
            "character_id": test_context["character_id"],
            "monster_id": "boss_dragon_elite",
            "map_id": "dungeon_001",
            "difficulty": "hard"
        })
        AssertHelper.status_code(resp, 200)
        data = resp.json()

        # 存储 battle_id 供后续步骤使用
        test_context["battle_id"] = "battle_day13_" + hashlib.md5(
            test_context["character_id"].encode()
        ).hexdigest()[:8]
        print(f"    ✅ [Combat-08] 战斗开始，battle_id={test_context['battle_id']}")

    def test_09_use_skill(self, game_session, test_context):
        """[回归-Combat-09] 使用技能"""
        assert test_context["battle_id"], "battle_id 未设置，依赖 test_08 先执行"
        resp = game_session.post("/post", json={
            "action": "use_skill",
            "battle_id": test_context["battle_id"],
            "skill_id": "flame_strike_lv5",
            "target": "boss_dragon_elite",
            "item_id": test_context["item_id"]
        })
        AssertHelper.status_code(resp, 200)
        data = resp.json()
        payload = data.get("json", {})
        assert payload.get("skill_id") == "flame_strike_lv5"
        print(f"    ✅ [Combat-09] 技能 'flame_strike_lv5' 释放成功")

    def test_10_battle_settlement(self, game_session, test_context):
        """[回归-Combat-10] 战斗结算"""
        assert test_context["battle_id"], "battle_id 未设置"
        resp = game_session.post("/post", json={
            "action": "battle_settlement",
            "battle_id": test_context["battle_id"],
            "result": "victory",
            "exp_gained": 2400,
            "items_dropped": ["dragon_scale", "rare_gem"],
            "gold_gained": 9999
        })
        AssertHelper.status_code(resp, 200)
        data = resp.json()
        payload = data.get("json", {})
        assert payload.get("result") == "victory"
        assert payload.get("exp_gained") == 2400
        assert "dragon_scale" in payload.get("items_dropped", [])
        print(f"    ✅ [Combat-10] 战斗结算: 胜利，获得 {payload['exp_gained']} 经验，{payload['gold_gained']} 金币")

    def test_11_duplicate_settlement(self, game_session, test_context):
        """[回归-Combat-11] 重复结算（幂等性验证）"""
        # 同一 battle_id 第二次结算，真实系统应返回 400（已结算）
        resp = game_session.post("/post", json={
            "action": "battle_settlement",
            "battle_id": test_context["battle_id"],
            "result": "victory",
            "_note": "重复结算测试"
        })
        # httpbin 总是200，真实系统应返回 400 "battle already settled"
        assert resp.status_code in (200, 400), (
            f"重复结算应返回 200 或 400，实际 {resp.status_code}"
        )
        print(f"    ✅ [Combat-11] 重复结算验证，status={resp.status_code}（真实系统应为400）")

    def test_12_regression_summary(self, game_session, test_context):
        """[回归-汇总-12] 依赖链数据完整性验证"""
        assert test_context["token"] is not None, "token 为空"
        assert test_context["player_id"], "player_id 为空"
        assert test_context["character_id"], "character_id 为空"
        assert test_context["item_id"], "item_id 为空"
        assert test_context["battle_id"], "battle_id 为空"

        print(f"\n    📊 [回归汇总] 完整依赖链验证：")
        print(f"       token:        {test_context['token']}")
        print(f"       player_id:    {test_context['player_id']}")
        print(f"       character_id: {test_context['character_id']}")
        print(f"       item_id:      {test_context['item_id']}")
        print(f"       battle_id:    {test_context['battle_id']}")
        print(f"    ✅ 全流程依赖链完整，Login→Player→Combat 串联成功！")


# =============================================================
# 主程序入口（直接运行时展示知识点）
# =============================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  Day 13 知识点总览")
    print("=" * 60)
    print("""
📌 今日核心知识点回顾

┌──────────────────┬────────────────────────────────────────┐
│ 模块              │ 掌握内容                                │
├──────────────────┼────────────────────────────────────────┤
│ Part 1 安全测试  │ Token鉴权 / 越权检测 / 注入防护         │
│ Part 2 Mock      │ patch / MagicMock / side_effect         │
│ Part 3 并发幂等  │ threading / 幂等性验证 / 竞态检测        │
│ Part 4 报告生成  │ Markdown报告 / 自定义数据收集            │
│ Part 5 回归实战  │ Login+Player+Combat 12个用例串联        │
└──────────────────┴────────────────────────────────────────┘

📌 常用命令速查

  # 运行所有测试
  python -m pytest requests_day13.py -v

  # 只跑安全测试
  python -m pytest requests_day13.py -v -k "Security"

  # 只跑回归测试
  python -m pytest requests_day13.py -v -k "Regression"

  # 只跑 Mock 测试
  python -m pytest requests_day13.py -v -k "Mock"

  # 跳过并发测试（节省时间）
  python -m pytest requests_day13.py -v -k "not Concurrency"

  # 生成 HTML 报告
  python -m pytest requests_day13.py -v --html=report_day13.html
""")

    print("\n运行 pytest 查看完整测试结果：")
    print("  python -m pytest requests_day13.py -v -s")
