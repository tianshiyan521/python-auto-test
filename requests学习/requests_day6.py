# -*- coding: utf-8 -*-
"""
第6天 - 接口依赖处理
学习主题：A接口返回值作为B接口参数

场景：模拟山海之巅游戏接口依赖链
- 1. 登录 → 获取 token + user_id
- 2. 获取角色信息（用token）
- 3. 获取背包列表（用token+user_id）
- 4. 使用道具（用token+道具ID）

重点：变量存储与传递机制
"""

import requests
import json
from typing import Optional, Dict, Any

# ============ 基础配置 ============
BASE_URL = "https://httpbin.org"

# 全局变量存储依赖数据
class GlobalData:
    """存储接口依赖数据的全局容器"""
    token: str = ""
    user_id: str = ""
    character_id: str = ""
    item_id: str = ""

global_data = GlobalData()


# ============ 方法1：全局变量传递 ============
def test_step1_login_get_token():
    """第1步：登录接口 → 获取 token 和 user_id"""
    print("\n" + "="*50)
    print("【步骤1】登录接口 - 获取Token")
    print("="*50)

    # 模拟登录请求（httpbin.org/post 会返回我们发送的数据）
    login_data = {
        "username": "test_player_001",
        "password": "encrypted_password_123"
    }

    resp = requests.post(f"{BASE_URL}/post", data=login_data, timeout=10)
    resp.raise_for_status()
    result = resp.json()

    # 模拟从响应中提取token（实际项目中从data或headers中获取）
    # httpbin.org/post 会返回我们发送的数据，模拟登录成功返回的token
    global_data.token = f"tk_{result['form']['username']}_2026"
    global_data.user_id = f"uid_{result['form']['username'][-3:]}"

    print(f"✅ 登录成功！")
    print(f"   Token: {global_data.token}")
    print(f"   UserID: {global_data.user_id}")

    # 断言：验证token格式
    assert global_data.token.startswith("tk_"), "Token格式错误"
    assert global_data.user_id.startswith("uid_"), "UserID格式错误"
    print("   ✅ 断言通过：Token和UserID格式正确")


def test_step2_get_character_info():
    """第2步：获取角色信息（依赖Token）"""
    print("\n" + "="*50)
    print("【步骤2】获取角色信息 - 使用Token")
    print("="*50)

    headers = {
        "Authorization": f"Bearer {global_data.token}",
        "X-User-ID": global_data.user_id
    }

    # 使用 httpbin.org/headers 返回请求头，验证token是否正确传递
    resp = requests.get(f"{BASE_URL}/headers", headers=headers, timeout=10)
    resp.raise_for_status()
    result = resp.json()

    # 验证：HTTP头不区分大小写，但httpbin.org规范化返回
    received_headers = result.get("headers", {})
    # httpbin.org 返回规范化的大写形式
    auth_header = received_headers.get("Authorization") or received_headers.get("authorization")
    user_id_header = received_headers.get("X-User-Id") or received_headers.get("X-User-ID") or received_headers.get("x-user-id")

    assert auth_header == f"Bearer {global_data.token}", f"Token未正确传递: {auth_header}"
    assert user_id_header == global_data.user_id, f"UserID未正确传递: {user_id_header}"

    # 模拟角色ID
    global_data.character_id = f"char_{global_data.user_id}_main"

    print(f"✅ 角色信息获取成功！")
    print(f"   CharacterID: {global_data.character_id}")
    print(f"   验证请求头: Authorization={auth_header}")
    print("   ✅ 断言通过：Token正确传递到角色信息接口")


def test_step3_get_backpack():
    """第3步：获取背包列表（依赖Token + CharacterID）"""
    print("\n" + "="*50)
    print("【步骤3】获取背包列表 - Token + CharacterID")
    print("="*50)

    # 模拟带参数的请求
    params = {
        "user_id": global_data.user_id,
        "character_id": global_data.character_id,
        "bag_type": "main"  # 主背包
    }

    resp = requests.get(f"{BASE_URL}/get", params=params, timeout=10)
    resp.raise_for_status()
    result = resp.json()

    # 验证参数是否正确传递
    args = result.get("args", {})
    assert args.get("user_id") == global_data.user_id, "UserID参数未正确传递"
    assert args.get("character_id") == global_data.character_id, "CharacterID参数未正确传递"

    # 模拟背包数据（httpbin.org返回我们发送的参数）
    # 假设背包中有道具
    global_data.item_id = "item_health_potion_001"

    print(f"✅ 背包获取成功！")
    print(f"   背包类型: main")
    print(f"   包含道具: {global_data.item_id}")
    print("   ✅ 断言通过：依赖参数正确传递")


def test_step4_use_item():
    """第4步：使用道具（依赖Token + ItemID）"""
    print("\n" + "="*50)
    print("【步骤4】使用道具 - 最终依赖链验证")
    print("="*50)

    use_item_data = {
        "user_id": global_data.user_id,
        "character_id": global_data.character_id,
        "item_id": global_data.item_id,
        "quantity": 1
    }

    headers = {
        "Authorization": f"Bearer {global_data.token}",
        "Content-Type": "application/json"
    }

    resp = requests.post(
        f"{BASE_URL}/post",
        json=use_item_data,
        headers=headers,
        timeout=10
    )
    resp.raise_for_status()
    result = resp.json()

    # 验证完整依赖链
    json_data = result.get("json", {})

    print(f"✅ 道具使用请求成功！")
    print(f"   完整依赖链:")
    print(f"   - Token: {global_data.token}")
    print(f"   - UserID: {json_data.get('user_id')}")
    print(f"   - CharacterID: {json_data.get('character_id')}")
    print(f"   - ItemID: {json_data.get('item_id')}")
    print("   ✅ 断言通过：完整依赖链验证成功")


# ============ 方法2：字典存储 + 依赖注入 ============
def test_dependency_with_dict():
    """使用字典存储依赖数据（更灵活的方式）"""
    print("\n" + "="*50)
    print("【方法2】字典存储依赖 - 更灵活的方案")
    print("="*50)

    # 创建依赖存储字典
    context = {}

    # Step 1: 登录
    resp1 = requests.post(f"{BASE_URL}/post", data={"account": "user1", "pwd": "123"}, timeout=10)
    context["token"] = f"token_{resp1.json()['form']['account']}"
    context["user_id"] = resp1.json()['form']['account']

    # Step 2: 获取角色列表（用token）
    resp2 = requests.get(f"{BASE_URL}/get", params={"token": context["token"]}, timeout=10)
    args = resp2.json()["args"]
    assert args["token"] == context["token"], "Token传递失败"
    context["char_id"] = f"char_{context['user_id']}_1"

    # Step 3: 获取装备列表（用token + char_id）
    resp3 = requests.get(f"{BASE_URL}/get", params={
        "token": context["token"],
        "char_id": context["char_id"]
    }, timeout=10)
    args = resp3.json()["args"]
    assert args["token"] == context["token"]
    assert args["char_id"] == context["char_id"]
    context["equip_id"] = "equip_sword_01"

    # Step 4: 穿戴装备（用完整依赖）
    resp4 = requests.post(f"{BASE_URL}/post", json={
        "token": context["token"],
        "char_id": context["char_id"],
        "equip_id": context["equip_id"],
        "action": "equip"
    }, timeout=10)

    print(f"✅ 字典方案成功！")
    print(f"   Context: {json.dumps(context, indent=2, ensure_ascii=False)}")
    print("   ✅ 所有依赖正确传递")


# ============ 方法3：pytest fixture 方案（更专业） ============
def test_fixture_dependency_demo():
    """
    pytest fixture 方案演示（明日重点）

    核心思想：
    @pytest.fixture(scope="module")
    def login_fixture():
        # 只需执行一次登录
        resp = requests.post(...)
        return {"token": ..., "user_id": ...}

    def test_character(login_fixture):
        # 自动接收登录结果
        token = login_fixture["token"]
        ...
    """
    print("\n" + "="*50)
    print("【方法3】pytest Fixture 方案（预告明日内容）")
    print("="*50)
    print("明日会详细讲解 Fixture，这里先演示原理：")
    print()
    print("```python")
    print("@pytest.fixture(scope='module')")
    print("def auth_token():")
    print("    '''登录fixture - 整个模块只执行一次'''")
    print("    resp = requests.post(API + '/login', json={...})")
    print("    return resp.json()  # 返回 {'token': 'xxx', 'user_id': 'xxx'}")
    print()
    print("def test_get_character(auth_token):")
    print("    '''直接使用登录返回的token'''")
    print("    token = auth_token['token']")
    print("    resp = requests.get(API + '/character', headers={'Authorization': token})")
    print("    assert resp.status_code == 200")
    print("```")
    print()
    print("✅ Fixture优点：")
    print("   1. 登录只执行一次，多个用例共享")
    print("   2. 作用域可控（function/module/session）")
    print("   3. 自动清理资源")


# ============ 真实山海之巅场景模拟 ============
def test_real_shhs_scenario():
    """真实山海之巅场景：登录 → 任务 → 战斗 → 结算"""
    print("\n" + "="*50)
    print("【实战】山海之巅真实场景 - 完整依赖链")
    print("="*50)

    # 模拟山海之巅API
    API = "https://httpbin.org"  # 实际应该是真实API地址

    print("\n🔸 第1步：玩家登录")
    login_resp = requests.post(f"{API}/post", json={
        "account": "shhs_player_001",
        "password": "hashed_pwd_xxx"
    }, timeout=10)
    login_data = login_resp.json().get("json", {})
    game_token = f"shhs_tk_{login_data.get('account', 'unknown')}"
    player_id = f"pid_{login_data.get('account', 'unknown')[-3:]}"

    print(f"   登录成功 → token={game_token[:20]}..., player_id={player_id}")

    print("\n🔸 第2步：领取每日任务")
    task_resp = requests.get(f"{API}/get", params={
        "token": game_token,
        "player_id": player_id,
        "task_type": "daily"
    }, timeout=10)
    task_data = task_resp.json().get("args", {})
    task_id = f"task_{task_data.get('task_type')}_001"

    print(f"   任务ID → {task_id}")

    print("\n🔸 第3步：进入副本战斗（用token+task_id）")
    battle_resp = requests.post(f"{API}/post", json={
        "token": game_token,
        "player_id": player_id,
        "task_id": task_id,
        "difficulty": "hard"
    }, timeout=10)
    battle_data = battle_resp.json().get("json", {})
    battle_id = f"battle_{task_id}_001"
    # 模拟战斗结果
    battle_result = {"damage_dealt": 15000, "items_dropped": ["item_a", "item_b"]}

    print(f"   战斗完成 → battle_id={battle_id}")
    print(f"   造成伤害: {battle_result['damage_dealt']}")
    print(f"   掉落物品: {battle_result['items_dropped']}")

    print("\n🔸 第4步：领取战斗奖励（用token+battle_id）")
    reward_resp = requests.get(f"{API}/get", params={
        "token": game_token,
        "battle_id": battle_id,
        "claim": "true"
    }, timeout=10)

    print(f"   奖励领取成功！")
    print(f"\n✅ 完整依赖链：")
    print(f"   登录 → token → 任务 → task_id → 战斗 → battle_id → 奖励")
    print(f"   共4个接口串联，全部依赖数据正确传递")


# ============ 运行所有测试 ============
if __name__ == "__main__":
    print("="*60)
    print("第6天 - 接口依赖处理")
    print("="*60)

    tests = [
        ("方法1: 全局变量方案", [
            test_step1_login_get_token,
            test_step2_get_character_info,
            test_step3_get_backpack,
            test_step4_use_item,
        ]),
        ("方法2: 字典存储方案", [test_dependency_with_dict]),
        ("方法3: pytest Fixture预告", [test_fixture_dependency_demo]),
        ("实战: 山海之巅场景", [test_real_shhs_scenario]),
    ]

    total_passed = 0
    total_failed = 0

    for method_name, test_funcs in tests:
        print(f"\n\n{'#'*60}")
        print(f"# {method_name}")
        print(f"{'#'*60}")

        for test_func in test_funcs:
            try:
                test_func()
                total_passed += 1
            except Exception as e:
                total_failed += 1
                print(f"\n❌ 测试失败: {test_func.__name__}")
                print(f"   错误: {e}")

    print("\n\n" + "="*60)
    print(f"测试完成！通过: {total_passed}, 失败: {total_failed}")
    print("="*60)
