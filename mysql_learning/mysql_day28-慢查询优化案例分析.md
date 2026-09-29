# 🐬 今日MySQL学习 · Day 28/30

**主题**：实战：慢查询优化案例分析

---

**【学习目标】**
- 掌握慢查询定位的完整流程：从发现问题 → EXPLAIN分析 → 优化方案 → 验证效果
- 学会读懂 EXPLAIN 的每一列，特别是 type、key、rows、Extra
- 通过3个真实案例，理解索引优化、SQL改写、架构调整三种优化手段

---

**【核心语法】**

## 1. 慢查询日志配置

```sql
-- 查看慢查询是否开启
SHOW VARIABLES LIKE 'slow_query_log%';

-- 开启慢查询日志（阈值设为1秒）
SET GLOBAL slow_query_log = ON;
SET GLOBAL long_query_time = 1;    -- 超过1秒的查询才记录

-- 查看慢查询日志文件位置
SHOW VARIABLES LIKE 'slow_query_log_file';

-- 记录没有使用索引的查询
SET GLOBAL log_queries_not_using_indexes = ON;
```

## 2. EXPLAIN 关键列解读

```sql
-- 查看执行计划
EXPLAIN SELECT * FROM players WHERE server_id = 1 AND level > 50;

-- EXPLAIN 各列含义：
-- id        : 查询序号，子查询会有多个id
-- select_type: SIMPLE/PRIMARY/SUBQUERY/DERIVED 等
-- table      : 访问哪张表
-- type       : ⭐访问类型（从好到差：system > const > eq_ref > ref > range > index > ALL）
-- key        : ⭐实际使用了哪个索引（NULL = 没用索引）
-- key_len    : 索引使用的字节长度（判断复合索引用了几列）
-- rows       : ⭐预估扫描行数（越小越好）
-- Extra      : ⭐附加信息（Using index=覆盖索引好，Using filesort=额外排序差）
```

## 3. EXPLAIN type 详解（从最优到最差）

```
system    → 表只有一行（const的特例）
const     → 主键/唯一索引精确匹配，只读1行
eq_ref    → JOIN时主键/唯一索引匹配，每次只读1行
ref       → 非唯一索引匹配，可能读多行
range     → 索引范围扫描（BETWEEN, >, <, IN）
index     → 全索引扫描（比ALL好一点，但还是要扫整棵索引树）
ALL       → ⭐全表扫描（最差，必须优化！）
```

## 4. EXPLAIN Extra 关键信息

```
Using index         → 覆盖索引，不回表，性能极佳 ✅
Using where         → WHERE过滤，在存储引擎层或服务层过滤
Using filesort      → ⭐额外排序操作（不是用索引排序），性能差 ❌
Using temporary     → ⭐使用临时表（GROUP BY/DISTINCT/UNION），性能差 ❌
Using index condition → 索引下推（ICP），减少回表次数 ✅
```

## 5. 查看慢查询日志内容

```sql
-- 用mysqldumpslow分析慢查询日志（在命令行执行）
-- 按查询时间排序，取前10条
mysqldumpslow -s t -t 10 /var/lib/mysql/slow.log

-- 按查询次数排序，取前10条
mysqldumpslow -s c -t 10 /var/lib/mysql/slow.log
```

---

**【实战示例】**

### 📌 案例1：全表扫描 → 添加索引优化

**场景**：恐龙岛排行榜页面加载超慢，查询5秒才返回

```sql
-- 问题SQL：查询某服务器战力排行榜前50名
SELECT player_id, player_name, power_value, level
FROM player_dinosaurs
WHERE server_id = 1 AND is_active = 1
ORDER BY power_value DESC
LIMIT 50;

-- 🔍 Step 1：EXPLAIN 分析
EXPLAIN SELECT player_id, player_name, power_value, level
FROM player_dinosaurs
WHERE server_id = 1 AND is_active = 1
ORDER BY power_value DESC
LIMIT 50;

-- 结果：
-- type: ALL          ← ⚠️ 全表扫描！
-- key: NULL          ← ⚠️ 没用索引
-- rows: 500000       ← ⚠️ 扫描50万行
-- Extra: Using where; Using filesort ← ⚠️ 文件排序
```

```sql
-- 🔍 Step 2：定位根因
-- 1. WHERE条件 server_id=1 AND is_active=1 没有索引 → 全表扫描
-- 2. ORDER BY power_value 没有索引 → 额外排序
-- 3. 50万行全扫再排序 → 5秒很正常

-- ✅ Step 3：优化方案 — 添加复合索引
-- 最左前缀原则：WHERE条件列 → ORDER BY列
CREATE INDEX idx_server_active_power
ON player_dinosaurs(server_id, is_active, power_value);

-- 🔍 Step 4：再次 EXPLAIN
EXPLAIN SELECT player_id, player_name, power_value, level
FROM player_dinosaurs
WHERE server_id = 1 AND is_active = 1
ORDER BY power_value DESC
LIMIT 50;

-- 结果：
-- type: range         ← ✅ 索引范围扫描
-- key: idx_server_active_power ← ✅ 用了复合索引
-- rows: 50            ← ✅ 只扫描50行！
-- Extra: Using index condition ← ✅ 索引下推
```

```sql
-- 📊 Step 5：效果对比
-- 优化前：5.2秒，扫描500000行
-- 优化后：0.03秒，扫描50行
-- 性能提升：173倍！

-- ⚡ 测试人员验证脚本（Python）
import pymysql
import time

conn = pymysql.connect(host='localhost', user='root', password='123456',
                       database='dino_island')
cursor = conn.cursor()

# 测试优化前后的查询时间
for label, sql in [
    ("优化前(无索引)", "SELECT SQL_NO_CACHE player_id, player_name, power_value FROM player_dinosaurs WHERE server_id=1 AND is_active=1 ORDER BY power_value DESC LIMIT 50"),
    ("优化后(有索引)", "SELECT SQL_NO_CACHE player_id, player_name, power_value FROM player_dinosaurs WHERE server_id=1 AND is_active=1 ORDER BY power_value DESC LIMIT 50"),
]:
    start = time.time()
    cursor.execute(sql)
    rows = cursor.fetchall()
    elapsed = time.time() - start
    print(f"{label}: {elapsed:.3f}秒, 返回{len(rows)}行")

cursor.close()
conn.close()
```

---

### 📌 案例2：索引失效 → SQL改写优化

**场景**：恐龙岛充值流水查询，按日期范围查询近7天充值记录，耗时3秒

```sql
-- 问题SQL：查询最近7天的充值记录
SELECT order_id, player_id, amount, create_time
FROM recharge_orders
WHERE DATE_FORMAT(create_time, '%Y-%m-%d') >= '2026-06-29'
  AND DATE_FORMAT(create_time, '%Y-%m-%d') <= '2026-07-06'
  AND server_id = 1;

-- 🔍 Step 1：EXPLAIN 分析
EXPLAIN SELECT order_id, player_id, amount, create_time
FROM recharge_orders
WHERE DATE_FORMAT(create_time, '%Y-%m-%d') >= '2026-06-29'
  AND DATE_FORMAT(create_time, '%Y-%m-%d') <= '2026-07-06'
  AND server_id = 1;

-- 结果：
-- type: ALL          ← ⚠️ 全表扫描！
-- key: NULL          ← ⚠️ 索引失效！
-- rows: 800000       ← ⚠️ 扫描80万行
-- Extra: Using where ← ⚠️ 服务层过滤

-- 表上已有索引：
-- INDEX idx_server_time ON recharge_orders(server_id, create_time)
-- 但 WHERE 里对 create_time 用了 DATE_FORMAT() 函数 → 索引失效！
```

```sql
-- 🔍 Step 2：定位根因
-- ⭐ 规则：对索引列使用函数/计算/隐式转换 → 索引失效
-- DATE_FORMAT(create_time, ...) 把索引列包在函数里
-- MySQL 无法用 B+树 快速定位，只能逐行计算再过滤

-- ✅ Step 3：优化方案 — 改写SQL，去掉函数
SELECT order_id, player_id, amount, create_time
FROM recharge_orders
WHERE create_time >= '2026-06-29 00:00:00'
  AND create_time < '2026-07-07 00:00:00'   -- ⚡ 注意用 < 次日0点，避免漏数据
  AND server_id = 1;

-- 🔍 Step 4：再次 EXPLAIN
EXPLAIN SELECT order_id, player_id, amount, create_time
FROM recharge_orders
WHERE create_time >= '2026-06-29 00:00:00'
  AND create_time < '2026-07-07 00:00:00'
  AND server_id = 1;

-- 结果：
-- type: range         ← ✅ 索引范围扫描
-- key: idx_server_time ← ✅ 复合索引生效
-- rows: 7000          ← ✅ 只扫7000行（7天的数据）
-- Extra: Using index condition ← ✅ 索引下推

-- 📊 效果对比
-- 优化前：3.1秒，扫描800000行
-- 优化后：0.05秒，扫描7000行
-- 性能提升：62倍！
```

```sql
-- 📝 更多索引失效场景汇总（测试人员必知）

-- ❌ 场景A：对索引列用函数
WHERE DATE_FORMAT(create_time, '%Y-%m') = '2026-07'  → 索引失效
-- ✅ 改写
WHERE create_time >= '2026-07-01' AND create_time < '2026-08-01'

-- ❌ 场景B：隐式类型转换
WHERE player_id = '123'  → player_id是INT，字符串隐式转换，索引失效
-- ✅ 改写
WHERE player_id = 123

-- ❌ 场景C：OR条件中有一侧无索引
WHERE indexed_col = 1 OR non_indexed_col = 2  → 全表扫描
-- ✅ 改写：拆成两条分别查，UNION ALL 合并
SELECT ... WHERE indexed_col = 1
UNION ALL
SELECT ... WHERE non_indexed_col = 2

-- ❌ 场景D：LIKE 以通配符开头
WHERE player_name LIKE '%恐龙%'  → 索引失效
-- ✅ 改写：只能用全文索引或搜索引擎
WHERE player_name LIKE '恐龙%'  → ✅ 前缀匹配可以用索引

-- ❌ 场景E：NOT IN / NOT EXISTS / != / <>（不一定失效，但效率低）
WHERE server_id != 1  → 大部分情况下不如 = 高效
```

---

### 📌 案例3：临时表+文件排序 → 架构调整优化

**场景**：恐龙岛领地争夺实时战况统计，每个领地的参战人数、胜率、平均战力，接口返回超10秒

```sql
-- 问题SQL：领地争夺综合统计
SELECT t territory_id, t.territory_name,
       COUNT(b.record_id) AS battle_count,
       SUM(CASE WHEN b.is_winner = 1 THEN 1 ELSE 0 END) AS win_count,
       ROUND(SUM(CASE WHEN b.is_winner = 1 THEN 1 ELSE 0 END) * 100.0
             / NULLIF(COUNT(b.record_id), 0), 2) AS win_rate,
       AVG(p.power_value) AS avg_power
FROM territories t
LEFT JOIN battle_records b ON t.territory_id = b.territory_id
  AND b.create_time >= '2026-07-01'
LEFT JOIN player_dinosaurs p ON b.player_id = p.player_id
  AND p.is_active = 1
GROUP BY t.territory_id, t.territory_name
ORDER BY win_rate DESC;

-- 🔍 Step 1：EXPLAIN 分析
EXPLAIN SELECT t.territory_id, t.territory_name,
       COUNT(b.record_id) AS battle_count,
       SUM(CASE WHEN b.is_winner = 1 THEN 1 ELSE 0 END) AS win_count,
       ROUND(SUM(CASE WHEN b.is_winner = 1 THEN 1 ELSE 0 END) * 100.0
             / NULLIF(COUNT(b.record_id), 0), 2) AS win_rate,
       AVG(p.power_value) AS avg_power
FROM territories t
LEFT JOIN battle_records b ON t.territory_id = b.territory_id
  AND b.create_time >= '2026-07-01'
LEFT JOIN player_dinosaurs p ON b.player_id = p.player_id
  AND p.is_active = 1
GROUP BY t.territory_id, t.territory_name
ORDER BY win_rate DESC;

-- 结果（简化版）：
-- t表:  type: ALL, rows: 200
-- b表:  type: ALL, rows: 2000000  ← ⚠️ 200万战斗记录全表扫描
-- p表:  type: ALL, rows: 500000   ← ⚠️ 50万玩家全表扫描
-- Extra: Using temporary; Using filesort ← ⚠️ 临时表+额外排序

-- 问题根因：
-- 1. 三表LEFT JOIN，中间表battle_records有200万行，没有合适索引
-- 2. GROUP BY产生临时表
-- 3. ORDER BY win_rate（计算列）无法用索引 → filesort
```

```sql
-- ✅ Step 2：优化方案 — 三步走

-- 方案A：添加索引（第一步，最容易做）
CREATE INDEX idx_b_territory_time
ON battle_records(territory_id, create_time);

CREATE INDEX idx_p_player_active
ON player_dinosaurs(player_id, is_active);

-- 方案B：SQL改写 — 拆分子查询，先聚合再关联（第二步）
-- 先在 battle_records 上做聚合（只扫该表的索引）
-- 再与 territories 关联（只200行）
-- 最后关联 player_dinosaurs 取平均战力

SELECT t.territory_id, t.territory_name,
       b_agg.battle_count, b_agg.win_count,
       b_agg.win_rate,
       p_agg.avg_power
FROM territories t
INNER JOIN (
    -- 子查询1：每领地的战斗统计（只扫battle_records索引）
    SELECT territory_id,
           COUNT(*) AS battle_count,
           SUM(CASE WHEN is_winner = 1 THEN 1 ELSE 0 END) AS win_count,
           ROUND(SUM(CASE WHEN is_winner = 1 THEN 1 ELSE 0 END) * 100.0
                 / NULLIF(COUNT(*), 0), 2) AS win_rate
    FROM battle_records
    WHERE create_time >= '2026-07-01'
    GROUP BY territory_id
) b_agg ON t.territory_id = b_agg.territory_id
LEFT JOIN (
    -- 子查询2：每领地的参战玩家平均战力（先聚合再关联）
    SELECT b.territory_id,
           AVG(p.power_value) AS avg_power
    FROM battle_records b
    INNER JOIN player_dinosaurs p ON b.player_id = p.player_id
    WHERE b.create_time >= '2026-07-01' AND p.is_active = 1
    GROUP BY b.territory_id
) p_agg ON t.territory_id = p_agg.territory_id
ORDER BY b_agg.win_rate DESC;
```

```sql
-- 🔍 Step 3：优化后 EXPLAIN（关键变化）
-- b_agg子查询：
--   type: range ← ✅ 索引范围扫描
--   key: idx_b_territory_time ← ✅
--   rows: 30000 ← ✅ 只扫3万行（7月数据）
--   Extra: Using index condition ← ✅
-- p_agg子查询：
--   type: ref ← ✅ 索引匹配
--   key: idx_p_player_active ← ✅
-- t主表：
--   type: ALL, rows: 200 ← 200行小表全扫可接受
-- Extra中没有 Using temporary ← ✅ 临时表消失

-- 📊 效果对比
-- 优化前：10.5秒
-- 优化后：0.8秒
-- 性能提升：13倍！
```

```sql
-- 方案C：架构调整 — 物化统计表（终极方案，第三步）
-- ⭐ 如果这个统计页面被高频访问（每分钟刷新），再怎么优化SQL都不够
-- 解决方案：预计算，定时刷新到统计快照表

-- 创建领地统计快照表
CREATE TABLE territory_stats_snapshot (
    territory_id INT PRIMARY KEY,
    territory_name VARCHAR(50),
    battle_count INT DEFAULT 0,
    win_count INT DEFAULT 0,
    win_rate DECIMAL(5,2) DEFAULT 0,
    avg_power DECIMAL(10,2) DEFAULT 0,
    snapshot_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_win_rate (win_rate DESC)     -- ⭐ 排行榜专用索引
);

-- 每5分钟刷新一次（用存储过程 + 事件或外部定时任务）
INSERT INTO territory_stats_snapshot (territory_id, territory_name,
    battle_count, win_count, win_rate, avg_power, snapshot_time)
SELECT t.territory_id, t.territory_name,
       b_agg.battle_count, b_agg.win_count,
       b_agg.win_rate, p_agg.avg_power,
       NOW()
FROM territories t
INNER JOIN (
    SELECT territory_id,
           COUNT(*) AS battle_count,
           SUM(CASE WHEN is_winner = 1 THEN 1 ELSE 0 END) AS win_count,
           ROUND(SUM(CASE WHEN is_winner = 1 THEN 1 ELSE 0 END) * 100.0
                 / NULLIF(COUNT(*), 0), 2) AS win_rate
    FROM battle_records
    WHERE create_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    GROUP BY territory_id
) b_agg ON t.territory_id = b_agg.territory_id
LEFT JOIN (
    SELECT b.territory_id, AVG(p.power_value) AS avg_power
    FROM battle_records b
    INNER JOIN player_dinosaurs p ON b.player_id = p.player_id
    WHERE b.create_time >= DATE_SUB(NOW(), INTERVAL 7 DAY) AND p.is_active = 1
    GROUP BY b.territory_id
) p_agg ON t.territory_id = p_agg.territory_id
ON DUPLICATE KEY UPDATE
    battle_count = VALUES(battle_count),
    win_count = VALUES(win_count),
    win_rate = VALUES(win_rate),
    avg_power = VALUES(avg_power),
    snapshot_time = NOW();

-- ⭐ 现在前端直接查快照表，0.01秒返回
SELECT * FROM territory_stats_snapshot ORDER BY win_rate DESC;

-- 📊 效果对比
-- 原始SQL：10.5秒
-- 加索引+改写：0.8秒
-- 物化快照表：0.01秒
-- 完整优化链：1050倍提升！
```

---

### 📌 慢查询优化方法论总结

```sql
-- ⭐ 慢查询优化四步法

-- Step 1: 定位慢查询
-- 方法1：慢查询日志 mysqldumpslow
-- 方法2：SHOW PROCESSLIST 看当前执行中的查询
-- 方法3：performance_schema.events_statements_summary_by_digest

-- Step 2: EXPLAIN 分析
-- 重点关注：type、key、rows、Extra
-- type = ALL → 必须优化
-- key = NULL → 没用索引
-- Extra 有 Using filesort / Using temporary → 需优化

-- Step 3: 选择优化手段
-- 手段1：添加索引（最常见，成本最低）
--   → WHERE条件列 + ORDER BY列 → 复合索引
-- 手段2：改写SQL（消除索引失效、减少JOIN层数）
--   → 不对索引列用函数/计算
--   → 拆子查询先聚合再关联
-- 手段3：架构调整（终极方案）
--   → 物化/快照表
--   → 分表分库
--   → 引入缓存（Redis）

-- Step 4: 验证效果
-- EXPLAIN对比前后
-- 实际执行时间对比
-- 用 Python 脚本自动化对比
```

---

**【注意事项/易错点】**

1. **EXPLAIN 的 rows 是估算值，不准确**
   - `rows` 是基于统计信息的估算，实际行数可能差异很大
   - 验证真实效果要用 `SELECT COUNT(*)` 或实际执行测时间
   - 优化后 rows 减少不代表一定变快（要看实际执行）

2. **添加索引不是万能的**
   - 索引加速查询，但拖慢写入（INSERT/UPDATE/DELETE 要维护索引）
   - 一张表索引不要超过5-6个，多了反而降低整体性能
   - 复合索引注意最左前缀原则，列顺序很关键

3. **SQL改写要保证语义一致**
   - 优化后SQL的结果必须和原SQL完全一致
   - LEFT JOIN 拆成子查询时，注意NULL值处理差异
   - 用测试数据对比优化前后结果集，确保没有偏差

4. **慢查询日志的坑**
   - `long_query_time` 是SQL执行时间，不包括锁等待时间
   - 某些查询慢是因为被锁阻塞（看 `SHOW PROCESSLIST` 的 State 列）
   - 开 `log_queries_not_using_indexes` 会记录大量全索引扫描的查询，日志可能很大

---

**【今日练习题】**

### 练习1：亲手分析一个慢查询

```sql
-- 在你的本地 MySQL 中执行以下步骤：

-- 1. 创建测试表和数据
CREATE TABLE test_orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    player_id INT,
    server_id INT,
    amount DECIMAL(10,2),
    status VARCHAR(20),
    create_time DATETIME,
    INDEX idx_player (player_id)
);

-- 2. 插入一些测试数据
INSERT INTO test_orders (player_id, server_id, amount, status, create_time)
VALUES
(1, 1, 100.00, 'paid', '2026-07-01 10:00:00'),
(2, 1, 200.00, 'paid', '2026-07-01 11:00:00'),
(3, 2, 150.00, 'pending', '2026-07-02 09:00:00'),
(4, 1, 300.00, 'paid', '2026-07-03 08:00:00'),
(5, 2, 50.00, 'cancelled', '2026-07-04 12:00:00'),
(6, 1, 250.00, 'paid', '2026-07-05 14:00:00');

-- 3. 写一个慢查询并 EXPLAIN
EXPLAIN SELECT * FROM test_orders WHERE DATE_FORMAT(create_time, '%Y-%m') = '2026-07';

-- 4. 观察结果：type是不是ALL？key是不是NULL？

-- 5. 改写SQL消除函数
EXPLAIN SELECT * FROM test_orders WHERE create_time >= '2026-07-01' AND create_time < '2026-08-01';

-- 6. 对比两个EXPLAIN的差异，记录你的发现
```

### 练习2：复合索引最左前缀验证

```sql
-- 给 test_orders 加复合索引
CREATE INDEX idx_server_time_amount ON test_orders(server_id, create_time, amount);

-- 以下3个查询，哪些能用索引？逐一 EXPLAIN 验证：
-- Q1: WHERE server_id = 1                    （命中第1列）
-- Q2: WHERE server_id = 1 AND create_time >= '2026-07-01'  （命中前2列）
-- Q3: WHERE create_time >= '2026-07-01'      （跳过第1列，能用索引吗？）

EXPLAIN SELECT * FROM test_orders WHERE server_id = 1;
EXPLAIN SELECT * FROM test_orders WHERE server_id = 1 AND create_time >= '2026-07-01';
EXPLAIN SELECT * FROM test_orders WHERE create_time >= '2026-07-01';

-- ⭐ 记录每个查询的 type 和 key，理解最左前缀原则
```

---

**【一句话总结】**

慢查询优化的核心是：**先EXPLAIN定位（看type/key/rows/Extra），再对症下药——加索引最简单、改SQL消失效最直接、物化快照表是终极方案，优化前后必须对比结果集确保语义一致。**

---

*进度：Day 28/30 完成 ✅ | 明天预告：Day 29 - MySQL与测试开发*
