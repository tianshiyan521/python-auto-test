"""
Requests + SQLite 联合实战
把14天学的接口测试技能和数据库技能串起来：
接口测试 → 结果存数据库 → 数据库查询生成报告 → 数据驱动从DB读取用例

SQLite 是 Python 内置数据库，语法和 MySQL 几乎一样
真实项目里只需把 connection 改成 pymysql.connect(...) 就能迁移到 MySQL
"""

import sqlite3
import requests
import json
import time
import sys
from datetime import datetime

# 解决 Windows 终端编码问题
sys.stdout.reconfigure(encoding="utf-8")


# ============================================================
# Part 1: SQLite 数据库初始化 —— 建表（和 MySQL 建表语法几乎一样）
# ============================================================

def init_database(db_path="test_results.db"):
    """创建测试数据库和表结构"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 表1: test_cases —— 测试用例表（和 MySQL CREATE TABLE 语法完全一样）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_name TEXT NOT NULL,
            api_url TEXT NOT NULL,
            method TEXT NOT NULL DEFAULT 'GET',
            headers TEXT DEFAULT '{}',
            params TEXT DEFAULT '{}',
            body TEXT DEFAULT '{}',
            expected_status INTEGER DEFAULT 200,
            expected_field TEXT DEFAULT '',
            expected_value TEXT DEFAULT '',
            priority TEXT DEFAULT 'P1',
            module TEXT DEFAULT '通用',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 表2: test_results —— 测试结果表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            case_name TEXT NOT NULL,
            actual_status INTEGER,
            actual_response TEXT,
            is_passed INTEGER DEFAULT 0,
            error_msg TEXT DEFAULT '',
            response_time_ms REAL DEFAULT 0,
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (case_id) REFERENCES test_cases(id)
        )
    """)

    # 表3: test_summary —— 每日测试汇总表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_date TEXT NOT NULL,
            total_cases INTEGER DEFAULT 0,
            passed_cases INTEGER DEFAULT 0,
            failed_cases INTEGER DEFAULT 0,
            pass_rate TEXT DEFAULT '0%',
            avg_response_time_ms REAL DEFAULT 0,
            modules TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    print("✅ Part 1: 数据库初始化完成（3张表: test_cases / test_results / test_summary）")
    print("   SQLite建表语法和MySQL几乎一样，真实项目只需改连接方式")
    print("   sqlite3.connect() → pymysql.connect(host, user, password, db)")
    print()
    return conn


# ============================================================
# Part 2: 插入测试用例数据 —— 数据准备（INSERT INTO 和 MySQL 一样）
# ============================================================

def insert_test_cases(conn):
    """向数据库插入测试用例数据"""
    cursor = conn.cursor()

    # 先清空旧数据，保证每次运行干净
    cursor.execute("DELETE FROM test_cases")
    cursor.execute("DELETE FROM test_results")
    cursor.execute("DELETE FROM test_summary")

    # 定义测试用例 —— 模拟山海之巅项目的接口测试矩阵
    test_cases = [
        # ---- GET 请求用例 ----
        {
            "case_name": "获取用户信息-正常",
            "api_url": "https://httpbin.org/get",
            "method": "GET",
            "headers": '{"Accept": "application/json"}',
            "params": '{"user_id": "10001", "game": "shanhai"}',
            "body": '{}',
            "expected_status": 200,
            "expected_field": "args.user_id",
            "expected_value": "10001",
            "priority": "P0",
            "module": "Login"
        },
        {
            "case_name": "获取用户信息-空参数",
            "api_url": "https://httpbin.org/get",
            "method": "GET",
            "headers": '{}',
            "params": '{}',
            "body": '{}',
            "expected_status": 200,
            "expected_field": "args",
            "expected_value": "{}",
            "priority": "P1",
            "module": "Login"
        },
        {
            "case_name": "获取用户信息-特殊字符注入",
            "api_url": "https://httpbin.org/get",
            "method": "GET",
            "headers": '{}',
            "params": '{"user_id": "1 OR 1=1"}',
            "body": '{}',
            "expected_status": 200,
            "expected_field": "args.user_id",
            "expected_value": "1 OR 1=1",
            "priority": "P1",
            "module": "Security"
        },
        {
            "case_name": "404路径-不存在的API",
            "api_url": "https://httpbin.org/status/404",
            "method": "GET",
            "headers": '{}',
            "params": '{}',
            "body": '{}',
            "expected_status": 404,
            "expected_field": "",
            "expected_value": "",
            "priority": "P2",
            "module": "Smoke"
        },
        # ---- POST 请求用例 ----
        {
            "case_name": "玩家登录-正常",
            "api_url": "https://httpbin.org/post",
            "method": "POST",
            "headers": '{"Content-Type": "application/json"}',
            "params": '{}',
            "body": '{"username": "test_player", "password": "abc123"}',
            "expected_status": 200,
            "expected_field": "json.username",
            "expected_value": "test_player",
            "priority": "P0",
            "module": "Login"
        },
        {
            "case_name": "玩家登录-空用户名",
            "api_url": "https://httpbin.org/post",
            "method": "POST",
            "headers": '{"Content-Type": "application/json"}',
            "params": '{}',
            "body": '{"username": "", "password": "abc123"}',
            "expected_status": 200,
            "expected_field": "json.username",
            "expected_value": "",
            "priority": "P1",
            "module": "Login"
        },
        {
            "case_name": "创建角色-正常",
            "api_url": "https://httpbin.org/post",
            "method": "POST",
            "headers": '{"Content-Type": "application/json"}',
            "params": '{}',
            "body": '{"name": "战神", "class": "warrior", "level": 1}',
            "expected_status": 200,
            "expected_field": "json.name",
            "expected_value": "战神",
            "priority": "P0",
            "module": "Player"
        },
        {
            "case_name": "战斗结算-正常",
            "api_url": "https://httpbin.org/post",
            "method": "POST",
            "headers": '{"Content-Type": "application/json"}',
            "params": '{}',
            "body": '{"battle_id": "B001", "result": "win", "score": 100}',
            "expected_status": 200,
            "expected_field": "json.result",
            "expected_value": "win",
            "priority": "P0",
            "module": "Combat"
        },
        # ---- PUT 请求用例 ----
        {
            "case_name": "更新玩家信息-正常",
            "api_url": "https://httpbin.org/put",
            "method": "PUT",
            "headers": '{"Content-Type": "application/json"}',
            "params": '{}',
            "body": '{"nickname": "新名字", "avatar": "img_001"}',
            "expected_status": 200,
            "expected_field": "json.nickname",
            "expected_value": "新名字",
            "priority": "P1",
            "module": "Player"
        },
        # ---- DELETE 请求用例 ----
        {
            "case_name": "删除道具-正常",
            "api_url": "https://httpbin.org/delete",
            "method": "DELETE",
            "headers": '{}',
            "params": '{"item_id": "I001"}',
            "body": '{}',
            "expected_status": 200,
            "expected_field": "",
            "expected_value": "",
            "priority": "P2",
            "module": "Item"
        },
        # ---- 边界用例 ----
        {
            "case_name": "超长用户名(500字符)",
            "api_url": "https://httpbin.org/post",
            "method": "POST",
            "headers": '{"Content-Type": "application/json"}',
            "params": '{}',
            "body": '{"username": "AAAAAAAAAA...repeat50times...AAAAAAAAAA"}',
            "expected_status": 200,
            "expected_field": "",
            "expected_value": "",
            "priority": "P2",
            "module": "Boundary"
        },
        {
            "case_name": "响应延迟测试(1秒)",
            "api_url": "https://httpbin.org/delay/1",
            "method": "GET",
            "headers": '{}',
            "params": '{}',
            "body": '{}',
            "expected_status": 200,
            "expected_field": "",
            "expected_value": "",
            "priority": "P2",
            "module": "Performance"
        },
    ]

    for case in test_cases:
        cursor.execute("""
            INSERT INTO test_cases (case_name, api_url, method, headers, params, body,
                                    expected_status, expected_field, expected_value,
                                    priority, module)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            case["case_name"], case["api_url"], case["method"],
            case["headers"], case["params"], case["body"],
            case["expected_status"], case["expected_field"], case["expected_value"],
            case["priority"], case["module"]
        ))

    conn.commit()
    print(f"✅ Part 2: 插入 {len(test_cases)} 条测试用例到数据库")
    print("   INSERT INTO 和 MySQL 语法一样，SQLite 用 ? 占位符，MySQL 用 %s")
    print()

    # 查看插入结果（SELECT 语法完全一样）
    cursor.execute("SELECT id, case_name, method, priority, module FROM test_cases")
    rows = cursor.fetchall()
    print("   📋 用例清单:")
    print(f"   {'ID':>3} | {'用例名':<28} | {'方法':<7} | {'优先级':<4} | {'模块':<10}")
    print("   " + "-" * 60)
    for row in rows:
        print(f"   {row[0]:>3} | {row[1]:<28} | {row[2]:<7} | {row[3]:<4} | {row[4]:<10}")
    print()
    return len(test_cases)


# ============================================================
# Part 3: 执行接口测试 —— 从数据库读取用例 → requests调用 → 结果存回数据库
# ============================================================

def safe_get_nested(data, field_path, default=None):
    """安全提取嵌套字段（Day4学的技能）"""
    if not field_path:
        return default
    keys = field_path.split(".")
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default)
        elif isinstance(current, list):
            try:
                current = current[int(key)]
            except (ValueError, IndexError):
                return default
        else:
            return default
    return current


def execute_test_from_db(conn, session=None):
    """从数据库读取测试用例 → 执行接口测试 → 结果存回数据库"""
    if session is None:
        session = requests.Session()

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM test_cases ORDER BY priority, id")
    cases = cursor.fetchall()

    total = len(cases)
    passed = 0
    failed = 0
    total_time = 0

    print("=" * 70)
    print("🚀 Part 3: 从数据库读取用例 → 执行接口测试 → 结果存回数据库")
    print("=" * 70)
    print(f"   共读取 {total} 条用例，开始执行...\n")

    for case in cases:
        (case_id, case_name, api_url, method, headers_str,
         params_str, body_str, expected_status, expected_field,
         expected_value, priority, module, created_at) = case

        # 从数据库读取的 JSON 字符串 → 解析为 Python 对象
        headers = json.loads(headers_str) if headers_str and headers_str != '{}' else {}
        params = json.loads(params_str) if params_str and params_str != '{}' else {}
        body = json.loads(body_str) if body_str and body_str != '{}' else {}

        # 执行请求（带重试机制）
        start_time = time.time()
        is_passed = False
        error_msg = ""
        actual_status = 0
        actual_response = ""

        for retry in range(3):
            try:
                if method.upper() == "GET":
                    resp = session.get(api_url, params=params, headers=headers, timeout=10)
                elif method.upper() == "POST":
                    resp = session.post(api_url, json=body, headers=headers, timeout=10)
                elif method.upper() == "PUT":
                    resp = session.put(api_url, json=body, headers=headers, timeout=10)
                elif method.upper() == "DELETE":
                    resp = session.delete(api_url, params=params, headers=headers, timeout=10)
                elif method.upper() == "PATCH":
                    resp = session.patch(api_url, json=body, headers=headers, timeout=10)
                else:
                    resp = session.get(api_url, timeout=10)

                actual_status = resp.status_code
                actual_response = resp.text[:500]  # 只存前500字符，避免数据库太大
                elapsed_ms = (time.time() - start_time) * 1000
                total_time += elapsed_ms

                # 断言1: 状态码
                if actual_status != expected_status:
                    is_passed = False
                    error_msg = f"状态码不符: 期望{expected_status}, 实际{actual_status}"
                    break

                # 断言2: JSON字段值（如果指定了 expected_field）
                if expected_field and expected_value:
                    try:
                        resp_json = resp.json()
                        actual_val = safe_get_nested(resp_json, expected_field)

                        # expected_value 可能是字典的字符串表示
                        if expected_value.startswith("{"):
                            expected_val = json.loads(expected_value)
                        else:
                            expected_val = expected_value

                        if actual_val != expected_val:
                            is_passed = False
                            error_msg = f"字段值不符: 期望{expected_val}, 实际{actual_val}"
                            break
                    except json.JSONDecodeError:
                        is_passed = False
                        error_msg = "响应非JSON格式"
                        break

                # 全部断言通过
                is_passed = True
                break

            except requests.exceptions.Timeout:
                error_msg = f"请求超时(重试{retry+1}/3)"
                time.sleep(1)
            except requests.exceptions.ConnectionError:
                error_msg = f"连接失败(重试{retry+1}/3)"
                time.sleep(2)
            except Exception as e:
                error_msg = str(e)
                break

        # ✅ 核心：测试结果存入数据库！
        cursor.execute("""
            INSERT INTO test_results (case_id, case_name, actual_status, actual_response,
                                      is_passed, error_msg, response_time_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            case_id, case_name, actual_status, actual_response,
            1 if is_passed else 0, error_msg, elapsed_ms if is_passed else 0
        ))
        conn.commit()

        # 统计
        if is_passed:
            passed += 1
            print(f"   ✅ [{priority}] {case_name} ({actual_status}, {elapsed_ms:.0f}ms)")
        else:
            failed += 1
            print(f"   ❌ [{priority}] {case_name} → {error_msg}")

    avg_time = total_time / total if total > 0 else 0
    print()
    print(f"   📊 执行完成: {passed}/{total} 通过, {failed} 失败, 平均响应 {avg_time:.0f}ms")
    print()

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "avg_time": avg_time
    }


# ============================================================
# Part 4: 数据库查询生成测试报告 —— SELECT 聚合查询（和 MySQL 语法一样）
# ============================================================

def generate_report_from_db(conn):
    """从数据库查询测试结果，生成Markdown测试报告"""
    cursor = conn.cursor()

    print("=" * 70)
    print("📊 Part 4: 从数据库查询生成测试报告")
    print("=" * 70)

    # ---- 查询1: 总体统计 ----
    # MySQL和SQLite的聚合函数完全一样：COUNT, SUM, AVG, MAX, MIN
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            SUM(is_passed) as passed,
            SUM(CASE WHEN is_passed = 0 THEN 1 ELSE 0 END) as failed,
            AVG(response_time_ms) as avg_time,
            MAX(response_time_ms) as max_time,
            MIN(response_time_ms) as min_time
        FROM test_results
    """)
    stats = cursor.fetchone()
    total, passed, failed, avg_time, max_time, min_time = stats
    pass_rate = (passed / total * 100) if total > 0 else 0

    print(f"   总体统计: {total}条, {passed}通过, {failed}失败, 通过率{pass_rate:.1f}%")
    print(f"   响应时间: 平均{avg_time:.0f}ms, 最快{min_time:.0f}ms, 最慢{max_time:.0f}ms")
    print()

    # ---- 查询2: 按模块分组统计（GROUP BY，和MySQL一样）----
    cursor.execute("""
        SELECT
            c.module,
            COUNT(*) as total,
            SUM(r.is_passed) as passed,
            AVG(r.response_time_ms) as avg_time
        FROM test_results r
        JOIN test_cases c ON r.case_id = c.id
        GROUP BY c.module
        ORDER BY passed DESC, total DESC
    """)
    module_stats = cursor.fetchall()

    print("   📋 模块统计:")
    print(f"   {'模块':<12} | {'总数':>4} | {'通过':>4} | {'通过率':>6} | {'平均耗时':>8}")
    print("   " + "-" * 50)
    for row in module_stats:
        module, m_total, m_passed, m_avg = row
        m_rate = (m_passed / m_total * 100) if m_total > 0 else 0
        print(f"   {module:<12} | {m_total:>4} | {m_passed:>4} | {m_rate:>5.1f}% | {m_avg:>7.0f}ms")
    print()

    # ---- 查询3: 按优先级统计 ----
    cursor.execute("""
        SELECT
            c.priority,
            COUNT(*) as total,
            SUM(r.is_passed) as passed
        FROM test_results r
        JOIN test_cases c ON r.case_id = c.id
        GROUP BY c.priority
        ORDER BY c.priority
    """)
    priority_stats = cursor.fetchall()

    print("   📋 优先级统计:")
    for row in priority_stats:
        pri, p_total, p_passed = row
        p_rate = (p_passed / p_total * 100) if p_total > 0 else 0
        print(f"   {pri}: {p_passed}/{p_total} ({p_rate:.0f}%)")
    print()

    # ---- 查询4: 失败用例详情（WHERE 过滤，和 MySQL 一样）----
    cursor.execute("""
        SELECT r.case_name, c.module, c.priority, r.actual_status,
               c.expected_status, r.error_msg, r.response_time_ms
        FROM test_results r
        JOIN test_cases c ON r.case_id = c.id
        WHERE r.is_passed = 0
        ORDER BY c.priority, r.response_time_ms DESC
    """)
    failed_cases = cursor.fetchall()

    if failed_cases:
        print("   ❌ 失败用例详情:")
        for row in failed_cases:
            name, module, pri, actual_st, expected_st, err, rt = row
            print(f"   [{pri}] {name} ({module}): {err}")
    else:
        print("   🎉 全部通过，无失败用例！")
    print()

    # ---- 查询5: 响应时间最慢的5个用例（ORDER BY + LIMIT，和 MySQL 一样）----
    cursor.execute("""
        SELECT r.case_name, c.module, r.response_time_ms, r.is_passed
        FROM test_results r
        JOIN test_cases c ON r.case_id = c.id
        ORDER BY r.response_time_ms DESC
        LIMIT 5
    """)
    slow_cases = cursor.fetchall()

    print("   🐌 响应最慢Top5:")
    for row in slow_cases:
        name, module, rt, passed_flag = row
        status = "✅" if passed_flag else "❌"
        print(f"   {status} {name} ({module}): {rt:.0f}ms")
    print()

    # ---- 生成Markdown报告文件 ----
    report_lines = [
        "# 接口测试报告（Requests + SQLite）",
        f"\n**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
        f"**数据来源**: SQLite数据库 test_results.db\n\n",
        "## 总体统计\n",
        f"| 指标 | 值 |",
        f"|------|------|",
        f"| 总用例数 | {total} |",
        f"| 通过数 | {passed} |",
        f"| 失败数 | {failed} |",
        f"| 通过率 | {pass_rate:.1f}% |",
        f"| 平均响应时间 | {avg_time:.0f}ms |",
        f"| 最快响应时间 | {min_time:.0f}ms |",
        f"| 最慢响应时间 | {max_time:.0f}ms |\n\n",
        "## 模块统计\n",
        "| 模块 | 总数 | 通过 | 通过率 | 平均耗时 |",
        "|------|------|------|--------|----------|",
    ]
    for row in module_stats:
        module, m_total, m_passed, m_avg = row
        m_rate = (m_passed / m_total * 100) if m_total > 0 else 0
        report_lines.append(f"| {module} | {m_total} | {m_passed} | {m_rate:.1f}% | {m_avg:.0f}ms |")

    report_lines.extend([
        "\n\n## 优先级统计\n",
        "| 优先级 | 总数 | 通过 | 通过率 |",
        "|--------|------|------|--------|",
    ])
    for row in priority_stats:
        pri, p_total, p_passed = row
        p_rate = (p_passed / p_total * 100) if p_total > 0 else 0
        report_lines.append(f"| {pri} | {p_total} | {p_passed} | {p_rate:.0f}% |")

    if failed_cases:
        report_lines.extend([
            "\n\n## 失败用例\n",
            "| 用例名 | 模块 | 优先级 | 错误信息 |",
            "|--------|------|--------|----------|",
        ])
        for row in failed_cases:
            name, module, pri, actual_st, expected_st, err, rt = row
            report_lines.append(f"| {name} | {module} | {pri} | {err} |")

    report_lines.extend([
        "\n\n## 响应最慢Top5\n",
        "| 用例名 | 模块 | 耗时 | 状态 |",
        "|--------|------|------|------|",
    ])
    for row in slow_cases:
        name, module, rt, passed_flag = row
        status = "通过" if passed_flag else "失败"
        report_lines.append(f"| {name} | {module} | {rt:.0f}ms | {status} |")

    report_content = "\n".join(report_lines)
    report_path = "requests学习/test_report_db.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"✅ Markdown报告已生成: {report_path}")
    print()

    # ---- 存入汇总表 ----
    modules_str = ", ".join([row[0] for row in module_stats])
    cursor.execute("""
        INSERT INTO test_summary (run_date, total_cases, passed_cases, failed_cases,
                                  pass_rate, avg_response_time_ms, modules)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d"),
        total, passed, failed,
        f"{pass_rate:.1f}%", avg_time, modules_str
    ))
    conn.commit()
    print("✅ 测试汇总数据已存入 test_summary 表")

    return stats


# ============================================================
# Part 5: SQLite vs MySQL 语法对比 —— 真实项目迁移指南
# ============================================================

def show_sqlite_vs_mysql_comparison():
    """SQLite 和 MySQL 的语法对比，教你如何在真实项目中迁移"""
    print("=" * 70)
    print("📖 Part 5: SQLite vs MySQL 语法对比 —— 真实项目迁移指南")
    print("=" * 70)

    comparisons = [
        ("连接数据库",
         "sqlite3.connect('test.db')",
         "pymysql.connect(host='localhost', user='root', password='123', db='test')"),

        ("建表语法",
         "CREATE TABLE ... (完全一样)",
         "CREATE TABLE ... (完全一样，MySQL多了AUTO_INCREMENT关键词)"),

        ("占位符",
         "? (问号占位符)",
         "%s (百分号s占位符)"),

        ("自增ID",
         "INTEGER PRIMARY KEY AUTOINCREMENT",
         "INT PRIMARY KEY AUTO_INCREMENT"),

        ("字符串类型",
         "TEXT",
         "VARCHAR(255) / TEXT"),

        ("时间类型",
         "TIMESTAMP (SQLite实际存为TEXT)",
         "DATETIME / TIMESTAMP (MySQL有真正的时间类型)"),

        ("LIMIT用法",
         "SELECT ... LIMIT 5",
         "SELECT ... LIMIT 5 (完全一样)"),

        ("聚合函数",
         "COUNT/SUM/AVG/MAX/MIN (完全一样)",
         "COUNT/SUM/AVG/MAX/MIN (完全一样)"),

        ("GROUP BY",
         "GROUP BY module (完全一样)",
         "GROUP BY module (完全一样)"),

        ("JOIN",
         "JOIN / LEFT JOIN (完全一样)",
         "JOIN / LEFT JOIN (完全一样)"),

        ("CASE WHEN",
         "CASE WHEN ... THEN ... ELSE ... END",
         "CASE WHEN ... THEN ... ELSE ... END (完全一样)"),

        ("事务",
         "conn.commit() / conn.rollback()",
         "conn.commit() / conn.rollback() (完全一样)"),
    ]

    print(f"\n   {'操作':<14} | {'SQLite':<40} | {'MySQL':<40}")
    print("   " + "-" * 100)
    for item in comparisons:
        print(f"   {item[0]:<14} | {item[1]:<40} | {item[2]:<40}")

    print("\n   🎯 迁移步骤:")
    print("   1. pip install pymysql")
    print("   2. 把 sqlite3.connect() 改成 pymysql.connect(host, user, password, database)")
    print("   3. 把 ? 占位符改成 %s 占位符")
    print("   4. INTEGER → INT, TEXT → VARCHAR, AUTOINCREMENT → AUTO_INCREMENT")
    print("   5. 其他语法（SELECT/JOIN/GROUP BY/聚合）完全不用改！")
    print()


# ============================================================
# Part 6: 数据驱动实战 —— 从数据库读取用例，参数化执行
# ============================================================

def data_driven_from_db(conn):
    """从数据库读取特定条件的用例，做数据驱动执行"""
    cursor = conn.cursor()

    print("=" * 70)
    print("🔄 Part 6: 数据驱动实战 —— 从数据库读取用例，条件筛选执行")
    print("=" * 70)

    # 场景1: 只跑P0优先级用例（冒烟测试）
    cursor.execute("""
        SELECT case_name, api_url, method, params, body, expected_status
        FROM test_cases
        WHERE priority = 'P0'
        ORDER BY id
    """)
    p0_cases = cursor.fetchall()

    print(f"\n   🔥 冒烟测试（P0优先级）: {len(p0_cases)} 条用例")
    session = requests.Session()
    p0_passed = 0

    for case in p0_cases:
        name, url, method, params_str, body_str, expected_st = case
        params = json.loads(params_str) if params_str and params_str != '{}' else {}
        body = json.loads(body_str) if body_str and body_str != '{}' else {}

        try:
            if method.upper() == "GET":
                resp = session.get(url, params=params, timeout=10)
            elif method.upper() == "POST":
                resp = session.post(url, json=body, timeout=10)
            else:
                resp = session.get(url, timeout=10)

            result = "✅ PASS" if resp.status_code == expected_st else f"❌ FAIL({resp.status_code})"
            if resp.status_code == expected_st:
                p0_passed += 1
            print(f"   {result} {name}")
        except Exception as e:
            print(f"   ❌ ERROR {name}: {e}")

    print(f"   冒烟结果: {p0_passed}/{len(p0_cases)} 通过")
    print()

    # 场景2: 只跑Security模块用例（安全测试）
    cursor.execute("""
        SELECT case_name, api_url, method, params, body, expected_status, expected_field, expected_value
        FROM test_cases
        WHERE module = 'Security'
        ORDER BY id
    """)
    sec_cases = cursor.fetchall()

    print(f"   🔒 安全测试（Security模块）: {len(sec_cases)} 条用例")
    sec_passed = 0

    for case in sec_cases:
        name, url, method, params_str, body_str, expected_st, exp_field, exp_value = case
        params = json.loads(params_str) if params_str and params_str != '{}' else {}
        body = json.loads(body_str) if body_str and body_str != '{}' else {}

        try:
            resp = session.get(url, params=params, timeout=10)
            result = "✅ PASS" if resp.status_code == expected_st else f"❌ FAIL({resp.status_code})"
            if resp.status_code == expected_st:
                sec_passed += 1
            print(f"   {result} {name}")
        except Exception as e:
            print(f"   ❌ ERROR {name}: {e}")

    print(f"   安全测试结果: {sec_passed}/{len(sec_cases)} 通过")
    print()

    # 场景3: 查询历史测试汇总（从 test_summary 表）
    cursor.execute("""
        SELECT run_date, total_cases, passed_cases, failed_cases, pass_rate, avg_response_time_ms
        FROM test_summary
        ORDER BY run_date DESC
        LIMIT 10
    """)
    summaries = cursor.fetchall()

    print("   📊 历史测试汇总:")
    print(f"   {'日期':<12} | {'总数':>4} | {'通过':>4} | {'失败':>4} | {'通过率':>6} | {'平均耗时':>8}")
    print("   " + "-" * 50)
    for row in summaries:
        date, total, passed, failed, rate, avg = row
        print(f"   {date:<12} | {total:>4} | {passed:>4} | {failed:>4} | {rate:>6} | {avg:>7.0f}ms")
    print()

    return p0_passed, sec_passed


# ============================================================
# Part 7: 数据库高级操作 —— UPDATE / DELETE / 子查询
# ============================================================

def advanced_db_operations(conn):
    """演示 UPDATE / DELETE / 子查询等数据库操作在测试中的应用"""
    cursor = conn.cursor()

    print("=" * 70)
    print("⚙️ Part 7: 数据库高级操作 —— UPDATE/DELETE/子查询")
    print("=" * 70)

    # ---- UPDATE: 批量更新用例优先级 ----
    print("\n   操作1: UPDATE —— 将所有Boundary模块用例优先级从P2升为P1")
    cursor.execute("""
        UPDATE test_cases
        SET priority = 'P1'
        WHERE module = 'Boundary'
    """)
    conn.commit()
    updated = cursor.rowcount
    print(f"   ✅ 更新了 {updated} 条记录")

    # 验证更新结果
    cursor.execute("""
        SELECT case_name, priority FROM test_cases WHERE module = 'Boundary'
    """)
    for row in cursor.fetchall():
        print(f"   {row[0]}: 优先级={row[1]}")
    print()

    # ---- DELETE: 删除超过7天的测试结果（数据清理）----
    print("   操作2: DELETE —— 模拟清理旧测试结果")
    cursor.execute("""
        SELECT COUNT(*) FROM test_results
    """)
    before_count = cursor.fetchone()[0]
    print(f"   当前结果数: {before_count}")

    # SQLite没有DATE_SUB，用字符串比较（真实MySQL项目用 WHERE executed_at < DATE_SUB(NOW(), INTERVAL 7 DAY))
    cursor.execute("""
        SELECT COUNT(*) FROM test_results
        WHERE executed_at < '2026-01-01'
    """)
    old_count = cursor.fetchone()[0]
    print(f"   超过7天的记录（模拟）: {old_count} 条")
    print("   MySQL写法: WHERE executed_at < DATE_SUB(NOW(), INTERVAL 7 DAY)")
    print()

    # ---- 子查询: 找出响应时间高于平均值的失败用例 ----
    print("   操作3: 子查询 —— 找出响应时间高于平均值的用例")
    cursor.execute("""
        SELECT r.case_name, c.module, r.response_time_ms, r.is_passed
        FROM test_results r
        JOIN test_cases c ON r.case_id = c.id
        WHERE r.response_time_ms > (
            SELECT AVG(response_time_ms) FROM test_results
        )
        ORDER BY r.response_time_ms DESC
    """)
    slow_results = cursor.fetchall()

    avg_time_query = cursor.execute("""
        SELECT AVG(response_time_ms) FROM test_results
    """)
    avg_val = cursor.fetchone()[0]
    print(f"   平均响应时间: {avg_val:.0f}ms")
    print(f"   高于平均的用例: {len(slow_results)} 个")
    for row in slow_results:
        status = "✅" if row[3] else "❌"
        print(f"   {status} {row[0]} ({row[1]}): {row[2]:.0f}ms")
    print()

    # ---- 视图创建（CREATE VIEW，和MySQL一样）----
    print("   操作4: CREATE VIEW —— 创建测试通过率视图")
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS v_module_pass_rate AS
        SELECT
            c.module,
            COUNT(*) as total_cases,
            SUM(r.is_passed) as passed_cases,
            ROUND(SUM(r.is_passed) * 100.0 / COUNT(*), 1) as pass_rate_pct,
            ROUND(AVG(r.response_time_ms), 0) as avg_time_ms
        FROM test_results r
        JOIN test_cases c ON r.case_id = c.id
        GROUP BY c.module
    """)
    conn.commit()
    print("   ✅ 视图 v_module_pass_rate 创建成功")

    # 从视图查询（和查普通表完全一样）
    cursor.execute("SELECT * FROM v_module_pass_rate")
    view_data = cursor.fetchall()
    print(f"   {'模块':<12} | {'总数':>4} | {'通过':>4} | {'通过率':>6} | {'平均耗时':>8}")
    print("   " + "-" * 50)
    for row in view_data:
        print(f"   {row[0]:<12} | {row[1]:>4} | {row[2]:>4} | {row[3]:>5}% | {row[4]:>7}ms")
    print()


# ============================================================
# 主函数：串联所有Part
# ============================================================

def main():
    print("=" * 70)
    print("🚀 Requests + SQLite 联合实战")
    print("   14天接口测试技能 × 18天MySQL数据库技能 = 真实项目核心能力")
    print("=" * 70)
    print()

    # Part 1: 建表
    conn = init_database()

    # Part 2: 插入测试用例
    case_count = insert_test_cases(conn)

    # Part 3: 从DB读取用例 → 执行测试 → 结果存回DB
    stats = execute_test_from_db(conn)

    # Part 4: 从DB查询 → 生成报告
    generate_report_from_db(conn)

    # Part 5: SQLite vs MySQL对比
    show_sqlite_vs_mysql_comparison()

    # Part 6: 数据驱动实战
    data_driven_from_db(conn)

    # Part 7: 高级数据库操作
    advanced_db_operations(conn)

    # 最终汇总
    print("=" * 70)
    print("🎉 Requests + SQLite 联合实战完成！")
    print("=" * 70)
    print()
    print("   📦 产出物:")
    print("   1. 代码文件: requests_db_integration.py")
    print("   2. 数据库文件: test_results.db（SQLite，可用任何DB工具打开）")
    print("   3. 测试报告: test_report_db.md")
    print()
    print("   🔑 今天学到的核心能力:")
    print("   - SQLite建表/插入/查询/更新/删除/子查询/视图 → 和MySQL语法几乎一样")
    print("   - 接口测试结果存数据库 → 真实项目的标准做法")
    print("   - 数据库驱动的测试执行 → 从DB读用例、筛选执行、存回结果")
    print("   - 数据库查询生成报告 → GROUP BY / JOIN / 聚合函数实战")
    print()
    print("   🎯 迁移到MySQL只需3步:")
    print("   1. pip install pymysql")
    print("   2. sqlite3.connect() → pymysql.connect()")
    print("   3. ? → %s 占位符")
    print()

    conn.close()


if __name__ == "__main__":
    main()
