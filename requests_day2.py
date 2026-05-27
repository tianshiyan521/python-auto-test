"""
Python Requests 学习 - 第2天
主题：POST/PUT/DELETE请求（完整增删改查）
"""

import requests
import json

print("=" * 50)
print("📚 Day 2: POST/PUT/DELETE 请求（CRUD）")
print("=" * 50)

# ==================== 理论部分 ====================
print("\n【CRUD 增删改查】")
print("""
HTTP方法    | 操作     | 说明
-----------|---------|------
GET        | 查       | 获取资源
POST       | 增       | 创建新资源
PUT        | 改       | 完整更新资源
DELETE     | 删       | 删除资源
PATCH      | 改       | 部分更新资源
""")

# ==================== 1. POST 请求 ====================
print("\n" + "=" * 50)
print("➕ 实战1: POST 请求（创建资源）")
print("=" * 50)

url_post = "https://httpbin.org/post"

# 表单数据
form_data = {
    "username": "test_user",
    "email": "test@example.com",
    "age": 25
}

print(f"\nPOST URL: {url_post}")
print(f"表单数据: {form_data}")

response = requests.post(url_post, data=form_data)
print(f"\n状态码: {response.status_code} ({response.reason})")

result = response.json()
print(f"\n服务器收到的数据:")
print(f"  form: {result.get('form')}")

# JSON 数据
print("\n" + "-" * 40)
print("【发送 JSON 数据】")

json_data = {
    "name": "张三",
    "score": 98,
    "courses": ["语文", "数学", "英语"]
}

response_json = requests.post(url_post, json=json_data)
print(f"状态码: {response_json.status_code}")
result_json = response_json.json()
print(f"服务器收到的JSON: {result_json.get('json')}")

# ==================== 2. PUT 请求 ====================
print("\n" + "=" * 50)
print("✏️ 实战2: PUT 请求（完整更新）")
print("=" * 50)

url_put = "https://httpbin.org/put"

# 完整更新用户信息
update_data = {
    "user_id": 12345,
    "username": "updated_user",
    "email": "new_email@example.com",
    "age": 26,
    "city": "杭州"
}

print(f"\nPUT URL: {url_put}")
print(f"更新数据: {update_data}")

response_put = requests.put(url_put, json=update_data)
print(f"\n状态码: {response_put.status_code} ({response_put.reason})")

result_put = response_put.json()
print(f"服务器收到的数据: {result_put.get('json')}")

# ==================== 3. DELETE 请求 ====================
print("\n" + "=" * 50)
print("🗑️ 实战3: DELETE 请求（删除资源）")
print("=" * 50)

url_delete = "https://httpbin.org/delete"

print(f"\nDELETE URL: {url_delete}")

# DELETE 通常不带请求体，但可以带参数
params = {"id": "12345", "confirm": "yes"}
response_delete = requests.delete(url_delete, params=params)
print(f"状态码: {response_delete.status_code} ({response_delete.reason})")

result_delete = response_delete.json()
print(f"服务器收到的参数: {result_delete.get('args')}")

# ==================== 4. PATCH 请求 ====================
print("\n" + "=" * 50)
print("🔧 实战4: PATCH 请求（部分更新）")
print("=" * 50)

url_patch = "https://httpbin.org/patch"

# 只更新部分字段
patch_data = {
    "email": "patched_email@example.com"  # 只更新邮箱
}

print(f"\nPATCH URL: {url_patch}")
print(f"部分更新数据: {patch_data}")

response_patch = requests.patch(url_patch, json=patch_data)
print(f"状态码: {response_patch.status_code} ({response_patch.reason})")

result_patch = response_patch.json()
print(f"服务器收到的数据: {result_patch.get('json')}")

# ==================== 5. 综合练习：模拟用户注册登录 ====================
print("\n" + "=" * 50)
print("🎯 综合练习：模拟用户注册 → 登录 → 更新 → 删除")
print("=" * 50)

print("\n【步骤1: 注册用户】")
register_data = {
    "username": "game_player_001",
    "password": "secure_pass123",
    "level": 1,
    "coins": 100
}
resp = requests.post("https://httpbin.org/post", json=register_data)
print(f"注册结果: {resp.status_code}")
print(f"返回数据: {resp.json().get('json')}")

print("\n【步骤2: 查询用户信息（GET）】")
resp = requests.get("https://httpbin.org/get", params={"user_id": "game_player_001"})
print(f"查询结果: {resp.status_code}")

print("\n【步骤3: 更新用户等级（PUT）】")
update_level = {"level": 5, "coins": 500}
resp = requests.put("https://httpbin.org/put", json=update_level)
print(f"更新结果: {resp.status_code}")
print(f"更新后数据: {resp.json().get('json')}")

print("\n【步骤4: 删除用户（DELETE）】")
resp = requests.delete("https://httpbin.org/delete/game_player_001")
print(f"删除结果: {resp.status_code}")

# ==================== 6. 请求头进阶 ====================
print("\n" + "=" * 50)
print("📋 进阶：Content-Type 与数据格式")
print("=" * 50)

print("""
常见 Content-Type:
- application/x-www-form-urlencoded  (表单数据)
- multipart/form-data              (文件上传)
- application/json                (JSON数据)
- text/plain                      (纯文本)
- application/xml                 (XML数据)
""")

# 自定义 Content-Type
print("\n【自定义请求头】")
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer xxx_token_xxx",
    "X-Request-ID": "req_12345"
}

response = requests.post(
    "https://httpbin.org/post",
    headers=headers,
    json={"data": "test"}
)
print(f"状态码: {response.status_code}")
print(f"收到的请求头: {response.json().get('headers')}")

# ==================== 7. 错误处理完整版 ====================
print("\n" + "=" * 50)
print("⚠️ 完整错误处理")
print("=" * 50)

print("""
【错误处理代码模板】

import requests
from requests.exceptions import (
    ConnectionError,      # 连接错误
    Timeout,              # 超时
    HTTPError,            # HTTP错误
    RequestException      # 所有请求异常的父类
)

def safe_request(method, url, **kwargs):
    try:
        response = requests.request(method, url, timeout=10, **kwargs)
        response.raise_for_status()  # 状态码非200时抛异常
        return response.json()
    except ConnectionError:
        return {"error": "连接失败，请检查网络"}
    except Timeout:
        return {"error": "请求超时"}
    except HTTPError as e:
        return {"error": f"HTTP错误: {e}"}
    except RequestException as e:
        return {"error": f"请求异常: {e}"}
""")

# 演示错误处理
print("\n【错误处理演示】")
try:
    bad_resp = requests.get("https://httpbin.org/status/500", timeout=5)
    bad_resp.raise_for_status()
except requests.exceptions.HTTPError as e:
    print(f"捕获到 HTTP 错误: {e}")

try:
    timeout_resp = requests.get("https://httpbin.org/delay/10", timeout=2)
except requests.exceptions.Timeout:
    print("捕获到超时错误！（延迟10秒，超时2秒）")

print("\n" + "=" * 50)
print("✅ Day 2 学习完成！")
print("=" * 50)
print("""
【今日收获】
1. ✅ 掌握 POST 请求（创建资源）
2. ✅ 掌握 PUT 请求（完整更新）
3. ✅ 掌握 DELETE 请求（删除资源）
4. ✅ 掌握 PATCH 请求（部分更新）
5. ✅ 理解 CRUD 完整流程
6. ✅ 学会自定义 Content-Type 请求头
7. ✅ 掌握完整的错误处理机制

【明天预告】
Day 3: Postman基本操作（界面、Collection、环境变量）
""")
