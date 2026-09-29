# 🐬 今日MySQL学习 · Day 14/30

**主题**：事务与锁

---

## 【学习目标】

- 理解事务 ACID 四大特性及其含义
- 掌握 BEGIN/COMMIT/ROLLBACK 和 SAVEPOINT 的用法
- 搞懂四种隔离级别 + 脏读/不可重复读/幻读这三个并发问题
- 了解基本锁机制（行锁、表锁、共享锁、排他锁）

---

## 【核心语法】

```sql
-- ==================== 事务控制 ====================

-- 方式一：显式开启事务
START TRANSACTION;
    UPDATE accounts SET balance = balance - 100 WHERE id = 1;
    UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;   -- 提交，数据永久写入
-- 或 ROLLBACK;  -- 回滚，撤销所有修改

-- 方式二：BEGIN 简写（效果相同）
BEGIN;
    INSERT INTO orders (user_id, amount) VALUES (1, 99.99);
    UPDATE inventory SET stock = stock - 1 WHERE product_id = 10;
COMMIT;

-- ==================== 保存点（部分回滚） ====================
BEGIN;
    INSERT INTO logs (msg) VALUES ('步骤1完成');
    SAVEPOINT sp1;                           -- 设置保存点
    INSERT INTO logs (msg) VALUES ('步骤2完成');
    SAVEPOINT sp2;
    INSERT INTO logs (msg) VALUES ('步骤3完成');
    -- 只想撤销步骤3，保留步骤1、2
    ROLLBACK TO SAVEPOINT sp2;               -- 回滚到sp2，步骤3被撤销
    RELEASE SAVEPOINT sp1;                   -- 释放保存点
COMMIT;

-- ==================== 查看/设置隔离级别 ====================
-- 查看当前隔离级别
SELECT @@transaction_isolation;              -- MySQL 8.0+
-- SELECT @@tx_isolation;                    -- MySQL 5.7

-- 查看全局隔离级别
SELECT @@global.transaction_isolation;

-- 设置当前会话隔离级别
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;

-- 设置全局隔离级别
SET GLOBAL TRANSACTION ISOLATION LEVEL REPEATABLE READ;

-- ==================== 查看自动提交状态 ====================
SELECT @@autocommit;                         -- 1=自动提交, 0=手动提交
SET autocommit = 0;                          -- 关闭自动提交（会话级）

-- ==================== 锁相关 ====================
-- 排他锁（写锁）：锁定行，其他事务不能读/写
SELECT * FROM accounts WHERE id = 1 FOR UPDATE;

-- 共享锁（读锁）：锁定行，其他事务可读但不能写
SELECT * FROM accounts WHERE id = 1 LOCK IN SHARE MODE;

-- 查看当前锁等待
SHOW ENGINE INNODB STATUS\G                  -- 查看InnoDB详细状态（含锁信息）
```

---

## 【ACID 四大特性】

| 特性 | 含义 | 类比 |
|------|------|------|
| **A** tomicity 原子性 | 要么全做，要么全不做 | 银行转账：扣A钱和加B钱必须同时成功 |
| **C** onsistency 一致性 | 事务前后数据符合所有约束规则 | 转账后总金额不变，不能凭空多出钱 |
| **I** solation 隔离性 | 并发事务之间互不干扰 | 两个人同时买最后一件商品，不能都买成功 |
| **D** urability 持久性 | 提交后数据永久保存，断电不丢失 | 提交后即便数据库崩溃，重启后数据还在 |

> **记忆口诀**：**A** 全有或全无 → **C** 数据不错乱 → **I** 互不干扰 → **D** 提交就永存

---

## 【四种隔离级别与并发问题对照表】

```
隔离级别       │ 脏读 │ 不可重复读 │ 幻读 │ 性能
──────────────┼──────┼────────────┼──────┼──────
READ UNCOMMITTED│  ✗   │    ✗       │  ✗   │ 最高（几乎不用）
READ COMMITTED │  ✓   │    ✗       │  ✗   │ 较高（Oracle默认）
REPEATABLE READ│  ✓   │    ✓       │  ✗*  │ 中等（MySQL默认）
SERIALIZABLE   │  ✓   │    ✓       │  ✓   │ 最低（串行执行）
──────────────┼──────┼────────────┼──────┼──────
✗ = 有问题  ✓ = 已解决
* MySQL的REPEATABLE READ通过Next-Key Lock部分解决了幻读
```

### 三个并发问题图解

```
【脏读 Dirty Read】
事务A修改数据但未提交 → 事务B读到了这个未提交的数据 → 事务A回滚了
结果：事务B读到了一个"不存在"的值

时间线：
  A: UPDATE balance=500 WHERE id=1  (原值1000)
  B: SELECT balance FROM ...        → 读到500 ← 这就是脏读！
  A: ROLLBACK                       → 滚回1000
  B已经基于500做了后续操作 → 逻辑错误!

────────────────────────────────────────

【不可重复读 Non-Repeatable Read】
事务B两次读取同一行数据 → 中间事务A修改了这行并提交
结果：两次读到不同值

时间线：
  B: SELECT balance → 1000
  A: UPDATE balance=2000 WHERE id=1 → COMMIT
  B: SELECT balance → 2000  ← 两次读到不同值！不可重复读！

────────────────────────────────────────

【幻读 Phantom Read】
事务B两次查询满足条件的数据 → 中间事务A插入了新行并提交
结果：第二次查询比第一次"多出几行"

时间线：
  B: SELECT * FROM orders WHERE amount>100 → 3行
  A: INSERT INTO orders VALUES (4, 200) → COMMIT
  B: SELECT * FROM orders WHERE amount>100 → 4行 ← 多了"幻影行"！
```

---

## 【实战示例】

### 示例1：银行转账（事务原子性演示）

```sql
-- 准备工作：创建账户表
CREATE TABLE accounts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(20),
    balance DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    CHECK (balance >= 0)
);

INSERT INTO accounts VALUES (1, '阿克', 1000.00), (2, '小明', 500.00);

-- 转账操作（阿克转200给小明）
BEGIN;
    -- 扣阿克的钱
    UPDATE accounts SET balance = balance - 200 WHERE id = 1;
    -- 加小明的钱
    UPDATE accounts SET balance = balance + 200 WHERE id = 2;
COMMIT;

-- 验证：总余额不变
SELECT SUM(balance) AS total_balance FROM accounts;
-- 应该还是 1500.00：原子性保证！

-- 模拟转账失败场景：余额不足
BEGIN;
    UPDATE accounts SET balance = balance - 2000 WHERE id = 1;  -- 阿克只有1000
    -- CHECK约束会报错：Check constraint is violated
    UPDATE accounts SET balance = balance + 2000 WHERE id = 2;
ROLLBACK;  -- 回滚，任何一方都没变

-- 验证数据完整性
SELECT * FROM accounts;  -- 阿克仍是800，小明仍是700
```

### 示例2：四种隔离级别行为对比

> **演示需要两个MySQL会话窗口同时操作**，这里用注释标注两个会话的时间线。

```sql
-- 准备数据
CREATE TABLE demo (
    id INT PRIMARY KEY,
    value INT
);
INSERT INTO demo VALUES (1, 100);

-- ========== 场景A：脏读（READ UNCOMMITTED下可见） ==========
-- 【会话1】  【会话2】
SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
BEGIN;
BEGIN;
--            UPDATE demo SET value=999 WHERE id=1;
--            （未提交！）
SELECT value FROM demo WHERE id=1;   -- 读出 999 ← 脏读！
--            ROLLBACK;
SELECT value FROM demo WHERE id=1;   -- 又变回 100 ← 数据"凭空消失"

-- ========== 场景B：不可重复读（READ COMMITTED下可见） ==========
-- 【会话1】  【会话2】
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
BEGIN;
BEGIN;
SELECT value FROM demo WHERE id=1;   -- 100
--            UPDATE demo SET value=200 WHERE id=1;
--            COMMIT;  ← 提交了！
SELECT value FROM demo WHERE id=1;   -- 200 ← 同一事务两次读到不同值！

-- ========== 场景C：REPEATABLE READ（MySQL默认） ==========
-- 【会话1】  【会话2】
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;
BEGIN;
BEGIN;
SELECT value FROM demo WHERE id=1;   -- 200（当前值）
--            UPDATE demo SET value=300 WHERE id=1;
--            COMMIT;
SELECT value FROM demo WHERE id=1;   -- 仍然200！← 快照读，可重复

-- ========== 场景D：幻读（REPEATABLE READ + INSERT） ==========
-- 【会话1】  【会话2】
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;
BEGIN;
BEGIN;
SELECT COUNT(*) FROM demo;           -- 1行
--            INSERT INTO demo VALUES (2, 50);
--            COMMIT;
SELECT COUNT(*) FROM demo;           -- 还是1行（快照读防幻读！）
-- 但如果执行 UPDATE demo SET value=value WHERE id=2;
-- MySQL的Next-Key Lock会在某些情况下阻止幻读
```

### 示例3：游戏测试场景 — 装备购买事务

> 结合《恐龙岛》项目：玩家购买装备，涉及扣金币 + 扣库存 + 加背包

```sql
-- 建表：模拟游戏数据库
CREATE TABLE players (
    player_id INT PRIMARY KEY,
    name VARCHAR(20),
    gold INT NOT NULL CHECK (gold >= 0)
);

CREATE TABLE equipment (
    equip_id INT PRIMARY KEY,
    name VARCHAR(30),
    price INT NOT NULL,
    stock INT NOT NULL CHECK (stock >= 0)
);

CREATE TABLE backpack (
    id INT AUTO_INCREMENT PRIMARY KEY,
    player_id INT,
    equip_id INT,
    quantity INT DEFAULT 1,
    acquired_time DATETIME DEFAULT NOW(),
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    FOREIGN KEY (equip_id) REFERENCES equipment(equip_id)
);

-- 初始数据
INSERT INTO players VALUES (1, '阿克', 5000), (2, '小白', 3000);
INSERT INTO equipment VALUES
    (101, '屠龙刀', 2000, 5),
    (102, '玄铁甲', 1500, 3);

-- 购买装备：阿克买一把屠龙刀
BEGIN;
    -- 1. 扣金币
    UPDATE players SET gold = gold - 2000 WHERE player_id = 1;
    -- 2. 扣库存
    UPDATE equipment SET stock = stock - 1 WHERE equip_id = 101 AND stock > 0;
    -- 3. 加背包（用 SELECT 测库存是否扣成功）
    INSERT INTO backpack (player_id, equip_id)
    SELECT 1, 101
    FROM equipment
    WHERE equip_id = 101 AND stock >= 0;  -- 库存扣了1，变成了4，≥0 OK

    -- 4. 验证：金币不能为负数
    -- 如果检查失败，回滚
    SELECT
        CASE WHEN (SELECT gold FROM players WHERE player_id = 1) < 0
             THEN 'INSUFFICIENT_GOLD'
             ELSE 'OK'
        END AS status;
    -- 实际项目用代码判断，这里演示思路
COMMIT;

-- 验证结果
SELECT * FROM players;      -- 阿克金币: 3000
SELECT * FROM equipment;    -- 屠龙刀库存: 4
SELECT * FROM backpack;     -- 多了一条记录

-- 测试并发场景：最后一件商品两人同时买
-- 假设屠龙刀只剩1件
UPDATE equipment SET stock = 1 WHERE equip_id = 101;

-- 【会话1】               【会话2】
BEGIN;                      BEGIN;
SELECT stock FROM equipment
WHERE equip_id = 101        SELECT stock FROM equipment
  FOR UPDATE;  ← 排他锁     WHERE equip_id = 101
                              FOR UPDATE;  ← 等待会话1释放锁！
UPDATE equipment SET stock = stock - 1
WHERE equip_id = 101;
INSERT INTO backpack ...;
COMMIT;  ← 释放锁
                            -- 此时读到 stock=0，业务判断不执行购买
                            ROLLBACK;
```

---

## 【注意事项/易错点】

| # | 易错点 | 说明 |
|---|--------|------|
| 1 | **忘记COMMIT导致锁不释放** | 长时间未提交的事务会占用锁资源，阻塞其他操作。生产环境大忌！ |
| 2 | **MySQL默认自动提交** | 单条UPDATE没有BEGIN也会自动提交，想回滚必须手动开启事务。`SELECT @@autocommit;` 确认状态 |
| 3 | **DDL语句隐式提交** | CREATE TABLE、ALTER TABLE、DROP TABLE、TRUNCATE 等在执行前会隐式提交当前事务，无法回滚！ |
| 4 | **死锁不自动解决** | 事务A等B释放锁，B等A释放锁 → 死锁。InnoDB会自动检测并回滚其中一个事务，但代码应该处理重试逻辑 |
| 5 | **REPEATABLE READ 不是万能的** | 它通过MVCC快照读解决不可重复读，但当前读（SELECT ... FOR UPDATE）仍能看到最新已提交数据 |

### 死锁示例

```sql
-- 死锁典型场景（两个会话交叉锁定资源）
-- 【会话1】            【会话2】
BEGIN;                  BEGIN;
UPDATE t SET v=1        UPDATE t SET v=2
WHERE id=1;  -- 锁住id=1   WHERE id=2;  -- 锁住id=2
UPDATE t SET v=1        UPDATE t SET v=2
WHERE id=2;  -- 等会话2释放   WHERE id=1;  -- 等会话1释放
-- 💥 死锁！InnoDB自动检测，回滚代价小的事务

-- 避免死锁的方法：总是按相同顺序访问资源！
-- 好的写法：两个事务都先锁id=1再锁id=2
```

---

## 【今日练习题】

### 练习题1：转账事务 + 日志记录

写一段完整的事务SQL：
1. 从 accounts 表完成一次转账（自己建表插入数据）
2. 同时向 transfer_logs 表插入一条转账日志
3. 要求：如果余额不足，整个事务回滚，日志也不插入

> 提示：用 `BEGIN ... IF判断 ... COMMIT/ROLLBACK` 结构

### 练习题2：测试场景 — 并发扣库存验证

假设 equipment 表中某件装备只剩1件库存。设计一个测试验证方案：
1. 两个"玩家"会话同时执行购买操作
2. 预期结果：只有一个购买成功，库存不会变成负数
3. 写出你的 SQL 测试步骤和预期断言

---

## 【一句话总结】

> **事务就是"一组操作要么全成功要么全撤销"的原子单元，隔离级别决定了并发事务之间能看到对方多少数据变更——隔离越高数据越安全但性能越差，MySQL默认的REPEATABLE READ是大多数场景的最佳平衡点。**

---

*下期预告：Day 15 — 存储过程（CREATE PROCEDURE、IN/OUT/INOUT参数、流程控制）*
