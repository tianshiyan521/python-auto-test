# =============================================================
# Python + Requests 14天学习计划 - Day 12
# 主题：项目实战 Day 2 — 山海之巅 Player / Combat / Item 业务模块
# 日期：2026-06-02
# =============================================================

"""
Day 12 学习大纲
===============
Part 1：业务模块接口概览
    - Player 模块：玩家信息、更新昵称/头像、背包、装备
    - Combat 模块：开始战斗、使用技能、战斗结算、超时处理
    - Item 模块：使用道具、装备穿戴、卸下装备、背包查询

Part 2：跨模块依赖链
    - Login → Player → Combat → Item 完整流程
    - module scope fixture 实战
    - token + user_id + character_id + battle_id 多级依赖

Part 3：边界与异常
    - 不存在的玩家ID
    - 背包为空时
    - 重复装备同一槽位
    - 非法战斗状态
    - 道具数量不足
"""

import requests
import json
import time
import random
import string
import pytest

# ── 配置 ─────────────────────────────────────────────────────
BASE_URL = "https://httpbin.org"


# =============================================================
# Part 0：复用 Day 11 的核心框架类（精简版）
# =============================================================

class EnvConfig:
    ENV = "test"
    TEST_ACCOUNTS = {
        "normal_user": {"username": "testplayer01", "password": "Test@123456"},
        "vip_user":    {"username": "vipplayer01", "password": "Vip@123456"},
        "gm_user":     {"username": "gmadmin", "password": "Gm@123456"},
    }
    TIMEOUT = {"fast": 5, "normal": 10, "slow": 30}
    RETRY = {"max_retries": 3, "retry_delay": 1}


class BaseAPI:
    """统一请求封装 — 自动重试 + Session + 日志 + 敏感信息脱敏"""

    def __init__(self, base_url=BASE_URL, timeout=10, max_retries=3):
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "ShanZhiTestFramework/1.0",
        })

    def _request(self, method, path, **kwargs):
        url = f"{self.base_url}{path}"
        kwargs.setdefault("timeout", self.timeout)
        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                start = time.time()
                resp = self.session.request(method, url, **kwargs)
                elapsed = time.time() - start
                # 5xx 服务端错误自动重试
                if resp.status_code >= 500 and attempt < self.max_retries:
                    print(f"  [重试] 第{attempt}次 {resp.status_code}，1s后重试...")
                    time.sleep(1)
                    continue
                return resp
            except (requests.ConnectionError, requests.Timeout) as e:
                last_exception = e
                if attempt < self.max_retries:
                    print(f"  [重试] 第{attempt}次连接异常: {e}")
                    time.sleep(1)
                    continue
                raise
        if last_exception:
            raise last_exception
        return resp

    def get(self, path, params=None, **kwargs):
        return self._request("GET", path, params=params, **kwargs)

    def post(self, path, json_data=None, **kwargs):
        print(f"  [请求] POST {self.base_url}{path}")
        if json_data and "password" in json_data:
            safe = {**json_data, "password": "***"}
            print(f"  [请求体] {json.dumps(safe, ensure_ascii=False)}")
        return self._request("POST", path, json=json_data, **kwargs)

    def put(self, path, json_data=None, **kwargs):
        print(f"  [请求] PUT {self.base_url}{path}")
        return self._request("PUT", path, json=json_data, **kwargs)

    def delete(self, path, **kwargs):
        print(f"  [请求] DELETE {self.base_url}{path}")
        return self._request("DELETE", path, **kwargs)

    def add_header(self, key, value):
        self.session.headers[key] = value

    def close(self):
        self.session.close()


class AssertHelper:
    """断言工具类"""

    @staticmethod
    def assert_status(resp, expected=200, msg=""):
        actual = resp.status_code
        hint = f" — {msg}" if msg else ""
        assert actual == expected, f"状态码断言失败{hint}: 期望 {expected}, 实际 {actual}"

    @staticmethod
    def assert_success(resp, msg=""):
        AssertHelper.assert_status(resp, 200, msg or "接口应返回200")

    @staticmethod
    def assert_json_field(resp_body, field, expected, msg=""):
        """支持 . 分隔的嵌套路径"""
        fields = field.split(".")
        value = resp_body
        for f in fields:
            if isinstance(value, dict):
                assert f in value, f"字段 '{field}' 不存在: 缺少 '{f}'"
                value = value[f]
            else:
                assert False, f"字段 '{field}' 路径错误: '{f}' 父级不是字典"
        hint = f" — {msg}" if msg else ""
        assert value == expected, f"字段断言失败{hint}: '{field}' 期望 {expected}, 实际 {value}"

    @staticmethod
    def assert_field_exists(resp_body, field, msg=""):
        fields = field.split(".")
        value = resp_body
        for f in fields:
            if isinstance(value, dict):
                assert f in value, f"字段 '{field}' 不存在{msg}: 缺少 '{f}'"
                value = value[f]
            else:
                assert False, "字段路径错误"
        return value

    @staticmethod
    def assert_not_empty(value, field_name="字段", msg=""):
        hint = f" — {msg}" if msg else ""
        assert value is not None and value != "" and value != [], \
            f"'{field_name}' 不应为空{hint}, 实际值: {value}"

    @staticmethod
    def assert_in_range(value, min_val, max_val, field_name="字段", msg=""):
        hint = f" — {msg}" if msg else ""
        assert min_val <= value <= max_val, \
            f"'{field_name}' 超出范围{hint}: {value} 不在 [{min_val}, {max_val}]"


class DataGenerator:
    @staticmethod
    def random_username(prefix="test", length=8):
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
        return f"{prefix}_{suffix}"

    @staticmethod
    def random_phone():
        return random.choice(["13", "15", "18", "19"]) + ''.join(random.choices(string.digits, k=9))

    @staticmethod
    def random_password(length=12):
        chars = string.ascii_letters + string.digits + "!@#$%"
        pwd = [random.choice(string.ascii_uppercase),
               random.choice(string.ascii_lowercase),
               random.choice(string.digits),
               random.choice("!@#$%")]
        pwd += random.choices(chars, k=length - 4)
        random.shuffle(pwd)
        return ''.join(pwd)

    @staticmethod
    def random_item_id():
        return f"item_{random.randint(1000, 9999)}"


# ── 全局 API 实例和共享数据 ──────────────────────────────────
api = BaseAPI(base_url=BASE_URL, timeout=15, max_retries=3)
shared = {}  # 模拟全局数据存储（token, user_id, character_id, battle_id, item_id）


# =============================================================
# Part 1：知识讲解 — 业务模块接口概览
# =============================================================

print("=" * 70)
print("  Day 12：项目实战 Day 2 — 业务模块接口测试")
print("=" * 70)
print("""
📌 山海之巅核心业务模块

  ┌──────────────────────────────────────────────────┐
  │  Login 模块 (Day 11 已完成)                       │
  │  └── 登录 → token, user_id                       │
  ├──────────────────────────────────────────────────┤
  │  Player 模块 ★ 今日                           │
  │  ├── GET  /player/info      获取玩家信息         │
  │  ├── PUT  /player/update    更新昵称/头像        │
  │  ├── GET  /player/backpack  查看背包             │
  │  └── GET  /player/equipment 查看装备             │
  ├──────────────────────────────────────────────────┤
  │  Combat 模块 ★ 今日                           │
  │  ├── POST /combat/start     开始战斗             │
  │  ├── POST /combat/skill     使用技能             │
  │  └── POST /combat/settle    战斗结算             │
  ├──────────────────────────────────────────────────┤
  │  Item 模块 ★ 今日                            │
  │  ├── POST /item/use         使用道具             │
  │  ├── POST /item/equip       装备道具             │
  │  └── POST /item/unequip     卸下装备             │
  └──────────────────────────────────────────────────┘

📌 跨模块依赖链（今天重点）

  Login ─→ Player ─→ Combat ─→ Item
    │         │          │         │
    │ token   │ user_id  │ battle  │ item_id
    │         │ char_id  │ _id     │
    └── 多级依赖传递，前一个接口的返回值是后一个接口的参数
""")
time.sleep(0.5)


# =============================================================
# Part 2：跨模块依赖链 — conftest 模拟（module scope fixture）
# =============================================================

print("=" * 70)
print("  Part 2：Fixture 依赖链 — Module Scope 模拟")
print("=" * 70)


class ModuleFixture:
    """
    模拟 pytest module scope fixture
    关键概念：module scope = 同一个模块中只执行一次，后续用例复用
    """
    def __init__(self):
        self.data = {}
        self.setup_done = False

    def setup(self):
        """模拟 conftest.py 中的 fixture setup"""
        if self.setup_done:
            return

        print("\n  🔧 [Fixture Setup] 开始初始化测试环境...")

        # 步骤1：登录
        login_resp = api.post("/post", json_data={
            "username": "testplayer01",
            "password": "Test@123456",
            "platform": "android",
        })
        AssertHelper.assert_success(login_resp)
        self.data["token"] = "eyJhbGciOiJIUzI1NiJ9.mock_token_day12"
        self.data["user_id"] = "10086"
        print(f"  ✅ 登录完成 → user_id={self.data['user_id']}")

        # 步骤2：获取角色信息（用 token + user_id）
        api.add_header("Authorization", f"Bearer {self.data['token']}")
        char_resp = api.post("/post", json_data={
            "action": "get_character",
            "user_id": self.data["user_id"],
        })
        AssertHelper.assert_success(char_resp)
        self.data["character_id"] = "char_0421"
        self.data["character_name"] = "山海战士"
        self.data["level"] = 50
        self.data["hp"] = 5000
        self.data["atk"] = 850
        print(f"  ✅ 角色信息 → {self.data['character_name']} Lv.{self.data['level']}")

        self.setup_done = True
        print(f"  🔧 [Fixture Setup] 初始化完成（共享数据可在模块内复用）\n")

    def teardown(self):
        """模拟 fixture teardown"""
        print("\n  🔧 [Fixture Teardown] 清理测试数据...")
        api.add_header("Authorization", "")
        self.data.clear()
        self.setup_done = False
        print("  ✅ 清理完成")


fixture = ModuleFixture()

print("""
📌 Module Scope Fixture 关键点：

   scope='module' 意味着：
   ├── 整个测试文件只执行1次 setup
   ├── 所有测试用例共享同一个 token/user_id/character_id
   ├── teardown 在所有用例执行完后才执行
   └── 大幅减少重复的登录请求（性能提升！）

   scope 对比：
   ├── function：每个用例都登录1次 → N个用例=N次登录 ❌慢
   ├── class：   每个类登录1次     → M个类=M次登录
   ├── module：  每个文件登录1次    → 1次登录 ✅推荐
   └── session： 整个运行登录1次    → 1次登录 ✅最快
""")
time.sleep(0.5)


# =============================================================
# Part 3：Player 模块测试（5个用例）
# =============================================================

print("=" * 70)
print("  Part 3：Player 模块 — 玩家信息/更新/背包/装备")
print("=" * 70)

# 确保 fixture 已初始化
fixture.setup()


class TestPlayerModule:
    """山海之巅 — Player 模块测试"""

    # ── TC-P01: 获取玩家信息 ─────────────────────────────────
    def test_p01_get_player_info(self):
        """TC-P01: GET /player/info — 获取玩家完整信息"""
        print("\n  📌 TC-P01: 获取玩家信息")

        resp = api.post("/post", json_data={
            "api": "/player/info",
            "user_id": fixture.data["user_id"],
            "character_id": fixture.data["character_id"],
        })
        body = resp.json()

        AssertHelper.assert_success(resp, "获取玩家信息应返回200")
        # 验证返回数据完整
        AssertHelper.assert_json_field(body, "json.user_id", "10086")
        AssertHelper.assert_json_field(body, "json.character_id", "char_0421")
        AssertHelper.assert_field_exists(body, "json", "响应应包含完整数据")
        print("  [通过] 玩家信息接口正常")

    # ── TC-P02: 更新玩家昵称 ────────────────────────────────
    def test_p02_update_nickname(self):
        """TC-P02: PUT /player/update — 更新玩家昵称"""
        print("\n  📌 TC-P02: 更新玩家昵称")

        new_name = f"山海勇士_{random.randint(1000, 9999)}"
        resp = api.put("/put", json_data={
            "api": "/player/update",
            "user_id": fixture.data["user_id"],
            "character_id": fixture.data["character_id"],
            "nickname": new_name,
            "action": "update_nickname",
        })
        body = resp.json()

        AssertHelper.assert_success(resp, "更新昵称应返回200")
        AssertHelper.assert_json_field(body, "json.nickname", new_name, "昵称应为新值")
        AssertHelper.assert_json_field(body, "json.action", "update_nickname")
        print(f"  [通过] 昵称已更新: {new_name}")

    # ── TC-P03: 更新玩家信息（多字段） ──────────────────────
    def test_p03_update_multi_fields(self):
        """TC-P03: 批量更新玩家信息 — 昵称+头像+签名"""
        print("\n  📌 TC-P03: 批量更新玩家信息")

        update_data = {
            "api": "/player/update",
            "user_id": fixture.data["user_id"],
            "character_id": fixture.data["character_id"],
            "nickname": "战神归来",
            "avatar_id": "avatar_007",
            "signature": "山海之巅，我为主宰！",
            "action": "batch_update",
        }
        resp = api.post("/put", json_data=update_data)
        body = resp.json()

        AssertHelper.assert_success(resp)
        AssertHelper.assert_json_field(body, "json.nickname", "战神归来", "昵称应更新")
        AssertHelper.assert_json_field(body, "json.avatar_id", "avatar_007", "头像ID应更新")
        AssertHelper.assert_json_field(body, "json.signature", "山海之巅，我为主宰！", "签名应更新")
        print("  [通过] 三字段批量更新成功")

    # ── TC-P04: 查看背包 ─────────────────────────────────────
    def test_p04_check_backpack(self):
        """TC-P04: GET /player/backpack — 查看背包物品列表"""
        print("\n  📌 TC-P04: 查看背包")

        resp = api.post("/post", json_data={
            "api": "/player/backpack",
            "user_id": fixture.data["user_id"],
            "character_id": fixture.data["character_id"],
        })
        body = resp.json()

        AssertHelper.assert_success(resp)
        AssertHelper.assert_field_exists(body, "json", "背包接口应返回数据")
        print("  [通过] 背包查询正常")

    # ── TC-P05: 查看装备 ─────────────────────────────────────
    def test_p05_check_equipment(self):
        """TC-P05: GET /player/equipment — 查看当前装备"""
        print("\n  📌 TC-P05: 查看装备")

        resp = api.post("/post", json_data={
            "api": "/player/equipment",
            "character_id": fixture.data["character_id"],
        })
        body = resp.json()

        AssertHelper.assert_success(resp)
        # 存储装备信息供 Item 模块使用
        fixture.data["equipped_slot"] = "weapon"
        fixture.data["equipped_item"] = "sword_of_dragon"
        print("  [通过] 装备查询正常")


# =============================================================
# Part 4：Combat 模块测试（4个用例）
# =============================================================

print("\n" + "=" * 70)
print("  Part 4：Combat 模块 — 战斗开始/技能/结算/超时")
print("=" * 70)


class TestCombatModule:
    """山海之巅 — Combat 模块测试"""

    # ── TC-C01: 开始战斗 ────────────────────────────────────
    def test_c01_start_battle(self):
        """TC-C01: POST /combat/start — PVE战斗开始"""
        print("\n  📌 TC-C01: 开始战斗")

        resp = api.post("/post", json_data={
            "api": "/combat/start",
            "user_id": fixture.data["user_id"],
            "character_id": fixture.data["character_id"],
            "battle_type": "pve",           # PVE 副本战斗
            "dungeon_id": "shanhain_temple",
            "difficulty": "normal",
        })
        body = resp.json()

        AssertHelper.assert_success(resp, "开始战斗应返回200")
        AssertHelper.assert_json_field(body, "json.battle_type", "pve")
        AssertHelper.assert_json_field(body, "json.dungeon_id", "shanhain_temple")

        # 存储 battle_id 供后续用例使用（核心依赖链！）
        fixture.data["battle_id"] = "battle_0421_001"
        fixture.data["enemy_hp"] = 10000
        print(f"  [通过] 战斗已开始 → battle_id={fixture.data['battle_id']}")

    # ── TC-C02: 使用技能 ────────────────────────────────────
    def test_c02_use_skill(self):
        """TC-C02: POST /combat/skill — 对敌人施放技能"""
        print("\n  📌 TC-C02: 使用技能")

        resp = api.post("/post", json_data={
            "api": "/combat/skill",
            "battle_id": fixture.data["battle_id"],
            "character_id": fixture.data["character_id"],
            "skill_id": "fire_storm_3",
            "skill_level": 3,
            "target": "enemy_main",
        })
        body = resp.json()

        AssertHelper.assert_success(resp)
        AssertHelper.assert_json_field(body, "json.skill_id", "fire_storm_3")
        AssertHelper.assert_json_field(body, "json.battle_id", fixture.data["battle_id"])
        print("  [通过] 技能施放成功")

    # ── TC-C03: 战斗结算 ────────────────────────────────────
    def test_c03_settle_battle(self):
        """TC-C03: POST /combat/settle — 战斗结算，获取奖励"""
        print("\n  📌 TC-C03: 战斗结算")

        resp = api.post("/post", json_data={
            "api": "/combat/settle",
            "battle_id": fixture.data["battle_id"],
            "character_id": fixture.data["character_id"],
            "result": "victory",            # 胜利
            "enemy_hp_remaining": 0,
            "damage_dealt": 12500,
            "turns": 15,
        })
        body = resp.json()

        AssertHelper.assert_success(resp)
        AssertHelper.assert_json_field(body, "json.result", "victory", "战斗结果应为胜利")
        AssertHelper.assert_json_field(body, "json.damage_dealt", 12500)

        # 存储掉落的道具ID
        fixture.data["dropped_item_id"] = "item_8842"
        fixture.data["gold_earned"] = 500
        print(f"  [通过] 战斗胜利！获得道具: {fixture.data['dropped_item_id']}, 金币: {fixture.data['gold_earned']}")

    # ── TC-C04: 非正常战斗状态 ───────────────────────────────
    def test_c04_invalid_combat_state(self):
        """TC-C04: 边界测试 — 对不存在的战斗使用技能"""
        print("\n  📌 TC-C04: 无效战斗状态")

        resp = api.post("/post", json_data={
            "api": "/combat/skill",
            "battle_id": "battle_not_exist_99999",
            "character_id": fixture.data["character_id"],
            "skill_id": "slash_1",
            "skill_level": 1,
            "target": "enemy_main",
        })
        body = resp.json()

        AssertHelper.assert_success(resp)
        # 验证不存在的战斗ID被正确传递
        AssertHelper.assert_json_field(body, "json.battle_id", "battle_not_exist_99999")
        print("  [通过] 无效战斗状态场景已覆盖")


# =============================================================
# Part 5：Item 模块测试（5个用例）
# =============================================================

print("\n" + "=" * 70)
print("  Part 5：Item 模块 — 使用道具/装备穿戴/卸下装备")
print("=" * 70)


class TestItemModule:
    """山海之巅 — Item 模块测试"""

    # ── TC-I01: 使用消耗型道具 ──────────────────────────────
    def test_i01_use_consumable(self):
        """TC-I01: POST /item/use — 使用消耗型道具（药水）"""
        print("\n  📌 TC-I01: 使用消耗型道具")

        potion_id = "hp_potion_large"
        resp = api.post("/post", json_data={
            "api": "/item/use",
            "user_id": fixture.data["user_id"],
            "character_id": fixture.data["character_id"],
            "item_id": potion_id,
            "quantity": 1,
            "item_type": "consumable",
        })
        body = resp.json()

        AssertHelper.assert_success(resp, "使用道具应返回200")
        AssertHelper.assert_json_field(body, "json.item_id", potion_id)
        AssertHelper.assert_json_field(body, "json.quantity", 1)
        AssertHelper.assert_json_field(body, "json.item_type", "consumable")
        print(f"  [通过] 消耗品 {potion_id} 使用成功")

    # ── TC-I02: 穿戴装备 ─────────────────────────────────────
    def test_i02_equip_item(self):
        """TC-I02: POST /item/equip — 给角色穿戴装备"""
        print("\n  📌 TC-I02: 穿戴装备")

        equip_item = "dragon_scale_armor"
        resp = api.post("/post", json_data={
            "api": "/item/equip",
            "character_id": fixture.data["character_id"],
            "item_id": equip_item,
            "equip_slot": "chest",          # 装备到胸甲槽位
        })
        body = resp.json()

        AssertHelper.assert_success(resp, "穿戴装备应返回200")
        AssertHelper.assert_json_field(body, "json.item_id", equip_item)
        AssertHelper.assert_json_field(body, "json.equip_slot", "chest")
        fixture.data["equipped_chest"] = equip_item
        print(f"  [通过] 装备 {equip_item} 已穿戴到 chest 槽位")

    # ── TC-I03: 卸下装备 ─────────────────────────────────────
    def test_i03_unequip_item(self):
        """TC-I03: POST /item/unequip — 卸下槽位装备"""
        print("\n  📌 TC-I03: 卸下装备")

        resp = api.post("/post", json_data={
            "api": "/item/unequip",
            "character_id": fixture.data["character_id"],
            "equip_slot": "chest",
        })
        body = resp.json()

        AssertHelper.assert_success(resp, "卸下装备应返回200")
        AssertHelper.assert_json_field(body, "json.equip_slot", "chest")
        print("  [通过] 装备已从 chest 槽位卸下")

    # ── TC-I04: 装备冲突 — 同一槽位重复装备 ──────────────────
    def test_i04_equip_duplicate_slot(self):
        """TC-I04: 边界测试 — 在有装备的槽位上重复装备"""
        print("\n  📌 TC-I04: 重复装备同一槽位")

        # 先装备一个
        resp1 = api.post("/post", json_data={
            "api": "/item/equip",
            "character_id": fixture.data["character_id"],
            "item_id": "helmet_of_war",
            "equip_slot": "head",
        })
        AssertHelper.assert_success(resp1)
        print("    第一次装备: helmet_of_war → head")

        # 再装备另一个到同一槽位（应覆盖或报错）
        resp2 = api.post("/post", json_data={
            "api": "/item/equip",
            "character_id": fixture.data["character_id"],
            "item_id": "crown_of_magic",
            "equip_slot": "head",           # 同一槽位！
        })
        AssertHelper.assert_success(resp2)
        print("    第二次装备: crown_of_magic → head（同一槽位）")

        # 验证第二次装备的 item_id 被正确传递
        body2 = resp2.json()
        AssertHelper.assert_json_field(body2, "json.item_id", "crown_of_magic")
        print("  [通过] 重复装备槽位场景已覆盖（第二次覆盖第一次）")

    # ── TC-I05: 道具数量不足 ─────────────────────────────────
    def test_i05_insufficient_items(self):
        """TC-I05: 边界测试 — 请求消耗超过拥有数量的道具"""
        print("\n  📌 TC-I05: 道具数量不足")

        resp = api.post("/post", json_data={
            "api": "/item/use",
            "user_id": fixture.data["user_id"],
            "character_id": fixture.data["character_id"],
            "item_id": "rare_crystal",
            "quantity": 999,                # 远超实际拥有量
            "item_type": "consumable",
        })
        body = resp.json()

        AssertHelper.assert_success(resp)
        AssertHelper.assert_json_field(body, "json.quantity", 999)
        AssertHelper.assert_json_field(body, "json.item_id", "rare_crystal")
        print("  [通过] 道具数量不足场景已覆盖（请求999个，实际应拒绝或返回错误）")


# =============================================================
# Part 6：综合依赖链测试 — 完整山海之巅工作流
# =============================================================

print("\n" + "=" * 70)
print("  Part 6：综合依赖链 — 完整工作流 (Login → Combat → Item)")
print("=" * 70)


class TestFullWorkflow:
    """完整业务流程：从登录到战斗结算到道具使用"""

    def test_workflow_login_to_loot(self):
        """
        完整工作流验证：
        Login(获取token) → Player(角色信息) → Combat(战斗) → Item(使用掉落道具)

        这是接口测试中最重要的测试场景之一，
        验证所有模块的接口依赖链是否正确传递。
        """
        print("\n  📌 完整工作流：Login → Player → Combat → Item")

        # 步骤1：登录
        print("  [1/6] 登录...")
        resp = api.post("/post", json_data={
            "action": "login",
            "username": "testplayer01",
            "password": "Test@123456",
        })
        AssertHelper.assert_success(resp)
        wf_token = "wf_token_fullchain"
        wf_user_id = "10086"
        print(f"    ✅ 登录成功 user_id={wf_user_id}")

        # 步骤2：获取角色信息
        print("  [2/6] 获取角色信息...")
        resp = api.post("/post", json_data={
            "api": "/player/info",
            "user_id": wf_user_id,
        })
        AssertHelper.assert_success(resp)
        wf_character_id = "char_workflow"
        print(f"    ✅ 角色获取 character_id={wf_character_id}")

        # 步骤3：开始战斗
        print("  [3/6] 开始战斗...")
        resp = api.post("/post", json_data={
            "api": "/combat/start",
            "user_id": wf_user_id,
            "character_id": wf_character_id,
            "battle_type": "pve",
            "dungeon_id": "dragon_lair",
        })
        AssertHelper.assert_success(resp)
        wf_battle_id = "wf_battle_001"
        print(f"    ✅ 战斗开始 battle_id={wf_battle_id}")

        # 步骤4：施放技能
        print("  [4/6] 施放技能...")
        resp = api.post("/post", json_data={
            "api": "/combat/skill",
            "battle_id": wf_battle_id,
            "character_id": wf_character_id,
            "skill_id": "ultimate_strike",
            "skill_level": 5,
            "target": "dragon_boss",
        })
        AssertHelper.assert_success(resp)
        print("    ✅ 技能施放成功")

        # 步骤5：战斗结算
        print("  [5/6] 战斗结算...")
        resp = api.post("/post", json_data={
            "api": "/combat/settle",
            "battle_id": wf_battle_id,
            "character_id": wf_character_id,
            "result": "victory",
            "damage_dealt": 99999,
            "turns": 8,
        })
        AssertHelper.assert_success(resp)
        wf_dropped_item = "dragon_egg_mythic"
        print(f"    ✅ 战斗胜利！掉落: {wf_dropped_item}")

        # 步骤6：使用掉落道具
        print("  [6/6] 使用掉落道具...")
        resp = api.post("/post", json_data={
            "api": "/item/use",
            "user_id": wf_user_id,
            "character_id": wf_character_id,
            "item_id": wf_dropped_item,
            "quantity": 1,
            "item_type": "treasure",
        })
        body = resp.json()

        AssertHelper.assert_success(resp, "道具使用应返回200")
        AssertHelper.assert_json_field(body, "json.item_id", wf_dropped_item)
        AssertHelper.assert_json_field(body, "json.quantity", 1)
        print(f"    ✅ 道具 {wf_dropped_item} 使用成功")

        print("\n  🎉 完整工作流 6 步骤全部通过！")


# =============================================================
# Part 7：数据驱动 + 边界矩阵
# =============================================================

print("\n" + "=" * 70)
print("  Part 7：Player 模块数据驱动测试")
print("=" * 70)


# 更新昵称的边界值矩阵
nickname_test_data = [
    {"nickname": "战神",     "expected": "success", "desc": "2字昵称（最小合法）"},
    {"nickname": "山海之巅无敌战神归来", "expected": "success", "desc": "10字昵称（正常）"},
    {"nickname": "",         "expected": "fail",    "desc": "空昵称"},
    {"nickname": "a",        "expected": "fail",    "desc": "1字昵称（太短）"},
    {"nickname": "山海之巅是最强大的游戏世界欢迎你", "expected": "fail", "desc": "超长昵称(17字)"},
    {"nickname": "  战神  ", "expected": "success", "desc": "有前后空格"},
    {"nickname": "<b>粗体</b>", "expected": "fail", "desc": "HTML标签"},
]

class TestNicknameParametrize:
    """昵称更新 — 数据驱动测试"""

    @pytest.mark.parametrize("case", nickname_test_data, ids=[
        c["desc"] for c in nickname_test_data
    ])
    def test_update_nickname_boundary(self, case):
        """数据驱动：昵称边界值测试"""
        print(f"\n  📌 昵称边界: {case['desc']} — '{case['nickname']}'")

        resp = api.post("/put", json_data={
            "api": "/player/update",
            "user_id": fixture.data["user_id"],
            "character_id": fixture.data["character_id"],
            "nickname": case["nickname"],
            "action": "update_nickname",
            "test_desc": case["desc"],
        })
        body = resp.json()

        AssertHelper.assert_success(resp)
        AssertHelper.assert_json_field(body, "json.nickname", case["nickname"],
                                       f"昵称应匹配: {case['desc']}")
        print(f"  [通过] {case['desc']}: 昵称正确传递")


# =============================================================
# 运行所有测试
# =============================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  Day 12 测试执行开始")
    print("=" * 70)

    start_time = time.time()
    result = pytest.main([
        __file__,
        "-v", "-s", "--tb=short",
        "-W", "ignore::DeprecationWarning",
        "-p", "no:cacheprovider",  # 避免缓存干扰
    ])
    elapsed = time.time() - start_time

    # Teardown
    fixture.teardown()
    api.close()

    print("\n" + "=" * 70)
    print(f"  Day 12 测试完成！总耗时: {elapsed:.2f}s")
    print(f"  退出码: {result}")
    print("=" * 70)
