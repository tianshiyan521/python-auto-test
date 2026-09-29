# -*- coding: utf-8 -*-
"""
Python+Requests 14天学习计划 - Day 5
接口断言：状态码断言、JSON字段断言、pytest断言写法

学习目标：
1. 掌握状态码断言的多种写法
2. 掌握JSON字段断言（字段存在、值匹配、类型检查）
3. 掌握pytest断言写法（assert + pytest.raises + fixture）
4. 了解断言失败时的信息输出技巧
"""

import requests
import json
import pytest

# ============================================================
# 一、状态码断言
# ============================================================

def test_status_code_basic():
    """最基本的断言：状态码是否为200"""
    resp = requests.get("https://httpbin.org/get")
    # 方式1：直接 assert
    assert resp.status_code == 200
    print(f"✅ 状态码断言通过: {resp.status_code}")


def test_status_code_with_message():
    """带自定义错误信息的断言（失败时更易定位）"""
    resp = requests.get("https://httpbin.org/get")
    # 方式2：assert + 错误信息，方便排查
    assert resp.status_code == 200, f"期望200，实际{resp.status_code}"
    print(f"✅ 带信息的状态码断言通过")


def test_status_code_helpers():
    """requests内置的状态码判断方法"""
    resp = requests.get("https://httpbin.org/get")
    # 方式3：使用requests内置属性
    assert resp.ok, "响应不OK"           # 2xx为True
    assert resp.reason == "OK", f"reason不是OK，是{resp.reason}"
    # raise_for_status()：非2xx直接抛HTTPError，常用于"不成功就报错"场景
    resp.raise_for_status()              # 2xx不报错，4xx/5xx抛异常
    print(f"✅ requests内置状态码判断全部通过")


def test_status_code_not_found():
    """断言404等非200状态码"""
    resp = requests.get("https://httpbin.org/status/404")
    assert resp.status_code == 404, f"期望404，实际{resp.status_code}"
    # 注意：404不会触发raise_for_status的异常，要手动assert
    print(f"✅ 404状态码断言通过")


def test_status_code_5xx():
    """5xx服务端错误的断言"""
    resp = requests.get("https://httpbin.org/status/500")
    assert resp.status_code == 500, f"期望500，实际{resp.status_code}"
    # raise_for_status() 对5xx会抛异常，可以用pytest.raises捕获
    with pytest.raises(requests.exceptions.HTTPError):
        resp.raise_for_status()
    print(f"✅ 500状态码 + raise_for_status异常捕获通过")


# ============================================================
# 二、JSON字段断言
# ============================================================

def test_json_field_exists():
    """断言JSON返回中某个字段存在"""
    resp = requests.get("https://httpbin.org/get")
    data = resp.json()
    # httpbin.org/get 返回 { "args": {}, "headers": {...}, "origin": "...", "url": "..." }
    assert "headers" in data, "返回数据缺少headers字段"
    assert "url" in data, "返回数据缺少url字段"
    print(f"✅ 字段存在性断言通过，字段列表: {list(data.keys())}")


def test_json_field_value():
    """断言JSON字段的值"""
    resp = requests.get("https://httpbin.org/get?name=tester&role=qa")
    data = resp.json()
    # 断言args中的值
    assert data["args"]["name"] == "tester", f"name期望tester，实际{data['args'].get('name')}"
    assert data["args"]["role"] == "qa", f"role期望qa，实际{data['args'].get('role')}"
    print(f"✅ 字段值断言通过: name={data['args']['name']}, role={data['args']['role']}")


def test_json_field_type():
    """断言JSON字段的数据类型"""
    resp = requests.get("https://httpbin.org/get")
    data = resp.json()
    # 断言字段类型
    assert isinstance(data["args"], dict), f"args应为dict，实际{type(data['args'])}"
    assert isinstance(data["headers"], dict), f"headers应为dict，实际{type(data['headers'])}"
    assert isinstance(data["url"], str), f"url应为str，实际{type(data['url'])}"
    print(f"✅ 字段类型断言通过")


def test_json_field_with_post():
    """POST请求的JSON字段断言"""
    payload = {
        "player_name": "测试勇士",
        "level": 30,
        "skills": ["火球术", "冰冻术", "闪电链"],
        "stats": {"attack": 850, "defense": 320, "hp": 5000}
    }
    resp = requests.post("https://httpbin.org/post", json=payload)
    data = resp.json()

    # 1. 断言状态码
    assert resp.status_code == 200
    # 2. 断言返回的data字段（httpbin会原样返回）
    returned_data = data["data"]  # 注意：httpbin返回的data是JSON字符串
    parsed = json.loads(returned_data)
    assert parsed["player_name"] == "测试勇士"
    assert parsed["level"] == 30
    assert len(parsed["skills"]) == 3
    assert "火球术" in parsed["skills"]
    assert parsed["stats"]["attack"] == 850
    assert parsed["stats"]["hp"] == 5000
    # 3. 断言Content-Type
    assert "application/json" in data["headers"]["Content-Type"]
    print(f"✅ POST JSON字段断言全部通过")


def test_json_nested_field_safe():
    """安全断言嵌套字段（防KeyError）"""
    resp = requests.get("https://httpbin.org/get")
    data = resp.json()

    # 方式1：dict.get() 安全取值，不存在返回None
    origin = data.get("origin")
    assert origin is not None, "origin字段缺失或为None"

    # 方式2：不存在的字段，get返回None而不是报KeyError
    missing = data.get("non_exist_field")
    assert missing is None, f"不存在的字段应返回None，实际{missing}"

    # 方式3：带默认值
    fallback = data.get("non_exist", "default_value")
    assert fallback == "default_value"

    print(f"✅ 安全取值断言通过，origin={origin}")


# ============================================================
# 三、pytest断言进阶写法
# ============================================================

def test_pytest_assert_in():
    """pytest: 断言包含关系（in / not in）"""
    resp = requests.get("https://httpbin.org/get")
    data = resp.json()
    url = data["url"]
    assert "httpbin.org" in url, f"url中应包含httpbin.org，实际{url}"
    assert "baidu.com" not in url, f"url中不应包含baidu.com"
    print(f"✅ in/not in 断言通过")


def test_pytest_assert_comparison():
    """pytest: 断言比较运算（>, <, >=, <=）"""
    resp = requests.get("https://httpbin.org/get")
    # 断言响应时间
    assert resp.elapsed.total_seconds() < 5.0, f"响应时间{resp.elapsed.total_seconds():.2f}s超过5s"
    # 断言响应头数量
    assert len(resp.headers) > 0, "响应头为空"
    print(f"✅ 比较运算断言通过，响应时间: {resp.elapsed.total_seconds():.2f}s")


def test_pytest_raises():
    """pytest: 断言异常被抛出（pytest.raises）"""
    # 场景：传入非法URL应该抛异常
    with pytest.raises(requests.exceptions.MissingSchema):
        requests.get("not_a_valid_url")
    print(f"✅ pytest.raises异常断言通过")


def test_pytest_raises_with_match():
    """pytest: 断言异常信息匹配（raises + match）"""
    # 场景：HTTPError的异常信息包含状态码
    resp = requests.get("https://httpbin.org/status/404")
    with pytest.raises(requests.exceptions.HTTPError) as exc_info:
        resp.raise_for_status()
    # match() 用正则匹配异常信息
    assert "404" in str(exc_info.value), f"异常信息应包含404，实际{exc_info.value}"
    print(f"✅ raises + match断言通过，异常信息: {exc_info.value}")


# ============================================================
# 四、综合实战：模拟山海之巅接口断言
# ============================================================

def test_shanzhi_player_login_assert():
    """实战：模拟山海之巅-玩家登录接口的完整断言"""
    # 模拟登录请求（用httpbin模拟）
    login_data = {
        "username": "warrior_001",
        "password": "test123456"
    }
    resp = requests.post("https://httpbin.org/post", json=login_data)
    data = resp.json()

    # ---- 第一层：状态码断言 ----
    assert resp.status_code == 200, f"登录接口状态码错误: {resp.status_code}"

    # ---- 第二层：返回结构断言 ----
    assert "data" in data, "返回缺少data字段"
    assert "headers" in data, "返回缺少headers字段"

    # ---- 第三层：业务字段断言 ----
    parsed = json.loads(data["data"])
    assert parsed["username"] == "warrior_001", "用户名不匹配"
    assert parsed["password"] == "test123456", "密码不匹配"

    # ---- 第四层：Content-Type断言 ----
    assert "application/json" in data["headers"]["Content-Type"], "Content-Type应为JSON"

    # ---- 第五层：响应时间断言 ----
    assert resp.elapsed.total_seconds() < 10.0, f"响应超时: {resp.elapsed.total_seconds():.2f}s"

    print(f"✅ 山海之巅-登录接口完整断言全部通过")


def test_shanzhi_get_player_info_assert():
    """实战：模拟山海之巅-获取玩家信息接口的完整断言"""
    # 模拟获取玩家信息
    resp = requests.get("https://httpbin.org/get", params={
        "player_id": "P10086",
        "server": "s1"
    })
    data = resp.json()

    # 断言1：状态码
    assert resp.status_code == 200

    # 断言2：返回结构
    assert "args" in data
    assert "headers" in data

    # 断言3：查询参数正确返回
    assert data["args"]["player_id"] == "P10086"
    assert data["args"]["server"] == "s1"

    # 断言4：字段类型
    assert isinstance(data["args"], dict)
    assert isinstance(data["headers"], dict)

    # 断言5：origin不为空（有真实IP返回）
    assert data.get("origin") is not None, "origin不应为空"

    print(f"✅ 山海之巅-玩家信息接口完整断言通过")


def test_shanzhi_edge_cases():
    """实战：边界情况断言（空参、特殊字符、超长字段）"""
    # 边界1：空参数GET
    resp = requests.get("https://httpbin.org/get")
    assert resp.status_code == 200
    assert resp.json()["args"] == {}, "无参数时args应为空字典"

    # 边界2：特殊字符参数
    special = "测试<>\"'&中文"
    resp = requests.get("https://httpbin.org/get", params={"q": special})
    assert resp.status_code == 200
    # httpbin会编码后返回
    assert resp.json()["args"]["q"] == special, "特殊字符应正确回传"

    # 边界3：DELETE请求断言
    resp = requests.delete("https://httpbin.org/delete")
    assert resp.status_code == 200

    # 边界4：PUT请求断言
    resp = requests.put("https://httpbin.org/put", json={"action": "update"})
    assert resp.status_code == 200
    put_data = resp.json()
    assert "data" in put_data

    print(f"✅ 边界情况断言全部通过")


# ============================================================
# 五、断言失败时的调试技巧
# ============================================================

def test_assert_with_detail_info():
    """断言失败时输出详细信息，方便定位"""
    resp = requests.get("https://httpbin.org/get?token=abc123")
    data = resp.json()

    # 技巧1：断言时输出完整响应（失败时一眼看到问题）
    assert data["args"]["token"] == "abc123", \
        f"token不匹配！完整返回: {json.dumps(data, ensure_ascii=False, indent=2)}"

    # 技巧2：多个断言合一（一次检查多个条件，失败信息清晰）
    checks = {
        "状态码": resp.status_code == 200,
        "有args字段": "args" in data,
        "token正确": data.get("args", {}).get("token") == "abc123",
        "响应时间<5s": resp.elapsed.total_seconds() < 5.0,
    }
    failed = [k for k, v in checks.items() if not v]
    assert not failed, f"以下检查未通过: {failed}"

    print(f"✅ 断言调试技巧演示通过，全部{len(checks)}项检查OK")


# ============================================================
# 运行说明：
#   pytest requests_day5.py -v          # 详细输出
#   pytest requests_day5.py -v -s       # 详细输出 + print内容
#   pytest requests_day5.py -k "shanzhi"  # 只跑山海之巅相关测试
#   pytest requests_day5.py::test_status_code_basic  # 只跑单个用例
# ============================================================
