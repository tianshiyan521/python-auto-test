# =============================================================
# Python + Requests 14天学习计划 - Day 9
# 主题：pytest 框架 Day 2 — conftest.py 多文件实战 + pytest.ini + allure 报告
# 日期：2026-05-21
# =============================================================

"""
Day 9 学习大纲
=============
Part 1：conftest.py 多文件架构实战
    - 项目级 conftest.py（根目录）
    - 模块级 conftest.py（子目录）
    - fixture 作用域在多文件中的查找顺序
    - 共享 fixture、模块独享 fixture

Part 2：pytest.ini / pyproject.toml 深度配置
    - addopts 常用组合
    - markers 注册
    - log_cli 实时日志
    - testpaths / python_files / python_classes / python_functions 自定义

Part 3：allure 报告
    - 安装 allure-pytest
    - @allure.title / @allure.description / @allure.step
    - @allure.severity / @allure.feature / @allure.story
    - 生成 JSON 数据（--alluredir）
    - 用 Python 模拟 allure 报告结构（无需安装 allure CLI）

Part 4：综合实战 — 模拟山海之巅多模块测试项目
    - tests/
        conftest.py（项目级：auth_headers, api_base_url）
      ├── login/
      │     conftest.py（模块级：login_payload）
      │     test_login.py
      ├── player/
      │     conftest.py（模块级：player_token）
      │     test_player.py
      └── combat/
            test_combat.py
"""

import requests
import json
import time
import os
import sys
import random
import pytest
from datetime import datetime

# ── httpbin.org 作为模拟后端 ─────────────────────────────────────
BASE_URL = "https://httpbin.org"


# ─────────────────────────────────────────────────────────────────
# Part 1：conftest.py 多文件架构实战（代码内模拟，无需真实目录）
# ─────────────────────────────────────────────────────────────────

print("=" * 60)
print("Part 1：conftest.py 多文件架构实战")
print("=" * 60)


class ConftestArchDemo:
    """
    模拟多层 conftest.py 的 fixture 查找顺序。

    真实项目目录结构：
    ─────────────────────────────────────
    tests/
    ├── conftest.py          ← 项目级（session/module scope 全局可见）
    ├── login/
    │   ├── conftest.py      ← 模块级（只在 login/ 可见）
    │   └── test_login.py
    ├── player/
    │   ├── conftest.py      ← 模块级（只在 player/ 可见）
    │   └── test_player.py
    └── combat/
        └── test_combat.py   ← 无 conftest，直接用项目级 fixture
    ─────────────────────────────────────

    查找规则（从近到远）：
    1. 当前测试文件目录的 conftest.py
    2. 父目录 conftest.py
    3. 根目录 conftest.py
    4. pytest 内建 fixture
    """

    # ── 模拟项目级 conftest.py ───────────────────────────────────
    @staticmethod
    def project_conftest_fixtures():
        """项目级 fixture（scope=session）：全局共享，整个测试会话只初始化一次"""

        # fixture: api_base_url（session 级）
        api_base_url = BASE_URL
        print(f"  [项目级 conftest] api_base_url = {api_base_url}")

        # fixture: auth_headers（session 级）
        auth_headers = {
            "Authorization": "Bearer mock-token-abc123",
            "Content-Type": "application/json",
            "X-App-Version": "1.0.0"
        }
        print(f"  [项目级 conftest] auth_headers = {auth_headers}")

        return api_base_url, auth_headers

    # ── 模拟 login/ 模块级 conftest.py ──────────────────────────
    @staticmethod
    def login_module_conftest(api_base_url):
        """login 模块级 fixture（scope=module）：只在 login/ 目录内可用"""

        # fixture: login_payload（module 级）
        login_payload = {
            "username": "test_user",
            "password": "Test@12345",
            "platform": "PC"
        }
        print(f"  [login 模块 conftest] login_payload = {login_payload}")

        # fixture: login_response（module 级）：调用登录接口
        resp = requests.post(
            f"{api_base_url}/post",
            json=login_payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        login_response = {
            "status_code": resp.status_code,
            "token": "mock-token-from-login",
            "user_id": "u_10086"
        }
        print(f"  [login 模块 conftest] login_response.status = {resp.status_code}")
        return login_payload, login_response

    # ── 模拟 player/ 模块级 conftest.py ─────────────────────────
    @staticmethod
    def player_module_conftest(api_base_url, auth_headers):
        """player 模块级 fixture（scope=module）：依赖项目级 auth_headers"""

        # fixture: player_info（module 级）：调用玩家信息接口
        resp = requests.get(
            f"{api_base_url}/get",
            headers=auth_headers,
            params={"player_id": "p_88888", "level": 30},
            timeout=10
        )
        player_info = {
            "status_code": resp.status_code,
            "player_id": "p_88888",
            "level": 30,
            "character": "warrior"
        }
        print(f"  [player 模块 conftest] player_info.status = {resp.status_code}")
        return player_info


def demo_conftest_architecture():
    """演示多层 conftest.py 架构"""
    print("\n【场景】山海之巅多模块测试项目 conftest.py 架构演示\n")
    demo = ConftestArchDemo()

    # Step 1：项目级 fixture 初始化（session scope，全局唯一）
    print("─ Step 1：项目级 conftest.py（session 级 fixture）")
    api_base_url, auth_headers = demo.project_conftest_fixtures()

    # Step 2：login 模块级 fixture 初始化（module scope）
    print("\n─ Step 2：login/ 模块级 conftest.py（module 级 fixture）")
    login_payload, login_response = demo.login_module_conftest(api_base_url)

    # Step 3：player 模块级 fixture 初始化（module scope）
    print("\n─ Step 3：player/ 模块级 conftest.py（module 级 fixture）")
    player_info = demo.player_module_conftest(api_base_url, auth_headers)

    # Step 4：combat 测试（无模块级 conftest，直接使用项目级 fixture）
    print("\n─ Step 4：combat/ 测试（直接用项目级 fixture，无模块级 conftest）")
    resp = requests.post(
        f"{api_base_url}/post",
        headers=auth_headers,
        json={"action": "attack", "target": "boss_01", "skill": "blade_storm"},
        timeout=10
    )
    print(f"  [combat 无模块 conftest] combat.status = {resp.status_code}")

    print("\n✅ Part 1 完成：多层 conftest.py 架构演示通过")
    return {
        "api_base_url": api_base_url,
        "auth_headers": auth_headers,
        "login_response": login_response,
        "player_info": player_info,
        "combat_status": resp.status_code
    }


part1_result = demo_conftest_architecture()


# ─────────────────────────────────────────────────────────────────
# Part 2：pytest.ini 深度配置（打印配置内容 + 说明每项含义）
# ─────────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("Part 2：pytest.ini / pyproject.toml 深度配置")
print("=" * 60)

PYTEST_INI_CONTENT = """
[pytest]
# ── 默认运行选项 ───────────────────────────────────────────────
#  -v       : 详细输出（每条用例单独一行）
#  -s       : 不捕获 stdout（print 能实时显示）
#  --tb=short : 失败时只显示简短 traceback
#  --strict-markers : 未注册的 marker 会报错（防拼写错误）
addopts = -v -s --tb=short --strict-markers

# ── 自定义测试路径 ─────────────────────────────────────────────
testpaths = tests

# ── 自定义文件/类/函数命名规则 ────────────────────────────────
python_files = test_*.py *_test.py check_*.py
python_classes = Test* Check* Suite*
python_functions = test_* check_* verify_*

# ── 注册自定义 marker（防止 PytestUnknownMarkWarning）────────
markers =
    smoke:     冒烟测试 - 每次发布前必跑
    regression: 回归测试 - 完整功能验证
    login:     登录模块相关用例
    player:    玩家模块相关用例
    combat:    战斗模块相关用例
    slow:      慢速用例（>3s）
    flaky:     不稳定用例（网络抖动可能失败）

# ── 实时日志 ──────────────────────────────────────────────────
log_cli = true
log_cli_level = INFO
log_cli_format = %(asctime)s [%(levelname)s] %(name)s: %(message)s
log_cli_date_format = %H:%M:%S

# ── 超时设置（需 pytest-timeout 插件）─────────────────────────
timeout = 30

# ── 重跑失败用例（需 pytest-rerunfailures 插件）───────────────
# reruns = 2
# reruns_delay = 1
"""

PYPROJECT_TOML_CONTENT = """
[tool.pytest.ini_options]
addopts = "-v -s --tb=short --strict-markers"
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*", "Suite*"]
python_functions = ["test_*", "verify_*"]
markers = [
    "smoke: 冒烟测试",
    "regression: 回归测试",
    "login: 登录模块",
    "combat: 战斗模块",
]
log_cli = true
log_cli_level = "INFO"
timeout = 30
"""

print("\n📄 pytest.ini 配置文件内容（山海之巅项目）：")
print(PYTEST_INI_CONTENT)

print("📄 等效 pyproject.toml 配置（现代写法）：")
print(PYPROJECT_TOML_CONTENT)

# 常用运行命令速查
RUN_COMMANDS = [
    ("运行全部用例",            "pytest"),
    ("详细模式",               "pytest -v"),
    ("显示 print 输出",        "pytest -s"),
    ("只跑冒烟测试",            "pytest -m smoke"),
    ("只跑登录+玩家模块",       "pytest -m 'login or player'"),
    ("跳过慢速用例",            "pytest -m 'not slow'"),
    ("只跑包含关键字的用例",    "pytest -k 'login'"),
    ("失败停止",               "pytest -x"),
    ("只跑上次失败的用例",      "pytest --lf"),
    ("生成 HTML 报告",         "pytest --html=report.html --self-contained-html"),
    ("生成 allure 数据",        "pytest --alluredir=./allure-results"),
    ("查看 allure 报告",        "allure serve ./allure-results"),
    ("并发执行(4进程)",         "pytest -n 4"),
]

print("🚀 pytest 高频运行命令速查（共 {} 条）：".format(len(RUN_COMMANDS)))
for desc, cmd in RUN_COMMANDS:
    print(f"  {'·'} {desc:<20} →  {cmd}")

print("\n✅ Part 2 完成：pytest.ini 深度配置演示完成")


# ─────────────────────────────────────────────────────────────────
# Part 3：allure 报告（装饰器语法 + 模拟报告结构输出）
# ─────────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("Part 3：allure 报告集成")
print("=" * 60)

# ── 演示 allure 装饰器写法 ─────────────────────────────────────
ALLURE_DEMO_CODE = '''
import allure
import requests
import pytest

# ── allure 常用装饰器 ──────────────────────────────────────────

@allure.feature("用户登录")          # 功能模块（大分类）
@allure.story("正常登录流程")         # 用户故事（中分类）
@allure.title("测试正常用户名密码登录")  # 用例标题
@allure.severity(allure.severity_level.CRITICAL)  # 严重程度
def test_normal_login():
    """验证正常用户名密码可以成功登录"""

    with allure.step("Step 1: 准备登录参数"):
        payload = {"username": "admin", "password": "Admin@123"}
        allure.attach(
            json.dumps(payload, ensure_ascii=False),
            name="请求参数",
            attachment_type=allure.attachment_type.JSON
        )

    with allure.step("Step 2: 发送登录请求"):
        resp = requests.post("https://httpbin.org/post", json=payload)

    with allure.step("Step 3: 断言响应"):
        assert resp.status_code == 200, f"状态码异常: {resp.status_code}"
        data = resp.json()
        assert data["json"]["username"] == "admin"
        allure.attach(
            resp.text[:500],
            name="响应体",
            attachment_type=allure.attachment_type.TEXT
        )


@allure.feature("战斗系统")
@allure.story("普通攻击")
@allure.title("测试角色普通攻击命中率")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("skill,target", [
    ("普通攻击", "小怪"),
    ("必杀技", "精英怪"),
    ("AOE", "BOSS"),
])
def test_combat_attack(skill, target):
    with allure.step(f"使用 [{skill}] 攻击 [{target}]"):
        resp = requests.post(
            "https://httpbin.org/post",
            json={"skill": skill, "target": target}
        )
        assert resp.status_code == 200
'''

print("\n📋 allure 装饰器写法示例（实际用法）：")
print(ALLURE_DEMO_CODE)

# ── 模拟 allure 报告 JSON 结构 ────────────────────────────────
def build_allure_report_demo():
    """模拟生成 allure 报告的 JSON 数据结构（演示用）"""

    test_cases = [
        {
            "name": "test_normal_login",
            "title": "测试正常用户名密码登录",
            "feature": "用户登录",
            "story": "正常登录流程",
            "severity": "critical",
            "status": "passed",
            "duration_ms": 312,
            "steps": [
                {"name": "Step 1: 准备登录参数", "status": "passed"},
                {"name": "Step 2: 发送登录请求", "status": "passed"},
                {"name": "Step 3: 断言响应",    "status": "passed"},
            ]
        },
        {
            "name": "test_login_empty_password",
            "title": "测试空密码登录被拒绝",
            "feature": "用户登录",
            "story": "异常登录流程",
            "severity": "normal",
            "status": "passed",
            "duration_ms": 198,
            "steps": [
                {"name": "Step 1: 构造空密码请求", "status": "passed"},
                {"name": "Step 2: 验证响应 400",   "status": "passed"},
            ]
        },
        {
            "name": "test_combat_attack[普通攻击-小怪]",
            "title": "使用[普通攻击]攻击[小怪]",
            "feature": "战斗系统",
            "story": "普通攻击",
            "severity": "normal",
            "status": "passed",
            "duration_ms": 275,
            "steps": [
                {"name": "使用 [普通攻击] 攻击 [小怪]", "status": "passed"},
            ]
        },
        {
            "name": "test_combat_attack[必杀技-精英怪]",
            "title": "使用[必杀技]攻击[精英怪]",
            "feature": "战斗系统",
            "story": "普通攻击",
            "severity": "normal",
            "status": "passed",
            "duration_ms": 301,
            "steps": [
                {"name": "使用 [必杀技] 攻击 [精英怪]", "status": "passed"},
            ]
        },
        {
            "name": "test_get_player_bag",
            "title": "测试获取玩家背包列表",
            "feature": "玩家系统",
            "story": "背包管理",
            "severity": "minor",
            "status": "passed",
            "duration_ms": 224,
            "steps": [
                {"name": "Step 1: 带 token 请求背包接口", "status": "passed"},
                {"name": "Step 2: 验证背包数据结构",       "status": "passed"},
            ]
        },
    ]

    # 汇总统计
    total = len(test_cases)
    passed = sum(1 for t in test_cases if t["status"] == "passed")
    failed = total - passed
    total_ms = sum(t["duration_ms"] for t in test_cases)

    report = {
        "report_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "project": "山海之巅 API 自动化测试",
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": f"{passed/total*100:.1f}%",
            "total_duration_ms": total_ms
        },
        "test_cases": test_cases
    }
    return report


allure_report = build_allure_report_demo()

print("📊 模拟 allure 报告摘要（JSON 数据结构）：")
print(json.dumps(allure_report["summary"], ensure_ascii=False, indent=2))

print("\n📋 用例详情：")
for i, tc in enumerate(allure_report["test_cases"], 1):
    status_icon = "✅" if tc["status"] == "passed" else "❌"
    print(f"  {i}. {status_icon} [{tc['feature']}] {tc['title']}  ({tc['duration_ms']}ms)")
    for step in tc["steps"]:
        step_icon = "  ✓" if step["status"] == "passed" else "  ✗"
        print(f"      {step_icon} {step['name']}")

print(f"\n📈 测试通过率：{allure_report['summary']['pass_rate']}  "
      f"（{allure_report['summary']['passed']}/{allure_report['summary']['total']}）")

print("\n✅ Part 3 完成：allure 报告结构演示完成")


# ─────────────────────────────────────────────────────────────────
# Part 4：综合实战 — 多模块 pytest 测试套件（直接跑，不需要文件结构）
# ─────────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("Part 4：综合实战 — 山海之巅多模块测试套件")
print("=" * 60)

# ── 全局 session 级 fixture（模拟项目级 conftest.py）─────────
_SESSION_STATE = {}


def get_session_fixture():
    """模拟 session 级 fixture：全局只初始化一次"""
    if "auth" not in _SESSION_STATE:
        resp = requests.post(
            f"{BASE_URL}/post",
            json={"username": "admin", "password": "Admin@123", "platform": "PC"},
            timeout=10
        )
        assert resp.status_code == 200, "session fixture 登录失败"
        _SESSION_STATE["auth"] = {
            "token": "mock-session-token-xyz",
            "user_id": "u_99999",
            "headers": {
                "Authorization": "Bearer mock-session-token-xyz",
                "Content-Type": "application/json",
            }
        }
        print(f"  [session fixture] 初始化完成（token: {_SESSION_STATE['auth']['token'][:20]}...）")
    else:
        print("  [session fixture] 复用已有 session（无需重新登录）")
    return _SESSION_STATE["auth"]


# ── 测试用例集合 ───────────────────────────────────────────────

def _run_test(name: str, fn) -> dict:
    """统一执行测试并记录结果"""
    start = time.time()
    status = "PASSED"
    error_msg = ""
    try:
        fn()
    except AssertionError as e:
        status = "FAILED"
        error_msg = str(e)
    except Exception as e:
        status = "ERROR"
        error_msg = str(e)
    elapsed = round((time.time() - start) * 1000)
    icon = "✅" if status == "PASSED" else "❌"
    print(f"  {icon} {name:<42}  {status}  ({elapsed}ms)"
          + (f"  → {error_msg}" if error_msg else ""))
    return {"name": name, "status": status, "duration_ms": elapsed}


results = []

# ── Login 模块（模拟 tests/login/ conftest + test_login.py）────

print("\n── Login 模块 ──────────────────────────────────────────")

def test_login_normal():
    auth = get_session_fixture()
    resp = requests.post(
        f"{BASE_URL}/post",
        json={"username": "admin", "password": "Admin@123"},
        headers=auth["headers"],
        timeout=10
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["json"]["username"] == "admin"

def test_login_empty_username():
    resp = requests.post(
        f"{BASE_URL}/post",
        json={"username": "", "password": "Admin@123"},
        timeout=10
    )
    # httpbin 永远返回 200，这里模拟空值校验（业务层断言）
    data = resp.json()
    assert resp.status_code == 200  # httpbin 本身 200
    assert data["json"]["username"] == ""  # 空用户名被传递

def test_login_special_chars():
    resp = requests.post(
        f"{BASE_URL}/post",
        json={"username": "admin'; DROP TABLE users;--", "password": "test"},
        timeout=10
    )
    assert resp.status_code == 200  # 接口仍需正常响应（由业务层拒绝）
    data = resp.json()
    assert "username" in data["json"]

def test_login_with_platform_param():
    """登录携带 platform 参数（PC/Android/iOS）— 单次请求验证平台字段传递"""
    resp = requests.post(
        f"{BASE_URL}/post",
        json={"username": "admin", "password": "Admin@123", "platform": "PC"},
        headers={"Content-Type": "application/json"},
        timeout=15
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["json"]["platform"] == "PC"
    assert data["json"]["username"] == "admin"
    # 注：真实项目中用 @pytest.mark.parametrize 逐个验证，此处为避免超时只验证 PC

results.append(_run_test("test_login_normal",          test_login_normal))
results.append(_run_test("test_login_empty_username",  test_login_empty_username))
results.append(_run_test("test_login_special_chars",   test_login_special_chars))
results.append(_run_test("test_login_with_platform",   test_login_with_platform_param))

# ── Player 模块（模拟 tests/player/ conftest + test_player.py）─

print("\n── Player 模块 ─────────────────────────────────────────")

def test_player_get_info():
    auth = get_session_fixture()
    resp = requests.get(
        f"{BASE_URL}/get",
        headers=auth["headers"],
        params={"player_id": "p_12345", "fields": "name,level,hp"},
        timeout=10
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["args"]["player_id"] == "p_12345"
    assert data["args"]["fields"] == "name,level,hp"

def test_player_update_info():
    auth = get_session_fixture()
    resp = requests.put(
        f"{BASE_URL}/put",
        headers=auth["headers"],
        json={"player_id": "p_12345", "nickname": "战天一号", "avatar": "avatar_03"},
        timeout=10
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["json"]["nickname"] == "战天一号"

def test_player_get_bag():
    auth = get_session_fixture()
    resp = requests.get(
        f"{BASE_URL}/get",
        headers=auth["headers"],
        params={"player_id": "p_12345", "bag_type": "equipment"},
        timeout=10
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["args"]["bag_type"] == "equipment"

def test_player_equip_item():
    auth = get_session_fixture()
    resp = requests.post(
        f"{BASE_URL}/post",
        headers=auth["headers"],
        json={"action": "equip", "item_id": "sword_003", "slot": "main_hand"},
        timeout=10
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["json"]["action"] == "equip"
    assert data["json"]["slot"] == "main_hand"

results.append(_run_test("test_player_get_info",    test_player_get_info))
results.append(_run_test("test_player_update_info", test_player_update_info))
results.append(_run_test("test_player_get_bag",     test_player_get_bag))
results.append(_run_test("test_player_equip_item",  test_player_equip_item))

# ── Combat 模块（无模块级 conftest，直接使用项目级 fixture）──────

print("\n── Combat 模块 ─────────────────────────────────────────")

def test_combat_start():
    auth = get_session_fixture()
    resp = requests.post(
        f"{BASE_URL}/post",
        headers=auth["headers"],
        json={"action": "start_combat", "dungeon_id": "dungeon_007", "difficulty": "hard"},
        timeout=10
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["json"]["action"] == "start_combat"
    assert data["json"]["difficulty"] == "hard"

def test_combat_use_skill():
    auth = get_session_fixture()
    for skill in ["普通攻击", "蓄力斩", "回旋踢", "必杀技"]:
        resp = requests.post(
            f"{BASE_URL}/post",
            headers=auth["headers"],
            json={"action": "use_skill", "skill_name": skill, "target": "boss"},
            timeout=10
        )
        assert resp.status_code == 200
        assert resp.json()["json"]["skill_name"] == skill

def test_combat_end_settlement():
    auth = get_session_fixture()
    resp = requests.post(
        f"{BASE_URL}/post",
        headers=auth["headers"],
        json={
            "action": "end_combat",
            "result": "win",
            "kill_count": 15,
            "time_used_sec": 120,
            "rewards": ["exp_500", "gold_200", "item_sword_core"]
        },
        timeout=10
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["json"]["result"] == "win"
    assert data["json"]["kill_count"] == 15
    assert "item_sword_core" in data["json"]["rewards"]

def test_combat_timeout_handling():
    """战斗超时场景（模拟超时30分钟自动结算）"""
    auth = get_session_fixture()
    resp = requests.post(
        f"{BASE_URL}/post",
        headers=auth["headers"],
        json={
            "action": "timeout_settlement",
            "reason": "time_limit_exceeded",
            "elapsed_sec": 1800  # 30分钟
        },
        timeout=10
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["json"]["reason"] == "time_limit_exceeded"
    assert data["json"]["elapsed_sec"] == 1800

results.append(_run_test("test_combat_start",             test_combat_start))
results.append(_run_test("test_combat_use_skill",         test_combat_use_skill))
results.append(_run_test("test_combat_end_settlement",    test_combat_end_settlement))
results.append(_run_test("test_combat_timeout_handling",  test_combat_timeout_handling))

# ── 测试结果汇总 ───────────────────────────────────────────────

print("\n" + "=" * 60)
print("测试结果汇总")
print("=" * 60)

total   = len(results)
passed  = sum(1 for r in results if r["status"] == "PASSED")
failed  = total - passed
total_ms = sum(r["duration_ms"] for r in results)

print(f"\n  总用例数：{total}")
print(f"  通过：    {passed} ✅")
print(f"  失败：    {failed} ❌")
print(f"  通过率：  {passed/total*100:.1f}%")
print(f"  总耗时：  {total_ms}ms  ({total_ms/1000:.2f}s)")

# 按模块汇总
modules = {
    "Login":  [r for r in results if "login"  in r["name"]],
    "Player": [r for r in results if "player" in r["name"]],
    "Combat": [r for r in results if "combat" in r["name"]],
}
print("\n  模块分布：")
for mod, mod_results in modules.items():
    mod_passed = sum(1 for r in mod_results if r["status"] == "PASSED")
    print(f"    {mod:<8}: {mod_passed}/{len(mod_results)} 通过")


# ─────────────────────────────────────────────────────────────────
# 本日知识点回顾
# ─────────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("📚 Day 9 知识点回顾")
print("=" * 60)

KNOWLEDGE_SUMMARY = """
1. conftest.py 多文件架构
   ├─ 查找顺序：当前目录 → 父目录 → 根目录 → pytest 内建
   ├─ session scope：整个测试会话只初始化一次（适合 token、DB 连接）
   ├─ module scope：每个测试模块初始化一次（适合模块级准备数据）
   └─ function scope（默认）：每个测试函数都重新初始化

2. pytest.ini 关键配置项
   ├─ addopts：默认运行参数（如 -v -s --tb=short）
   ├─ markers：必须注册自定义 marker，否则 --strict-markers 报错
   ├─ testpaths：限定测试目录（加速发现）
   ├─ log_cli：实时日志输出（调试神器）
   └─ python_files/classes/functions：自定义命名规则

3. allure 报告装饰器速查
   ├─ @allure.feature / @allure.story   → 功能分类（大/中）
   ├─ @allure.title                     → 用例标题
   ├─ @allure.severity(BLOCKER/CRITICAL/NORMAL/MINOR/TRIVIAL)
   ├─ with allure.step("步骤名")        → 测试步骤（报告可展开）
   ├─ allure.attach(data, name, type)   → 附件（截图/JSON/文本）
   └─ 生成命令：pytest --alluredir=results && allure serve results

4. 多模块测试实战要点
   ├─ 项目级 conftest 存放：API base_url、auth_headers、DB 连接
   ├─ 模块级 conftest 存放：该模块专属的测试数据和 fixture
   ├─ 无模块 conftest 时：pytest 自动向上查找，直到根目录
   └─ fixture 依赖注入：直接写参数名，pytest 自动注入对应 fixture

5. 踩坑提醒
   ├─ pytest.ini 中的 markers 如果不注册 + 开启 --strict-markers，跑不起来
   ├─ conftest.py 必须放在 tests/ 目录下（不能放在 src/ 目录）
   ├─ allure-pytest 安装后还需要单独安装 allure CLI（Java程序）才能生成报告
   └─ 用 allure.attach 时，attachment_type 要从 allure.attachment_type 取常量
"""

print(KNOWLEDGE_SUMMARY)

print("=" * 60)
print(f"✅ Day 9 全部完成！时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"   共 {total} 个测试，{passed} 个通过，耗时 {total_ms/1000:.2f}s")
print("   下一步 → Day 10：数据驱动测试（CSV/Excel 读取 + parametrize 进阶）")
print("=" * 60)
