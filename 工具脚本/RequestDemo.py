# ===== requests_day1_get_demo.py =====
# Requests Day1: GET 请求基础演示
# 练习环境：httpbin.org（免费HTTP测试服务）

import requests

# ========== 1. 最简单的GET请求 ==========
print("=" * 50)
print("【1】最简单的GET请求")
print("=" * 50)

r = requests.get("https://httpbin.org/uuid")
print(f"状态码: {r.status_code}")          # 应该输出 200
print(f"响应类型: {type(r)}")               # <class 'requests.models.Response'>

# ========== 2. 获取响应内容的三种方式 ==========
print("\n" + "=" * 50)
print("【2】三种方式查看响应内容")
print("=" * 50)

# 方式A: r.text — 原始文本
print(f"\n--- r.text (前100字符) ---")
print(r.text[:100])

# 方式B: r.json() — 自动转为Python字典
data = r.json()
print(f"\n--- r.json() (类型: {type(data)}) ---")
print(f"返回的URL: {data.get('url')}")

# 方式C: r.headers — 响应头
print(f"\n--- r.headers (部分) ---")
print(f"Content-Type: {r.headers.get('Content-Type')}")
print(f"Server: {r.headers.get('Server')}")

# ========== 3. 带参数的GET请求 ==========
print("\n" + "=" * 50)
print("【3】带参数的GET请求")
print("=" * 50)

payload = {
    "username": "test_user",
    "page": 1,
    "size": 10
}
r2 = requests.get("https://httpbin.org/get", params=payload)

print(f"实际请求URL: {r2.url}")
# 输出类似: https://httpbin.org/get?username=test_user&page=1&size=10

result = r2.json()
print(f"接收到的参数: {result['args']}")

# ========== 4. 第一个断言（测试核心！） ==========
print("\n" + "=" * 50)
print("【4】第一个接口断言（测试的灵魂）")
print("=" * 50)

# 断言状态码是200
assert r2.status_code == 200, f"期望200, 实际{r2.status_code}"
print("✅ 状态码断言通过: 200")

# 断言参数正确返回
assert result['args']['username'] == 'test_user'
assert result['args']['page'] == '1'
print("✅ 参数回显断言通过")

# 断言响应头包含JSON
content_type = r2.headers.get('Content-Type', '')
assert 'json' in content_type, f"期望JSON格式, 实际{content_type}"
print("✅ 响应格式断言通过: application/json")

print("\n🎉 全部测试通过！Day1 完成！")
