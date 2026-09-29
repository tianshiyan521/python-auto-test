🐬 今日MySQL学习 · Day 12/30
**主题**：索引基础（什么是索引、B+树原理、PRIMARY KEY/UNIQUE/普通索引、EXPLAIN查看执行计划）

---

**【学习目标】**
- 理解索引的本质与作用，知道为什么查询能从全表扫描变成精准定位
- 掌握 MySQL 三种主要索引类型（主键索引、唯一索引、普通索引）的创建与区别
- 学会用 EXPLAIN 分析查询执行计划，判断索引是否生效

---

**【核心语法】**

## 1. 创建索引的三种方式

```sql
-- 方式一：CREATE INDEX（只能建普通索引和唯一索引）
CREATE INDEX idx_player_name ON players(player_name);         -- 普通索引
CREATE UNIQUE INDEX idx_email ON users(email);                 -- 唯一索引

-- 方式二：ALTER TABLE 添加索引
ALTER TABLE players ADD INDEX idx_level (level);               -- 普通索引
ALTER TABLE players ADD UNIQUE INDEX idx_nickname (nickname);  -- 唯一索引

-- 方式三：建表时直接指定（最推荐，一气呵成）
CREATE TABLE orders (
    order_id    INT AUTO_INCREMENT PRIMARY KEY,                -- 主键索引（自动创建）
    order_no    VARCHAR(32) NOT NULL,
    user_id     INT NOT NULL,
    status      TINYINT DEFAULT 0,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE INDEX idx_order_no (order_no),                      -- 唯一索引
    INDEX idx_user_id (user_id),                                -- 普通索引
    INDEX idx_status_created (status, created_at)               -- 复合索引（Day 13 详解）
);
```

## 2. 查看与删除索引

```sql
-- 查看表的所有索引
SHOW INDEX FROM players;
SHOW INDEX FROM orders;

-- 删除索引
DROP INDEX idx_player_name ON players;
ALTER TABLE players DROP INDEX idx_level;
```

## 3. EXPLAIN 查看执行计划

```sql
-- 不加索引：全表扫描
EXPLAIN SELECT * FROM players WHERE player_name = '张三';

-- 加索引后：索引查找
CREATE INDEX idx_player_name ON players(player_name);
EXPLAIN SELECT * FROM players WHERE player_name = '张三';
```

**EXPLAIN 关键字段解读：**

| 字段 | 含义 | 关注点 |
|------|------|--------|
| type | 访问类型 | 从好到差：system > const > eq_ref > ref > range > index > **ALL**（全表扫描） |
| key | 实际使用的索引 | NULL 表示没用索引 |
| rows | 预估扫描行数 | 越小越好 |
| Extra | 额外信息 | Using index（覆盖索引，好）、Using filesort（额外排序，坏）、Using temporary（临时表，坏） |

**type 值速记（重点记住这几个）：**
- `const`：主键/唯一索引精确匹配，最快
- `ref`：普通索引等值匹配，很快
- `range`：索引范围扫描（BETWEEN、>、<），较快
- `index`：全索引扫描，比 ALL 稍好
- `ALL`：**全表扫描**，最慢，要优化！

---

**【实战示例】**

### 示例1：基础 —— 创建索引前后 EXPLAIN 对比

```sql
-- 准备测试数据
CREATE TABLE test_index_demo (
    id       INT AUTO_INCREMENT PRIMARY KEY,
    name     VARCHAR(50),
    age      INT,
    city     VARCHAR(20),
    INDEX idx_age (age)                     -- 建表时建索引
);

-- 插入一些数据（用存储过程批量插更快，这里演示少量）
INSERT INTO test_index_demo (name, age, city) VALUES
('张三', 25, '南昌'), ('李四', 30, '北京'), ('王五', 25, '上海'),
('赵六', 28, '广州'), ('钱七', 25, '深圳'), ('孙八', 35, '杭州');

-- ① 没有索引的列 → 全表扫描
EXPLAIN SELECT * FROM test_index_demo WHERE city = '南昌';
-- type: ALL,  key: NULL  → 全表扫，每行都检查

-- ② 有索引的列 → 索引查找
EXPLAIN SELECT * FROM test_index_demo WHERE age = 25;
-- type: ref,  key: idx_age  → 走索引，只查匹配行

-- ③ 主键查询 → 最快
EXPLAIN SELECT * FROM test_index_demo WHERE id = 1;
-- type: const,  key: PRIMARY  → 主键直接定位

-- 清理
DROP TABLE test_index_demo;
```

### 示例2：进阶 —— 三种索引类型的区别与选择

```sql
-- 场景：玩家表
CREATE TABLE game_players (
    player_id    INT AUTO_INCREMENT PRIMARY KEY,          -- ① 主键索引：自增ID，唯一+非空
    nickname     VARCHAR(30) NOT NULL,
    email        VARCHAR(100),
    level        INT DEFAULT 1,
    vip_level    TINYINT DEFAULT 0,
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- ② 唯一索引：昵称不能重复，邮箱不能重复
    UNIQUE INDEX idx_nickname (nickname),
    UNIQUE INDEX idx_email (email),

    -- ③ 普通索引：按等级查询很频繁，但等级值大量重复
    INDEX idx_level (level),
    INDEX idx_vip (vip_level)
);

-- 主键索引 vs 唯一索引 vs 普通索引 的核心区别：
-- ┌──────────┬────────┬──────────┬──────────┐
-- │          │ 主键索引 │ 唯一索引  │ 普通索引  │
-- ├──────────┼────────┼──────────┼──────────┤
-- │ 允许NULL  │  ✗      │  ✓       │  ✓       │
-- │ 允许重复  │  ✗      │  ✗       │  ✓       │
-- │ 每表个数  │  1个    │  多个     │  多个     │
-- │ 物理存储  │ 聚簇索引 │ 二级索引  │ 二级索引  │
-- │ 典型场景  │ ID     │ 手机号    │ 状态/分类 │
-- └──────────┴────────┴──────────┴──────────┘

-- 实际查询验证
EXPLAIN SELECT * FROM game_players WHERE player_id = 100;   -- const
EXPLAIN SELECT * FROM game_players WHERE nickname = '龙骑士'; -- const（唯一索引也走const）
EXPLAIN SELECT * FROM game_players WHERE level = 50;         -- ref（普通索引）
EXPLAIN SELECT * FROM game_players WHERE vip_level = 0;      -- ref，但重复值多，可能不如全表扫
```

### 示例3：测试场景 —— 用 EXPLAIN 验证慢查询是否走索引

```sql
-- 测试场景：接口测试发现「查询某玩家所有订单」接口响应慢
-- 需要验证数据库层面是否走了索引

-- 订单表（初始设计：order_no 有唯一索引，user_id 没索引）
CREATE TABLE test_orders (
    order_id   INT AUTO_INCREMENT PRIMARY KEY,
    order_no   VARCHAR(32) NOT NULL,
    user_id    INT NOT NULL,
    amount     DECIMAL(10,2),
    status     TINYINT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE INDEX idx_order_no (order_no)
);

-- ① 按订单号查 → 走唯一索引，很快
EXPLAIN SELECT * FROM test_orders WHERE order_no = 'ORD20260611001';
-- type: const ✓

-- ② 按用户ID查 → 没索引！全表扫描
EXPLAIN SELECT * FROM test_orders WHERE user_id = 10086;
-- type: ALL ✗  → 这就是慢查询根因

-- ③ 给 user_id 加索引
ALTER TABLE test_orders ADD INDEX idx_user_id (user_id);

-- ④ 再查 → 走索引了
EXPLAIN SELECT * FROM test_orders WHERE user_id = 10086;
-- type: ref ✓

-- ⑤ 测试人员的工作流总结：
-- 报Bug → 看SQL → EXPLAIN → 发现ALL → 建议加索引 → 验证type从ALL变ref → 回归通过
```

---

**【注意事项/易错点】**

1. **索引不是越多越好**
   - 每个索引占用存储空间
   - INSERT/UPDATE/DELETE 时索引也要维护，写入变慢
   - 经验：一张表索引别超过 5-6 个，优先给 WHERE/JOIN/ORDER BY 的高频列加

2. **主键索引是聚簇索引（Clustered Index），其他都是二级索引**
   - 聚簇索引：数据行按主键顺序物理存储，主键查询直接拿到整行数据
   - 二级索引：叶子节点存的是主键值，查询非索引列需要**回表**（先查索引拿主键，再查主键拿数据）
   - 这就是为什么 `SELECT *` 有时比 `SELECT 索引列` 慢——后者可以"覆盖索引"不回表

3. **B+ 树为什么不选 B 树或 Hash？**
   - B+ 树 vs B 树：B+ 树只在叶子存数据，非叶节点只存键，一个节点能存更多键 → 树更矮 → 磁盘IO更少；叶子之间有双向链表 → 范围查询极快
   - B+ 树 vs Hash：Hash 等值查询 O(1) 更快，但不支持范围查询（> < BETWEEN ORDER BY 全废），所以 MySQL 默认用 B+ 树
   - Memory 引擎支持 Hash 索引，InnoDB 默认 B+ 树

4. **EXPLAIN 的 rows 是估算值**
   - 不一定精确，但能判断大致量级
   - 优化器可能选错索引（统计信息过期），可以 `ANALYZE TABLE players;` 更新

5. **WHERE 条件用函数会导致索引失效**
   ```sql
   -- ✗ 索引失效：对列用了函数
   SELECT * FROM players WHERE YEAR(created_at) = 2026;
   -- ✓ 索引生效：改写为范围条件
   SELECT * FROM players WHERE created_at >= '2026-01-01' AND created_at < '2027-01-01';
   ```
   这是 Day 13 索引优化的重点内容，先有这个意识。

---

**【今日练习题】**

### 练习1：创建索引并用 EXPLAIN 验证（必做）

```sql
-- 1. 创建以下表
CREATE TABLE practice_users (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    username   VARCHAR(30) NOT NULL,
    email      VARCHAR(100),
    age        INT,
    city       VARCHAR(20),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. 插入一些数据（至少10条，city 重复几个值）
INSERT INTO practice_users (username, email, age, city) VALUES
('player1', 'p1@test.com', 20, '南昌'),
('player2', 'p2@test.com', 25, '北京'),
('player3', 'p3@test.com', 20, '南昌'),
('player4', 'p4@test.com', 30, '上海'),
('player5', 'p5@test.com', 25, '南昌'),
('player6', 'p6@test.com', 35, '广州'),
('player7', 'p7@test.com', 20, '北京'),
('player8', 'p8@test.com', 28, '深圳'),
('player9', 'p9@test.com', 25, '南昌'),
('player10', 'p10@test.com', 30, '上海');

-- 3. 分别执行以下 EXPLAIN，记录 type 和 key：
--    (a) SELECT * FROM practice_users WHERE id = 1;
--    (b) SELECT * FROM practice_users WHERE city = '南昌';
--    (c) SELECT * FROM practice_users WHERE email = 'p1@test.com';

-- 4. 给 city 加普通索引，给 email 加唯一索引
-- 5. 再执行 (b)(c) 的 EXPLAIN，对比变化
-- 6. 用 SHOW INDEX FROM practice_users; 查看所有索引
```

### 练习2：判断该加什么类型的索引（思考题）

```sql
-- 场景：下面这个查询很慢，怎么优化？
SELECT * FROM practice_users WHERE username = 'player5';

-- 问题：
-- (1) 该给 username 加什么类型的索引？普通索引还是唯一索引？为什么？
-- (2) 加完索引后，用 EXPLAIN 验证 type 应该是什么？
-- (3) 如果查询改成 WHERE age > 25，走索引了吗？type 是什么？
```

---

**【一句话总结】**
索引就是数据库的"目录"，B+ 树让查询从翻遍整本书（ALL）变成直接翻到对应页（ref/const）；三种索引区别在于是否允许重复和 NULL；EXPLAIN 是验证索引是否生效的唯一标准。
