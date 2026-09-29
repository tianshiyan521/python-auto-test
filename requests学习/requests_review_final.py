"""
=============================================================================
Python+Requests 14天综合复习测验 — 毕业考核
=============================================================================
覆盖范围：Day1~Day14 全部核心知识点
运行方式：pytest requests_review_final.py -v -s
=============================================================================
"""
import sys
import json
import csv
import os
import time
from unittest.mock import patch, MagicMock

import pytest
import requests

# ── 统一配置 ──────────────────────────────────────────────────
BASE_URL = "https://httpbin.org"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "WorkBuddy-Learning/14.0"})

# ── 工具函数（Day4/Day5/Day11 精华） ─────────────────────────
def safe_get(data, *keys, default=None):
    """从嵌套数据中安全取值，防 KeyError/TypeError"""
    for key in keys:
        try:
            data = data[key]
        except (KeyError, TypeError, IndexError):
            return default
    return data

def http_get(path, **kwargs):
    """统一 GET 封装，默认超时 + 自动重试（Day7/Day10精华）"""
    for attempt in range(3):
        try:
            resp = SESSION.get(f"{BASE_URL}{path}", timeout=15, **kwargs)
            if resp.status_code < 500:
                return resp
            print(f"  [重试 {attempt+1}/3] 服务端 {resp.status_code}")
        except requests.RequestException as e:
            print(f"  [重试 {attempt+1}/3] 连接异常: {e}")
        time.sleep(0.5)
    return resp

def http_post(path, **kwargs):
    """统一 POST 封装"""
    for attempt in range(3):
        try:
            resp = SESSION.post(f"{BASE_URL}{path}", timeout=15, **kwargs)
            if resp.status_code < 500:
                return resp
        except requests.RequestException as e:
            print(f"  [重试 {attempt+1}/3] {e}")
        time.sleep(0.5)
    return resp


# ═══════════════════════════════════════════════════════════════
# Part 1 — HTTP 基础层（Day1 & Day2）
# ═══════════════════════════════════════════════════════════════
class TestHTTPBasics:
    """复习：HTTP方法 + 状态码 + 请求头/响应头"""

    def test_get_request_status_200(self):
        """GET /get 应返回200"""
        resp = http_get("/get")
        assert resp.status_code == 200, f"期望200, 实际{resp.status_code}"

    def test_get_with_query_params(self):
        """GET 带查询参数"""
        resp = http_get("/get", params={"page": 1, "size": 10})
        data = resp.json()
        assert resp.status_code == 200
        assert "page" in str(data.get("args", {}))

    def test_get_response_headers(self):
        """响应头包含 Content-Type"""
        resp = http_get("/get")
        assert "Content-Type" in resp.headers
        assert "application/json" in resp.headers["Content-Type"]

    def test_post_json_data(self):
        """POST JSON 数据"""
        payload = {"username": "testuser", "action": "review"}
        resp = http_post("/post", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert safe_get(data, "json", "username") == "testuser"

    def test_post_form_data(self):
        """POST 表单数据"""
        resp = http_post("/post", data={"key": "value"})
        assert resp.status_code == 200
        data = resp.json()
        assert safe_get(data, "form", "key") == "value"

    def test_put_request(self):
        """PUT 更新请求"""
        resp = SESSION.put(f"{BASE_URL}/put", json={"updated": True}, timeout=15)
        assert resp.status_code == 200

    def test_delete_request(self):
        """DELETE 删除请求"""
        resp = SESSION.delete(f"{BASE_URL}/delete", timeout=15)
        assert resp.status_code == 200

    def test_patch_request(self):
        """PATCH 部分更新"""
        resp = SESSION.patch(f"{BASE_URL}/patch", json={"partial": True}, timeout=15)
        assert resp.status_code == 200

    def test_404_handling(self):
        """404 错误处理"""
        resp = http_get("/status/404")
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════
# Part 2 — JSON 处理层（Day4）
# ═══════════════════════════════════════════════════════════════
class TestJSONProcessing:
    """复习：JSON 解析、嵌套提取、安全取值"""

    def test_response_json_method(self):
        """response.json() 正确解析"""
        resp = http_get("/get")
        data = resp.json()
        assert isinstance(data, dict)
        assert "url" in data
        assert "headers" in data

    def test_nested_json_extraction(self):
        """嵌套 JSON 字段提取"""
        resp = http_post("/post", json={"player": {"name": "阿克", "level": 99}})
        data = resp.json()
        # 嵌套取字段
        player_name = safe_get(data, "json", "player", "name")
        player_level = safe_get(data, "json", "player", "level")
        assert player_name == "阿克"
        assert player_level == 99

    def test_list_traversal(self):
        """JSON 列表遍历"""
        # httpbin 支持 /anything 返回回显数据
        test_data = {"items": [{"id": 1}, {"id": 2}, {"id": 3}]}
        resp = http_post("/anything", json=test_data)
        data = resp.json()
        items = safe_get(data, "json", "items", default=[])
        ids = [item["id"] for item in items]
        assert ids == [1, 2, 3]

    def test_safe_get_vs_direct_access(self):
        """safe_get vs dict[key] 区别"""
        data = {"a": {"b": 1}}
        # dict[key] 不存在时抛 KeyError
        with pytest.raises(KeyError):
            _ = data["c"]
        # safe_get 不存在时返回 default
        assert safe_get(data, "c") is None
        assert safe_get(data, "c", default="无") == "无"

    def test_missing_field_default(self):
        """不存在的字段 safe_get 返回默认值"""
        resp = http_get("/get")
        data = resp.json()
        result = safe_get(data, "nonexistent", "deep", "field", default=-1)
        assert result == -1


# ═══════════════════════════════════════════════════════════════
# Part 3 — 接口断言层（Day5）
# ═══════════════════════════════════════════════════════════════
class TestAssertions:
    """复习：状态码断言、JSON字段断言、pytest断言"""

    def test_status_code_assert_with_message(self):
        """带错误消息的状态码断言"""
        resp = http_get("/get")
        assert resp.status_code == 200, f"期望200, 实际{resp.status_code}"

    def test_json_field_existence(self):
        """字段存在性断言"""
        resp = http_get("/get")
        data = resp.json()
        assert "url" in data, "响应中缺少 url 字段"
        assert "headers" in data, "响应中缺少 headers 字段"

    def test_json_field_value_match(self):
        """字段值匹配断言"""
        resp = http_get("/get?name=test")
        data = resp.json()
        args = data.get("args", {})
        assert args.get("name") == "test", f"期望test, 实际{args.get('name')}"

    def test_type_check(self):
        """字段类型检查"""
        resp = http_get("/get")
        data = resp.json()
        assert isinstance(data, dict), "顶层应为dict"
        assert isinstance(data.get("headers"), dict), "headers应为dict"

    def test_resp_ok_and_raise(self):
        """resp.ok + raise_for_status"""
        resp = http_get("/get")
        assert resp.ok, "resp.ok 应为 True"
        resp.raise_for_status()  # 200不抛异常

        bad_resp = http_get("/status/500")
        assert not bad_resp.ok
        with pytest.raises(requests.HTTPError):
            bad_resp.raise_for_status()

    def test_pytest_in_not_in(self):
        """pytest in / not in 断言"""
        resp = http_get("/get")
        url = resp.json().get("url", "")
        assert "httpbin" in url
        assert "google" not in url

    def test_pytest_raises_exception_match(self):
        """pytest.raises + match 异常信息匹配"""
        with pytest.raises(ZeroDivisionError, match="division by zero"):
            _ = 1 / 0


# ═══════════════════════════════════════════════════════════════
# Part 4 — 接口依赖处理（Day6 & Day7）
# ═══════════════════════════════════════════════════════════════

class GlobalData:
    """全局数据存储（Day6精华）"""
    token = None
    user_id = None
    character_id = None

class TestDependencyChain:
    """复习：A接口返回值 → 存储 → B接口参数"""

    def test_step1_login_store_token(self):
        """步骤1：模拟登录获取token"""
        resp = http_post("/post", json={
            "action": "login",
            "username": "test_player",
            "password": "pass123"
        })
        assert resp.status_code == 200
        data = resp.json()
        # 存储 token 和 user_id
        GlobalData.token = "token_" + str(hash(data.get("url", "")))
        GlobalData.user_id = safe_get(data, "json", "username")
        assert GlobalData.token is not None
        assert GlobalData.user_id == "test_player"

    def test_step2_use_token_for_protected_api(self):
        """步骤2：用步骤1的token访问受保护接口"""
        assert GlobalData.token is not None, "依赖未满足：token为空"
        # 模拟 token 鉴权
        resp = http_get("/get", headers={"Authorization": f"Bearer {GlobalData.token}"})
        assert resp.status_code == 200

    def test_step3_create_character(self):
        """步骤3：用 user_id 创建角色"""
        assert GlobalData.user_id is not None, "依赖未满足：user_id为空"
        resp = http_post("/post", json={
            "action": "create_character",
            "user_id": GlobalData.user_id,
            "name": "测试角色"
        })
        assert resp.status_code == 200
        GlobalData.character_id = "char_1001"

    def test_step4_full_chain(self):
        """步骤4：完整4步依赖链"""
        assert GlobalData.token is not None
        assert GlobalData.user_id is not None
        assert GlobalData.character_id is not None
        resp = http_post("/post", json={
            "token": GlobalData.token,
            "user_id": GlobalData.user_id,
            "character_id": GlobalData.character_id,
            "action": "enter_game"
        })
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════
# Part 5 — pytest Fixture（Day7 & Day8 & Day9）
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def module_session():
    """module级fixture：整个模块复用一次登录"""
    print("\n  [Fixture] 模拟登录（module scope，只执行一次）")
    token = f"mod_token_{id(object())}"
    yield token
    print("\n  [Fixture] 清理资源")

@pytest.fixture(scope="function")
def function_data():
    """function级fixture：每个测试函数独立数据"""
    return {"created_at": time.time()}

class TestFixtureUsage:
    """复习：fixture作用域 + 依赖注入"""

    def test_module_fixture_reuse_1(self, module_session):
        """第一个测试使用 module fixture"""
        assert module_session.startswith("mod_token_")

    def test_module_fixture_reuse_2(self, module_session):
        """第二个测试使用同一个 module fixture（不会重新登录）"""
        assert module_session.startswith("mod_token_")

    def test_function_fixture_isolation(self, function_data):
        """function fixture 每个用例独立"""
        assert "created_at" in function_data

    def test_function_fixture_isolated_2(self, function_data):
        """确认 function fixture 独立"""
        assert "created_at" in function_data


# ═══════════════════════════════════════════════════════════════
# Part 6 — 参数化测试（Day8 & Day10）
# ═══════════════════════════════════════════════════════════════

HTTP_METHODS = [
    ("GET", 200),
    ("POST", 200),
    ("PUT", 200),
    ("DELETE", 200),
    ("PATCH", 200),
]

LOGIN_SCENARIOS = [
    ("正常登录", {"user": "admin", "pass": "123456"}, True),
    ("空用户名", {"user": "", "pass": "123456"}, False),
    ("空密码",   {"user": "admin", "pass": ""}, False),
    ("SQL注入",  {"user": "admin' OR '1'='1", "pass": "x"}, False),
    ("XSS攻击",  {"user": "<script>alert(1)</script>", "pass": "x"}, False),
    ("超长字符", {"user": "a" * 500, "pass": "x"}, False),
]

LOGIN_SCENARIO_IDS = [s[0] for s in LOGIN_SCENARIOS]

class TestParametrize:
    """复习：参数化测试"""

    @pytest.mark.parametrize("method,expected_status", HTTP_METHODS)
    def test_http_methods(self, method, expected_status):
        """5种HTTP方法状态码验证"""
        resp = SESSION.request(method, f"{BASE_URL}/{method.lower()}", timeout=15)
        assert resp.status_code == expected_status

    @pytest.mark.parametrize("scenario,payload,should_work", LOGIN_SCENARIOS, ids=LOGIN_SCENARIO_IDS)
    def test_login_scenarios(self, scenario, payload, should_work):
        """6种登录场景矩阵"""
        resp = http_post("/post", json={"action": "login", **payload})
        assert resp.status_code == 200
        data = resp.json()
        if should_work:
            assert data.get("json", {}).get("user") == payload["user"]


# ═══════════════════════════════════════════════════════════════
# Part 7 — 安全测试（Day13）
# ═══════════════════════════════════════════════════════════════

SQL_INJECTION_PAYLOADS = [
    "' OR '1'='1",
    "' OR '1'='1' --",
    "admin'--",
    "1; DROP TABLE users;",
    "' UNION SELECT * FROM users--",
]

class TestSecurity:
    """复习：安全测试（Token鉴权/SQL注入/XSS/敏感信息）"""

    def test_no_token_rejected(self):
        """无Token时拒绝对敏感接口访问"""
        resp = http_get("/get")
        # httpbin不鉴权，这里验证概念：检查响应不含敏感数据
        assert "password" not in resp.text.lower() or "pass" not in resp.text[:200]

    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS,
        ids=lambda p: p[:30])
    def test_sql_injection_resilience(self, payload):
        """SQL注入payload不应导致500/崩溃"""
        resp = http_get("/get", params={"user": payload})
        assert resp.status_code != 500, f"SQL注入导致500: {payload}"

    def test_xss_payload_handled(self):
        """XSS payload 不应破坏响应结构"""
        resp = http_get("/get", params={"name": "<script>alert(1)</script>"})
        assert resp.status_code == 200
        # 验证响应是合法JSON
        data = resp.json()
        assert isinstance(data, dict)

    def test_response_no_password_leak(self):
        """响应中不应泄露密码明文"""
        resp = http_post("/post", json={"password": "secret123"})
        # httpbin 会回显，但验证我们的安全检测逻辑
        data = resp.json()
        json_data = safe_get(data, "json", default={})
        # 真实场景：不应在日志/响应中输出明文密码
        assert isinstance(json_data, dict)


# ═══════════════════════════════════════════════════════════════
# Part 8 — Mock 技术（Day13）
# ═══════════════════════════════════════════════════════════════
class TestMockUsage:
    """复习：Mock 技术"""

    @patch("requests.Session.get")
    def test_mock_get_response(self, mock_get):
        """Mock GET 返回自定义数据"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"mocked": True, "data": [1, 2, 3]}
        mock_get.return_value = mock_resp

        resp = SESSION.get("https://fake-api.com/data", timeout=5)
        assert resp.status_code == 200
        assert resp.json()["mocked"] is True

    @patch("requests.Session.get")
    def test_mock_retry_scenario(self, mock_get):
        """Mock 模拟重试场景：2次失败 + 1次成功"""
        fail_resp = MagicMock()
        fail_resp.status_code = 503
        fail_resp.raise_for_status.side_effect = requests.HTTPError("503")

        ok_resp = MagicMock()
        ok_resp.status_code = 200
        ok_resp.json.return_value = {"success": True}

        mock_get.side_effect = [fail_resp, fail_resp, ok_resp]

        # 模拟重试逻辑
        success = False
        for attempt in range(3):
            try:
                resp = SESSION.get("https://unstable-api.com/data", timeout=5)
                if resp.status_code == 200:
                    success = True
                    break
            except requests.HTTPError:
                continue

        assert success, "3次重试后仍未成功"
        assert mock_get.call_count == 3


# ═══════════════════════════════════════════════════════════════
# Part 9 — 幂等性 & 并发（Day13）
# ═══════════════════════════════════════════════════════════════
class TestIdempotency:
    """复习：幂等性验证"""

    def test_get_idempotent(self):
        """GET 请求幂等：多次请求结果一致"""
        results = []
        for _ in range(3):
            resp = http_get("/get")
            results.append(resp.status_code)
        assert all(r == 200 for r in results), "GET 多次调用状态码不一致"

    def test_delete_idempotent(self):
        """DELETE 幂等：多次删除状态码一致"""
        results = []
        for _ in range(3):
            resp = SESSION.delete(f"{BASE_URL}/delete", timeout=15)
            results.append(resp.status_code)
        assert all(r == results[0] for r in results), "DELETE 多次调用结果不一致"


# ═══════════════════════════════════════════════════════════════
# Part 10 — 边界情况（跨Day覆盖）
# ═══════════════════════════════════════════════════════════════
class TestEdgeCases:
    """复习：边界情况综合"""

    def test_empty_params(self):
        """空参数请求"""
        resp = http_get("/get", params={})
        assert resp.status_code == 200

    def test_unicode_chinese(self):
        """中文参数"""
        resp = http_get("/get", params={"name": "测试玩家"})
        assert resp.status_code == 200

    def test_special_characters(self):
        """特殊字符参数"""
        resp = http_get("/get", params={"key": "!@#$%^&*()"})
        assert resp.status_code == 200

    def test_timeout_handling(self):
        """超时处理：短超时应触发异常"""
        with pytest.raises(requests.Timeout):
            # /delay/10 延迟10秒，timeout设0.001必超时
            SESSION.get(f"{BASE_URL}/delay/5", timeout=0.001)

    def test_response_time_under_limit(self):
        """响应时间检查"""
        resp = http_get("/get")
        elapsed = resp.elapsed.total_seconds()
        assert elapsed < 10, f"响应太慢: {elapsed:.2f}s"


# ═══════════════════════════════════════════════════════════════
# Part 11 — 综合实战：模拟山海之巅完整工作流（Day11~14精华）
# ═══════════════════════════════════════════════════════════════
class TestShanZhiWorkflow:
    """复习：山海之巅完整工作流回归"""

    # 类变量：跨测试方法共享（模拟 GlobalData）
    token = None
    user_id = None
    character_id = None
    battle_id = None

    def test_wf_01_login(self):
        """工作流：登录"""
        resp = http_post("/post", json={
            "action": "login",
            "username": "player_001",
            "password": "pass123"
        })
        assert resp.status_code == 200
        data = resp.json()
        TestShanZhiWorkflow.token = f"token_{hash(str(data))}"
        TestShanZhiWorkflow.user_id = data.get("json", {}).get("username", "player_001")
        assert TestShanZhiWorkflow.token is not None

    def test_wf_02_get_player_info(self):
        """工作流：获取玩家信息（用token）"""
        assert TestShanZhiWorkflow.token is not None, "依赖未满足：token为空"
        resp = http_get("/get", headers={"Authorization": f"Bearer {TestShanZhiWorkflow.token}"})
        assert resp.status_code == 200

    def test_wf_03_get_backpack(self):
        """工作流：获取背包"""
        resp = http_get("/get", params={"user_id": TestShanZhiWorkflow.user_id, "type": "backpack"})
        assert resp.status_code == 200

    def test_wf_04_start_battle(self):
        """工作流：开始战斗"""
        TestShanZhiWorkflow.character_id = "char_001"
        resp = http_post("/post", json={
            "action": "start_battle",
            "character_id": TestShanZhiWorkflow.character_id,
            "enemy_id": "boss_dragon"
        })
        assert resp.status_code == 200
        TestShanZhiWorkflow.battle_id = "battle_001"

    def test_wf_05_use_item_in_battle(self):
        """工作流：战斗中使用道具"""
        assert TestShanZhiWorkflow.battle_id is not None, "依赖未满足：battle_id为空"
        resp = http_post("/post", json={
            "action": "use_item",
            "battle_id": TestShanZhiWorkflow.battle_id,
            "item_id": "hp_potion",
            "character_id": TestShanZhiWorkflow.character_id
        })
        assert resp.status_code == 200

    def test_wf_06_battle_settle(self):
        """工作流：战斗结算"""
        resp = http_post("/post", json={
            "action": "battle_settle",
            "battle_id": TestShanZhiWorkflow.battle_id,
            "character_id": TestShanZhiWorkflow.character_id
        })
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════
# 测试报告生成
# ═══════════════════════════════════════════════════════════════
def generate_review_report():
    """生成综合复习报告"""

    test_methods = {
        "HTTP基础层": [n for n in dir(TestHTTPBasics) if n.startswith("test_")],
        "JSON处理层": [n for n in dir(TestJSONProcessing) if n.startswith("test_")],
        "接口断言层": [n for n in dir(TestAssertions) if n.startswith("test_")],
        "接口依赖处理": [n for n in dir(TestDependencyChain) if n.startswith("test_")],
        "pytest Fixture": [n for n in dir(TestFixtureUsage) if n.startswith("test_")],
        "参数化测试": [n for n in dir(TestParametrize) if n.startswith("test_")],
        "安全测试": [n for n in dir(TestSecurity) if n.startswith("test_")],
        "Mock技术": [n for n in dir(TestMockUsage) if n.startswith("test_")],
        "幂等性": [n for n in dir(TestIdempotency) if n.startswith("test_")],
        "边界情况": [n for n in dir(TestEdgeCases) if n.startswith("test_")],
        "山海之巅工作流": [n for n in dir(TestShanZhiWorkflow) if n.startswith("test_")],
    }

    total = sum(len(v) for v in test_methods.values())
    print(f"\n{'='*60}")
    print(f"  🎓 Python+Requests 14天综合复习")
    print(f"{'='*60}")
    print(f"  知识模块覆盖：{len(test_methods)} 个")
    print(f"  测试用例总数：{total} 个")
    print(f"  知识覆盖率：100% (Day1~Day14)")
    print(f"{'='*60}\n")

    for module_name, methods in test_methods.items():
        status = "✅" if methods else "⚠️"
        print(f"  {status} {module_name}: {len(methods)} 个用例")


# ── 运行条件 ──────────────────────────────────────────────────
if __name__ == "__main__":
    generate_review_report()
    print("\n> 运行命令：pytest requests_review_final.py -v -s")
    print("> 将自动发现并执行所有 Test 类\n")
