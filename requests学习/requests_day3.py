"""
Python Requests 学习 - 第3天
主题：Postman 基本操作 + Python模拟Postman核心功能

Postman 是最流行的API调试工具，但它的底层原理就是：
  发HTTP请求 → 收响应 → 显示结果
今天我们用 Python 代码模拟 Postman 的核心功能，
理解原理后你再用 Postman 会非常轻松。
"""

import requests
import json
import time

print("=" * 60)
print("  Day 3: Postman 基本操作 + Python模拟Postman")
print("=" * 60)


# ==================== 理论部分 ====================
print("\n" + "=" * 60)
print("  【理论】Postman 5大核心功能")
print("=" * 60)
print("""
Postman界面功能区：
┌─────────────────────────────────────────────────────┐
│ ① Collections（集合）                                │
│    把多个相关接口组织到一个文件夹里                     │
│    例：山海之巅API / 用户模块 / 登录接口               │
│                                                       │
│ ② 请求构建区（URL + Method + Body）                   │
│    选择方法(GET/POST等) → 输入URL → 填写参数/请求体    │
│                                                       │
│ ③ 环境变量（Environment Variables）                    │
│    区分不同环境：开发/测试/生产                         │
│    用 {{base_url}} 代替具体地址                        │
│    例：开发环境 base_url=http://dev.api.com            │
│        生产环境 base_url=https://api.com               │
│                                                       │
│ ④ Tests（断言/测试脚本）                               │
│    在响应返回后自动验证结果                             │
│    例：pm.test("状态码200", ()=>{                      │
│          pm.response.to.have.status(200);             │
│        });                                            │
│                                                       │
│ ⑤ 响应查看区（Response Viewer）                        │
│    状态码、响应头、响应体(JSON/HTML/图片)               │
│    还能看到响应时间，方便性能检查                       │
└─────────────────────────────────────────────────────┘
""")


# ==================== 功能1: Python模拟环境变量 ====================
print("\n" + "=" * 60)
print("  功能1: Python模拟 Postman 环境变量")
print("=" * 60)

# Postman 环境变量 → Python 字典
environments = {
    "开发环境": {
        "base_url": "http://dev-api.shanhai.com",
        "token": "dev_token_12345",
        "version": "v1"
    },
    "测试环境": {
        "base_url": "http://test-api.shanhai.com",
        "token": "test_token_67890",
        "version": "v2"
    },
    "生产环境": {
        "base_url": "https://api.shanhai.com",
        "token": "prod_token_abcde",
        "version": "v2"
    }
}

# 当前选择的环境
current_env = "开发环境"

def get_env(key):
    """获取当前环境的变量值（模拟 Postman 的 {{变量名}}）"""
    return environments[current_env].get(key, "")

print(f"\n当前环境: {current_env}")
print(f"base_url = {get_env('base_url')}")
print(f"token    = {get_env('token')}")
print(f"version  = {get_env('version')}")

print("\n--- 切换到生产环境 ---")
current_env = "生产环境"
print(f"当前环境: {current_env}")
print(f"base_url = {get_env('base_url')}")
print(f"token    = {get_env('token')}")

# 用环境变量构建URL（模拟 Postman 的 {{base_url}}/users）
url = f"{get_env('base_url')}/{get_env('version')}/users"
print(f"\n拼接后的URL: {url}")
print("（在Postman中就是: {{base_url}}/{{version}}/users）")


# ==================== 功能2: Python模拟Collection ====================
print("\n\n" + "=" * 60)
print("  功能2: Python模拟 Postman Collection（接口集合）")
print("=" * 60)

# 模拟 Postman Collection 结构
shanhai_collection = {
    "name": "山海之巅API",
    "requests": [
        {
            "name": "用户登录",
            "method": "POST",
            "url": "/api/v1/login",
            "body": {"username": "test", "password": "123456"},
            "expected_status": 200
        },
        {
            "name": "获取玩家信息",
            "method": "GET",
            "url": "/api/v1/player/info",
            "params": {"player_id": "1001"},
            "expected_status": 200
        },
        {
            "name": "购买装备",
            "method": "POST",
            "url": "/api/v1/shop/buy",
            "body": {"item_id": "sword_01", "quantity": 1},
            "expected_status": 200
        },
        {
            "name": "更新角色属性",
            "method": "PUT",
            "url": "/api/v1/player/attributes",
            "body": {"attack": 150, "defense": 80},
            "expected_status": 200
        },
        {
            "name": "退出登录",
            "method": "POST",
            "url": "/api/v1/logout",
            "expected_status": 200
        }
    ]
}

print(f"\n集合名称: {shanhai_collection['name']}")
print(f"接口数量: {len(shanhai_collection['requests'])}")
print("\n接口列表:")
for i, req in enumerate(shanhai_collection["requests"], 1):
    method_colors = {"GET": "✅", "POST": "➕", "PUT": "✏️", "DELETE": "🗑️"}
    icon = method_colors.get(req["method"], "📌")
    print(f"  {i}. {icon} {req['method']:6s} | {req['name']:12s} | {req['url']}")


# ==================== 功能3: 用 httpbin 模拟 Collection 批量执行 ====================
print("\n\n" + "=" * 60)
print("  功能3: 批量执行 Collection（模拟Postman Runner）")
print("=" * 60)
print("（使用 httpbin.org 真实发送请求）\n")

# 用 httpbin 构建可执行的 Collection
test_collection = [
    {
        "name": "GET - 获取数据",
        "method": "GET",
        "url": "https://httpbin.org/get",
        "params": {"key": "value1", "page": "1"}
    },
    {
        "name": "POST - 创建用户",
        "method": "POST",
        "url": "https://httpbin.org/post",
        "json": {"username": "test_user", "role": "tester"}
    },
    {
        "name": "PUT - 更新信息",
        "method": "PUT",
        "url": "https://httpbin.org/put",
        "json": {"username": "test_user", "role": "senior_tester"}
    },
    {
        "name": "DELETE - 删除资源",
        "method": "DELETE",
        "url": "https://httpbin.org/delete",
        "params": {"id": "1001"}
    }
]

# 执行结果汇总
results = []
total_start = time.time()

for req in test_collection:
    print(f"  ▶ {req['name']} [{req['method']}]")
    start = time.time()

    try:
        kwargs = {}
        if "params" in req:
            kwargs["params"] = req["params"]
        if "json" in req:
            kwargs["json"] = req["json"]

        response = requests.request(
            method=req["method"],
            url=req["url"],
            timeout=10,
            **kwargs
        )
        elapsed = (time.time() - start) * 1000  # 转毫秒

        success = response.status_code == 200
        results.append({
            "name": req["name"],
            "method": req["method"],
            "status": response.status_code,
            "time_ms": round(elapsed, 0),
            "passed": success
        })

        status_icon = "✅" if success else "❌"
        print(f"    {status_icon} 状态码: {response.status_code} | 耗时: {elapsed:.0f}ms")

    except Exception as e:
        elapsed = (time.time() - start) * 1000
        results.append({
            "name": req["name"],
            "method": req["method"],
            "status": "ERROR",
            "time_ms": round(elapsed, 0),
            "passed": False,
            "error": str(e)
        })
        print(f"    ❌ 错误: {e}")

total_time = (time.time() - total_start) * 1000

# 输出测试报告（模拟 Postman Runner 结果）
print(f"\n{'=' * 60}")
print(f"  Collection 执行报告")
print(f"{'=' * 60}")
print(f"  总用例数: {len(results)}")
passed = sum(1 for r in results if r["passed"])
print(f"  通过: {passed}  |  失败: {len(results) - passed}")
print(f"  总耗时: {total_time:.0f}ms")
print(f"\n  {'名称':20s} | {'方法':6s} | {'状态码':6s} | {'耗时':8s} | 结果")
print(f"  {'-' * 20}-+-{'-' * 6}-+-{'-' * 6}-+-{'-' * 8}-+-----")
for r in results:
    status = str(r["status"]).center(6)
    time_str = f'{r["time_ms"]}ms'.center(8)
    result = "PASS" if r["passed"] else "FAIL"
    print(f"  {r['name']:20s} | {r['method']:6s} | {status} | {time_str} | {result}")


# ==================== 功能4: Python模拟 Tests 断言 ====================
print("\n\n" + "=" * 60)
print("  功能4: Python模拟 Postman Tests（断言）")
print("=" * 60)

print("""
Postman 的 Tests 是用 JavaScript 写的断言脚本：
  pm.test("状态码是200", () => {
      pm.response.to.have.status(200);
  });

在 Python 中，我们用 assert 实现：
  assert response.status_code == 200, "状态码应该是200"

下面用 Python 实现类似 Postman 的断言框架：
""")

class PostmanTest:
    """Python 模拟 Postman 的 Tests 功能"""

    def __init__(self, response):
        self.response = response
        self.tests = []
        self.passed = 0
        self.failed = 0

    def test(self, name, condition, error_msg=""):
        """模拟 pm.test(name, fn)"""
        if condition:
            self.tests.append({"name": name, "result": "PASS"})
            self.passed += 1
            print(f"    ✅ {name}")
        else:
            self.tests.append({"name": name, "result": "FAIL", "error": error_msg})
            self.failed += 1
            print(f"    ❌ {name} - {error_msg}")

    def report(self):
        """输出测试结果"""
        print(f"\n    Tests: {self.passed} passed, {self.failed} failed")
        return self.failed == 0


print("【实战：对登录接口做断言】\n")
response = requests.post(
    "https://httpbin.org/post",
    json={"username": "test_user", "password": "123456"},
    timeout=10
)

# 创建断言实例
pm = PostmanTest(response)
print(f"  接口: POST https://httpbin.org/post")
print(f"  状态码: {response.status_code}\n")

# 写断言（就像在 Postman 里写 Tests）
pm.test("状态码是 200", response.status_code == 200)
pm.test("响应时间小于500ms", response.elapsed.total_seconds() < 0.5)
pm.test("Content-Type 包含 json", "json" in response.headers.get("Content-Type", ""))
pm.test("返回数据不为空", len(response.text) > 0)

# 解析 JSON 后断言
data = response.json()
pm.test("返回了 JSON 格式", data is not None)
pm.test("请求方式记录正确", data.get("method") == "POST")
pm.test("服务器收到了用户名", data.get("json", {}).get("username") == "test_user")

pm.report()


# ==================== 功能5: 变量传递（接口依赖预演） ====================
print("\n\n" + "=" * 60)
print("  功能5: 变量传递（为Day6-7接口依赖做准备）")
print("=" * 60)

print("""
Postman 中，可以在 Tests 里提取A接口的返回值，传给B接口：
  // 在登录接口的 Tests 中
  var token = pm.response.json().token;
  pm.environment.set("token", token);

  // 在下一个请求中引用
  Headers: Authorization: Bearer {{token}}

Python 中用一个字典就能实现：
""")

# 全局变量字典（模拟 Postman 的环境变量存储）
global_vars = {}

print("【步骤1: 登录接口 → 提取 token】")
login_resp = requests.post(
    "https://httpbin.org/post",
    json={"username": "test_user", "password": "123456"},
    timeout=10
)
# 模拟从响应中提取 token
login_data = login_resp.json()
# httpbin 会回显我们的数据，这里模拟提取
extracted_token = login_data.get("json", {}).get("username", "") + "_token_generated"
global_vars["token"] = extracted_token
global_vars["user_id"] = "10086"

print(f"  登录成功，提取 token: {global_vars['token']}")
print(f"  提取 user_id: {global_vars['user_id']}")

print("\n【步骤2: 用 token 请求用户信息】")
headers_with_token = {
    "Authorization": f"Bearer {global_vars['token']}",
    "X-User-ID": global_vars["user_id"]
}

info_resp = requests.get(
    "https://httpbin.org/get",
    headers=headers_with_token,
    timeout=10
)
info_data = info_resp.json()
received_headers = info_data.get("headers", {})
print(f"  请求成功！")
print(f"  服务器收到的 Authorization: {received_headers.get('Authorization', 'None')}")
print(f"  服务器收到的 X-User-ID: {received_headers.get('X-User-Id', 'None')}")
print(f"\n  变量传递成功！这就是接口依赖的核心原理。")


# ==================== 知识点总结 ====================
print("\n\n" + "=" * 60)
print("  Day 3 知识点总结")
print("=" * 60)
print("""
Postman 核心功能 vs Python 对应方案：

┌──────────────────────┬──────────────────────────────┐
│ Postman 功能          │ Python 实现方式               │
├──────────────────────┼──────────────────────────────┤
│ Collection（集合）    │ 列表/字典组织多个请求          │
│ Environment（环境变量）│ 字典 + 字符串格式化            │
│ Request Builder       │ requests.request(method, url) │
│ Tests（断言）         │ assert 或自定义断言类          │
│ Collection Runner     │ for 循环 + 结果收集           │
│ 变量传递 {{xxx}}      │ 字典存取 + f-string           │
└──────────────────────┴──────────────────────────────┘

Postman 操作要点：
1. 新建 Collection → 把相关接口放一起
2. 新建 Environment → 设置 base_url、token 等变量
3. 写请求 → 用 {{base_url}} 引用环境变量
4. 写 Tests → 自动验证每个接口的响应
5. Runner → 一键运行整个 Collection

【为什么学 Postman？】
- 手工测试时快速调试接口（不需要写代码）
- 生成接口文档（自带文档功能）
- 与团队共享（导入导出 Collection）
- 自动化测试的基础（支持导出为自动化脚本）
""")


# ==================== 练习题 ====================
print("\n" + "=" * 60)
print("  Day 3 练习题（3道选择题）")
print("=" * 60)
print("""
【第1题】Postman 中 {{base_url}} 的作用是？
  A. 定义全局变量
  B. 引用环境变量的值
  C. 声明常量
  D. 定义接口路径
  正确答案: B
  解析: 双花括号 {{}} 是 Postman 中引用环境变量的语法

【第2题】Postman Collection 的主要用途是？
  A. 发送单个请求
  B. 组织和管理多个相关接口
  C. 生成代码
  D. 管理环境变量
  正确答案: B
  解析: Collection 是接口集合，类似文件夹，把相关接口放一起管理

【第3题】以下哪种方式可以在 Python 中实现 Postman 的环境变量功能？
  A. 用列表存储变量
  B. 用字典 + f-string 格式化
  C. 用全局常量
  D. 直接写死URL
  正确答案: B
  解析: 字典存储环境变量，f-string 或 format() 动态替换 URL 中的变量
""")


# ==================== 完成标志 ====================
print("\n" + "=" * 60)
print("  Day 3 学习完成！")
print("=" * 60)
print("""
  【今日收获】
  1. 理解 Postman 的5大核心功能
  2. 掌握 Python 模拟环境变量（字典 + 格式化）
  3. 掌握 Python 模拟 Collection（列表组织请求）
  4. 实现了 Collection Runner（批量执行 + 测试报告）
  5. 实现了 Postman Tests 断言（自定义断言类）
  6. 掌握变量传递原理（为Day6-7做准备）

  【明天预告】
  Day 4: Requests + JSON处理（解析接口返回数据，提取字段）

  【课后建议】
  如果电脑上有 Postman，试着操作一下：
  1. 下载安装 Postman Desktop
  2. 创建一个 Collection "Httpbin练习"
  3. 添加今天代码中的4个请求
  4. 新建环境变量 base_url = https://httpbin.org
  5. 在 Tests 里写 pm.test("状态码200", ...)
""")
