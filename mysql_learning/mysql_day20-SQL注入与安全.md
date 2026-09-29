# 🐬 今日MySQL学习 · Day 20/30

**主题**：SQL注入与安全

---

## 【学习目标】

- 理解 SQL 注入的原理和危害（数据泄露、删库、提权）
- 掌握防范 SQL 注入的核心方法：参数化查询、预编译语句
- 学会站在**测试人员**角度：通过黑盒/白盒手段检测 SQL 注入漏洞

---

## 【核心语法】

### 1. 错误写法：字符串拼接（危险 ❌）

```sql
-- 假设这是应用层拼出来的 SQL
SET @username = 'admin';
SET @password = "' OR '1'='1";

-- 直接拼接 → 灾难！整个 WHERE 永远为真
SELECT * FROM users
WHERE username = @username AND password = @password;
-- 实际执行：WHERE username='admin' AND password='' OR '1'='1'
-- 结果：返回全部用户
```

### 2. 正确写法：预编译参数化（安全 ✅）

```sql
-- PREPARE + EXECUTE USING 是 MySQL 的预编译方案
SET @sql = "SELECT * FROM users WHERE username = ? AND password = ?";
SET @u = 'admin';
SET @p = 'admin123';

PREPARE stmt FROM @sql;
EXECUTE stmt USING @u, @p;
DEALLOCATE PREPARE stmt;
```

### 3. 输入过滤（辅助手段，不可单独依赖）

```sql
-- 对特殊字符进行转义，MySQL 提供 QUOTE()
SELECT QUOTE("' OR '1'='1");
-- 返回: '\' OR \'1\'=\'1'  （单引号被转义）

-- 也可以用 REPLACE 手工清理
SELECT REPLACE("' OR '1'='1", "'", "''");
```

### 4. 最小权限原则（建账号时）

```sql
-- 应用账号只给必要权限，绝不给 DROP/GRANT
CREATE USER 'app_user'@'%' IDENTIFIED BY 'StrongPwd!2026';
GRANT SELECT, INSERT, UPDATE ON shop.* TO 'app_user'@'%';
FLUSH PRIVILEGES;
-- 这样即使被注入，攻击者也只能 SELECT/INSERT/UPDATE，无法 DROP TABLE
```

### 5. INFORMATION_SCHEMA 检测异常（运维/审计用）

```sql
-- 查看是否有可疑的存储过程（攻击者常用来留后门）
SELECT ROUTINE_NAME, ROUTINE_TYPE, CREATED
FROM INFORMATION_SCHEMA.ROUTINES
WHERE ROUTINE_SCHEMA = 'shop'
  AND CREATED > DATE_SUB(NOW(), INTERVAL 7 DAY);

-- 查 mysql.user 中是否有异常账号
SELECT user, host, account_locked
FROM mysql.user
WHERE user NOT IN ('root','mysql.sys','mysql.session','app_user');
```

---

## 【实战示例】

### 示例 1：典型 SQL 注入 payload（测试用，不要在生产用）

```sql
-- ① 永真注入（最常见）
' OR '1'='1
' OR 1=1 -- 
admin' --

-- ② 联合查询注入（查其他表数据）
' UNION SELECT username, password FROM users --

-- ③ 报错注入（利用 extractvalue）
' AND extractvalue(1, concat(0x7e, (SELECT database()), 0x7e))

-- ④ 布尔盲注（页面只有"登录成功/失败"两种状态时用）
' AND (SELECT SUBSTRING(database(),1,1))='s' --

-- ⑤ 时间盲注（连布尔都没有时用）
' OR IF(1=1, SLEEP(5), 0) --
-- 页面响应明显变慢 → 存在注入
```

### 示例 2：用 Python 模拟攻击 & 验证修复（游戏登录接口）

```python
import pymysql

def vulnerable_login(username, password):
    """错误示范：字符串拼接"""
    conn = pymysql.connect(host="127.0.0.1", user="root", password="root", db="game")
    sql = f"SELECT * FROM player WHERE username='{username}' AND password='{password}'"
    cur = conn.cursor()
    cur.execute(sql)
    return cur.fetchone()

def safe_login(username, password):
    """正确示范：参数化查询"""
    conn = pymysql.connect(host="127.0.0.1", user="root", password="root", db="game")
    sql = "SELECT * FROM player WHERE username=%s AND password=%s"
    cur = conn.cursor()
    cur.execute(sql, (username, password))   # 关键：传参数而非拼字符串
    return cur.fetchone()

# ❌ 攻击成功
print(vulnerable_login("admin", "' OR '1'='1"))   # 返回第一行用户

# ✅ 攻击失败
print(safe_login("admin", "' OR '1'='1"))         # 返回 None
```

### 示例 3：测试人员在接口测试中检测 SQL 注入

```python
import requests

# 假设游戏 GM 后台查询玩家信息的接口
url = "http://game-api.local/player/search"

# 构造注入 payload 测试
payloads = [
    "1' OR '1'='1",
    "1' UNION SELECT username, password FROM player--",
    "1' AND SLEEP(3)--",
]

for p in payloads:
    r = requests.get(url, params={"player_id": p})
    # 判断依据：
    #   1) 响应时间 > 3s → 时间盲注
    #   2) 返回数据明显异常（多出字段、暴库信息）→ 联合注入
    #   3) 状态码 500 + 暴露 SQL 错误 → 报错注入
    print(f"payload: {p!r:40s}  status: {r.status_code}  time: {r.elapsed.total_seconds():.2f}s")
    if "SQL" in r.text or "syntax" in r.text.lower():
        print("⚠️ 疑似 SQL 注入漏洞：响应中包含 SQL 错误信息")
```

---

## 【注意事项/易错点】

### 1. 转义不等于防注入

```sql
-- ❌ 错误观念："我加了 addslashes / mysql_real_escape_string 就安全了"
-- 真相：GBK 宽字节注入、整数型无引号、二次注入都能绕过

-- ✅ 正确观念：永远用参数化查询（PREPARE/EXECUTE 或 ORM）
```

### 2. 数字型参数千万别加引号

```python
# ❌ 看似安全但其实没意义
sql = f"SELECT * FROM player WHERE id='{player_id}'"

# ✅ 数字型也用参数化
sql = "SELECT * FROM player WHERE id=%s"
cur.execute(sql, (player_id,))   # 传 int，驱动会自动处理
```

### 3. 错误信息不要直接返回给前端

```sql
-- 应用层关闭详细错误回显，统一返回"系统异常"
-- MySQL 端可以这样配置
SET GLOBAL log_error_verbosity = 1;   -- 减少错误细节
-- 或者在 my.cnf 中
-- [mysqld]
-- log_error_verbosity=1
```

### 4. 性能 / 安全双提醒

- **预编译会被缓存**：同一 SQL 模板第二次执行时，MySQL 不会重新解析，性能反而更好
- **不要用 root 跑应用**：MySQL 的 `root` 拥有 FILE、PROCESS、SHUTDOWN 等危险权限，被注入等于交出整个服务器
- **日志审计开启**：开启 general_log 或 binlog，便于事后追溯异常查询

---

## 【今日练习题】

### 练习 1：亲手体验一次注入（本地测试库）

1. 在你的本地 MySQL 中执行：
   ```sql
   CREATE DATABASE sql_inject_demo;
   USE sql_inject_demo;
   CREATE TABLE users(id INT PRIMARY KEY, username VARCHAR(50), password VARCHAR(50));
   INSERT INTO users VALUES (1,'admin','admin123'),(2,'test','test123');
   ```
2. 用 `mysql` 命令行，分别执行以下两条，对比结果：
   ```sql
   SET @p = "' OR '1'='1";
   SELECT * FROM users WHERE username='admin' AND password=@p;   -- 危险
   PREPARE s FROM 'SELECT * FROM users WHERE username=? AND password=?';
   EXECUTE s USING 'admin', @p;                                    -- 安全
   DEALLOCATE PREPARE s;
   ```

### 练习 2：站在测试视角找漏洞

3. 找一段你之前写过的、用 `f"..."` 拼接 SQL 的代码（Python / Java 都可以），用本节学到的 `'`、`UNION`、`SLEEP` 三个 payload 跑一遍，验证是否真的能被攻击。  
   如果能 → 立刻改成参数化。  
   如果不能 → 写下你做了什么防御措施（参数化 / ORM / 白名单 / 转义？），发到你的"测试笔记"里。

---

## 【一句话总结】

> **SQL 注入的本质是"代码和数据没分开"，唯一可靠的解药是参数化查询（Prepared Statement）；测试人员要养成"看到字符串拼 SQL 就报警"的肌肉记忆。**
