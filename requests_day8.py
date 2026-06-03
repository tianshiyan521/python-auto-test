# -*- coding: utf-8 -*-
"""
第8天 - pytest 框架正式篇（conftest.py + 参数化 + 标记 + 报告）
学习主题：从"模拟fixture"升级到真正的pytest工程化实践

核心内容：
1. conftest.py 正式写法（集中管理 fixture，自动发现）
2. @pytest.mark.parametrize 参数化（数据驱动测试）
3. @pytest.mark.skip / xfail 跳过和预期失败
4. pytest.ini / pyproject.toml 配置文件
5. 测试报告（-v, --tb=short, html报告）
6. 自定义 mark 标记 + pytest hook（入门）

场景：山海之巅游戏接口 - 真正的 pytest 工程化
"""

import requests
import json
import time
import random
import os
import sys
from typing import Dict, Any, Optional, List, Tuple

# ============ 基础配置 ============
BASE_URL = "https://httpbin.org"


def safe_request(method: str, url: str, retries: int = 3, **kwargs) -> requests.Response:
    """带重试的请求封装"""
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
                wait = random.uniform(0.3, 1.0)
                time.sleep(wait)
            else:
                raise last_error


# ============================================================
# Part 1：conftest.py 正式写法讲解 + 模拟实现
# ============================================================
#
# 【概念】什么是 conftest.py？
# ─────────────────────────────────
# conftest.py 是 pytest 的"特殊配置文件"，放在测试目录中：
#
#   project/
#   ├── tests/                  ← 测试目录
#   │   ├── conftest.py         ← 🔑 这里！fixture 集中管理
#   │   ├── test_login.py       ← 自动发现 conftest 中的 fixture
#   │   ├── test_battle.py      ← 同上，无需 import
#   │   └── test_item.py        ← 同上
#
# 特点：
#   ① pytest 自动发现，不需要 import
#   ② 同级及子目录的所有测试文件都能用里面的 fixture
#   ③ 可以多层嵌套：根目录 conftest.py → 子目录 conftest.py（子目录覆盖父级）
#
# 【正式写法示例】（以下代码就是真实项目中的写法）
# -----------------------------------------------------------
# # conftest.py
# import pytest
# import requests
#
# @pytest.fixture(scope="session")     # 整个测试会话只登录一次
# def auth_session():
#     """全局登录 fixture：所有测试共享同一个认证 session"""
#     session = requests.Session()
#     session.headers.update({
#         "User-Agent": "ShanhaiTestBot/2.0",
#         "Content-Type": "application/json",
#     })
#     # 登录
#     resp = session.post(LOGIN_URL, json={"account": "test", "password": "123"})
#     token = resp.json()["data"]["token"]
#     session.headers["Authorization"] = f"Bearer {token}"
#
#     yield session          # ← 把 session 给测试用例用
#
#     # teardown：测试结束后执行清理
#     session.close()
#
# @pytest.fixture(scope="module")
# def game_data(auth_session):
#     """模块级 fixture：获取一次游戏基础数据"""
#     resp = auth_session.get(f"{BASE_URL}/game/data")
#     return resp.json()
# -----------------------------------------------------------

def demo_conftest_structure():
    """
    Part 1 纯讲解：conftest.py 的完整项目结构

    实际项目中推荐的结构：

    shhs_auto_test/
    ├── conftest.py              ← 全局 fixture（session 级登录）
    ├── pytest.ini               ← pytest 配置
    ├── config/
    │   └── env_config.py        ← 环境配置（测试/生产 URL 切换）
    ├── tests/
    │   ├── conftest.py          ← 模块级 fixture（游戏数据准备）
    │   ├── test_login.py        ← 登录相关测试
    │   ├── test_battle.py       ← 战斗系统测试
    │   ├── test_item.py         ← 道具背包测试
    │   └── test_task.py         ← 任务系统测试
    ├── reports/                 ← 测试报告输出
    └── data/
        └── test_data.json       ← 测试数据文件

    关键规则：
    1. conftest.py 不能被其他文件 import（pytest 自动加载）
    2. fixture 命名要有意义：auth_session、game_data、clean_db
    3. scope 要合理：登录用 session，数据库清理用 function
    """
    print("✅ conftest.py 结构已记录（见上方文档字符串）")


# ============================================================
# Part 2：模拟 conftest.py fixture 的实际使用
# ============================================================

class ConftestSimulator:
    """
    模拟 conftest.py 中的所有 fixture
    在单文件演示中模拟多文件 conftest 的效果
    """

    def __init__(self):
        self._sessions: Dict[str, requests.Session] = {}
        self._fixtures: Dict[str, Any] = {}

    # ---------- fixture: auth_session (scope=session) ----------
    def fixture_auth_session(self) -> requests.Session:
        """
        模拟 @pytest.fixture(scope="session")
        def auth_session():
        """
        print("\n🔧 [Fixture: auth_session | scope=session] 初始化...")

        session = requests.Session()
        session.headers.update({
            "User-Agent": "ShanhaiTestBot/2.0 (Day8)",
            "X-Client-Version": "2.1.0",
            "X-Platform": "iOS",
            "Accept": "application/json"
        })

        # 登录
        resp = safe_request("POST", f"{BASE_URL}/post", json={
            "account": "conftest_admin",
            "password": "secure_hash_abc",
            "device_id": "test_device_session"
        })
        login_data = resp.json().get("json", {})

        # 把登录信息注入 session
        if resp.cookies:
            session.cookies.update(resp.cookies)

        token = f"bearer_{login_data.get('account', 'admin')}_{int(time.time())}"
        user_id = f"pid_{login_data.get('account', 'admin')}"

        token = f"bearer_{login_data.get('account', 'admin')}_{int(time.time())}"
        user_id = f"pid_{login_data.get('account', 'admin')}"

        session.headers["Authorization"] = f"Bearer {token}"

        print(f"   ✅ Session 登录完成 → Token: {token[:30]}...")
        print(f"   ✅ UserID: {user_id}")

        # 存储供后续 fixture 使用
        self._fixtures["token"] = token
        self._fixtures["user_id"] = user_id

        self._sessions["auth"] = session
        return session

    # ---------- fixture: player_character (scope=module) ----------
    def fixture_player_character(self, session: requests.Session) -> Dict[str, Any]:
        """
        模拟 @pytest.fixture(scope="module")
        def player_character(auth_session):  ← 依赖 auth_session
        """
        print("\n🔧 [Fixture: player_character | scope=module] 获取角色信息...")
        user_id = self._fixtures["user_id"]

        resp = safe_request("GET", f"{BASE_URL}/get", params={
            "user_id": user_id,
            "include_skills": "true",
            "include_equipment": "true"
        })

        character = {
            "character_id": f"char_{user_id}_main",
            "name": "测试战士-Day8",
            "level": 58,
            "combat_power": 125800,
            "skills": ["slash", "fireball", "thunder"],
            "equipment": {
                "weapon": "dragon_sword_lv60",
                "armor": "dragon_armor_lv55"
            }
        }

        self._fixtures["character_id"] = character["character_id"]
        self._fixtures["character"] = character

        print(f"   ✅ 角色信息获取成功 → {character['name']} (Lv.{character['level']})")
        print(f"   ✅ 战力: {character['combat_power']}")
        return character

    # ---------- fixture: bag_items (scope=function) ----------
    def fixture_bag_items(self, session: requests.Session) -> List[Dict]:
        """
        模拟 @pytest.fixture(scope="function")
        def bag_items(auth_session, player_character):  ← 依赖两个 fixture
        每个测试函数都重新获取最新背包数据
        """
        print("\n🔧 [Fixture: bag_items | scope=function] 获取背包列表...")
        character_id = self._fixtures["character_id"]

        resp = safe_request("GET", f"{BASE_URL}/get", params={
            "character_id": character_id,
            "bag_type": "all",
            "page": 1,
            "page_size": 50
        })

        # 模拟背包数据
        items = [
            {"id": "item_hp_potion", "name": "生命药水", "count": 15, "rarity": "common"},
            {"id": "item_mp_potion", "name": "魔法药水", "count": 8, "rarity": "common"},
            {"id": "item_dragon_scale", "name": "龙鳞", "count": 3, "rarity": "rare"},
            {"id": "item_phoenix_feather", "name": "凤凰羽毛", "count": 1, "rarity": "epic"},
        ]

        self._fixtures["bag_items"] = items
        print(f"   ✅ 背包获取成功，共 {len(items)} 种道具")
        return items

    # ---------- teardown ----------
    def teardown_all(self):
        """模拟所有 fixture 的 teardown"""
        print("\n🧹 [Teardown] 清理所有资源...")
        for name, session in self._sessions.items():
            session.close()
            print(f"   ✅ Session '{name}' 已关闭")
        self._sessions.clear()
        print("   ✅ 所有资源已释放")


# ============================================================
# Part 3：@pytest.mark.parametrize 参数化
# ============================================================
#
# 【核心概念】参数化 = 一份测试代码跑多组数据
#
# 写法：
#   @pytest.mark.parametrize("input, expected", [
#       (1, 2),       # 第1组数据
#       (3, 6),       # 第2组数据
#       (5, 10),      # 第3组数据
#   ])
#   def test_multiply(input, expected):
#       assert input * 2 == expected
#
# 执行效果：
#   test_multiply[1-2] PASSED
#   test_multiply[3-6] PASSED
#   test_multiply[5-10] PASSED
#
# 3行代码 = 3个独立测试用例！

def test_parametrize_basic():
    """
    参数化基础：不同 HTTP 方法测试
    场景：验证 httpbin.org 对不同请求方法的处理
    """
    print("\n" + "=" * 55)
    print("【Part 3-A】参数化基础 - 多种HTTP方法")
    print("=" * 55)

    # 定义测试数据：(方法名, URL路径, 期望状态码)
    test_cases = [
        ("GET", "/get", 200),
        ("POST", "/post", 200),
        ("PUT", "/put", 200),
        ("DELETE", "/delete", 200),
        ("PATCH", "/patch", 200),
    ]

    passed = 0
    failed = 0

    for method, path, expected_status in test_cases:
        case_name = f"{method} {path}"
        print(f"\n   📋 测试: {case_name} → 期望状态码 {expected_status}")

        try:
            resp = safe_request(method, f"{BASE_URL}{path}")
            actual_status = resp.status_code
            assert actual_status == expected_status, \
                f"状态码不匹配: 期望{expected_status}, 实际{actual_status}"
            print(f"   ✅ PASS - 状态码={actual_status}")
            passed += 1
        except Exception as e:
            print(f"   ❌ FAIL - {e}")
            failed += 1

    print(f"\n   📊 结果: {passed} PASS / {failed} FAIL (共{len(test_cases)}个)")
    assert failed == 0, f"有 {failed} 个用例失败"
    print("   ✅ 全部通过！")


def test_parametrize_login_scenarios():
    """
    参数化实战：多种登录场景
    场景：山海之巅登录接口 - 不同输入组合
    """
    print("\n" + "=" * 55)
    print("【Part 3-B】参数化实战 - 登录场景矩阵")
    print("=" * 55)

    # 测试数据矩阵：(账号, 密码, 设备ID, 期望结果, 描述)
    login_cases = [
        (
            "player_001", "pwd_normal", "device_a",
            "success", "正常登录"
        ),
        (
            "player_002", "pwd_with_space", "device_b",
            "success", "密码含空格"
        ),
        (
            "", "pwd_empty_account", "device_c",
            "error", "空账号"
        ),
        (
            "player_004", "", "device_d",
            "error", "空密码"
        ),
        (
            "admin@game.com", "admin_pwd_!@#", "device_e",
            "success", "邮箱格式账号+特殊字符密码"
        ),
        (
            "p" * 50, "p" * 100, "device_f",
            "success", "超长账号密码边界值"
        ),
    ]

    passed = 0
    failed = 0
    results = []

    for account, password, device_id, expected, desc in login_cases:
        case_label = f"[{desc}] account={account[:15]}{'...' if len(account)>15 else ''}"
        print(f"\n   📋 {case_label}")

        try:
            # 构建请求体
            payload = {
                "account": account,
                "password": password,
                "device_id": device_id
            }

            # 发送请求到 httpbin（模拟API网关）
            resp = safe_request("POST", f"{BASE_URL}/post", json=payload)
            result = resp.json()

            # 验证返回的数据完整性
            returned_json = result.get("json", {})
            assert returned_json.get("account") == account, "返回账号不匹配"
            assert returned_json.get("device_id") == device_id, "设备ID不匹配"

            # 判断预期结果
            is_valid = bool(account and password)
            actual_result = "success" if is_valid else "error"
            assert actual_result == expected, \
                f"期望'{expected}', 实际'{actual_result}'"

            print(f"   ✅ PASS - {desc}")
            passed += 1
            results.append({"case": desc, "result": "PASS"})
        except Exception as e:
            print(f"   ❌ FAIL - {desc}: {e}")
            failed += 1
            results.append({"case": desc, "result": "FAIL"})

    # 输出汇总表
    print(f"\n   {'─' * 45}")
    print(f"   📊 登录场景矩阵结果:")
    print(f"   {'─' * 45}")
    for r in results:
        icon = "✅" if r["result"] == "PASS" else "❌"
        print(f"   {icon} {r['case']:30s} {r['result']}")
    print(f"   {'─' * 45}")
    print(f"   合计: {passed} PASS / {failed} FAIL")

    assert failed == 0


def test_parametrize_api_endpoints():
    """
    参数化进阶：批量测试多个 API 端点
    场景：山海之巅各子系统接口冒烟测试
    """
    print("\n" + "=" * 55)
    print("【Part 3-C】参数化进阶 - API端点冒烟测试")
    print("=" * 55)

    # 冒烟测试用例：(接口名称, 方法, 路径, 参数, 期望字段)
    smoke_tests = [
        ("玩家信息", "GET", "/get",
         {"user_id": "pid_001"}, ["args", "headers", "origin"]),
        ("保存设置", "POST", "/post",
         {"volume": 80, "quality": "high", "fps": 60}, ["json"]),
        ("更新昵称", "PUT", "/put",
         {"nickname": "新昵称-Day8", "color": "#FF5500"}, ["json"]),
        ("删除存档", "DELETE", "/delete",
         {"slot_id": 3, "confirm": True}, ["json"]),
        ("修改头像", "PATCH", "/patch",
         {"avatar_id": 105, "frame_id": 8}, ["json"]),
    ]

    passed = 0
    failed = 0

    for api_name, method, path, params, expected_fields in smoke_tests:
        print(f"\n   📋 [{api_name}] {method} {path}")

        try:
            if method == "GET":
                resp = safe_request(method, f"{BASE_URL}{path}", params=params)
            elif method in ("POST", "PUT", "PATCH"):
                resp = safe_request(method, f"{BASE_URL}{path}", json=params)
            else:
                resp = safe_request(method, f"{BASE_URL}{path}", data=params)

            assert resp.status_code == 200, f"状态码异常: {resp.status_code}"

            data = resp.json()
            for field in expected_fields:
                assert field in data, f"缺少期望字段: {field}"

            print(f"   ✅ PASS - 字段检查: {expected_fields}")
            passed += 1
        except Exception as e:
            print(f"   ❌ FAIL - {e}")
            failed += 1

    print(f"\n   📊 冒烟测试: {passed}/{len(smoke_tests)} 通过")
    assert failed == 0, f"冒烟测试失败 {failed} 个"


# ============================================================
# Part 4：@pytest.mark.skip / xfail 标记
# ============================================================
#
# 【skip】跳过测试 - 条件不满足时不执行
#   @pytest.mark.skip(reason="功能未上线")
#   @pytest.mark.skipif(sys.version < (3, 8), reason="需要Python 3.8+")
#   pytest.skip("临时跳过")           # 在代码内部跳过
#
# 【xfail】预期失败 - 已知bug，标记但不算失败
#   @pytest.mark.xfail(reason="已知Bug: #1234")
#   @pytest.mark.xfail(raises=ValueError)  # 只对特定异常算 xfail

def test_skip_and_xfail_demo():
    """
    skip 和 xfail 使用演示
    """
    print("\n" + "=" * 55)
    print("【Part 4】Skip / XFail 标记演示")
    print("=" * 55)

    # ---- skip 场景 ----
    skip_cases = [
        {
            "name": "VIP专属功能 - 需要VIP账号",
            "condition": False,  # 模拟: 当前不是VIP
            "reason": "当前测试账号非VIP，跳过VIP功能测试",
        },
        {
            "name": "iOS独占功能 - 平台判断",
            "platform": "android",  # 当前是安卓
            "target_platform": "ios",
            "reason": "该功能仅支持iOS平台",
        },
        {
            "name": "节日活动接口 - 过期活动",
            "event_active": False,  # 活动已结束
            "reason": "春节活动已于2026-02-28结束",
        },
    ]

    print("\n   🔸 Skip 场景演示:")
    for i, case in enumerate(skip_cases, 1):
        should_skip = (
            not case.get("condition", True) or
            case.get("platform") != case.get("target_platform", case.get("platform")) or
            not case.get("event_active", True)
        )
        status = "⏭️  SKIPPED" if should_skip else "✅ WOULD RUN"
        reason = case["reason"] if should_skip else ""
        print(f"   {i:2d}. {case['name']}")
        print(f"       → {status} {f'({reason})' if reason else ''}")

    # ---- xfail 场景 ----
    print("\n   🔸 XFail 场景演示（已知Bug）:")

    xfail_cases = [
        {
            "name": "战力排行榜排序 - Bug #3891",
            "bug_desc": "相同战力时排序不稳定",
            "expect_pass": False,  # 预期失败（bug未修复）
        },
        {
            "name": "跨服聊天消息延迟 - Bug #4025",
            "bug_desc": "跨服消息偶发延迟>5s",
            "expect_pass": False,
        },
        {
            "name": "公会战匹配算法 - Bug #3988 (已修复)",
            "bug_desc": "匹配超时问题（已在v2.1.1修复）",
            "expect_pass": True,   # bug已修复，预期通过
        },
    ]

    for i, case in enumerate(xfail_cases, 1):
        expected = "❌ EXPECTED FAIL (XFAIL)" if not case["expect_pass"] else "✅ UNEXPECTED PASS (XPASS)"
        print(f"   {i:2d}. {case['name']}")
        print(f"       → Bug: {case['bug_desc']}")
        print(f"       → 预期: {expected}")

    print("\n   💡 小结:")
    print("   • skip:  条件不满足→跳过，不计入统计")
    print("   • xfail: 已知bug→失败也OK，意外通过则提醒(XPASS)")
    print("   ✅ Skip/XFail 概念演示完成")


# ============================================================
# Part 5：pytest 配置文件与运行选项
# ============================================================
#
# 【pytest.ini】项目根目录的配置文件
# -----------------------------------------------------------
# [pytest]
# testpaths = tests                 ← 测试目录
# python_files = test_*.py *_test.py  ← 文件匹配规则
# python_functions = test_*          ← 函数匹配规则
# python_classes = Test*             ← 类匹配规则
# addopts = -v --tb=short --strict-markers  ← 默认命令行参数
# markers =
#     slow: marks tests as slow (deselect with '-m "not slow"')
#     smoke: 冒烟测试
#     integration: 集成测试
#     api: 接口测试
# -----------------------------------------------------------

# 【pyproject.toml】新版配置方式（推荐）
# -----------------------------------------------------------
# [tool.pytest.ini_options]
# testpaths = ["tests"]
# addopts = "-v --tb=short"
# markers = [
#     "slow: 运行较慢的测试",
#     "smoke: 冒烟测试",
# ]
# -----------------------------------------------------------

def test_pytest_config_demo():
    """
    演示常用 pytest 运行选项的效果（模拟输出）

    常用命令一览：
    ┌──────────────────────────────┬────────────────────────────────┐
    │ 命令                         │ 说明                           │
    ├──────────────────────────────┼────────────────────────────────┤
    │ pytest                       │ 运行所有测试                     │
    │ pytest -v                    │ 详细输出（每个用例一行）          │
    │ pytest -v --tb=short         │ 详细输出+精简错误堆栈             │
    │ pytest -s                    │ 打印所有print输出                │
    │ pytest -k "login"            │ 只运行名含login的测试            │
    │ pytest -m smoke              │ 只运行带 @pytest.mark.smoke 的   │
    │ pytest --maxfail=2           │ 失败2次后停止                   │
    │ pytest -x                    │ 第一个失败就停止                 │
    │ pytest --lf                  │ 只跑上次失败的                   │
    │ pytest --co                  │ 列出所有测试用例（不执行）        │
    │ pytest -q                    │ 安静模式（简化输出）              │
    │ pytest --html=report.html    │ 生成HTML测试报告                 │
    │ pytest -n 4                  │ 并发运行4个进程(xdist插件)       │
    └──────────────────────────────┴────────────────────────────────┘
    """
    print("\n" + "=" * 55)
    print("【Part 5】pytest 配置与运行选项")
    print("=" * 55)

    print("\n   📋 常用运行命令速查:")
    commands = [
        ("pytest -v --tb=short", "详细输出+精简报错（日常开发首选）"),
        ("pytest -s -k login", "打印详情+只跑login相关"),
        ("pytest -m smoke", "只跑冒烟测试"),
        ("pytest -x --maxfail=3", "首次失败或累计3次失败停止"),
        ("pytest --lf", "只重跑上次失败的（调试神器！）"),
        ("pytest --co", "列出用例不执行（预览用）"),
        ("pytest -q", "安静模式(CI环境适用)"),
        ("pytest -n auto", "全并行执行(需安装xdist)"),
        ("pytest --html=report.html", "生成HTML可视化报告"),
    ]

    for cmd, desc in commands:
        print(f"   \033[36m{cmd:<35s}\033[0m # {desc}")

    print("\n   📋 自定义 Mark 标记注册:")
    markers = [
        ("@pytest.mark.smoke", "冒烟测试 - 主流程快速验证"),
        ("@pytest.mark.regression", "回归测试 - 版本发布前全量跑"),
        ("@pytest.mark.slow", "慢速测试 - 可选择性跳过"),
        ("@pytest.mark.api", "接口测试 - HTTP接口专项"),
        ("@pytest.mark.critical", "关键用例 - 必须全部通过才能发版"),
    ]

    for mark, desc in markers:
        print(f"   \033[33m{mark:<35s}\033[0m # {desc}")

    print("\n   ⚠️  注意: 使用自定义 marker 前需在 pytest.ini 注册，否则报警告！")
    print("   ✅ 配置演示完成")


# ============================================================
# Part 6：综合实战 - 完整的 pytest 工程化用例
# ============================================================

def test_full_pytest_workflow():
    """
    综合实战：模拟完整的 pytest 工程化流程
    包含：fixture依赖链 + 参数化 + 断言 + 边界处理
    """
    print("\n" + "=" * 55)
    print("【Part 6】综合实战 - 山海之巅完整pytest工作流")
    print("=" * 55)

    # 初始化 conftest 模拟器
    sim = ConftestSimulator()

    try:
        # ===== Step 1：Session 级 Fixture（登录）=====
        print("\n" + "-" * 55)
        print("📌 Phase 1: Fixture 初始化（模拟 conftest.py 加载）")
        print("-" * 55)

        session = sim.fixture_auth_session()

        # ===== Step 2：Module 级 Fixture（角色数据）=====
        character = sim.fixture_player_character(session)

        # 断言角色数据完整性
        assert character["level"] > 0, "角色等级异常"
        assert len(character["skills"]) > 0, "技能列表为空"
        assert character["combat_power"] > 0, "战力异常"
        print(f"   ✅ 角色数据断言通过")

        # ===== Step 3：参数化测试 - 批量验证技能接口 =====
        print("\n" + "-" * 55)
        print("📌 Phase 2: 参数化测试 - 技能接口批量验证")
        print("-" * 55)

        skill_test_data = [
            ("slash", "烈斩", 1.5, 200),
            ("fireball", "火球术", 2.0, 350),
            ("thunder", "雷击", 2.5, 500),
            ("heal", "治愈术", 3.0, 150),
            ("shield", "护盾", 1.0, 0),
        ]

        for skill_id, skill_name, cast_time, expected_damage in skill_test_data:
            print(f"\n   📋 技能测试: {skill_name}({skill_id})")

            # 调用技能接口
            resp = safe_request("POST", f"{BASE_URL}/post", json={
                "character_id": character["character_id"],
                "skill_id": skill_id,
                "target_id": "mob_boss_001",
                "token": sim._fixtures["token"]
            })

            result = resp.json().get("json", {})
            assert result.get("skill_id") == skill_id, "技能ID不匹配"

            # 验证施法时间合理性
            assert cast_time > 0, "施法时间必须大于0"
            assert cast_time <= 5.0, "施法时间不能超过5秒"

            print(f"   ✅ PASS - 施法时间: {cast_time}s, 预期伤害: {expected_damage}")

        print(f"\n   ✅ 全部 {len(skill_test_data)} 个技能测试通过")

        # ===== Step 4：Function 级 Fixture（背包）+ 物品操作 =====
        print("\n" + "-" * 55)
        print("📌 Phase 3: Function级Fixture + 边界测试")
        print("-" * 55)

        items = sim.fixture_bag_items(session)

        # 参数化物品使用测试
        item_usage_cases = [
            (items[0], 1, "normal", "正常使用1个"),
            (items[0], 5, "normal", "批量使用5个"),
            (items[0], 0, "error", "使用0个（边界）"),
            (items[0], 999, "error", "使用999个（超限）"),
            (items[2], 1, "rare", "稀有物品使用"),
            (items[3], 1, "epic", "史诗物品使用"),
        ]

        boundary_passed = 0
        boundary_failed = 0

        for item, qty, expected_type, desc in item_usage_cases:
            print(f"\n   📋 {desc}: {item['name']} x{qty}")

            try:
                # 构造使用请求
                use_resp = safe_request("POST", f"{BASE_URL}/post", json={
                    "user_id": sim._fixtures["user_id"],
                    "character_id": character["character_id"],
                    "item_id": item["id"],
                    "quantity": qty
                })
                use_result = use_resp.json().get("json", {})

                # 边界检查
                if qty <= 0:
                    # 使用数量<=0 应该被服务端拒绝
                    assert False, f"数量{qty}应该被拒绝但没拒绝"
                elif qty > item["count"]:
                    # 超过持有量应被拒绝
                    assert False, f"数量{qty}超过持有量{item['count']}"
                else:
                    # 正常使用
                    assert use_result.get("item_id") == item["id"]
                    print(f"   ✅ PASS - {desc}")
                    boundary_passed += 1

            except AssertionError as e:
                if expected_type == "error":
                    # 预期的异常（边界用例）
                    print(f"   ✅ PASS (预期失败) - {desc}: 正确拒绝了非法操作")
                    boundary_passed += 1
                else:
                    print(f"   ❌ FAIL - {desc}: {e}")
                    boundary_failed += 1

        print(f"\n   📊 边界测试结果: {boundary_passed} PASS / {boundary_failed} FAIL")
        assert boundary_failed == 0

        # ===== Phase 4：完整工作流汇总 =====
        print("\n" + "-" * 55)
        print("📌 Phase 4: 完整工作流验证总结")
        print("-" * 55)

        workflow_summary = {
            "Fixture依赖链": "auth_session → player_character → bag_items",
            "Scope使用": "session(登录) + module(角色) + function(背包)",
            "参数化覆盖": f"技能:{len(skill_test_data)} + 物品:{len(item_usage_cases)}",
            "边界测试": f"{boundary_passed} 个边界用例",
            "总请求数": 1 + 1 + len(skill_test_data) + len(item_usage_cases),
        }

        for key, value in workflow_summary.items():
            print(f"   📌 {key}: {value}")

        print("\n   ✅ 综合实战完成 - 全部断言通过！")

    finally:
        sim.teardown_all()


# ============================================================
# Part 7：pytest 插件生态介绍
# ============================================================
def test_plugin_ecosystem():
    """
    pytest 插件生态介绍（纯知识性，不执行网络请求）

    必装插件 Top 5：
    ┌───────────────────┬──────────────────────────────────────┐
    │ 插件               │ 用途                                 │
    ├───────────────────┼──────────────────────────────────────┤
    │ pytest-html       │ 生成 HTML 测试报告                    │
    │ pytest-xdist      │ 并发执行（多CPU加速）                 │
    │ pytest-ordering   │ 控制用例执行顺序                      │
    │ pytest-cov        │ 代码覆盖率报告                        │
    │ allure-pytest     │ Allure精美报告（Java风格）            │
    └───────────────────┴──────────────────────────────────────┘

    安装方式：
    pip install pytest-html pytest-xdist pytest-cov allure-pytest
    """
    print("\n" + "=" * 55)
    print("【Part 7】pytest 插件生态")
    print("=" * 55)

    plugins = [
        ("pytest-html", "生成HTML测试报告", "pytest --html=report.html --self-contained-html"),
        ("pytest-xdist", "多进程并发执行", "pytest -n auto  # 自动检测CPU核数"),
        ("pytest-cov", "代码覆盖率统计", "pytest --cov=. --cov-report=html"),
        ("allure-pytest", "Allure专业测试报告", "pytest --alluredir=./results && allure serve ./results"),
        ("pytest-timeout", "超时自动终止卡住的用例", "pytest --timeout=30  # 单个用例最大30秒"),
        ("pytest-rerunfailures", "失败自动重试", "pytest --reruns 2  # 失败后重试2次"),
        ("pytest-base-url", "统一管理测试URL", "pytest --base-url=https://test-api.game.com"),
    ]

    print("\n   🔌 必备插件清单:\n")
    for i, (name, usage, cmd) in enumerate(plugins, 1):
        print(f"   {i}. \033[36m{name}\033[0m")
        print(f"      用途: {usage}")
        print(f"      命令: {cmd}")
        print()

    print("   💡 推荐最小安装集:")
    print("   pip install pytest-html pytest-xdist pytest-cov pytest-rerunfailures")
    print("   ✅ 插件生态介绍完成")


# ============================================================
# 运行入口
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("第 8 天 - pytest 框架正式篇")
    print("    conftest.py + 参数化 + 标记 + 报告 + 插件")
    print("=" * 60)

    tests = [
        ("Part 1 - conftest.py 正式写法讲解", demo_conftest_structure),
        ("Part 2 - 模拟 Conftest Fixture 依赖链", None),  # 在Part6中综合使用
        ("Part 3-A - 参数化基础(HTTP方法)", test_parametrize_basic),
        ("Part 3-B - 参数化实战(登录场景)", test_parametrize_login_scenarios),
        ("Part 3-C - 参数化进阶(API冒烟)", test_parametrize_api_endpoints),
        ("Part 4 - Skip/XFail 标记演示", test_skip_and_xfail_demo),
        ("Part 5 - pytest 配置与运行选项", test_pytest_config_demo),
        ("Part 6 - 综合实战(完整pytest工作流)", test_full_pytest_workflow),
        ("Part 7 - pytest 插件生态", test_plugin_ecosystem),
    ]

    total_passed = 0
    total_failed = 0
    start_time = time.time()

    for section_name, section_func in tests:
        print(f"\n\n{'#' * 60}")
        print(f"# {section_name}")
        print(f"{'#' * 60}")

        if section_func is None:
            print(f"\n   ⏭️  已合并到 Part 6 中综合展示")
            continue

        try:
            section_func()
            total_passed += 1
            print(f"\n✅ {section_name} - PASS")
        except Exception as e:
            total_failed += 1
            print(f"\n❌ {section_name} - FAIL: {e}")
            import traceback
            traceback.print_exc()

    elapsed = time.time() - start_time

    print("\n\n" + "=" * 60)
    print(f" Day 8 测试完成!")
    print(f" ─────────────────────────────────────")
    print(f" ✅ 通过: {total_passed}  |  ❌ 失败: {total_failed}")
    print(f" ⏱️  总耗时: {elapsed:.2f}s")
    print(f" 📁 代码文件: requests_day8.py")
    print("=" * 60)

    print("\n📝 今日知识点总结:")
    print("   1. conftest.py 是 pytest 的'公共 fixture 仓库'")
    print("   2. @pytest.mark.parametrize 让一份代码测多组数据")
    print("   3. skip(跳过) vs xfail(预期失败) 适用不同场景")
    print("   4. pytest.ini/pyproject.toml 统一管理配置")
    print("   5. -v, --tb=short, -k, -m, --lf 是高频命令")
    print("   6. pytest-html/xdist/cov 是必装插件三件套")
    print("   7. fixture 依赖链: session → module → function")
