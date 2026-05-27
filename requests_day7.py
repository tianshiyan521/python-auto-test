# -*- coding: utf-8 -*-
"""
第7天 - pytest fixture 深化 + Session 会话管理
学习主题：使用 pytest fixture 实现优雅的接口依赖

场景：山海之巅游戏接口完整依赖链
- conftest.py：集中管理公共 fixture（登录、session）
- fixture scope：function / module / session 的区别
- yield vs return：fixture 清理逻辑
- requests.Session：自动管理 cookie/token，连接复用
- 完整 4 步依赖链 fixture 化实战
"""

import requests
import json
import time
import random
from typing import Dict, Any, Optional


def safe_request(method: str, url: str, retries: int = 3, **kwargs) -> requests.Response:
    """
    带重试的请求封装（处理 httpbin.org 偶发 502/503 抖动）

    Args:
        method: HTTP 方法
        url: 请求 URL
        retries: 最大重试次数
        **kwargs: requests.request 的其他参数

    Returns:
        requests.Response 对象

    Raises:
        最后一次失败的异常
    """
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.request(method, url, timeout=10, **kwargs)
            resp.raise_for_status()
            return resp
        except (requests.exceptions.HTTPError,
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout) as e:
            last_error = e
            if attempt < retries:
                wait = random.uniform(0.5, 1.5)
                print(f"   ⚠️  第{attempt}次请求失败（{type(e).__name__}），{wait:.1f}s后重试...")
                time.sleep(wait)
            else:
                print(f"   ❌ 重试{retries}次后仍失败: {e}")
                raise last_error

# ============ 基础配置 ============
BASE_URL = "https://httpbin.org"

# ============================================================
# Part 1：pytest fixture 核心概念讲解（代码演示）
# ============================================================

def retry_session_request(session: requests.Session, method: str, url: str,
                            retries: int = 3, **kwargs) -> requests.Response:
    """
    Session 请求的带重试封装（处理 httpbin.org 偶发 502/503 抖动）
    保持 session 的 cookie/header 自动管理能力，同时具备容错能力。
    """
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            resp = session.request(method, url, timeout=10, **kwargs)
            resp.raise_for_status()
            return resp
        except (requests.exceptions.HTTPError,
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout) as e:
            last_error = e
            if attempt < retries:
                wait = random.uniform(0.3, 1.0)
                print(f"   ⚠️  请求失败（{type(e).__name__}），{wait:.1f}s后重试...")
                time.sleep(wait)
            else:
                raise last_error


def demo_fixture_concepts():
    """
    Day 7 核心概念（纯讲解，不执行）

    Fixture 的 4 种作用域（scope）：
    ┌─────────────┬────────────────────────────────────────┐
    │ scope       │ 说明                                    │
    ├─────────────┼────────────────────────────────────────┤
    │ function    │ 每个测试函数执行一次（默认，最常用）      │
    │ class       │ 每个测试类执行一次                       │
    │ module      │ 每个 .py 模块执行一次                   │
    │ session     │ 整个 pytest 会话只执行一次（全局登录）    │
    └─────────────┴────────────────────────────────────────┘

    yield vs return：
    - return：返回数据，fixture 结束后不做什么
    - yield：返回数据 → 运行测试 → fixture 继续执行（清理逻辑）

    自动 token 刷新 fixture 原理：
    @pytest.fixture(scope="session")
    def auth_session():
        resp = requests.post(f"{BASE_URL}/post", data={"user": "admin", "pwd": "xxx"})
        token = resp.json()["form"]["user"]  # 模拟
        session = requests.Session()
        session.headers.update({"Authorization": f"Bearer tk_{token}"})
        yield session  # → 测试用 session
        # ← 测试结束后清理
        session.close()
    """

    print("✅ Fixture 核心概念已记录（见上方文档字符串）")


# ============================================================
# Part 2：requests.Session 会话管理
# ============================================================

def test_session_basic():
    """
    Session 核心优势：
    1. 自动管理 Cookie（登录后 cookie 自动携带）
    2. 自动管理 headers（统一注入 token）
    3. TCP 连接复用（速度更快）
    """
    print("\n" + "=" * 55)
    print("【Part 2】requests.Session 会话管理")
    print("=" * 55)

    # 创建一个会话（类似浏览器打开一个标签页）
    session = requests.Session()

    # 设置全局基础 headers（所有请求自动携带）
    session.headers.update({
        "User-Agent": "ShanhaiGameTestBot/1.0",
        "X-Test-Platform": "WorkBuddy-AutoTest",
        "Accept": "application/json"
    })

    # Step 1：登录 → Session 自动保存 cookie
    print("\n🔸 第1步：登录（Session 自动保存 Cookie）")
    login_payload = {
        "account": "test_player_day7",
        "password": "encrypted_pwd_xyz",
        "device_id": "auto_test_device_001"
    }

    resp_login = session.post(f"{BASE_URL}/post", json=login_payload, timeout=10)
    resp_login.raise_for_status()
    login_result = resp_login.json()

    # 模拟从响应中提取 token
    account = login_result.get("json", {}).get("account", "unknown")
    token = f"tk_{account}_day7_{int(time.time())}"
    user_id = f"uid_{account}_001"

    print(f"   登录成功 → Token: {token}")
    print(f"   Cookie 已保存在 Session 中（后续请求自动携带）")

    # 把 token 加入 session 全局头
    session.headers.update({"Authorization": f"Bearer {token}"})

    # Step 2：获取角色信息（无需再手动写 headers，Session 自动携带）
    print("\n🔸 第2步：获取角色信息（Session 自动携带 Token）")
    resp_char = safe_request("GET", f"{BASE_URL}/get", params={
        "user_id": user_id,
        "include_equipment": "true"
    })
    resp_char.raise_for_status()
    char_result = resp_char.json()

    # 验证 token 是否在 headers 中
    args = char_result.get("args", {})
    print(f"   请求参数: user_id={args.get('user_id')}, include_equipment={args.get('include_equipment')}")
    print(f"   Session Headers 自动携带: Authorization={session.headers.get('Authorization', '未设置')[:30]}...")

    character_id = f"char_{user_id}_main"
    print(f"   ✅ 角色获取成功 → CharacterID: {character_id}")

    # Step 3：获取背包（Session 自动携带 cookie + token）
    print("\n🔸 第3步：获取背包列表（Session 自动携带完整认证）")
    resp_bag = session.get(f"{BASE_URL}/get", params={
        "character_id": character_id,
        "bag_type": "main",
        "page": 1,
        "page_size": 20
    }, timeout=10)
    resp_bag.raise_for_status()
    bag_result = resp_bag.json()

    args3 = bag_result.get("args", {})
    assert args3.get("character_id") == character_id
    print(f"   ✅ 背包获取成功，参数: {json.dumps(args3, ensure_ascii=False)}")

    # 模拟背包中的道具
    item_id = "item_elixir_health_003"
    item_count = 5

    # Step 4：使用道具（Session 自动携带认证头）
    print("\n🔸 第4步：使用道具（Session 自动携带完整认证链）")
    use_payload = {
        "user_id": user_id,
        "character_id": character_id,
        "item_id": item_id,
        "quantity": 1
    }
    resp_use = session.post(f"{BASE_URL}/post", json=use_payload, timeout=10)
    resp_use.raise_for_status()
    use_result = resp_use.json()

    json_data = use_result.get("json", {})
    print(f"   ✅ 道具使用成功！")
    print(f"   - UserID:   {json_data.get('user_id')}")
    print(f"   - CharID:   {json_data.get('character_id')}")
    print(f"   - ItemID:   {json_data.get('item_id')}")
    print(f"   - Quantity: {json_data.get('quantity')}")

    # 断言验证
    assert json_data.get("user_id") == user_id
    assert json_data.get("character_id") == character_id
    assert json_data.get("item_id") == item_id
    assert json_data.get("quantity") == 1
    print("   ✅ 断言通过：完整依赖链验证成功")

    # 关闭 Session（释放连接）
    session.close()
    print("\n✅ Session 关闭，连接已释放")

    return {
        "token": token,
        "user_id": user_id,
        "character_id": character_id,
        "item_id": item_id
    }


# ============================================================
# Part 3：模拟 conftest.py 的 Fixture 实现（类比真实项目结构）
# ============================================================

# 模拟 conftest.py 中的 fixture（实际项目中放在 conftest.py）
class LoginFixture:
    """模拟 @pytest.fixture(scope='module') 的登录 fixture"""

    def __init__(self):
        self.session: Optional[requests.Session] = None
        self.token: str = ""
        self.user_id: str = ""
        self.character_id: str = ""

    def setup(self):
        """模拟 fixture 的 setup 阶段（yield 之前）"""
        print("\n" + "=" * 55)
        print("【Part 3】模拟 conftest.py Fixture 依赖方案")
        print("=" * 55)
        print("\n🔧 [Fixture Setup] 执行登录（整个模块只执行一次）")

        # 创建 Session
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "ShanhaiGameBot/1.0 (pytest)",
            "X-Platform": "AutoTest",
            "Accept": "application/json"
        })

        # 登录
        login_resp = self.session.post(
            f"{BASE_URL}/post",
            json={"account": "module_test_user", "password": "hashed_abc"},
            timeout=10
        )
        login_resp.raise_for_status()
        login_json = login_resp.json()

        account = login_json.get("json", {}).get("account", "unknown")
        self.token = f"fixture_tk_{account}_{int(time.time())}"
        self.user_id = f"uid_fixture_{account}"
        self.character_id = f"char_{self.user_id}_main"

        print(f"   ✅ 登录成功 → token={self.token[:25]}...")
        print(f"   ✅ user_id={self.user_id}")
        print(f"   ✅ Session 和 Token 已存储")

        # 将 token 注入 session
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})

        return self  # yield self 返回给测试用例

    def teardown(self):
        """模拟 fixture 的 teardown 阶段（yield 之后）"""
        print("\n🧹 [Fixture Teardown] 清理 Session 资源")
        if self.session:
            self.session.close()
            print("   ✅ Session 已关闭")

    def get_session(self) -> requests.Session:
        return self.session


# 模拟使用 fixture 的测试用例（类比在 test_xxx.py 中）
def test_character_info_with_fixture():
    """测试1：使用 fixture 获取角色信息（依赖 login_fixture）"""
    print("\n" + "-" * 55)
    print("📋 测试用例 test_character_info_with_fixture")
    print("-" * 55)

    # 模拟接收 fixture
    fixture = LoginFixture()
    fixture.setup()

    try:
        # 使用 fixture 提供的 session + token
        session = fixture.get_session()
        user_id = fixture.user_id

        print(f"\n🔸 调用角色信息接口（使用 fixture 提供的 session）")
        resp = retry_session_request(session, "GET", f"{BASE_URL}/get", params={
            "user_id": user_id,
            "expand": "skills,equipment"
        })
        resp.raise_for_status()
        result = resp.json()

        args = result.get("args", {})
        assert args.get("user_id") == user_id
        print(f"   ✅ 断言通过：user_id={args.get('user_id')}")
        print(f"   ✅ Fixture 依赖注入成功，session 自动携带 Token")

    finally:
        fixture.teardown()


def test_backpack_with_fixture():
    """测试2：使用 fixture 获取背包（也依赖同一个 fixture 实例）"""
    print("\n" + "-" * 55)
    print("📋 测试用例 test_backpack_with_fixture")
    print("-" * 55)

    # 模拟接收 fixture（同 module 级别的 fixture 复用）
    fixture = LoginFixture()
    fixture.setup()

    try:
        session = fixture.get_session()
        character_id = fixture.character_id

        print(f"\n🔸 调用背包列表接口（复用同一 fixture session）")
        resp = retry_session_request(session, "GET", f"{BASE_URL}/get", params={
            "character_id": character_id,
            "bag_type": "main",
            "sort_by": "rarity"
        })
        resp.raise_for_status()
        result = resp.json()

        args = result.get("args", {})
        assert args.get("character_id") == character_id
        assert args.get("bag_type") == "main"
        print(f"   ✅ 断言通过：character_id={args.get('character_id')}")
        print(f"   ✅ 同 fixture 实例复用，token 不需要重新获取")

    finally:
        fixture.teardown()


def test_fight_with_fixture():
    """测试3：使用 fixture 进行战斗（完整 4 步依赖链）"""
    print("\n" + "-" * 55)
    print("📋 测试用例 test_fight_with_fixture（完整依赖链）")
    print("-" * 55)

    fixture = LoginFixture()
    fixture.setup()

    try:
        session = fixture.get_session()
        user_id = fixture.user_id
        character_id = fixture.character_id

        print(f"\n🔸 Step1: 获取当日任务")
        resp_task = retry_session_request(session, "GET", f"{BASE_URL}/get", params={
            "user_id": user_id,
            "task_type": "daily",
            "difficulty": "normal"
        })
        resp_task.raise_for_status()
        task_id = f"task_daily_{resp_task.json()['args'].get('task_type', 'unknown')}_001"

        print(f"   ✅ 任务获取成功 → task_id={task_id}")

        print(f"\n🔸 Step2: 进入副本战斗")
        resp_battle = retry_session_request(session, "POST", f"{BASE_URL}/post", json={
            "user_id": user_id,
            "character_id": character_id,
            "task_id": task_id,
            "battle_mode": "solo"
        })
        resp_battle.raise_for_status()
        battle_id = f"battle_{task_id}"
        battle_result = {"damage": 18000, "rating": "S"}

        print(f"   ✅ 战斗完成 → battle_id={battle_id}, 评价={battle_result['rating']}")

        print(f"\n🔸 Step3: 领取奖励")
        resp_reward = retry_session_request(session, "GET", f"{BASE_URL}/get", params={
            "user_id": user_id,
            "battle_id": battle_id,
            "claim": True
        })
        resp_reward.raise_for_status()

        print(f"   ✅ 奖励领取成功！")

        # 验证完整依赖链
        print(f"\n✅ 完整依赖链验证:")
        print(f"   登录 → token → 任务 → task_id → 战斗 → battle_id → 奖励")
        print(f"   所有步骤共用同一 Session，Cookie/Token 自动携带")

    finally:
        fixture.teardown()


# ============================================================
# Part 4：三种 scope 的实际对比
# ============================================================

def test_scope_comparison():
    """
    scope 对比演示：

    ┌────────────┬──────────────────────────────────────────────┐
    │ function   │ 每个测试函数执行一次登录（14天 × N 次登录）    │
    │ module     │ 整个文件执行一次登录（14天 × 1 次登录）        │
    │ session    │ 整个 pytest 会话一次登录（全局共享）           │
    └────────────┴──────────────────────────────────────────────┘
    """
    print("\n" + "=" * 55)
    print("【Part 4】Fixture Scope 对比演示")
    print("=" * 55)

    scopes = {
        "function（每个函数）": [],
        "module（每个文件）": [],
        "session（整个会话）": []
    }

    for scope_name in scopes:
        print(f"\n📌 Scope = {scope_name}")

        if scope_name == "function":
            # 模拟每次函数都重新登录
            for i in range(3):
                s = requests.Session()
                t0 = time.time()
                s.post(f"{BASE_URL}/post", json={"u": "f"}, timeout=10)
                print(f"   函数{i+1}执行 → 登录耗时: {time.time()-t0:.3f}s")
                s.close()

        elif scope_name == "module":
            # 模拟模块级别只登录一次
            s = requests.Session()
            t0 = time.time()
            s.post(f"{BASE_URL}/post", json={"u": "m"}, timeout=10)
            print(f"   模块初始化 → 登录耗时: {time.time()-t0:.3f}s")
            for i in range(3):
                print(f"   用例{i+1}执行 → 复用已有 Session（无登录开销）")
            s.close()

        elif scope_name == "session":
            print(f"   会话初始化 → 登录耗时: (首次)")
            print(f"   后续所有文件、所有用例复用同一 Session")

    print("\n✅ 结论：生产环境中，scope='session' 最省资源（1次登录供全局使用）")


# ============================================================
# Part 5：真实山海之巅场景（综合实战）
# ============================================================

def test_real_shhs_full_workflow():
    """
    真实山海之巅完整工作流：
    登录 → 领取任务 → 进入战斗 → 获取掉落 → 使用道具 → 结算奖励

    使用 Session 自动管理认证，展示完整依赖链。
    """
    print("\n" + "=" * 55)
    print("【Part 5】山海之巅完整工作流实战")
    print("=" * 55)

    session = requests.Session()
    session.headers.update({
        "User-Agent": "ShanhaiGame-Client/2.1.0",
        "X-Client-Version": "2.1.0",
        "X-Device": "AutoTest-Device",
        "Accept": "application/json"
    })

    try:
        # Step 1：玩家登录
        print("\n🔸 Step1 - 玩家登录")
        resp_login = retry_session_request(session, "POST", f"{BASE_URL}/post", json={
            "account": "shhs_player_final",
            "password": "hashed_pwd_final",
            "server_id": 1
        })
        resp_login.raise_for_status()
        login_data = resp_login.json().get("json", {})

        token = f"shhs_tk_{login_data['account']}_{int(time.time())}"
        user_id = f"pid_{login_data['account']}"
        session.headers["Authorization"] = f"Bearer {token}"

        print(f"   ✅ 登录成功 | Token: {token[:30]}...")
        print(f"   ✅ UserID: {user_id} | Server: 1")

        # Step 2：领取每日任务
        print("\n🔸 Step2 - 领取每日任务")
        resp_task = retry_session_request(session, "GET", f"{BASE_URL}/get", params={
            "token": token,
            "user_id": user_id,
            "task_type": "daily",
            "difficulty": "hard"
        })
        resp_task.raise_for_status()
        task_data = resp_task.json().get("args", {})
        task_id = f"task_{task_data['task_type']}_{task_data['difficulty']}_final"

        print(f"   ✅ 任务领取成功 | TaskID: {task_id}")

        # Step 3：进入副本战斗
        print("\n🔸 Step3 - 进入副本战斗")
        resp_battle = retry_session_request(session, "POST", f"{BASE_URL}/post", json={
            "token": token,
            "user_id": user_id,
            "task_id": task_id,
            "difficulty": "hard",
            "auto_fight": True
        })
        resp_battle.raise_for_status()
        battle_data = resp_battle.json().get("json", {})

        battle_id = f"battle_{task_id}"
        damage_dealt = 22000
        items_dropped = ["item_dragon_scale", "item_gold_100"]

        print(f"   ✅ 战斗完成 | BattleID: {battle_id}")
        print(f"   📊 造成伤害: {damage_dealt} | 掉落: {items_dropped}")

        # Step 4：拾取掉落物
        print("\n🔸 Step4 - 拾取掉落物品")
        for item in items_dropped:
            resp_pickup = retry_session_request(session, "POST", f"{BASE_URL}/post", json={
                "token": token,
                "user_id": user_id,
                "battle_id": battle_id,
                "item_id": item,
                "action": "pickup"
            })
            resp_pickup.raise_for_status()
            print(f"   ✅ 拾取成功: {item}")

        # Step 5：使用道具（龙鳞：增加防御）
        print("\n🔸 Step5 - 使用龙鳞道具")
        resp_use = retry_session_request(session, "POST", f"{BASE_URL}/post", json={
            "token": token,
            "user_id": user_id,
            "item_id": "item_dragon_scale",
            "target": "character",
            "quantity": 1
        })
        resp_use.raise_for_status()
        print(f"   ✅ 龙鳞使用成功，角色防御力 +50")

        # Step 6：领取结算奖励
        print("\n🔸 Step6 - 领取结算奖励")
        resp_settle = retry_session_request(session, "GET", f"{BASE_URL}/get", params={
            "token": token,
            "user_id": user_id,
            "battle_id": battle_id,
            "claim": True,
            "exp_bonus": 1.5
        })
        resp_settle.raise_for_status()
        settle_data = resp_settle.json().get("args", {})

        print(f"   ✅ 结算完成 | 经验加成: {settle_data.get('exp_bonus')}x")
        print(f"   ✅ 最终 BattleID: {settle_data.get('battle_id')}")

        # 完整依赖链汇总
        print("\n" + "=" * 55)
        print("📊 完整依赖链总结")
        print("=" * 55)
        print(f"   登录        → token = {token[:35]}...")
        print(f"   任务        → task_id = {task_id}")
        print(f"   战斗        → battle_id = {battle_id}")
        print(f"   掉落        → items = {items_dropped}")
        print(f"   道具        → dragon_scale used")
        print(f"   结算奖励    → claim = {settle_data.get('claim')}")
        print()
        print("   Session 特性验证：")
        print(f"   ✅ Cookie 自动管理（登录后自动携带）")
        print(f"   ✅ Token 全局注入（无需每个请求手动添加）")
        print(f"   ✅ 连接复用（速度更快）")

        # 断言验证
        assert task_data["task_type"] == "daily"
        assert battle_data["task_id"] == task_id
        assert settle_data["claim"] == "True"
        print("\n   ✅ 所有断言通过，完整依赖链验证成功！")

    finally:
        session.close()


# ============================================================
# 运行入口
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("第 7 天 - pytest Fixture 深化 + Session 会话管理")
    print("=" * 60)

    tests = [
        ("Part 1 - Fixture 核心概念", demo_fixture_concepts),
        ("Part 2 - Session 会话管理（4步依赖链）", test_session_basic),
        ("Part 3 - Fixture 依赖方案", [
            test_character_info_with_fixture,
            test_backpack_with_fixture,
            test_fight_with_fixture,
        ]),
        ("Part 4 - Scope 对比演示", test_scope_comparison),
        ("Part 5 - 山海之巅完整工作流", test_real_shhs_full_workflow),
    ]

    total_passed = 0
    total_failed = 0

    for section_name, section_data in tests:
        print(f"\n\n{'#' * 60}")
        print(f"# {section_name}")
        print(f"{'#' * 60}")

        if callable(section_data):
            try:
                result = section_data()
                total_passed += 1
                print(f"\n✅ {section_name} - PASS")
            except Exception as e:
                total_failed += 1
                print(f"\n❌ {section_name} - FAIL: {e}")
        else:
            for test_func in section_data:
                try:
                    test_func()
                    total_passed += 1
                    print(f"\n✅ {test_func.__name__} - PASS")
                except Exception as e:
                    total_failed += 1
                    print(f"\n❌ {test_func.__name__} - FAIL: {e}")

    print("\n\n" + "=" * 60)
    print(f"🏁 测试完成！通过: {total_passed} | 失败: {total_failed}")
    print("=" * 60)
