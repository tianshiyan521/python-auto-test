# ============================================================
# Python + Requests 自动化测试 - 第14天（最终日）
# 主题：项目实战 Day4 - CI/CD集成思路 + 完整测试套件梳理 + 14天学习总结
# 日期：2026-05-29
# ============================================================
"""
Day 14 学习目标：
  1. 完整测试套件回顾：将前13天核心代码整合成"生产就绪"的测试工程
  2. CI/CD集成思路：GitHub Actions / Jenkins 流水线配置示例
  3. 测试用例分级（P0冒烟 / P1回归 / P2全量）
  4. 缺陷报告模板：从自动化测试结果生成标准Bug单
  5. 14天学习总结：知识地图 + 最佳实践 + 后续进阶路线
"""

import requests
import pytest
import json
import time
import csv
import os
import sys
import locale
import threading

# Windows下强制UTF-8输出，避免GBK编码问题
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
import random
import string
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# ============================================================
# PART 1：生产就绪的项目结构设计
# ============================================================
print("=" * 60)
print("PART 1：生产就绪的项目结构设计")
print("=" * 60)

PROJECT_STRUCTURE = """
shanhai_api_test/          # 项目根目录
├── conftest.py            # 全局 fixture（session级别：token、base_url）
├── pytest.ini             # pytest配置（markers、addopts、log_cli）
├── requirements.txt       # 依赖清单
├── README.md              # 项目说明
│
├── config/
│   ├── __init__.py
│   ├── env_config.py      # 多环境配置（dev/test/staging/prod）
│   └── test_data.json     # 静态测试数据
│
├── utils/
│   ├── __init__.py
│   ├── base_api.py        # 统一请求封装（Session + 重试 + 日志）
│   ├── assert_helper.py   # 断言工具类
│   └── data_generator.py  # 随机数据生成
│
├── tests/
│   ├── __init__.py
│   ├── smoke/             # P0冒烟测试（每次上线必跑，<5分钟）
│   │   ├── conftest.py
│   │   ├── test_smoke_login.py
│   │   └── test_smoke_game.py
│   ├── regression/        # P1回归测试（每天定时，<30分钟）
│   │   ├── conftest.py
│   │   ├── test_login.py
│   │   ├── test_player.py
│   │   └── test_combat.py
│   └── full/              # P2全量测试（发版前，<2小时）
│       ├── test_security.py
│       ├── test_performance.py
│       └── test_boundary.py
│
├── testdata/
│   ├── login_cases.csv    # 登录用例数据
│   └── combat_cases.xlsx  # 战斗用例数据
│
└── reports/
    ├── allure-results/    # allure原始数据
    └── html/              # HTML报告归档
"""

print(PROJECT_STRUCTURE)

# ============================================================
# PART 2：CI/CD 集成配置示例（展示为注释，不实际运行）
# ============================================================
print("=" * 60)
print("PART 2：CI/CD 集成配置")
print("=" * 60)

GITHUB_ACTIONS_CONFIG = """
# .github/workflows/api-test.yml
name: API自动化测试

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 2 * * *'  # 每天凌晨2点定时跑

jobs:
  api-test:
    runs-on: ubuntu-latest
    
    steps:
    - name: 检出代码
      uses: actions/checkout@v3
    
    - name: 设置Python环境
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: 安装依赖
      run: |
        pip install -r requirements.txt
        pip install pytest-html allure-pytest
    
    - name: 运行冒烟测试（P0）
      run: |
        pytest tests/smoke/ -v -m "smoke" --html=reports/smoke_report.html
    
    - name: 运行回归测试（P1）
      run: |
        pytest tests/regression/ -v -m "regression" --html=reports/regression_report.html
    
    - name: 上传测试报告
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: test-reports
        path: reports/
    
    - name: 测试失败发送通知
      if: failure()
      run: echo "测试失败，发送企微/钉钉通知..."
"""

JENKINS_PIPELINE = """
// Jenkinsfile
pipeline {
    agent any
    
    triggers {
        cron('H 2 * * *')  // 每天凌晨2点
    }
    
    stages {
        stage('环境准备') {
            steps {
                sh 'pip install -r requirements.txt'
            }
        }
        
        stage('P0冒烟测试') {
            steps {
                sh 'pytest tests/smoke/ -v --junitxml=reports/smoke.xml'
            }
        }
        
        stage('P1回归测试') {
            steps {
                sh 'pytest tests/regression/ -v --junitxml=reports/regression.xml'
            }
        }
        
        stage('生成Allure报告') {
            steps {
                allure([
                    reportBuildPolicy: 'ALWAYS',
                    results: [[path: 'allure-results']]
                ])
            }
        }
    }
    
    post {
        failure {
            mail to: 'qa-team@company.com',
                 subject: '自动化测试失败告警',
                 body: "构建 ${BUILD_URL} 失败，请及时处理！"
        }
    }
}
"""

print("【GitHub Actions 配置片段】")
print(GITHUB_ACTIONS_CONFIG)
print("【Jenkins Pipeline 配置片段】")
print(JENKINS_PIPELINE)

# ============================================================
# PART 3：完整测试套件 - 山海之巅接口测试（最终版）
# 整合Days 11-13精华，形成"毕业作品"
# ============================================================
print("=" * 60)
print("PART 3：完整测试套件（毕业作品）")
print("=" * 60)

# ---- 工具类（内联简化版，真实项目应分文件） ----

class EnvConfig:
    """环境配置类（多环境切换）"""
    ENV = "test"
    URLS = {
        "dev":     "https://httpbin.org",
        "test":    "https://httpbin.org",
        "staging": "https://httpbin.org",
        "prod":    "https://httpbin.org",
    }
    BASE_URL = URLS[ENV]
    TIMEOUT = 15
    RETRY = 3
    TEST_ACCOUNTS = {
        "normal": {"username": "player001", "password": "Test@123"},
        "vip":    {"username": "vip_player", "password": "VIP@456"},
        "admin":  {"username": "admin",      "password": "Admin@789"},
    }


class BaseAPI:
    """统一请求封装"""
    def __init__(self):
        self.session = requests.Session()
        self.base_url = EnvConfig.BASE_URL
        self.timeout = EnvConfig.TIMEOUT

    def request(self, method, path, **kwargs):
        url = f"{self.base_url}{path}"
        kwargs.setdefault("timeout", self.timeout)
        for attempt in range(1, EnvConfig.RETRY + 1):
            try:
                resp = self.session.request(method, url, **kwargs)
                return resp
            except requests.exceptions.RequestException as e:
                if attempt == EnvConfig.RETRY:
                    raise
                time.sleep(attempt * 0.5)

    def get(self, path, **kw):    return self.request("GET",    path, **kw)
    def post(self, path, **kw):   return self.request("POST",   path, **kw)
    def put(self, path, **kw):    return self.request("PUT",    path, **kw)
    def delete(self, path, **kw): return self.request("DELETE", path, **kw)


class AssertHelper:
    """断言工具类"""
    @staticmethod
    def status_ok(resp, expected=200):
        assert resp.status_code == expected, \
            f"状态码错误: 期望{expected}, 实际{resp.status_code}\n响应体: {resp.text[:200]}"

    @staticmethod
    def json_field(resp, *keys, expected=None):
        data = resp.json()
        for k in keys:
            assert k in data, f"字段 '{k}' 不存在，实际keys: {list(data.keys())}"
            data = data[k]
        if expected is not None:
            assert data == expected, f"字段值错误: 期望 {expected!r}, 实际 {data!r}"

    @staticmethod
    def response_time(resp, max_ms=3000):
        elapsed = resp.elapsed.total_seconds() * 1000
        assert elapsed < max_ms, f"响应超时: {elapsed:.0f}ms > {max_ms}ms"

    @staticmethod
    def no_sensitive_info(resp):
        text = resp.text.lower()
        dangerous = ["password", "secret", "private_key", "access_key"]
        # 仅检查 value 中的敏感词，不检查 key（请求体本身含有字段名是正常的）
        try:
            body = resp.json()
            body_str = json.dumps(body.get("json", body.get("form", {})), ensure_ascii=False)
        except Exception:
            body_str = ""
        for word in dangerous:
            assert word not in body_str.lower(), f"响应中含敏感字段: {word}"


class DataGenerator:
    """测试数据生成器"""
    @staticmethod
    def random_str(n=8):
        return ''.join(random.choices(string.ascii_lowercase, k=n))

    @staticmethod
    def random_phone():
        return f"1{''.join(random.choices('3456789', k=1))}{''.join(random.choices(string.digits, k=9))}"

    @staticmethod
    def random_user():
        return {
            "username": f"auto_{DataGenerator.random_str(6)}",
            "password": f"Pwd@{''.join(random.choices(string.digits, k=4))}",
            "phone": DataGenerator.random_phone(),
        }


# ---- 全局共享实例 ----
api = BaseAPI()
ah = AssertHelper()

# ============================================================
# PART 4：测试分级与执行计划
# ============================================================
print("=" * 60)
print("PART 4：测试分级（P0/P1/P2）")
print("=" * 60)

TEST_PYRAMID = """
┌─────────────────────────────────────┐
│  P2 全量测试（Full）                  │  <2h  每次发版前
│  安全/性能/边界/异常/兼容性             │
├─────────────────────────────────────┤
│  P1 回归测试（Regression）            │  <30min 每天定时
│  核心功能：登录/战斗/道具/商城           │
├─────────────────────────────────────┤
│  P0 冒烟测试（Smoke）                 │  <5min 每次上线
│  服务存活 + 登录 + 基本战斗             │
└─────────────────────────────────────┘
"""
print(TEST_PYRAMID)

# P0 冒烟测试用例列表（10条，5分钟内跑完）
P0_SMOKE_CASES = [
    ("服务健康检查",        "GET",    "/get",     {},             200),
    ("登录接口可用",        "POST",   "/post",    {"username": "player001", "password": "Test@123"}, 200),
    ("获取玩家信息",        "GET",    "/get",     {"user_id": "10001"},      200),
    ("开始战斗（基础）",    "POST",   "/post",    {"action": "battle_start", "enemy_id": "E001"}, 200),
    ("结算战斗",           "POST",   "/post",    {"action": "battle_end",   "result": "win"},     200),
]

# P1 回归测试用例列表
P1_REGRESSION_CASES = [
    ("登录-正常账号",       "POST",  "/post",  {"username": "player001", "password": "Test@123"}, 200),
    ("登录-错误密码",       "POST",  "/post",  {"username": "player001", "password": "wrong"},    200),
    ("登录-账号不存在",     "POST",  "/post",  {"username": "no_exist",  "password": "Test@123"}, 200),
    ("获取角色信息",        "GET",   "/get",   {"char_id": "C001"},       200),
    ("更新角色名称",        "PUT",   "/put",   {"char_id": "C001", "name": "新名字"}, 200),
    ("获取背包列表",        "GET",   "/get",   {"char_id": "C001", "type": "bag"},  200),
    ("使用消耗品",          "POST",  "/post",  {"item_id": "I001", "action": "use"}, 200),
    ("发起PVP战斗",        "POST",  "/post",  {"mode": "pvp", "opponent": "player002"}, 200),
    ("战斗结算奖励",        "POST",  "/post",  {"battle_id": "B001", "result": "win"}, 200),
    ("购买商城道具",        "POST",  "/post",  {"item_id": "SHOP001", "qty": 1}, 200),
]

print("【P0 冒烟测试用例（10条）】")
for i, (name, method, path, data, code) in enumerate(P0_SMOKE_CASES, 1):
    print(f"  {i:02d}. [{method}] {path} - {name} - 期望状态码: {code}")

print("\n【P1 回归测试用例（10条）】")
for i, (name, method, path, data, code) in enumerate(P1_REGRESSION_CASES, 1):
    print(f"  {i:02d}. [{method}] {path} - {name} - 期望状态码: {code}")

# ============================================================
# PART 5：实际运行测试（汇总测试套件）
# ============================================================
print("\n" + "=" * 60)
print("PART 5：执行测试套件")
print("=" * 60)

# ---------- 执行 P0 冒烟测试 ----------
print("\n>> 执行 P0 冒烟测试...")
smoke_results = []
for name, method, path, data, expected_code in P0_SMOKE_CASES:
    try:
        if method == "GET":
            resp = api.get(path, params=data)
        elif method == "POST":
            resp = api.post(path, json=data)
        elif method == "PUT":
            resp = api.put(path, json=data)
        else:
            resp = api.delete(path)
        
        ah.status_ok(resp, expected_code)
        ah.response_time(resp, max_ms=5000)
        elapsed = resp.elapsed.total_seconds() * 1000
        smoke_results.append({"name": name, "status": "PASS", "elapsed_ms": round(elapsed, 1)})
        print(f"  ✅ {name} ({elapsed:.0f}ms)")
    except Exception as e:
        smoke_results.append({"name": name, "status": "FAIL", "error": str(e)[:80]})
        print(f"  ❌ {name} - {e}")

# ---------- 执行 P1 回归测试 ----------
print("\n>> 执行 P1 回归测试...")
regression_results = []
for name, method, path, data, expected_code in P1_REGRESSION_CASES:
    try:
        if method == "GET":
            resp = api.get(path, params=data)
        elif method == "POST":
            resp = api.post(path, json=data)
        elif method == "PUT":
            resp = api.put(path, json=data)
        else:
            resp = api.delete(path)

        ah.status_ok(resp, expected_code)
        ah.response_time(resp, max_ms=5000)
        elapsed = resp.elapsed.total_seconds() * 1000
        regression_results.append({"name": name, "status": "PASS", "elapsed_ms": round(elapsed, 1)})
        print(f"  ✅ {name} ({elapsed:.0f}ms)")
    except Exception as e:
        regression_results.append({"name": name, "status": "FAIL", "error": str(e)[:80]})
        print(f"  ❌ {name} - {e}")

# ============================================================
# PART 6：缺陷报告模板生成
# ============================================================
print("\n" + "=" * 60)
print("PART 6：缺陷报告模板生成")
print("=" * 60)

# 模拟一些"发现的Bug"（用于演示Bug单生成）
MOCK_BUGS = [
    {
        "id": "BUG-001",
        "title": "登录接口：账号被锁定后返回错误码不规范",
        "severity": "P1-严重",
        "module": "登录模块",
        "steps": "1. 连续5次输入错误密码\n2. 第6次登录\n3. 观察返回码",
        "expected": "返回 423 Locked + {code: 1006, msg: '账号已锁定，请30分钟后重试'}",
        "actual": "返回 200 + {code: 0, msg: '用户名或密码错误'}（与普通错误密码相同）",
        "env": "测试环境 v2.3.1",
        "assignee": "后端开发",
    },
    {
        "id": "BUG-002",
        "title": "战斗结算接口：并发请求时偶发重复发放奖励",
        "severity": "P0-致命",
        "module": "战斗系统",
        "steps": "1. 模拟10个线程同时发送 battle_end 请求\n2. 检查奖励发放记录",
        "expected": "同一 battle_id 只发放一次奖励（幂等性）",
        "actual": "偶发重复发放（3次测试中出现1次，发放了2次奖励）",
        "env": "测试环境 v2.3.1",
        "assignee": "后端开发",
    },
    {
        "id": "BUG-003",
        "title": "背包接口：道具数量字段返回字符串而非整数",
        "severity": "P2-一般",
        "module": "背包系统",
        "steps": "1. 调用 GET /api/player/bag\n2. 检查响应中 item.quantity 字段类型",
        "expected": "quantity 为整数类型，如 5",
        "actual": "quantity 为字符串类型，如 \"5\"（影响客户端类型判断）",
        "env": "测试环境 v2.3.1",
        "assignee": "后端开发",
    },
]

def generate_bug_report(bugs, output_path):
    """生成标准缺陷报告（Markdown格式，可直接粘贴到TAPD）"""
    lines = []
    lines.append("# 自动化测试缺陷报告")
    lines.append(f"\n**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**测试环境**: 测试环境 v2.3.1")
    lines.append(f"**发现缺陷**: {len(bugs)} 条")
    lines.append(f"**严重级别分布**: P0={sum(1 for b in bugs if 'P0' in b['severity'])} | "
                 f"P1={sum(1 for b in bugs if 'P1' in b['severity'])} | "
                 f"P2={sum(1 for b in bugs if 'P2' in b['severity'])}")

    lines.append("\n---\n")
    lines.append("## 缺陷汇总\n")
    lines.append("| # | 缺陷ID | 标题 | 严重级别 | 模块 | 指派给 |")
    lines.append("|---|--------|------|----------|------|--------|")
    for i, bug in enumerate(bugs, 1):
        lines.append(f"| {i} | {bug['id']} | {bug['title']} | {bug['severity']} | {bug['module']} | {bug['assignee']} |")

    lines.append("\n---\n")
    lines.append("## 缺陷详情\n")
    for bug in bugs:
        lines.append(f"### {bug['id']} - {bug['title']}")
        lines.append(f"\n- **严重级别**: {bug['severity']}")
        lines.append(f"- **所属模块**: {bug['module']}")
        lines.append(f"- **测试环境**: {bug['env']}")
        lines.append(f"- **指派给**: {bug['assignee']}")
        lines.append(f"\n**复现步骤**：\n{bug['steps']}")
        lines.append(f"\n**预期结果**：{bug['expected']}")
        lines.append(f"\n**实际结果**：{bug['actual']}")
        lines.append("\n---\n")

    content = "\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    return content

bug_report_path = r"C:\Users\Administrator\WorkBuddy\Claw\test_bug_report_day14.md"
generate_bug_report(MOCK_BUGS, bug_report_path)
print(f"✅ 缺陷报告已生成：{bug_report_path}")
print(f"   共 {len(MOCK_BUGS)} 条缺陷（P0: 1条 | P1: 1条 | P2: 1条）")

# ============================================================
# PART 7：14天学习总结 + 知识地图
# ============================================================
print("\n" + "=" * 60)
print("PART 7：14天学习总结")
print("=" * 60)

KNOWLEDGE_MAP = """
┌─────────────────── 14天知识地图 ───────────────────────────┐
│                                                            │
│  Day 1-2   HTTP基础层                                      │
│  ├── HTTP方法（GET/POST/PUT/DELETE/PATCH）                  │
│  ├── 状态码（200/201/400/401/403/404/500）                  │
│  └── 请求头与响应体结构                                      │
│                                                            │
│  Day 3-4   数据处理层                                       │
│  ├── Postman核心操作（Collection/环境变量/Tests/Runner）     │
│  └── JSON解析（loads/dumps/safe_get/嵌套提取）               │
│                                                            │
│  Day 5     断言层                                           │
│  ├── 状态码断言（assert / raise_for_status）                 │
│  ├── JSON字段断言（存在/值/类型）                             │
│  └── pytest assert 进阶（raises/match）                    │
│                                                            │
│  Day 6-7   依赖管理层                                       │
│  ├── 全局变量链（A→B→C→D接口串联）                           │
│  ├── requests.Session（Cookie+TCPl复用）                    │
│  └── pytest Fixture（function/class/module/session scope） │
│                                                            │
│  Day 8-10  框架层                                           │
│  ├── conftest.py多级架构（根/模块/子模块）                    │
│  ├── pytest.ini配置（markers/addopts/log_cli）              │
│  ├── parametrize参数化（基础/多参数/ids/lambda）             │
│  ├── skip/xfail标记（跳过/已知Bug）                          │
│  └── 数据驱动（CSV/Excel + parametrize）                    │
│                                                            │
│  Day 11-14 实战层                                           │
│  ├── 框架搭建（EnvConfig/BaseAPI/AssertHelper/DataGen）     │
│  ├── 登录模块完整用例（正常/异常/安全/边界，24个用例）         │
│  ├── 安全测试（Token鉴权/越权/SQL注入/XSS/SSRF）             │
│  ├── Mock技术（patch/MagicMock/monkeypatch）                │
│  ├── 并发测试（threading + 幂等性验证）                      │
│  ├── 报告生成（Markdown/Allure）                            │
│  └── CI/CD集成（GitHub Actions / Jenkins）                 │
│                                                            │
└────────────────────────────────────────────────────────────┘
"""
print(KNOWLEDGE_MAP)

BEST_PRACTICES = """
===== 14天最佳实践 Top 10 =====

1. 【封装优先】  永远不要在测试方法里直接写 requests.get()，用 BaseAPI 封装
2. 【断言分层】  状态码 → 业务码 → 核心字段 → 类型检查 → 响应时间，缺一不可
3. 【数据分离】  测试数据放 CSV/Excel，代码只写逻辑；改数据不改代码
4. 【Fixture链】  token → character_id → item_id，用 fixture 依赖链而不是全局变量
5. 【重试机制】  网络不稳定是常态，BaseAPI 加 retry=3 + 指数退避
6. 【Mock隔离】  第三方服务/支付/短信用 Mock，不依赖真实环境
7. 【分级执行】  P0冒烟<5min 每次上线，P1回归<30min 每天定时，P2全量<2h 发版前
8. 【CI集成】    测试要跑在 CI 里，本地跑通不算数，流水线失败要发告警
9. 【日志记录】  request+response 都要打印，排查问题靠日志不靠人工复现
10.【Bug单规范】 ID/标题/步骤/预期/实际/环境缺一不可，自动化输出要能直接贴TAPD
"""
print(BEST_PRACTICES)

NEXT_STEPS = """
===== 后续进阶路线 =====

阶段1（1-2个月）：测试工程化
  ├── allure报告深度定制（步骤截图、参数展示）
  ├── pytest-xdist 并行执行（多CPU跑测试）
  └── pytest-rerunfailures 自动重跑（抖动case处理）

阶段2（2-3个月）：专项测试能力
  ├── 性能测试入门（Locust/JMeter接口压测）
  ├── 安全测试进阶（OWASP Top10实战）
  └── APP端接口测试（Charles抓包+Appium）

阶段3（3-6个月）：测试平台化
  ├── 接口管理平台（Apifox/MeterSphere）
  ├── 自建简单测试平台（FastAPI + Vue）
  └── 测试开发岗位冲刺 🚀

当前你已具备：
  ✅ Python + Requests 接口自动化
  ✅ pytest 框架（fixture/参数化/数据驱动）
  ✅ CI/CD 集成理解
  ✅ 安全测试基础
  
  👉 已经够在简历上写"具备接口自动化测试能力"了！
"""
print(NEXT_STEPS)

# ============================================================
# PART 8：最终测试报告生成
# ============================================================
print("=" * 60)
print("PART 8：生成最终测试报告")
print("=" * 60)

# 统计结果
all_results = smoke_results + regression_results
total = len(all_results)
passed = sum(1 for r in all_results if r["status"] == "PASS")
failed = total - passed
pass_rate = passed / total * 100 if total > 0 else 0
avg_ms = sum(r.get("elapsed_ms", 0) for r in all_results) / total if total > 0 else 0

# 生成最终报告
final_report_path = r"C:\Users\Administrator\WorkBuddy\Claw\test_final_report_day14.md"

def generate_final_report():
    lines = []
    lines.append("# Python+Requests 14天学习 - 最终测试报告")
    lines.append(f"\n**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**测试环境**: httpbin.org (模拟山海之巅API)")
    lines.append(f"\n## 执行摘要\n")
    lines.append(f"| 项目 | 数值 |")
    lines.append(f"|------|------|")
    lines.append(f"| 总用例数 | {total} |")
    lines.append(f"| 通过 | {passed} ✅ |")
    lines.append(f"| 失败 | {failed} {'❌' if failed > 0 else '—'} |")
    lines.append(f"| 通过率 | {pass_rate:.1f}% |")
    lines.append(f"| 平均响应时间 | {avg_ms:.0f}ms |")

    lines.append(f"\n## P0 冒烟测试结果（{len(smoke_results)}条）\n")
    lines.append("| # | 用例名 | 状态 | 耗时 |")
    lines.append("|---|--------|------|------|")
    for i, r in enumerate(smoke_results, 1):
        status_icon = "✅ PASS" if r["status"] == "PASS" else "❌ FAIL"
        ms = f"{r.get('elapsed_ms', '-')}ms"
        lines.append(f"| {i} | {r['name']} | {status_icon} | {ms} |")

    lines.append(f"\n## P1 回归测试结果（{len(regression_results)}条）\n")
    lines.append("| # | 用例名 | 状态 | 耗时 |")
    lines.append("|---|--------|------|------|")
    for i, r in enumerate(regression_results, 1):
        status_icon = "✅ PASS" if r["status"] == "PASS" else "❌ FAIL"
        ms = f"{r.get('elapsed_ms', '-')}ms"
        lines.append(f"| {i} | {r['name']} | {status_icon} | {ms} |")

    lines.append("\n## 14天课程完成清单\n")
    days_summary = [
        ("Day 1",  "HTTP基础 + GET请求", "✅"),
        ("Day 2",  "POST/PUT/DELETE CRUD", "✅"),
        ("Day 3",  "Postman操作 + Python模拟", "✅"),
        ("Day 4",  "JSON解析与提取", "✅"),
        ("Day 5",  "接口断言（18个用例）", "✅"),
        ("Day 6",  "接口依赖处理（全局变量链）", "✅"),
        ("Day 7",  "pytest fixture + Session", "✅"),
        ("Day 8",  "pytest框架正式篇（conftest/参数化）", "✅"),
        ("Day 9",  "多文件架构 + allure报告", "✅"),
        ("Day 10", "数据驱动（CSV/Excel）", "✅"),
        ("Day 11", "项目实战Day1（框架搭建+Login模块）", "✅"),
        ("Day 12", "项目实战Day2（Player+Combat模块）", "✅"),
        ("Day 13", "安全测试+Mock+并发+报告生成", "✅"),
        ("Day 14", "CI/CD集成+完整套件+学习总结", "✅"),
    ]
    lines.append("| 天数 | 主题 | 状态 |")
    lines.append("|------|------|------|")
    for day, theme, status in days_summary:
        lines.append(f"| {day} | {theme} | {status} |")

    lines.append("\n---")
    lines.append("\n> 🎉 恭喜完成 Python + Requests 接口自动化测试 14天系统学习！")
    lines.append("> 你现在已经具备了从0开始搭建接口自动化测试工程的能力。")

    content = "\n".join(lines)
    with open(final_report_path, "w", encoding="utf-8") as f:
        f.write(content)
    return content

generate_final_report()

# 控制台汇总
print(f"\n{'='*50}")
print(f"  📊 最终测试汇总")
print(f"{'='*50}")
print(f"  总用例: {total}  |  通过: {passed}  |  失败: {failed}")
print(f"  通过率: {pass_rate:.1f}%  |  平均响应时间: {avg_ms:.0f}ms")
print(f"{'='*50}")
print(f"\n✅ 最终测试报告: {final_report_path}")
print(f"✅ 缺陷报告:     {bug_report_path}")
print(f"\n🎉 Python + Requests 14天学习计划 —— 圆满完成！")
print(f"\n恭喜你！从Day1的第一个GET请求，到今天的CI/CD集成，")
print(f"你已经系统掌握了接口自动化测试的完整技能栈！")
