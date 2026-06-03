"""
Python Requests 学习 - 第1天
主题：HTTP基础 + 第一个GET请求
"""

import requests

print("=" * 50)
print("📚 Day 1: HTTP基础 + 第一个GET请求")
print("=" * 50)

# ==================== 理论部分 ====================
print("\n【HTTP基础概念】")
print("""
1. HTTP请求方法：
   - GET: 获取资源（查）
   - POST: 创建资源（增）
   - PUT: 更新资源（改）
   - DELETE: 删除资源（删）

2. HTTP状态码：
   - 200: 成功
   - 201: 创建成功
   - 400: 请求错误
   - 401: 未授权
   - 404: 资源不存在
   - 500: 服务器错误

3. 请求结构：
   - 请求行（方法 + URL + 协议版本）
   - 请求头（Headers）
   - 请求体（Body，POST/PUT才有）
""")

# ==================== 实战部分 ====================
print("\n" + "=" * 50)
print("🚀 实战：访问 httpbin.org/get")
print("=" * 50)

# 1. 简单的GET请求
url = "https://httpbin.org/get"
print(f"\n请求URL: {url}")

response = requests.get(url)

print(f"\n【响应信息】")
print(f"状态码: {response.status_code}")
print(f"状态码含义: {response.reason}")

# 2. 查看响应内容
print(f"\n【响应体类型】: {type(response.text)}")
print(f"响应体内容（前500字符）:\n{response.text[:500]}")

# 3. 解析JSON响应
print(f"\n【JSON解析】")
data = response.json()
print(f"解析后的数据类型: {type(data)}")
print(f"JSON内容:")
for key, value in data.items():
    print(f"  {key}: {value}")

# ==================== 带参数的GET请求 ====================
print("\n" + "=" * 50)
print("🌐 实战：带参数的GET请求")
print("=" * 50)

# 查询参数
params = {
    "name": "测试人员",
    "age": 25,
    "city": "杭州"
}

url_with_params = "https://httpbin.org/get"
print(f"\n请求参数: {params}")

response2 = requests.get(url_with_params, params=params)
print(f"状态码: {response2.status_code}")

result = response2.json()
print(f"服务器收到的参数 args: {result.get('args')}")

# ==================== 带请求头的GET请求 ====================
print("\n" + "=" * 50)
print("📋 实战：带自定义请求头的GET请求")
print("=" * 50)

headers = {
    "User-Agent": "Python-Requests-Day1/1.0",
    "Accept": "application/json",
    "X-Test-Header": "Hello from Day1"
}

url_headers = "https://httpbin.org/get"
print(f"自定义请求头: {headers}")

response3 = requests.get(url_headers, headers=headers)
print(f"状态码: {response3.status_code}")

result3 = response3.json()
print(f"服务器收到的请求头 headers: {result3.get('headers')}")

# ==================== 检查响应头 ====================
print("\n" + "=" * 50)
print("📦 响应头信息")
print("=" * 50)

print(f"\n响应头内容:")
for key, value in response3.headers.items():
    print(f"  {key}: {value}")

# ==================== 错误处理 ====================
print("\n" + "=" * 50)
print("⚠️ 错误处理示例")
print("=" * 50)

# 故意访问一个不存在的路径，测试404处理
try:
    bad_response = requests.get("https://httpbin.org/status/404", timeout=5)
    print(f"404请求 - 状态码: {bad_response.status_code}")
except requests.exceptions.Timeout:
    print("请求超时！")
except requests.exceptions.RequestException as e:
    print(f"请求异常: {e}")

# 正确的错误处理方式
print("\n【正确的错误处理写法】:")
print("""
try:
    response = requests.get(url, timeout=5)
    response.raise_for_status()  # 如果状态码不是200，会抛出异常
    data = response.json()
except requests.exceptions.ConnectionError:
    print("连接失败！")
except requests.exceptions.Timeout:
    print("请求超时！")
except requests.exceptions.HTTPError as e:
    print(f"HTTP错误: {e}")
""")

print("\n" + "=" * 50)
print("✅ Day 1 学习完成！")
print("=" * 50)
print("""
【今日收获】
1. 理解了HTTP协议的基础概念
2. 掌握了requests.get()的基本用法
3. 学会了如何传递URL参数和请求头
4. 了解了如何解析JSON响应
5. 学会了基本的错误处理

【明天预告】
Day 2: POST/PUT/DELETE请求（完整增删改查）
""")
