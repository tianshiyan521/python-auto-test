# 🐬 MySQL Day 8 · UNION与集合操作

> 学会用 UNION/UNION ALL 合并结果集，掌握集合运算思维

---

## 📌 学习目标

1. 理解 UNION 和 UNION ALL 的区别（去重 vs 不去重）
2. 会用 UNION 合并多个 SELECT 结果集
3. 了解 MySQL 中 INTERSECT（交集）和 MINUS（差集）的替代写法

---

## 🔑 核心语法

### 1. UNION / UNION ALL — 合并结果集

```sql
-- UNION：合并并去重（自动 DISTINCT）
SELECT 列1, 列2 FROM 表1
UNION
SELECT 列1, 列2 FROM 表2;

-- UNION ALL：合并不去重，性能更好
SELECT 列1, 列2 FROM 表1
UNION ALL
SELECT 列1, 列2 FROM 表2;

-- 可以对合并后的结果排序（ORDER BY 只能放最后）
(SELECT 列1, 列2 FROM 表1)
UNION ALL
(SELECT 列1, 列2 FROM 表2)
ORDER BY 列1 DESC;
```

### 2. INTERSECT — 求交集（MySQL 8.0 不支持，用替代方案）

```sql
-- 方式一：INNER JOIN（最推荐）
SELECT DISTINCT a.列1, a.列2
FROM 表1 a
INNER JOIN 表2 b ON a.列1 = b.列1 AND a.列2 = b.列2;

-- 方式二：IN + 子查询
SELECT DISTINCT 列1, 列2 FROM 表1
WHERE (列1, 列2) IN (SELECT 列1, 列2 FROM 表2);

-- 方式三：EXISTS
SELECT DISTINCT 列1, 列2 FROM 表1 a
WHERE EXISTS (SELECT 1 FROM 表2 b WHERE a.列1 = b.列1 AND a.列2 = b.列2);
```

### 3. MINUS / EXCEPT — 求差集（MySQL 8.0 不支持，用替代方案）

```sql
-- 表1有但表2没有的数据
-- 方式一：LEFT JOIN + IS NULL
SELECT DISTINCT a.列1, a.列2
FROM 表1 a
LEFT JOIN 表2 b ON a.列1 = b.列1 AND a.列2 = b.列2
WHERE b.列1 IS NULL;

-- 方式二：NOT EXISTS（语义最清晰）
SELECT 列1, 列2 FROM 表1 a
WHERE NOT EXISTS (SELECT 1 FROM 表2 b WHERE a.列1 = b.列1 AND a.列2 = b.列2);

-- 方式三：NOT IN（注意 NULL 陷阱！）
SELECT DISTINCT 列1, 列2 FROM 表1
WHERE (列1, 列2) NOT IN (SELECT 列1, 列2 FROM 表2 WHERE 列1 IS NOT NULL);
```

---

## 💻 实战示例

> 以下示例基于游戏项目玩家数据库，假设有两张表记录不同来源的玩家：
> - `players_qq`：QQ渠道注册的玩家
> - `players_wechat`：微信渠道注册的玩家

先建测试表：

```sql
CREATE TABLE players_qq (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nickname VARCHAR(50) NOT NULL,
    level INT DEFAULT 1
);

CREATE TABLE players_wechat (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nickname VARCHAR(50) NOT NULL,
    level INT DEFAULT 1
);

-- QQ渠道玩家数据
INSERT INTO players_qq VALUES (1, '青龙', 45), (2, '白虎', 38), (3, '朱雀', 52), (4, '玄武', 41);

-- 微信渠道玩家数据（注意"朱雀"和"白虎"两个渠道都有）
INSERT INTO players_wechat VALUES (1, '朱雀', 50), (2, '麒麟', 55), (3, '白虎', 40), (4, '饕餮', 60);
```

### 示例1：UNION — 合并所有玩家（去重）

```sql
-- 查所有渠道玩家，按昵称去重
SELECT nickname, level FROM players_qq
UNION
SELECT nickname, level FROM players_wechat;
```

| nickname | level |
|----------|-------|
| 青龙 | 45 |
| 白虎 | 38 |
| 朱雀 | 52 |
| 玄武 | 41 |
| 麒麟 | 55 |
| 饕餮 | 60 |

> 注意：白虎和朱雀各只出现一次（38和52来自qq，微信的40和50被去重掉了）

### 示例2：UNION ALL — 合并不去重 + 渠道标记

```sql
-- 保留所有数据，加一列标记来源
SELECT nickname, level, 'QQ' AS source FROM players_qq
UNION ALL
SELECT nickname, level, '微信' AS source FROM players_wechat
ORDER BY nickname;
```

| nickname | level | source |
|----------|-------|--------|
| 白虎 | 38 | QQ |
| 白虎 | 40 | 微信 |
| 麒麟 | 55 | 微信 |
| 青龙 | 45 | QQ |
| 朱雀 | 52 | QQ |
| 朱雀 | 50 | 微信 |
| 玄武 | 41 | QQ |
| 饕餮 | 60 | 微信 |

> 可以看到白虎和朱雀各有两条记录，来自不同渠道。`source` 列用常量标记来源，是 UNION ALL 的经典用法。

### 示例3：求交集 — 两边都有的玩家

```sql
-- 哪些玩家在QQ和微信都注册了？
SELECT DISTINCT a.nickname
FROM players_qq a
INNER JOIN players_wechat b ON a.nickname = b.nickname;
```

| nickname |
|----------|
| 白虎 |
| 朱雀 |

> 测试场景：可以用来验证"跨平台互通"是否正确，预期哪些玩家应该在两个平台都存在。

### 示例4：求差集 — 只在QQ不在微信的玩家

```sql
-- 只看 QQ 渠道独有、微信没有的玩家
SELECT nickname, level FROM players_qq a
WHERE NOT EXISTS (
    SELECT 1 FROM players_wechat b WHERE a.nickname = b.nickname
);
```

| nickname | level |
|----------|-------|
| 青龙 | 45 |
| 玄武 | 41 |

> 测试场景：可以用来做渠道独占玩家分析，比如"只玩QQ不玩微信端的玩家有哪些"。

### 示例5（综合）：完整集合运算对比

```sql
-- 1️⃣ 并集（所有玩家）
SELECT nickname FROM players_qq UNION SELECT nickname FROM players_wechat;
-- 结果：青龙 白虎 朱雀 玄武 麒麟 饕餮（6条，去重）

-- 2️⃣ 并集（不去重）
SELECT nickname FROM players_qq UNION ALL SELECT nickname FROM players_wechat;
-- 结果：8条（白虎和朱雀各2条）

-- 3️⃣ 交集（两个渠道都有的）
SELECT nickname FROM players_qq WHERE nickname IN (SELECT nickname FROM players_wechat);
-- 结果：白虎 朱雀

-- 4️⃣ 差集（QQ有微信没有的）
SELECT nickname FROM players_qq WHERE nickname NOT IN (SELECT nickname FROM players_wechat);
-- 结果：青龙 玄武
```

---

## ⚠️ 注意事项 / 易错点

### 1. UNION 要求列数和类型一致

```sql
-- ❌ 错误：列数不一致
SELECT id, nickname FROM t1
UNION
SELECT id FROM t2;  -- 报错！列数必须相同

-- ✅ 正确：补 NULL 占位
SELECT id, nickname FROM t1
UNION
SELECT id, NULL FROM t2;
```

### 2. UNION 自动去重，UNION ALL 不去重

```sql
-- 这两个结果不一样！
SELECT 1 UNION SELECT 1 UNION SELECT 2;      -- 结果：1, 2（去重了）
SELECT 1 UNION ALL SELECT 1 UNION ALL SELECT 2;  -- 结果：1, 1, 2（保留所有）
```

**性能提示**：如果确定数据不会重复（或者不需要去重），优先用 UNION ALL，因为 UNION 会额外做一次排序去重，性能差不少。

### 3. NOT IN 子查询的 NULL 陷阱

```sql
-- ⚠️ 如果子查询结果中有 NULL，NOT IN 会返回空！
SELECT 1 WHERE 1 NOT IN (2, 3, NULL);  -- 结果为空！
-- 原因：1 != NULL 的结果是 NULL（不是 TRUE），所以整条不匹配

-- ✅ 安全写法：用 NOT EXISTS 或过滤掉 NULL
SELECT 1 WHERE 1 NOT IN (2, 3);                    -- 结果：1
SELECT 1 a WHERE NOT EXISTS (SELECT 1 WHERE 1 IN (2, 3, NULL)); -- 结果：1
```

### 4. ORDER BY 只能放在最后一个 SELECT 后面

```sql
-- ❌ 错误：ORDER BY 只能放最后
(SELECT nickname FROM players_qq ORDER BY nickname)
UNION
(SELECT nickname FROM players_wechat);

-- ✅ 正确：ORDER BY 放到整个 UNION 后面
(SELECT nickname FROM players_qq)
UNION
(SELECT nickname FROM players_wechat)
ORDER BY nickname;
```

---

## 📝 今日练习题

### 练习题1：渠道玩家统计（必做）

建两张表你自己动手：
```sql
CREATE TABLE channel_a (name VARCHAR(20));
CREATE TABLE channel_b (name VARCHAR(20));
INSERT INTO channel_a VALUES ('小明'), ('小红'), ('小刚'), ('小红');
INSERT INTO channel_b VALUES ('小红'), ('小刚'), ('小美'), ('小美');
```

请写出以下查询：
1. 两个渠道的全部玩家（去重）
2. 两个渠道的全部玩家（不去重）
3. 两个渠道都有的玩家（交集）
4. 只在A渠道不在B渠道的玩家（差集）

### 练习题2：测试数据对比（进阶）

假设你有两张测试环境配置表 `config_v1` 和 `config_v2`（表结构相同：item_id INT, item_name VARCHAR(50)），现在版本升级后需要对比：
1. v2 比 v1 多了哪些配置项？
2. v1 中有但 v2 中被删掉的配置项有哪些？

用集合运算写出 SQL，并思考什么样的测试场景会用到这些查询。

---

## 🎯 一句话总结

> UNION 合并结果集，UNION ALL 不杀重更快；MySQL 不支持 INTERSECT/MINUS，用 JOIN 或子查询来替代，差集用 NOT EXISTS 最安全。

---

*Day 8/30 · UNION与集合操作 · 进阶篇开始，集合思维让 SQL 更灵活！*
