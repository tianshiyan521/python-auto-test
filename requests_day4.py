"""
Python Requests 学习 - 第4天
主题：Requests + JSON处理（解析接口返回数据，提取字段）

学习目标：
1. 理解 JSON 格式与 Python 字典的关系
2. 掌握 response.json() 和 json.loads() 的用法
3. 学会从嵌套 JSON 中提取字段
4. 处理 JSON 常见错误（KeyError、JSONDecodeError）
5. 用真实接口实战：解析 httpbin 返回的复杂嵌套数据
"""

import requests
import json
import time

print("=" * 60)
print("  Day 4: Requests + JSON处理")
print("=" * 60)


# ==================== 理论部分 ====================
print("\n" + "=" * 60)
print("  【理论】JSON 基础速览")
print("=" * 60)
print("""
JSON（JavaScript Object Notation）是前后端通信的标准数据格式。

JSON 与 Python 数据类型对应关系：
┌─────────────────┬────────────────────────┐
│ JSON 类型        │ Python 类型             │
├─────────────────┼────────────────────────┤
│ {"key": "value"}│ dict                   │
│ [1, 2, 3]       │ list                   │
│ "hello"         │ str                    │
│ 123             │ int / float            │
│ true / false    │ True / False           │
│ null            │ None                   │
└─────────────────┴────────────────────────┘

常用操作：
  json.loads(str)   → JSON字符串 → Python对象（解析）
  json.dumps(dict)  → Python对象 → JSON字符串（序列化）
  response.json()   → requests 封装的方法，同上
""")


# ==================== 基础1: JSON字符串解析 ====================
print("\n" + "=" * 60)
print("  基础1: json.loads() - JSON字符串 → Python字典")
print("=" * 60)

json_str = '{"name": "张三", "level": 88, "online": true, "items": null}'
print(f"JSON字符串: {json_str}")

# 解析 JSON 字符串为 Python 对象
data = json.loads(json_str)
print(f"\n解析后类型: {type(data)}")
print(f"解析后内容: {data}")
print(f"  name   = {data['name']}")
print(f"  level  = {data['level']}")
print(f"  online = {data['online']}")
print(f"  items  = {data['items']}")  # null → None

# 反向操作：Python对象 → JSON字符串
back_to_json = json.dumps(data, ensure_ascii=False)
print(f"\n转回JSON字符串: {back_to_json}")


# ==================== 基础2: 嵌套JSON解析 ====================
print("\n\n" + "=" * 60)
print("  基础2: 从嵌套JSON中提取字段（重点！）")
print("=" * 60)

# 模拟一个山海之巅API返回的复杂嵌套JSON
nested_json = {
    "code": 200,
    "msg": "success",
    "data": {
        "player_id": "10086",
        "name": "测试玩家",
        "level": 66,
        "attributes": {
            "attack": 888,
            "defense": 555,
            "hp": 15000,
            "speed": 120
        },
        "equipments": [
            {"slot": "weapon", "name": "倚天剑", "quality": "epic"},
            {"slot": "armor",  "name": "玄武甲", "quality": "rare"}
        ],
        "guild": {
            "name": "天下第一",
            "member_count": 128,
            "leader": {
                "id": "10000",
                "name": "会长李四"
            }
        }
    },
    "timestamp": 1715000000
}

print("【模拟山海之巅接口返回的嵌套JSON】")
print(f"  总字段数: {len(nested_json)}")
print()

# 一层层提取（路径式提取）
print("【逐层提取示例】")
print(f"  code = {nested_json['code']}")
print(f"  msg  = {nested_json['msg']}")
print(f"  data.level = {nested_json['data']['level']}")
print(f"  data.name  = {nested_json['data']['name']}")

# 提取嵌套属性
attack = nested_json["data"]["attributes"]["attack"]
hp = nested_json["data"]["attributes"]["hp"]
print(f"\n【提取角色属性】")
print(f"  攻击力: {attack}")
print(f"  生命值: {hp}")

# 提取列表中的元素
weapon = nested_json["data"]["equipments"][0]
print(f"\n【提取装备列表中的第一个】")
print(f"  第1件装备: {weapon['name']} ({weapon['quality']})")

# 遍历列表
print(f"\n【遍历所有装备】")
for i, equip in enumerate(nested_json["data"]["equipments"], 1):
    print(f"  {i}. {equip['slot']:8s} | {equip['name']:6s} | 品质: {equip['quality']}")

# 提取多层嵌套
guild_name = nested_json["data"]["guild"]["name"]
leader_name = nested_json["data"]["guild"]["leader"]["name"]
print(f"\n【提取多层嵌套】")
print(f"  公会名: {guild_name}")
print(f"  会长: {leader_name}")

# 用一行代码提取（防止 KeyError 安全写法）
def safe_get(data, path, default=None):
    """安全提取嵌套字段，路径用 "." 分隔，如 "data.attributes.attack" """
    keys = path.split(".")
    current = data
    try:
        for key in keys:
            current = current[key]
        return current
    except (KeyError, TypeError, IndexError):
        return default

print(f"\n【安全提取（防止KeyError）】")
print(f"  safe_get(data, 'data.attributes.attack') = {safe_get(nested_json, 'data.attributes.attack')}")
print(f"  safe_get(data, 'data.attributes.magic') = {safe_get(nested_json, 'data.attributes.magic')}")  # 不存在的key
print(f"  safe_get(data, 'data.equipments.2')     = {safe_get(nested_json, 'data.equipments.2')}")        # 索引越界


# ==================== 基础3: response.json() ====================
print("\n\n" + "=" * 60)
print("  基础3: response.json() - 解析API响应JSON")
print("=" * 60)

print("""
requests 库的响应对象有 3 种方式获取响应体：

  response.text    → 返回原始字符串（ bytes转str）
  response.content → 返回 bytes（用于图片/文件下载）
  response.json()  → 返回解析后的 Python 对象（字典/列表）

response.json() 底层就是：
  json.loads(response.text)
""")

# 实战：发送请求并解析JSON
print("\n【实战：GET请求 → 解析JSON】\n")
resp = requests.get("https://httpbin.org/get", timeout=10)
print(f"  状态码: {resp.status_code}")
print(f"  响应类型: {type(resp.text)} → {type(resp.json())}")

json_data = resp.json()
print(f"\n  响应内容（前3个字段）:")
for i, (key, value) in enumerate(json_data.items()):
    if i >= 3:
        print(f"    ...（共{len(json_data)}个字段）")
        break
    print(f"    {key}: {value}")


# ==================== 基础4: POST请求 + 复杂JSON ====================
print("\n\n" + "=" * 60)
print("  基础4: POST发送JSON → 解析响应JSON")
print("=" * 60)

print("\n【发送复杂JSON数据】\n")

# 构造山海之巅风格的请求体
shanhai_payload = {
    "player_id": "10086",
    "item_id": "weapon_001",
    "quantity": 1,
    "options": {
        "enhance_level": 5,
        "auto_repair": False
    },
    "coupon_codes": ["ABC123", "XYZ789"],
    "trade_type": "direct"  # direct / auction
}

resp = requests.post(
    "https://httpbin.org/post",
    json=shanhai_payload,
    timeout=10
)

print(f"  状态码: {resp.status_code}")

# 解析响应JSON
result = resp.json()
print(f"\n  响应的 JSON 结构:")
print(f"    code: {result.get('code', 'N/A')}")
print(f"    origin: {result.get('origin', 'N/A')}")
print(f"    url: {result.get('url', 'N/A')}")

# 提取请求体（httpbin会回显我们发过去的数据）
echo_data = result.get("json", {})
print(f"\n  服务器收到的请求体:")
print(f"    player_id: {echo_data.get('player_id')}")
print(f"    item_id: {echo_data.get('item_id')}")
print(f"    quantity: {echo_data.get('quantity')}")

# 提取嵌套字段
enhance_level = result.get("json", {}).get("options", {}).get("enhance_level")
print(f"\n  提取嵌套字段 options.enhance_level: {enhance_level}")

# 提取列表
coupon_codes = result.get("json", {}).get("coupon_codes", [])
print(f"  提取列表字段 coupon_codes: {coupon_codes}")


# ==================== 基础5: 处理JSON错误 ====================
print("\n\n" + "=" * 60)
print("  基础5: JSON常见错误处理")
print("=" * 60)

print("""
JSON解析中最常见的3种错误：

1. JSONDecodeError - 响应不是合法JSON
   → 用 try/except 捕获，或先检查 response.text

2. KeyError - 字段不存在
   → 用 dict.get("key") 或安全提取函数

3. TypeError - 试图对非字典/列表取值
   → 先判断类型 isinstance(data, dict)
""")

print("\n【错误1: 响应不是合法JSON（模拟）】")
try:
    bad_json_str = '{"name": "test", incomplete}'
    json.loads(bad_json_str)
except json.JSONDecodeError as e:
    print(f"  ❌ JSONDecodeError: {e}")

# 安全解析函数
def safe_json_parse(response):
    """安全解析响应JSON，失败返回None"""
    try:
        return response.json()
    except (json.JSONDecodeError, ValueError) as e:
        print(f"  ⚠️ JSON解析失败: {e}")
        return None

# 测试（合法响应）
print(f"\n【安全解析函数测试】")
test_resp = requests.get("https://httpbin.org/get", timeout=10)
result = safe_json_parse(test_resp)
print(f"  解析结果: {'✅ 成功' if result else '❌ 失败'}")

print("\n【错误2: 字段不存在（get()安全写法）】")
json_data = {"name": "张三", "level": 10}
print(f"  存在的字段 name: {json_data.get('name')}")           # 正常
print(f"  不存在的字段 age: {json_data.get('age')}")           # 返回 None，不报错
print(f"  不存在的字段 age，带默认值: {json_data.get('age', '未知')}")  # 返回默认值

print("\n【错误3: 列表索引越界】")
items = ["剑", "盾"]
print(f"  items[0] = {items[0]}")
print(f"  items[5] = {safe_get(items, '5', '不存在')}")


# ==================== 实战: httpbin 返回的复杂嵌套数据 ====================
print("\n\n" + "=" * 60)
print("  实战: httpbin 返回的复杂嵌套数据解析")
print("=" * 60)

print("\n【httpbin.org/json 返回结构化JSON】")
resp = requests.get("https://httpbin.org/json", timeout=10)
data = resp.json()
print(f"  响应结构:")
for key, value in data.items():
    if isinstance(value, dict):
        print(f"    {key}: {json.dumps(value, ensure_ascii=False)[:60]}...")
    else:
        print(f"    {key}: {value}")


print("\n【httpbin.org/anything 返回自定义请求的完整回显（最像真实API）】")

# 构造一个复杂请求，模拟真实山海之巅场景
realistic_request = {
    "header": {
        "app_version": "2.1.0",
        "device_id": "DEV-ABC123",
        "platform": "ios",
        "timestamp": int(time.time())
    },
    "body": {
        "action": "enhance_weapon",
        "player_id": "10086",
        "payload": {
            "weapon_id": "W001",
            "target_level": 10,
            "materials": [
                {"id": "stone_001", "count": 5},
                {"id": "gem_blue", "count": 2}
            ],
            "protect_enabled": True
        }
    }
}

resp = requests.post(
    "https://httpbin.org/anything",
    json=realistic_request,
    headers={"Content-Type": "application/json", "X-Token": "fake_token_xyz"},
    timeout=10
)

print(f"\n  状态码: {resp.status_code}")
result = resp.json()

# 解析关键字段
print(f"\n  【提取关键字段】")
print(f"    请求的 action: {result.get('json', {}).get('body', {}).get('action')}")
print(f"    玩家ID:        {result.get('json', {}).get('body', {}).get('player_id')}")
print(f"    武器ID:        {result.get('json', {}).get('body', {}).get('payload', {}).get('weapon_id')}")
print(f"    目标等级:      {result.get('json', {}).get('body', {}).get('payload', {}).get('target_level')}")
print(f"    是否保护:      {result.get('json', {}).get('body', {}).get('payload', {}).get('protect_enabled')}")

# 遍历材料列表
materials = result.get("json", {}).get("body", {}).get("payload", {}).get("materials", [])
print(f"\n  【遍历强化材料】")
for mat in materials:
    print(f"    材料ID: {mat.get('id')}，数量: {mat.get('count')}")

# 提取响应头
print(f"\n  【提取响应头】")
print(f"    Content-Type: {resp.headers.get('Content-Type')}")
print(f"    服务器: {resp.headers.get('Server', 'N/A')}")


# ==================== 实战: 真实山海之巅风格JSON解析 ====================
print("\n\n" + "=" * 60)
print("  实战: 模拟山海之巅真实API返回的JSON解析")
print("=" * 60)

# 模拟《山海之巅》服务器返回的典型数据结构
shanhai_api_response = {
    "code": 0,
    "msg": "操作成功",
    "data": {
        "task_list": [
            {
                "task_id": "T001",
                "title": "击败10只野怪",
                "progress": {"current": 7, "target": 10},
                "rewards": [
                    {"type": "gold", "amount": 500},
                    {"type": "exp",  "amount": 1000}
                ],
                "deadline": "2026-05-20 23:59:59",
                "status": "ongoing"
            },
            {
                "task_id": "T002",
                "title": "通关第一章剧情",
                "progress": {"current": 1, "target": 1},
                "rewards": [
                    {"type": "gold", "amount": 2000},
                    {"type": "item", "item_id": "epic_sword_01"}
                ],
                "deadline": "2026-05-25 23:59:59",
                "status": "completed"
            }
        ],
        "total_count": 2,
        "page": 1,
        "page_size": 20
    }
}

print("\n【场景：解析每日任务列表】\n")

# 提取外层信息
print(f"  状态码: {shanhai_api_response['code']}")
print(f"  消息: {shanhai_api_response['msg']}")
print(f"  任务总数: {shanhai_api_response['data']['total_count']}")

# 遍历任务列表
print(f"\n  【任务列表解析】")
task_list = shanhai_api_response["data"]["task_list"]
for task in task_list:
    status_icon = "✅" if task["status"] == "completed" else "⏳"
    print(f"\n  {status_icon} 任务: {task['title']}")
    print(f"     进度: {task['progress']['current']}/{task['progress']['target']}")
    print(f"     截止: {task['deadline']}")

    # 遍历奖励
    print(f"     奖励:")
    for reward in task["rewards"]:
        if reward["type"] == "item":
            print(f"       - {reward['type']}: {reward.get('item_id', '')}")
        else:
            print(f"       - {reward['type']}: {reward['amount']}")


# ==================== 练习：模拟解析山海之巅排行榜 ====================
print("\n\n" + "=" * 60)
print("  练习: 解析山海之巅战力排行榜JSON")
print("=" * 60)

# 模拟排行榜API返回
leaderboard_response = {
    "code": 200,
    "data": {
        "ranking_type": "combat_power",
        "title": "战力排行榜",
        "my_rank": {
            "rank": 666,
            "player_id": "10086",
            "name": "我的小号",
            "combat_power": 52000
        },
        "top_players": [
            {"rank": 1,  "name": "无敌战神",  "combat_power": 888888, "guild": "刀光剑影"},
            {"rank": 2,  "name": "一剑西来",  "combat_power": 766666, "guild": "天下无双"},
            {"rank": 3,  "name": "万古长夜",  "combat_power": 655555, "guild": "风云再起"}
        ]
    }
}

print("\n【排行榜解析练习】\n")

# 练习题：用代码提取以下信息
print("  【你的任务：提取以下字段】\n")

# ① 排行榜标题
title = leaderboard_response.get("data", {}).get("title")
print(f"  ① 标题: {title}")

# ② 第1名的名字和公会
top1 = leaderboard_response.get("data", {}).get("top_players", [])[0]
print(f"  ② 第1名: {top1['name']}（公会：{top1['guild']}）")

# ③ 我的排名信息
my_rank = leaderboard_response.get("data", {}).get("my_rank", {})
print(f"  ③ 我的排名: 第{my_rank.get('rank')}名，战力 {my_rank.get('combat_power')}")

# ④ 用 for 循环打印前3名
print(f"  ④ 前3名详细信息:")
for player in leaderboard_response.get("data", {}).get("top_players", []):
    medal = ["🥇", "🥈", "🥉"][player["rank"] - 1] if player["rank"] <= 3 else f"#{player['rank']}"
    print(f"     {medal} {player['name']:8s} | 战力: {player['combat_power']:>7,} | 公会: {player['guild']}")


# ==================== 知识点总结 ====================
print("\n\n" + "=" * 60)
print("  Day 4 知识点总结")
print("=" * 60)
print("""
┌─────────────────────────────────────────────────────┐
│                    JSON处理核心                       │
├──────────────────┬──────────────────────────────────┤
│ response.json()  │ requests响应 → Python字典（最常用）│
│ json.loads(str)  │ JSON字符串 → Python对象           │
│ json.dumps(dict) │ Python对象 → JSON字符串           │
│ dict.get(key)    │ 安全取值，不存在的key返回None      │
│ safe_get(data,path)│ 安全提取嵌套字段（防KeyError）    │
└──────────────────┴──────────────────────────────────┘

【JSON解析实战技巧】
1. 先打印 response.json() 看看结构（print(json.dumps(data, indent=2))）
2. 用 .get() 而不是 [] 取值，防止 KeyError
3. 列表遍历用 for，索引用 [0]、[1]，注意边界
4. 遇到不确信的结构，用 isinstance() 先判断类型
5. 复杂嵌套用安全提取函数：safe_get(data, "a.b.c.d")

【明天预告】
Day 5: 接口断言（状态码断言、JSON字段断言、pytest断言写法）
""")

# 美化打印：indent=2 格式化JSON
print("\n【美化打印：indent=2 格式化JSON】")
print("  用 json.dumps(data, indent=2, ensure_ascii=False) 格式化输出，")
print("  让嵌套结构一目了然（接口调试神器）：\n")
sample = {
    "code": 0,
    "data": {
        "player": {"name": "张三", "level": 88}
    }
}
print(json.dumps(sample, indent=2, ensure_ascii=False))


# ==================== 练习题 ====================
print("\n" + "=" * 60)
print("  Day 4 练习题（3道选择题）")
print("=" * 60)
print("""
【第1题】以下哪个方法可以把 API 响应的 JSON 字符串解析为 Python 字典？
  A. response.text
  B. response.content
  C. response.json()
  D. json.dumps()
  正确答案: C
  解析: response.json() 等价于 json.loads(response.text)，专用于解析JSON响应

【第2题】当 JSON 中某个字段不存在时，用 dict["key"] 和 dict.get("key") 分别会怎样？
  A. 两者都返回 None
  B. 两者都会报错
  C. dict["key"] 报错，dict.get("key") 返回 None
  D. dict["key"] 返回 None，dict.get("key") 报错
  正确答案: C
  解析: dict["key"] 访问不存在的键会抛出 KeyError；
        dict.get("key") 返回 None 或默认值，不报错

【第3题】要从 {"data": {"items": [{"id": 1}, {"id": 2}]}} 中提取 id=2 的项，
  正确写法是？
  A. data["items"]["id"]
  B. data["items"][1]["id"]
  C. data["items"].get("id")
  D. data["items"][0]["id"]
  正确答案: B
  解析: items 是列表，[1] 取第2个元素，再 ["id"] 取id字段
""")


# ==================== 完成标志 ====================
print("\n" + "=" * 60)
print("  Day 4 学习完成！")
print("=" * 60)
print("""
  【今日收获】
  1. 理解 JSON 格式与 Python 数据类型的对应关系
  2. 掌握 json.loads()、json.dumps()、response.json() 三剑客
  3. 学会从嵌套 JSON 中提取字段（一层层 .[]下去）
  4. 掌握安全取值：dict.get(key) vs dict[key]
  5. 实现安全提取函数 safe_get()，防止 KeyError/TypeError
  6. 处理 JSONDecodeError 等常见异常
  7. 实战解析了 httpbin 返回的多种复杂JSON结构
  8. 模拟了山海之巅任务列表、战力排行榜等真实场景

  【明天预告】
  Day 5: 接口断言（状态码断言、JSON字段断言、pytest断言写法）

  【检查标准】
  1. 能正确解析 response.json()
  2. 能从嵌套JSON中提取任意深度的字段
  3. 能用 dict.get() 安全取值
  4. 能处理 JSONDecodeError 和 KeyError
  5. 能用 for 循环遍历 JSON 数组
""")
