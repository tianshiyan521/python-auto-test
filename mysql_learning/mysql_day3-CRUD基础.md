# 🐬 今日MySQL学习 · Day 3/30

**主题**：增删改查 CRUD 基础

---

## 【学习目标】
- 掌握 INSERT、SELECT、UPDATE、DELETE 四大基本操作
- 理解每个语句的语法结构和参数含义
- 能用 CRUD 模拟游戏/测试中的数据操作场景

---

## 【核心语法】

```sql
-- ========== 准备工作：先建好环境 ==========
USE game_test;

CREATE TABLE IF NOT EXISTS player (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    username    VARCHAR(50) NOT NULL UNIQUE,
    level       INT DEFAULT 1,
    gold        DECIMAL(10,2) DEFAULT 0.00,
    vip         BOOLEAN DEFAULT FALSE,
    created_at  DATETIME DEFAULT NOW()
);

-- ========== INSERT：插入数据 ==========

-- 写法1：指定列名（推荐！即使以后表加列也不会崩）
INSERT INTO player (username, level, gold)
VALUES ('张三', 10, 500.00);

-- 写法2：同时插入多行（效率高，少写多次INSERT）
INSERT INTO player (username, level, gold, vip)
VALUES
    ('李四', 20, 1200.00, TRUE),
    ('王五', 5,  100.00,  FALSE),
    ('赵六', 35, 9999.99, TRUE);

-- ========== SELECT：查询数据 ==========

-- 查全部列
SELECT * FROM player;

-- 查指定列
SELECT username, level, gold FROM player;

-- 给列起别名（AS 可省略）
SELECT username AS 用户名, level AS 等级, gold AS 金币
FROM player;

-- 去重
SELECT DISTINCT vip FROM player;

-- ========== UPDATE：修改数据 ==========

-- 修改单行
UPDATE player SET level = 15 WHERE username = '张三';

-- 修改多个字段
UPDATE player SET level = 25, gold = 2000.00 WHERE username = '李四';

-- 修改多行（满足条件的所有行都改）
UPDATE player SET vip = TRUE WHERE level >= 30;

-- ❌ 危险！没有WHERE会改全表！
-- UPDATE player SET gold = 0;    -- 所有人金币清零！

-- ========== DELETE：删除数据 ==========

-- 删除指定行
DELETE FROM player WHERE username = '赵六';

-- 删除多行（满足条件的全删）
DELETE FROM player WHERE level < 5;

-- 清空全表（保留表结构）
TRUNCATE TABLE player;  -- 比 DELETE 快，但不可回滚！
```

---

## 【实战示例】

### 示例1：模拟玩家注册（INSERT）

接口测试时，你要往数据库插一个测试账号，用完再删：

```sql
-- 插入测试账号
INSERT INTO player (username, level, gold)
VALUES ('test_user_001', 1, 0.00);

-- 验证插入成功
SELECT * FROM player WHERE username = 'test_user_001';

-- 测完删掉，不污染数据库
DELETE FROM player WHERE username = 'test_user_001';
```

### 示例2：模拟充值后验证数据（UPDATE + SELECT）

玩家充值了 100 元，游戏内增加 1000 金币，你要测充值接口：

```sql
-- 充值前查一下当前金币
SELECT gold FROM player WHERE username = '张三';
-- 结果：500.00

-- 模拟充值（或者充值接口执行后你来验证）
UPDATE player SET gold = gold + 1000 WHERE username = '张三';

-- 充值后验证：应该是 1500.00
SELECT gold FROM player WHERE username = '张三';
-- 结果：1500.00  ✅
```

### 示例3：接口测试常用的"查-改-查"验证流程

```sql
-- Step1：记录修改前的值（截图存档）
SELECT id, username, level, gold FROM player WHERE id = 1;

-- Step2：调用你的修改接口（让接口去改数据库）
-- （这步是你手动调接口或跑脚本，不是SQL）

-- Step3：用SQL验证接口改对了没有
SELECT id, username, level, gold FROM player WHERE id = 1;
-- 对比前后差异，就是你的测试断言
```

---

## 【注意事项/易错点】

| 易错点 | 说明 |
|--------|------|
| ❌ UPDATE / DELETE 没加 WHERE | **最危险的操作！** 没有 WHERE 就是改/删全表，测试环境还好，生产环境后果很严重 |
| ❌ INSERT 写法2列数和值数不匹配 | VALUES 里每行的值必须跟列名数量一致，少一个就报错 |
| ❌ 用 `*` 插入所有列 | `INSERT INTO player VALUES (...)` 不写列名，表加字段后就挂了，养成写列名的习惯 |
| ⚠️ TRUNCATE vs DELETE | `TRUNCATE` 更快但无法回滚，也会重置 AUTO_INCREMENT；`DELETE` 可以加 WHERE、可以回滚 |
| ⚠️ UPDATE 用加法而非赋值 | 充值要写 `gold = gold + 1000`，不是 `gold = 1000`（否则所有人金币变成1000！）|

---

## 【今日练习题】

**练习1**：往你的 `player` 表里插入至少4个玩家，然后执行：
```sql
SELECT * FROM player ORDER BY level DESC;
```
验证是否按等级从高到低排列。（ORDER BY 明天详讲，今天先用）

**练习2**：模拟一个测试场景：
- 先 `INSERT` 一个用户名为 `'bug_test'`、等级为1的玩家
- 然后 `UPDATE` 把他的等级改成 999
- 再 `SELECT` 验证改成功了
- 最后 `DELETE` 删掉这个测试数据

全程4条SQL跑完就是一个完整的 **CRUD 测试用例** ✅

---

## 【一句话总结】

> INSERT 存数据、SELECT 查数据、UPDATE 改数据、DELETE 删数据——CRUD 是所有数据库操作的基石，测试人员的日常就是用这四招验数据对不对。
