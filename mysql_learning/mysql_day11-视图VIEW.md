🐬 今日MySQL学习 · Day 11/30
**主题**：视图 VIEW

---

**【学习目标】**
- 理解视图的本质：虚拟表还是物理表？存储的是什么？
- 掌握视图的创建、修改、删除语法
- 了解视图的3大核心用途：简化查询、数据安全、逻辑抽象
- 知道可更新视图的限制条件

---

**【核心语法】**

```sql
-- 1. 创建视图
CREATE VIEW 视图名 AS
SELECT 列1, 列2, ...
FROM 表名
WHERE 条件;

-- 2. 创建或替换视图（推荐用这个，避免先删再建）
CREATE OR REPLACE VIEW 视图名 AS
SELECT 列1, 列2, ...
FROM 表名
WHERE 条件;

-- 3. 带检查选项的视图（INSERT/UPDATE时必须满足视图WHERE条件）
CREATE OR REPLACE VIEW 视图名 AS
SELECT ...
FROM 表名
WHERE 条件
WITH CHECK OPTION;        -- 只检查当前视图
-- WITH CASCADED CHECK OPTION;  -- 级联检查所有底层视图（默认）
-- WITH LOCAL CHECK OPTION;     -- 只检查当前视图，不级联

-- 4. 查看视图定义
SHOW CREATE VIEW 视图名;

-- 5. 查看所有视图
SELECT TABLE_NAME, TABLE_TYPE
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = '你的数据库名'
  AND TABLE_TYPE = 'VIEW';

-- 6. 修改视图（和 CREATE OR REPLACE 一样）
ALTER VIEW 视图名 AS
SELECT 列1, 列2, ...
FROM 表名
WHERE 条件;

-- 7. 删除视图
DROP VIEW IF EXISTS 视图名;
DROP VIEW IF EXISTS 视图1, 视图2;  -- 批量删除

-- 8. 视图嵌套（视图基于视图创建）
CREATE VIEW 视图B AS
SELECT ... FROM 视图A WHERE ...;
```

---

**【实战示例】**

### 示例1：基础 — 创建玩家摘要视图简化日常查询

```sql
-- 假设玩家表字段很多，日常只需要这几个
CREATE TABLE players (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,
    level INT DEFAULT 1,
    vip_level INT DEFAULT 0,
    gold DECIMAL(15,2) DEFAULT 0,
    diamond INT DEFAULT 0,
    server_id INT,
    guild_id INT,
    last_login DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TINYINT DEFAULT 1  -- 1正常 2封禁
);

-- 创建视图：只暴露常用字段，过滤掉封禁玩家
CREATE OR REPLACE VIEW v_player_summary AS
SELECT id, name, level, vip_level, gold, diamond, server_id, last_login
FROM players
WHERE status = 1;

-- 使用视图查询（像普通表一样用）
SELECT * FROM v_player_summary WHERE level >= 50;

-- 优点：不用每次都写 WHERE status = 1，视图帮你过滤了
```

### 示例2：进阶 — 多表关联视图 + 数据安全隔离

```sql
-- 订单表
CREATE TABLE orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    player_id INT NOT NULL,
    product_name VARCHAR(100),
    amount DECIMAL(10,2),
    pay_time DATETIME,
    pay_channel VARCHAR(20),  -- 微信/支付宝/苹果
    refund_status TINYINT DEFAULT 0  -- 0未退款 1已退款
);

-- 充值记录表
CREATE TABLE recharge_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    player_id INT NOT NULL,
    recharge_amount DECIMAL(10,2),
    diamond_added INT,
    recharge_time DATETIME
);

-- 视图1：运营人员视图 — 只看订单汇总，隐藏退款内部字段
CREATE OR REPLACE VIEW v_order_overview AS
SELECT
    o.id AS order_id,
    p.name AS player_name,
    o.product_name,
    o.amount,
    o.pay_time,
    o.pay_channel
FROM orders o
JOIN players p ON o.player_id = p.id
WHERE o.refund_status = 0;  -- 只显示未退款的

-- 视图2：财务视图 — 看完整信息包括退款
CREATE OR REPLACE VIEW v_order_finance AS
SELECT
    o.id AS order_id,
    p.name AS player_name,
    o.product_name,
    o.amount,
    o.pay_channel,
    o.refund_status,
    o.pay_time
FROM orders o
JOIN players p ON o.player_id = p.id;

-- 视图3：玩家充值汇总 — 把多表关联封装起来
CREATE OR REPLACE VIEW v_player_recharge_summary AS
SELECT
    p.id AS player_id,
    p.name,
    p.level,
    COUNT(r.id) AS recharge_count,
    IFNULL(SUM(r.recharge_amount), 0) AS total_recharge,
    IFNULL(SUM(r.diamond_added), 0) AS total_diamond
FROM players p
LEFT JOIN recharge_log r ON p.id = r.player_id
GROUP BY p.id, p.name, p.level;

-- 使用：查大R玩家
SELECT * FROM v_player_recharge_summary
WHERE total_recharge >= 1000
ORDER BY total_recharge DESC;

-- 数据安全：给运营只授权访问视图，不给原表权限
-- GRANT SELECT ON game_db.v_order_overview TO 'operator'@'%';
-- 运营看不到 refund_status 字段，看不到退款数据
```

### 示例3：工作/测试场景 — 用视图封装数据校验查询

```sql
-- 场景：测试人员每天要校验数据一致性
-- 比如检查订单金额和充值金额是否匹配

-- 视图：订单-充值一致性检查
CREATE OR REPLACE VIEW v_order_recharge_check AS
SELECT
    o.id AS order_id,
    o.player_id,
    p.name AS player_name,
    o.amount AS order_amount,
    IFNULL(SUM(r.recharge_amount), 0) AS recharge_total,
    o.amount - IFNULL(SUM(r.recharge_amount), 0) AS diff,
    CASE
        WHEN o.amount = IFNULL(SUM(r.recharge_amount), 0) THEN '一致'
        WHEN o.amount > IFNULL(SUM(r.recharge_amount), 0) THEN '充值不足'
        ELSE '充值超额'
    END AS check_result
FROM orders o
LEFT JOIN recharge_log r ON o.player_id = r.player_id
    AND r.recharge_time BETWEEN o.pay_time AND DATE_ADD(o.pay_time, INTERVAL 5 MINUTE)
JOIN players p ON o.player_id = p.id
WHERE o.refund_status = 0
GROUP BY o.id, o.player_id, p.name, o.amount, o.pay_time;

-- 每天跑一句就能发现不一致的数据
SELECT * FROM v_order_recharge_check
WHERE check_result != '一致';

-- 视图：每日数据概览（给测试日报用）
CREATE OR REPLACE VIEW v_daily_overview AS
SELECT
    CURDATE() AS report_date,
    COUNT(DISTINCT CASE WHEN DATE(last_login) = CURDATE() THEN id END) AS dau,
    COUNT(DISTINCT CASE WHEN DATE(created_at) = CURDATE() THEN id END) AS new_players,
    IFNULL(SUM(CASE WHEN DATE(pay_time) = CURDATE() THEN amount ELSE 0 END), 0) AS today_revenue,
    COUNT(DISTINCT CASE WHEN DATE(pay_time) = CURDATE() THEN player_id END) AS pay_users
FROM players p
LEFT JOIN orders o ON p.id = o.player_id;

-- 每天查一句就出日报数据
SELECT * FROM v_daily_overview;
```

---

**【注意事项/易错点】**

1. **视图不存储数据，只存储定义**
   - 视图是一个"保存的SELECT语句"，每次查询视图时都会执行底层SQL
   - 如果底层表有1000万行，`SELECT * FROM 视图` 也会扫描1000万行
   - 视图本身不能建索引（MySQL 8.0之前），性能依赖底层表的索引

2. **可更新视图的限制**
   - 只有"简单视图"才能 INSERT/UPDATE/DELETE（单表、无聚合、无DISTINCT、无GROUP BY）
   - 包含 JOIN、聚合函数、DISTINCT、GROUP BY、HAVING、UNION 的视图不可更新
   - 如果业务需要修改数据，直接操作原表，别通过视图

3. **WITH CHECK OPTION 陷阱**
   ```sql
   CREATE VIEW v_high_level AS
   SELECT id, name, level FROM players WHERE level >= 50
   WITH CHECK OPTION;

   -- 这条会报错！因为插入的 level=30 不满足视图的 WHERE 条件
   INSERT INTO v_high_level (id, name, level) VALUES (1, 'test', 30);

   -- 这条OK
   INSERT INTO v_high_level (id, name, level) VALUES (1, 'test', 60);
   ```

4. **视图嵌套层数不要太深**
   - 视图A → 视图B → 视图C，嵌套3层以上维护成本极高
   - 改底层表结构时，所有依赖的视图都可能出错
   - 建议：视图最多嵌套1层，保持扁平

5. **删除表后视图还在但会报错**
   - `DROP TABLE players` 后，`SELECT * FROM v_player_summary` 会报错
   - 视图不会随表自动删除，需要手动清理失效视图

6. **ALGORITHM 选择**
   - `MERGE`（默认）：将视图SQL和查询SQL合并优化，性能最好
   - `TEMPTABLE`：先执行视图SQL生成临时表，再查询临时表，性能差但支持某些聚合场景
   - `UNDEFINED`：MySQL自己选
   ```sql
   CREATE ALGORITHM=TEMPTABLE VIEW v_complex_stats AS ...
   -- 只有在MERGE无法处理时才用TEMPTABLE
   ```

---

**【今日练习题】**

### 练习1（必做）：创建视图并操作
```sql
-- 1. 创建一个商品表
CREATE TABLE products (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100),
    category VARCHAR(50),
    price DECIMAL(10,2),
    stock INT DEFAULT 0,
    is_on_sale TINYINT DEFAULT 1  -- 1在售 0下架
);

-- 2. 插入几条测试数据
INSERT INTO products (name, category, price, stock, is_on_sale) VALUES
('铁剑', '武器', 100.00, 50, 1),
('皮甲', '防具', 200.00, 30, 1),
('魔法书', '道具', 500.00, 10, 1),
('破烂盾牌', '防具', 50.00, 0, 0),   -- 下架
('金戒指', '饰品', 1000.00, 5, 1);

-- 任务：
-- A. 创建视图 v_on_sale：只显示在售商品（is_on_sale=1），包含name, category, price, stock
-- B. 通过视图查询所有在售武器
-- C. 通过视图把'魔法书'的价格改为450（验证可更新视图）
-- D. 尝试通过视图插入一条 is_on_sale=0 的商品，观察结果
-- E. 加上 WITH CHECK OPTION 后重试 D
```

### 练习2（扩展）：封装测试校验视图
```sql
-- 基于练习1的 products 表，创建一个视图 v_stock_check
-- 功能：显示库存不足的商品（stock < 20），额外显示一个状态列：
--   stock=0 显示'缺货'，0<stock<10 显示'紧张'，10<=stock<20 显示'偏低'
-- 然后用这个视图检查哪些商品需要补货
```

---

**【一句话总结】**

视图是保存的SELECT语句，本质是虚拟表——用它来简化复杂查询、隔离敏感数据、封装校验逻辑，但别指望它提升性能，也别嵌套太深。
