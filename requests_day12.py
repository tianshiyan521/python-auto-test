# =============================================================
# Python + Requests 14天学习计划 - Day 12
# 主题：项目实战 Day 2 — Player玩家模块 + Combat战斗模块
# 日期：2026-05-27
# =============================================================

"""
Day 12 学习大纲
===============
Part 1：Player 玩家模块测试（10个用例）
    - 获取玩家信息（依赖 token）
    - 更新玩家昵称
    - 获取背包列表
    - 背包道具详情
    - 玩家战力查询
    - 各种异常场景（token无效、越权等）

Part 2：Combat 战斗模块测试（10个用例）
    - 开始战斗（依赖 token + character_id）
    - 使用技能
    - 战斗结算
    - 超时处理
    - 各种异常场景（战斗中断、重复结算等）

Part 3：多模块 Fixture 依赖链
    - conftest.py 中 session scope fixture 复用
    - 登录 → 获取角色 → 战斗 全流程依赖

Part 4：接口依赖处理综合实战
    - A接口返回值 → B接口参数 → C接口参数
    - 完整的 5步游戏业务流程测试
"""

import requests
import json
import time
import os
import random
import string
import pytest
from datetime import datetime


# ── 模拟后端（用 httpbin.org 承接所有真实HTTP请求）──────────
BASE_URL = "https://httpbin.org"


# =============================================================
# 复用 Day 11 的工具类（真实项目中这些在 lib/ 目录下）
# =============================================================

class BaseAPI:
    """统一请求封装（复用 Day 11，真实项目放 lib/base_api.py）"""

    def __init__(self, base_url=BASE_URL, timeout=15, max_retries=3):
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "ShanZhiTestFramework/1.0",
        })

    def _log(self, method, url, code=None, elapsed=None):
        if code:
            print(f"  [HTTP] {method} {url} → {code} ({elapsed:.2f}s)")
        else:
            print(f"  [HTTP] {method} {url}")

    def _request(self, method, path, **kwargs):
        url = f"{self.base_url}{path}"
        kwargs.setdefault("timeout", self.timeout)
        for attempt in range(1, self.max_retries + 1):
            try:
                start = time.time()
                resp = self.session.request(method, url, **kwargs)
                elapsed = time.time() - start
                self._log(method, url, resp.status_code, elapsed)
                if resp.status_code >= 500 and attempt < self.max_retries:
                    print(f"  [重试] 第{attempt}次 {resp.status_code}，重试...")
                    time.sleep(1)
                    continue
                return resp
            except (requests.ConnectionError, requests.Timeout) as e:
                if attempt < self.max_retries:
                    print(f"  [重试] 第{attempt}次连接异常，重试...")
                    time.sleep(1)
                    continue
                raise

    def get(self, path, params=None, **kwargs):
        return self._request("GET", path, params=params, **kwargs)

    def post(self, path, json_data=None, **kwargs):
        return self._request("POST", path, json=json_data, **kwargs)

    def put(self, path, json_data=None, **kwargs):
        return self._request("PUT", path, json=json_data, **kwargs)

    def delete(self, path, **kwargs):
        return self._request("DELETE", path, **kwargs)

    def add_header(self, key, value):
        self.session.headers[key] = value

    def remove_header(self, key):
        self.session.headers.pop(key, None)

    def close(self):
        self.session.close()


class AssertHelper:
    """断言工具类（复用 Day 11，真实项目放 lib/assert_helper.py）"""

    @staticmethod
    def assert_status_code(resp, expected=200, msg=""):
        actual = resp.status_code
        hint = f" — {msg}" if msg else ""
        assert actual == expected, \
            f"状态码断言失败{hint}: 期望 {expected}, 实际 {actual}"

    @staticmethod
    def assert_success(resp, msg=""):
        AssertHelper.assert_status_code(resp, 200, msg or "接口应返回200")

    @staticmethod
    def assert_json_field(resp_body, field, expected, msg=""):
        """断言嵌套字段值（支持 a.b.c 路径）"""
        fields = field.split(".")
        value = resp_body
        for f in fields:
            assert isinstance(value, dict) and f in value, \
                f"字段 '{field}' 不存在: 缺少 '{f}'"
            value = value[f]
        hint = f" — {msg}" if msg else ""
        assert value == expected, \
            f"字段断言失败{hint}: '{field}' 期望 {expected!r}, 实际 {value!r}"

    @staticmethod
    def assert_json_field_exists(resp_body, field, msg=""):
        fields = field.split(".")
        value = resp_body
        for f in fields:
            assert isinstance(value, dict) and f in value, \
                f"字段 '{field}' 不存在{': ' + msg if msg else ''}"
            value = value[f]
        return value

    @staticmethod
    def assert_response_time(resp, max_seconds=5.0, msg=""):
        elapsed = resp.elapsed.total_seconds()
        hint = f" — {msg}" if msg else ""
        assert elapsed <= max_seconds, \
            f"响应时间超时{hint}: {elapsed:.2f}s > {max_seconds}s"

    @staticmethod
    def assert_not_empty(value, field_name="字段", msg=""):
        hint = f" — {msg}" if msg else ""
        assert value is not None and value != "" and value != [], \
            f"'{field_name}' 不应为空{hint}, 实际: {value!r}"

    @staticmethod
    def assert_in_list(actual, expected_list, msg=""):
        hint = f" — {msg}" if msg else ""
        assert actual in expected_list, \
            f"值不在预期列表中{hint}: {actual!r} 不在 {expected_list}"


class DataGenerator:
    """测试数据生成器（复用 Day 11）"""

    @staticmethod
    def random_username(prefix="player", length=6):
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
        return f"{prefix}_{suffix}"

    @staticmethod
    def random_nickname():
        prefixes = ["龙胆", "烈焰", "虚空", "苍穹", "幻影", "碎星", "破晓", "永恒"]
        suffixes = ["战士", "法师", "刺客", "弓手", "圣骑", "召唤师", "猎人"]
        return random.choice(prefixes) + random.choice(suffixes)

    @staticmethod
    def random_skill_id():
        return random.choice(["SKILL_001", "SKILL_002", "SKILL_003", "SKILL_004", "SKILL_005"])

    @staticmethod
    def random_item_id():
        return f"ITEM_{random.randint(1001, 9999)}"


# ── 全局 API 实例和共享数据 ───────────────────────────────
api = BaseAPI(base_url=BASE_URL, timeout=15, max_retries=3)
shared = {}  # 跨测试共享的数据（token、角色ID、战斗ID等）


# =============================================================
# Part 1：知识讲解 — 多模块接口测试设计
# =============================================================

print("=" * 70)
print("  Day 12 - 项目实战 Day 2：Player + Combat 模块测试")
print("=" * 70)

print("""
📌 Part 1：多模块接口依赖关系

  登录模块 (Login)
       │
       │ ── token ──────────────────────────┐
       │                                    │
       ▼                                    ▼
  玩家模块 (Player)                    战斗模块 (Combat)
  ├── 获取玩家信息（需 token）          ├── 开始战斗（需 token + character_id）
  ├── 更新昵称   （需 token）           ├── 使用技能（需 token + battle_id）
  ├── 背包列表   （需 token）           ├── 战斗结算（需 token + battle_id）
  └── 玩家战力   （需 token）           └── 超时处理（需 token + battle_id）
                │
                │ ── character_id ──────────┘
                ▼
             (传入战斗模块作为参数)

📌 Part 2：测试用例设计原则

  Player 模块（10个用例）：
  ├── 正向：信息查询 / 更新 / 背包 / 战力（4个）
  ├── 负向：token无效 / 无token / 不存在玩家 / 越权（4个）
  └── 边界：昵称长度边界 / 并发请求（2个）

  Combat 模块（10个用例）：
  ├── 正向：开始战斗 / 技能使用 / 战斗结算 / 获取战报（4个）
  ├── 负向：无效token / 战斗不存在 / 重复结算 / 参数缺失（4个）
  └── 边界：超时检测 / 连续请求（2个）

📌 Part 3：今日新知识点 — 接口依赖的 3 种处理方式

  方式1：类变量 shared = {}
    → 最简单，用于同一测试类内部的依赖传递

  方式2：pytest fixture（session scope）
    → 标准写法，跨测试文件共享，fixture 自动注入

  方式3：conftest.py 全局 fixture
    → 企业级标准，统一管理，可复用

  ⚡ 今天重点演示方式1（类变量）和方式2（fixture）
""")

time.sleep(0.5)


# =============================================================
# Part 2：Player 玩家模块测试（10个用例）
# =============================================================

print("=" * 70)
print("  Part 2：Player 玩家模块 — 10 个测试用例")
print("=" * 70)

print("""
📌 Player 模块接口清单（山海之巅真实接口对应）

  GET  /api/player/info              获取玩家基本信息
  PUT  /api/player/nickname          更新玩家昵称
  GET  /api/player/bag               获取背包道具列表
  GET  /api/player/bag/{item_id}     获取单个道具详情
  GET  /api/player/power             查询玩家战力
  GET  /api/player/achievements      查询玩家成就列表

  ⚠️  以上接口均需携带 Authorization: Bearer <token> 请求头
  ⚠️  这里用 httpbin.org 承接，验证我们的参数是否正确传递
""")


class TestPlayerModule:
    """
    Player 玩家模块测试

    📌 接口依赖说明：
        所有 Player 接口都需要 token（从登录接口获取）
        这里模拟登录获取 token，再用 token 调用后续接口
    """

    # ── 前置：模拟登录，获取 token ────────────────────────────
    @pytest.fixture(autouse=True, scope="class")
    def setup_token(self):
        """class scope fixture：整个 TestPlayerModule 只登录一次"""
        print("\n  [setup] 执行登录，获取 token...")

        login_payload = {
            "username": "testplayer01",
            "password": "Test@123456",
            "platform": "android",
        }
        resp = api.post("/post", json_data=login_payload)
        assert resp.status_code == 200, "登录失败，无法继续测试"

        # 模拟登录成功，存储 token 和角色信息
        shared["token"] = "Bearer eyJhbGciOiJIUzI1NiJ9.player_token"
        shared["character_id"] = "CHAR_10086"
        shared["player_level"] = 58
        shared["player_name"] = "testplayer01"

        # 将 token 注入到请求头中
        api.add_header("Authorization", shared["token"])
        print(f"  [setup] 登录成功，token 已设置，角色ID: {shared['character_id']}")

        yield  # 测试执行

        # 后置：清理 token
        api.remove_header("Authorization")
        print("\n  [teardown] 清理 token 完成")

    # ── TC01: 获取玩家信息 ─────────────────────────────────
    def test_player_01_get_info(self):
        """TC-P01: 获取玩家基本信息（正常）"""
        print("\n  📌 TC-P01: 获取玩家基本信息")

        params = {
            "character_id": shared["character_id"],
            "action": "get_player_info",
        }
        resp = api.get("/get", params=params)
        body = resp.json()

        AssertHelper.assert_success(resp, "获取玩家信息应返回200")
        AssertHelper.assert_json_field_exists(body, "args", "响应应包含args字段")
        AssertHelper.assert_json_field(body, "args.character_id", shared["character_id"], "角色ID应匹配")
        AssertHelper.assert_response_time(resp, max_seconds=5.0, msg="响应时间不超过5秒")
        print(f"  [通过] 玩家信息获取成功，角色: {shared['character_id']}")

    # ── TC02: 更新玩家昵称 ─────────────────────────────────
    def test_player_02_update_nickname(self):
        """TC-P02: 更新玩家昵称（正常）"""
        print("\n  📌 TC-P02: 更新玩家昵称")

        new_nickname = DataGenerator.random_nickname()
        payload = {
            "character_id": shared["character_id"],
            "nickname": new_nickname,
            "action": "update_nickname",
        }
        resp = api.put("/put", json_data=payload)
        body = resp.json()

        AssertHelper.assert_success(resp, "更新昵称应返回200")
        AssertHelper.assert_json_field_exists(body, "json", "响应应包含json字段")
        AssertHelper.assert_json_field(body, "json.nickname", new_nickname, "新昵称应匹配")
        AssertHelper.assert_json_field(body, "json.action", "update_nickname", "操作类型应正确")

        # 存储昵称供后续用例验证
        shared["nickname"] = new_nickname
        print(f"  [通过] 昵称更新成功: {new_nickname}")

    # ── TC03: 获取背包道具列表 ─────────────────────────────
    def test_player_03_get_bag(self):
        """TC-P03: 获取背包道具列表"""
        print("\n  📌 TC-P03: 获取背包道具列表")

        params = {
            "character_id": shared["character_id"],
            "action": "get_bag",
            "page": 1,
            "page_size": 20,
        }
        resp = api.get("/get", params=params)
        body = resp.json()

        AssertHelper.assert_success(resp)
        AssertHelper.assert_json_field(body, "args.action", "get_bag", "接口动作应为get_bag")
        AssertHelper.assert_json_field(body, "args.page_size", "20", "分页大小应为20")

        # 模拟提取背包中第一个道具ID（真实场景从响应中提取）
        mock_items = ["ITEM_1001", "ITEM_1002", "ITEM_2001"]
        shared["bag_item_id"] = random.choice(mock_items)
        print(f"  [通过] 背包列表获取成功，示例道具: {shared['bag_item_id']}")

    # ── TC04: 背包单个道具详情 ─────────────────────────────
    def test_player_04_get_item_detail(self):
        """TC-P04: 获取背包单个道具详情（依赖 TC03 的 bag_item_id）"""
        print("\n  📌 TC-P04: 背包道具详情（接口依赖演示）")

        # ⚡ 接口依赖：使用 TC03 存储的 bag_item_id
        item_id = shared.get("bag_item_id", "ITEM_1001")
        print(f"  [依赖] 使用 TC03 的 bag_item_id: {item_id}")

        params = {
            "character_id": shared["character_id"],
            "item_id": item_id,
            "action": "get_item_detail",
        }
        resp = api.get("/get", params=params)
        body = resp.json()

        AssertHelper.assert_success(resp)
        AssertHelper.assert_json_field(body, "args.item_id", item_id, "道具ID应与请求一致")
        AssertHelper.assert_json_field(body, "args.action", "get_item_detail")
        print(f"  [通过] 道具详情获取成功，道具ID: {item_id}")

    # ── TC05: 玩家战力查询 ─────────────────────────────────
    def test_player_05_get_power(self):
        """TC-P05: 查询玩家战力"""
        print("\n  📌 TC-P05: 玩家战力查询")

        params = {
            "character_id": shared["character_id"],
            "action": "get_power",
        }
        resp = api.get("/get", params=params)
        body = resp.json()

        AssertHelper.assert_success(resp)
        AssertHelper.assert_json_field(body, "args.action", "get_power")
        AssertHelper.assert_json_field(body, "args.character_id", shared["character_id"])

        # 模拟战力值（真实场景从响应中提取）
        shared["player_power"] = random.randint(50000, 200000)
        print(f"  [通过] 玩家战力查询成功，模拟战力: {shared['player_power']:,}")

    # ── TC06: 无效 token ─────────────────────────────────
    def test_player_06_invalid_token(self):
        """TC-P06: 无效token — 应返回401认证失败"""
        print("\n  📌 TC-P06: 无效token（负向用例）")

        # 临时替换为无效 token
        original_token = shared.get("token")
        api.add_header("Authorization", "Bearer invalid_token_xyz")

        params = {"character_id": shared["character_id"], "action": "get_player_info"}

        try:
            resp = api.get("/get", params=params)
            body = resp.json()
            # httpbin 不做真实鉴权，我们验证请求参数是否正确发送
            AssertHelper.assert_success(resp)
            # 验证无效token被正确传递（真实接口会返回401）
            assert "Authorization" in body.get("headers", {}), "Authorization头应被发送"
            print("  [通过] 无效token场景：请求已发出，真实环境应返回401")
        finally:
            # 恢复原来的 token
            if original_token:
                api.add_header("Authorization", original_token)

    # ── TC07: 无 token 请求 ──────────────────────────────
    def test_player_07_no_token(self):
        """TC-P07: 不携带token — 应返回401未认证"""
        print("\n  📌 TC-P07: 无token请求（负向用例）")

        # 创建一个独立的无 token 请求
        no_auth_session = requests.Session()
        url = f"{BASE_URL}/headers"
        resp = no_auth_session.get(url, timeout=15)
        body = resp.json()

        AssertHelper.assert_success(resp)
        # 验证确实没有携带 Authorization 头
        headers = body.get("headers", {})
        assert "Authorization" not in headers, "无token请求不应携带Authorization头"
        print("  [通过] 无token请求验证：确认未携带Authorization头")
        no_auth_session.close()

    # ── TC08: 越权访问其他玩家数据 ──────────────────────────
    def test_player_08_cross_user_access(self):
        """TC-P08: 越权访问 — 用自己的token访问其他玩家的私密数据"""
        print("\n  📌 TC-P08: 越权访问防护（负向用例）")

        # 尝试访问其他玩家的背包（character_id 不是自己的）
        other_player_id = "CHAR_99999"
        payload = {
            "action": "get_bag",
            "character_id": other_player_id,  # 用别人的ID
            "attacker_id": shared["character_id"],  # 我的ID
        }
        resp = api.post("/post", json_data=payload)
        body = resp.json()

        AssertHelper.assert_success(resp)
        # 验证请求被正确发出（真实接口应返回403）
        AssertHelper.assert_json_field(body, "json.character_id", other_player_id)
        print(f"  [通过] 越权访问场景：character_id={other_player_id}，真实环境应返回403")

    # ── TC09: 昵称长度边界测试 ──────────────────────────────
    @pytest.mark.parametrize("nickname,case_desc", [
        ("",          "空昵称"),
        ("A",         "1字符最短昵称"),
        ("X" * 12,    "12字符合法昵称"),
        ("X" * 13,    "13字符超出上限"),
        ("山海之巅战士",  "中文昵称"),
        ("Nick@Name!", "特殊字符昵称"),
    ])
    def test_player_09_nickname_boundary(self, nickname, case_desc):
        """TC-P09: 昵称长度边界测试（参数化）"""
        print(f"\n  📌 TC-P09: 昵称边界 — {case_desc}（长度={len(nickname)}）")

        payload = {
            "character_id": shared["character_id"],
            "nickname": nickname,
            "action": "update_nickname",
        }
        resp = api.put("/put", json_data=payload)
        body = resp.json()

        AssertHelper.assert_success(resp)
        AssertHelper.assert_json_field(body, "json.nickname", nickname)
        print(f"  [通过] 昵称边界测试: {case_desc} (长度={len(nickname)})")

    # ── TC10: 玩家信息响应时间 ──────────────────────────────
    def test_player_10_response_time(self):
        """TC-P10: 性能验证 — 玩家信息接口响应时间不超过5秒"""
        print("\n  📌 TC-P10: 性能验证（响应时间断言）")

        params = {
            "character_id": shared["character_id"],
            "action": "performance_test",
        }
        resp = api.get("/get", params=params)

        AssertHelper.assert_success(resp)
        # 响应时间上限5秒（httpbin.org 较慢，宽松设置）
        AssertHelper.assert_response_time(resp, max_seconds=5.0, msg="玩家信息接口")
        elapsed = resp.elapsed.total_seconds()
        print(f"  [通过] 响应时间: {elapsed:.2f}s ≤ 5.0s")


# =============================================================
# Part 3：Combat 战斗模块测试（10个用例）
# =============================================================

print("\n" + "=" * 70)
print("  Part 3：Combat 战斗模块 — 10 个测试用例")
print("=" * 70)

print("""
📌 Combat 模块接口清单（山海之巅真实接口对应）

  POST /api/combat/start              开始战斗
  POST /api/combat/skill              使用技能
  GET  /api/combat/status/{battle_id} 查询战斗状态
  POST /api/combat/settle             战斗结算
  GET  /api/combat/report/{battle_id} 获取战斗报告
  DELETE /api/combat/exit             退出战斗

  ⚠️  所有战斗接口均需 token + battle_id
  ⚠️  battle_id 由「开始战斗」接口返回
""")


class TestCombatModule:
    """
    Combat 战斗模块测试

    📌 接口依赖说明：
        战斗开始 → 返回 battle_id → 技能使用/状态查询/结算 都需要此 battle_id
        这是典型的「一接口依赖另一接口返回值」场景
    """

    @pytest.fixture(autouse=True, scope="class")
    def setup_combat_token(self):
        """class scope fixture：战斗测试的前置登录和token设置"""
        print("\n  [setup] Combat模块：模拟登录，设置token...")

        # 复用上面的 shared 字典（真实项目中用 conftest.py session fixture）
        if "token" not in shared:
            shared["token"] = "Bearer eyJhbGciOiJIUzI1NiJ9.combat_token"
            shared["character_id"] = "CHAR_10086"

        api.add_header("Authorization", shared["token"])
        print(f"  [setup] token已就位，character_id: {shared['character_id']}")

        yield

        api.remove_header("Authorization")
        print("\n  [teardown] 战斗模块测试完成，清理token")

    # ── TC01: 开始战斗 ────────────────────────────────────
    def test_combat_01_start_battle(self):
        """TC-C01: 开始战斗 — 获取 battle_id（后续用例依赖）"""
        print("\n  📌 TC-C01: 开始战斗")

        payload = {
            "character_id": shared["character_id"],
            "dungeon_id": "DUNGEON_101",       # 副本ID
            "difficulty": "normal",             # 难度：normal/hard/hell
            "action": "start_battle",
        }
        resp = api.post("/post", json_data=payload)
        body = resp.json()

        AssertHelper.assert_success(resp, "开始战斗应返回200")
        AssertHelper.assert_json_field_exists(body, "json", "响应应有json字段")
        AssertHelper.assert_json_field(body, "json.dungeon_id", "DUNGEON_101", "副本ID应匹配")
        AssertHelper.assert_json_field(body, "json.difficulty", "normal", "难度应为normal")

        # ⚡ 关键：存储 battle_id 供后续用例使用
        # 真实接口从 body["data"]["battle_id"] 提取
        # httpbin 场景下我们生成一个模拟ID
        battle_id = f"BATTLE_{int(time.time())}_{random.randint(1000, 9999)}"
        shared["battle_id"] = battle_id
        shared["battle_start_time"] = time.time()
        print(f"  [通过] 战斗开始成功，battle_id: {battle_id}")
        print(f"  [依赖] battle_id 已存储，供 TC-C02/C03/C04 使用")

    # ── TC02: 使用技能 ────────────────────────────────────
    def test_combat_02_use_skill(self):
        """TC-C02: 使用技能（依赖 TC-C01 的 battle_id）"""
        print("\n  📌 TC-C02: 使用技能（接口依赖演示）")

        # ⚡ 接口依赖：使用 TC-C01 返回的 battle_id
        battle_id = shared.get("battle_id")
        assert battle_id, "battle_id 不存在，请先执行 TC-C01"
        print(f"  [依赖] 使用 TC-C01 的 battle_id: {battle_id}")

        skill_id = DataGenerator.random_skill_id()
        payload = {
            "battle_id": battle_id,
            "character_id": shared["character_id"],
            "skill_id": skill_id,
            "target_id": "MONSTER_001",
            "action": "use_skill",
        }
        resp = api.post("/post", json_data=payload)
        body = resp.json()

        AssertHelper.assert_success(resp)
        AssertHelper.assert_json_field(body, "json.battle_id", battle_id, "battle_id应匹配")
        AssertHelper.assert_json_field(body, "json.skill_id", skill_id, "技能ID应匹配")
        AssertHelper.assert_json_field(body, "json.action", "use_skill")
        print(f"  [通过] 技能使用成功，技能ID: {skill_id}")

    # ── TC03: 查询战斗状态 ──────────────────────────────────
    def test_combat_03_get_status(self):
        """TC-C03: 查询战斗状态（依赖 battle_id）"""
        print("\n  📌 TC-C03: 查询战斗状态")

        battle_id = shared.get("battle_id")
        assert battle_id, "battle_id 不存在，请先执行 TC-C01"

        params = {
            "battle_id": battle_id,
            "character_id": shared["character_id"],
            "action": "get_battle_status",
        }
        resp = api.get("/get", params=params)
        body = resp.json()

        AssertHelper.assert_success(resp)
        AssertHelper.assert_json_field(body, "args.battle_id", battle_id)
        AssertHelper.assert_json_field(body, "args.action", "get_battle_status")
        print(f"  [通过] 战斗状态查询成功，battle_id: {battle_id}")

    # ── TC04: 战斗结算 ────────────────────────────────────
    def test_combat_04_settle(self):
        """TC-C04: 战斗结算（依赖 battle_id）"""
        print("\n  📌 TC-C04: 战斗结算")

        battle_id = shared.get("battle_id")
        assert battle_id, "battle_id 不存在，请先执行 TC-C01"

        battle_duration = int(time.time() - shared.get("battle_start_time", time.time()))
        payload = {
            "battle_id": battle_id,
            "character_id": shared["character_id"],
            "result": "win",               # 战斗结果
            "duration": battle_duration,   # 战斗耗时（秒）
            "kill_count": random.randint(5, 30),
            "action": "settle_battle",
        }
        resp = api.post("/post", json_data=payload)
        body = resp.json()

        AssertHelper.assert_success(resp, "战斗结算应返回200")
        AssertHelper.assert_json_field(body, "json.battle_id", battle_id)
        AssertHelper.assert_json_field(body, "json.result", "win")
        AssertHelper.assert_json_field(body, "json.action", "settle_battle")
        AssertHelper.assert_not_empty(body["json"]["kill_count"], "kill_count", "击杀数不应为空")

        # 存储结算结果
        shared["settle_result"] = body["json"]
        print(f"  [通过] 战斗结算成功，耗时: {battle_duration}s")

    # ── TC05: 获取战斗报告 ──────────────────────────────────
    def test_combat_05_get_report(self):
        """TC-C05: 获取战斗报告（依赖已结算的 battle_id）"""
        print("\n  📌 TC-C05: 获取战斗报告")

        battle_id = shared.get("battle_id")
        assert battle_id, "battle_id 不存在"

        params = {
            "battle_id": battle_id,
            "character_id": shared["character_id"],
            "action": "get_battle_report",
        }
        resp = api.get("/get", params=params)
        body = resp.json()

        AssertHelper.assert_success(resp)
        AssertHelper.assert_json_field(body, "args.battle_id", battle_id)
        AssertHelper.assert_json_field(body, "args.action", "get_battle_report")
        print(f"  [通过] 战斗报告获取成功")

    # ── TC06: 无效 battle_id ──────────────────────────────
    def test_combat_06_invalid_battle_id(self):
        """TC-C06: 无效battle_id — 真实接口应返回404"""
        print("\n  📌 TC-C06: 无效battle_id（负向用例）")

        fake_battle_id = "BATTLE_FAKE_99999999"
        params = {
            "battle_id": fake_battle_id,
            "character_id": shared["character_id"],
            "action": "get_battle_status",
        }
        resp = api.get("/get", params=params)
        body = resp.json()

        AssertHelper.assert_success(resp)
        # httpbin 返回200，真实接口应返回404 "战斗不存在"
        AssertHelper.assert_json_field(body, "args.battle_id", fake_battle_id)
        print("  [通过] 无效battle_id场景：参数正确发送，真实环境应返回404")

    # ── TC07: 重复结算 ────────────────────────────────────
    def test_combat_07_duplicate_settle(self):
        """TC-C07: 重复结算 — 同一battle_id结算两次，真实接口应返回400"""
        print("\n  📌 TC-C07: 重复战斗结算（负向用例）")

        battle_id = shared.get("battle_id", "BATTLE_DUPLICATE_TEST")
        payload = {
            "battle_id": battle_id,
            "character_id": shared["character_id"],
            "result": "win",
            "is_duplicate": True,  # 标记这是第二次结算
            "action": "settle_battle",
        }

        # 第一次结算（正常）
        resp1 = api.post("/post", json_data=payload)
        AssertHelper.assert_success(resp1)

        # 第二次结算（应被拒绝，真实接口返回400 "战斗已结算"）
        payload["settle_count"] = 2
        resp2 = api.post("/post", json_data=payload)
        AssertHelper.assert_success(resp2)  # httpbin 永远200

        print("  [通过] 重复结算场景：两次请求均发出，真实环境第二次应返回400")

    # ── TC08: 必填参数缺失 ────────────────────────────────
    @pytest.mark.parametrize("missing_field,expected_error", [
        ("battle_id",    "缺少battle_id"),
        ("character_id", "缺少character_id"),
        ("result",       "缺少result"),
    ])
    def test_combat_08_missing_params(self, missing_field, expected_error):
        """TC-C08: 必填参数缺失（参数化）"""
        print(f"\n  📌 TC-C08: 参数缺失 — {expected_error}")

        payload = {
            "battle_id": shared.get("battle_id", "BATTLE_TEST"),
            "character_id": shared["character_id"],
            "result": "win",
            "action": "settle_battle",
        }
        # 删除要测试的必填字段
        del payload[missing_field]

        resp = api.post("/post", json_data=payload)
        body = resp.json()

        AssertHelper.assert_success(resp)  # httpbin 永远200
        # 验证该字段确实没有被发送
        assert missing_field not in body.get("json", {}), \
            f"字段 '{missing_field}' 应该被移除"
        print(f"  [通过] 参数缺失 '{missing_field}' 场景：真实环境应返回400")

    # ── TC09: 超时场景处理 ──────────────────────────────────
    def test_combat_09_timeout_handling(self):
        """TC-C09: 超时处理 — 模拟战斗接口超时"""
        print("\n  📌 TC-C09: 超时场景处理")

        # 使用 httpbin 的 delay 接口模拟慢接口（delay=1s，超时阈值5s，应该通过）
        payload = {
            "battle_id": shared.get("battle_id", "BATTLE_TIMEOUT_TEST"),
            "action": "slow_combat_api",
        }
        start = time.time()
        # 用 delay/1 模拟稍慢的接口，但在5秒超时内
        resp = api.get("/delay/1")
        elapsed = time.time() - start

        AssertHelper.assert_success(resp)
        assert elapsed < 5.0, f"模拟慢接口超时: {elapsed:.2f}s > 5.0s"
        print(f"  [通过] 慢接口({elapsed:.2f}s)在超时阈值(5.0s)内正常返回")

    # ── TC10: 连续技能使用压测 ──────────────────────────────
    def test_combat_10_continuous_skills(self):
        """TC-C10: 连续使用多个技能（模拟连击）"""
        print("\n  📌 TC-C10: 连续技能使用（5连击）")

        battle_id = shared.get("battle_id", "BATTLE_COMBO_TEST")
        skill_ids = ["SKILL_001", "SKILL_002", "SKILL_003", "SKILL_004", "SKILL_005"]
        results = []

        for i, skill_id in enumerate(skill_ids, 1):
            payload = {
                "battle_id": battle_id,
                "character_id": shared["character_id"],
                "skill_id": skill_id,
                "combo_index": i,
                "action": "use_skill",
            }
            resp = api.post("/post", json_data=payload)
            AssertHelper.assert_success(resp)
            body = resp.json()
            AssertHelper.assert_json_field(body, "json.skill_id", skill_id)
            results.append(skill_id)
            print(f"    第{i}击: {skill_id} ✓")

        assert len(results) == 5, f"5连击只完成了 {len(results)} 次"
        print(f"  [通过] 5连击全部成功: {' → '.join(results)}")


# =============================================================
# Part 4：多模块全流程综合实战
# =============================================================

print("\n" + "=" * 70)
print("  Part 4：山海之巅完整游戏流程 — 端到端测试（5步）")
print("=" * 70)

print("""
📌 端到端测试流程（E2E Test）

  Step 1: 登录          → 获取 token
  Step 2: 获取角色信息  → 获取 character_id、玩家属性
  Step 3: 开始副本      → 获取 battle_id
  Step 4: 技能攻击      → 战斗过程（3次技能）
  Step 5: 战斗结算      → 获得经验、金币、道具

  💡 这就是接口依赖处理的完整体现：
     每一步的返回值都是下一步的输入参数
""")


class TestEndToEnd:
    """山海之巅完整游戏业务流程 — 端到端测试"""

    # ── E2E 完整流程 ────────────────────────────────────────
    def test_e2e_complete_game_flow(self):
        """
        E2E: 完整游戏流程（登录→查角色→开始战斗→技能→结算）

        这是今天最重要的测试用例！
        演示 5 步接口依赖链的完整处理方式。
        """
        print("\n  📌 E2E: 完整游戏流程测试")
        print("  " + "─" * 50)

        e2e_data = {}  # 流程内部的数据传递

        # ── Step 1: 登录 ───────────────────────────────────
        print("\n  ► Step 1: 用户登录")
        login_payload = {
            "username": "testplayer01",
            "password": "Test@123456",
            "platform": "pc",
        }
        resp = api.post("/post", json_data=login_payload)
        AssertHelper.assert_success(resp, "Step1 登录")
        # 模拟提取 token（真实接口: body["data"]["token"]）
        e2e_data["token"] = "Bearer eyJ.e2e_flow_token"
        api.add_header("Authorization", e2e_data["token"])
        print(f"    ✓ 登录成功，token 已获取")

        # ── Step 2: 获取角色信息 ───────────────────────────
        print("\n  ► Step 2: 获取角色信息（依赖 Step1 的 token）")
        params = {
            "username": "testplayer01",
            "action": "get_character",
        }
        resp = api.get("/get", params=params)
        AssertHelper.assert_success(resp, "Step2 获取角色")
        # 模拟提取 character_id（真实接口: body["data"]["character_id"]）
        e2e_data["character_id"] = "CHAR_E2E_10086"
        e2e_data["level"] = 58
        e2e_data["power"] = 128000
        print(f"    ✓ 角色获取成功，character_id: {e2e_data['character_id']}")
        print(f"    ✓ 玩家等级: {e2e_data['level']} 级，战力: {e2e_data['power']:,}")

        # ── Step 3: 开始副本 ────────────────────────────────
        print("\n  ► Step 3: 进入副本（依赖 Step2 的 character_id）")
        battle_payload = {
            "character_id": e2e_data["character_id"],  # ← 来自 Step2
            "dungeon_id": "DUNGEON_HELL_06",
            "difficulty": "hard",
            "action": "start_battle",
        }
        resp = api.post("/post", json_data=battle_payload)
        AssertHelper.assert_success(resp, "Step3 开始副本")
        # 模拟提取 battle_id（真实接口: body["data"]["battle_id"]）
        e2e_data["battle_id"] = f"BATTLE_E2E_{int(time.time())}"
        print(f"    ✓ 副本进入成功，battle_id: {e2e_data['battle_id']}")

        # ── Step 4: 连续使用技能 ─────────────────────────────
        print("\n  ► Step 4: 战斗过程（依赖 Step3 的 battle_id，连续3技能）")
        skills_used = []
        for round_num, skill_id in enumerate(["SKILL_001", "SKILL_002", "SKILL_003"], 1):
            skill_payload = {
                "battle_id": e2e_data["battle_id"],   # ← 来自 Step3
                "character_id": e2e_data["character_id"],  # ← 来自 Step2
                "skill_id": skill_id,
                "round": round_num,
                "action": "use_skill",
            }
            resp = api.post("/post", json_data=skill_payload)
            AssertHelper.assert_success(resp, f"Step4 第{round_num}技能")
            skills_used.append(skill_id)
            print(f"    ✓ 第{round_num}回合: {skill_id} 使用成功")

        # ── Step 5: 战斗结算 ─────────────────────────────────
        print("\n  ► Step 5: 战斗结算（依赖 battle_id + character_id）")
        settle_payload = {
            "battle_id": e2e_data["battle_id"],       # ← 来自 Step3
            "character_id": e2e_data["character_id"], # ← 来自 Step2
            "result": "win",
            "skills_used": skills_used,               # ← 来自 Step4
            "kill_count": 12,
            "action": "settle_battle",
        }
        resp = api.post("/post", json_data=settle_payload)
        body = resp.json()
        AssertHelper.assert_success(resp, "Step5 战斗结算")
        AssertHelper.assert_json_field(body, "json.battle_id", e2e_data["battle_id"])
        AssertHelper.assert_json_field(body, "json.result", "win")
        print(f"    ✓ 战斗结算成功，获得经验/金币/道具（模拟）")

        # ── 清理 ────────────────────────────────────────────
        api.remove_header("Authorization")

        # ── 最终汇总 ────────────────────────────────────────
        print("\n  " + "─" * 50)
        print(f"  🎉 E2E 完整游戏流程全部通过！")
        print(f"      token      → character_id: {e2e_data['character_id']}")
        print(f"      character  → battle_id:    {e2e_data['battle_id']}")
        print(f"      battle_id  → 技能×3 → 结算")
        print(f"      依赖链长度: 5 步")

    # ── 知识点总结 ──────────────────────────────────────────
    def test_knowledge_summary(self):
        """知识点总结：今日要点回顾"""
        print("\n" + "=" * 70)
        print("  📚 Day 12 知识点总结")
        print("=" * 70)
        print("""
  ✅ 今日掌握的内容：

  1. Player 模块测试设计
     ├── class scope fixture：整个测试类只登录一次（性能优化）
     ├── 正向/负向/边界 三类用例全覆盖（10个用例）
     ├── 接口依赖：TC03的bag_item_id → TC04使用
     └── 参数化昵称边界：6种长度场景一次覆盖

  2. Combat 模块测试设计
     ├── battle_id 依赖链：TC01 → TC02/TC03/TC04/TC05
     ├── 重复操作测试（duplicate settle）
     ├── 必填参数缺失（3种参数化）
     └── 超时测试（delay/1 模拟慢接口）

  3. E2E 端到端测试
     ├── 5步依赖链：登录→角色→副本→技能→结算
     ├── 每步的返回值作为下一步的输入
     └── 这是接口依赖处理的完整体现

  4. 接口依赖处理方式对比：
     ├── 方式1：shared = {} 类变量（简单场景）
     ├── 方式2：class scope fixture（单模块内）
     └── 方式3：conftest.py session fixture（跨文件）

  📝 明日预告（Day 13）：
     - 完整项目报告生成（allure + pytest-html）
     - 测试结果导出（Excel/JSON）
     - CI/CD 集成基础
        """)
        assert True  # 知识点总结用例，直接通过


# =============================================================
# 运行入口
# =============================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  Day 12 — 开始执行所有测试")
    print("=" * 70)

    start_time = time.time()
    result = pytest.main([
        __file__,
        "-v",
        "-s",
        "--tb=short",
        "-W", "ignore::DeprecationWarning",
    ])
    elapsed = time.time() - start_time

    print("\n" + "=" * 70)
    print(f"  Day 12 测试完成！总耗时: {elapsed:.2f}s")
    print(f"  退出码: {result} ({'成功' if result == 0 else '有失败'})")
    print("=" * 70)

    api.close()
