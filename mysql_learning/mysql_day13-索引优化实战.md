# 🐬 MySQL Day 13/30 · 索引优化实战

---

## 【学习目标】

- 掌握**复合索引**的创建规则和**最左前缀原则**
- 能识别日常开发中的 **7 种索引失效场景**，写出不走索引的 SQL 并修复
- 学会配置**慢查询日志**，用 EXPLAIN 分析执行计划定位性能瓶颈

---

## 【核心语法】

```sql
-- ============================================
-- 1. 复合索引（联合索引）创建
-- ============================================
-- 语法：CREATE INDEX 索引名 ON 表名(列1, 列2, 列3, ...);
-- 列的先后顺序很重要！直接影响最左前缀生效范围

CREATE INDEX idx_player_level_power 
    ON game_players(level, power, last_login);

-- ============================================
-- 2. 查看表上的索引
-- ============================================
SHOW INDEX FROM game_players;
-- 或查看建表语句（含索引定义）
SHOW CREATE TABLE game_players;

-- ============================================
-- 3. EXPLAIN 分析执行计划（最重要的优化工具）
-- ============================================
EXPLAIN SELECT * FROM game_players WHERE level = 30 AND power > 5000;

-- 关键字段速查：
-- type:  const > eq_ref > ref > range > index > ALL（越左越好）
-- key:   实际使用的索引名（NULL = 没用到索引）
-- rows:  估算扫描行数（越少越好）
-- Extra: 附加信息
--   • Using index：覆盖索引，最优
--   • Using where：在 server 层过滤
--   • Using filesort：需要额外排序，不好
--   • Using temporary：需要临时表，更不好

-- ============================================
-- 4. 慢查询日志配置（MySQL 5.7+/8.0）
-- ============================================
-- 查看慢查询是否开启
SHOW VARIABLES LIKE 'slow_query%';
SHOW VARIABLES LIKE 'long_query_time';

-- 临时开启（重启失效）
SET GLOBAL slow_query_log = ON;
SET GLOBAL long_query_time = 1;          -- 超过1秒记录
SET GLOBAL log_queries_not_using_indexes = ON;  -- 记录未使用索引的查询

-- 永久开启：编辑 my.cnf / my.ini
-- [mysqld]
-- slow_query_log = 1
-- slow_query_log_file = /var/log/mysql/slow.log
-- long_query_time = 1

-- ============================================
-- 5. 删除索引
-- ============================================
DROP INDEX idx_name ON table_name;
-- 或
ALTER TABLE table_name DROP INDEX idx_name;
```

---

## 【实战示例】

### 示例 1：最左前缀原则 —— 索引能用多少列？

```sql
-- 建测试表：游戏玩家表
CREATE TABLE players_test (
    id       INT PRIMARY KEY AUTO_INCREMENT,
    level    INT          NOT NULL COMMENT '等级',
    vip      TINYINT      NOT NULL COMMENT 'VIP等级',
    power    INT          NOT NULL COMMENT '战力',
    nickname VARCHAR(20)  NOT NULL COMMENT '昵称'
);

-- 创建复合索引：level → vip → power
CREATE INDEX idx_lev_vip_pow ON players_test(level, vip, power);

-- 插入示例数据
INSERT INTO players_test (level, vip, power, nickname) VALUES
(10, 1, 5000,  '战士阿强'),
(10, 2, 8000,  '法师小明'),
(15, 1, 12000, '刺客小暗'),
(20, 3, 20000, '坦克老王'),
(20, 1, 15000, '射手阿花'),
(30, 2, 30000, '辅助小美');

-- === 走索引的情况 ===
-- ✅ 使用全部3列：key_len最大，最优
EXPLAIN SELECT * FROM players_test 
WHERE level = 20 AND vip = 1 AND power > 10000;

-- ✅ 使用前2列：跳过最后一列，索引仍生效（range 查询后无法继续）
EXPLAIN SELECT * FROM players_test WHERE level = 20 AND vip = 1;

-- ✅ 只使用第1列：最左列必须有，否则整个索引报废
EXPLAIN SELECT * FROM players_test WHERE level = 10;

-- === 不走索引的情况 ===
-- ❌ 跳过最左列 level，直接从第2列开始 → 索引失效！
EXPLAIN SELECT * FROM players_test WHERE vip = 2;
-- type = ALL，全表扫描

-- ❌ 从第3列开始，前两列都没用 → 索引失效！
EXPLAIN SELECT * FROM players_test WHERE power > 10000;
-- type = ALL

-- ❌ 范围查询后面的列不走索引
-- level用上了，但 power 在范围查询 WHERE 之后，vip 只能用 ICP（索引条件下推）
EXPLAIN SELECT * FROM players_test 
WHERE level > 10 AND vip = 1 AND power > 10000;
-- key_len 可能只有 level 部分

-- ============================================
-- 直观理解最左前缀：像汽车车牌号
-- 索引 (level, vip, power) 相当于按 level→vip→power 排序的目录
-- 跳过 level 直接查 vip=2，就像不看首字母找名字一样，只能翻全书
-- ============================================
```

### 示例 2：索引失效 7 大场景（每个都必须记住！）

```sql
-- 建表准备
CREATE TABLE items_test (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    item_name   VARCHAR(50)  NOT NULL COMMENT '道具名称',
    price       DECIMAL(10,2) NOT NULL COMMENT '价格',
    item_type   VARCHAR(20)  NOT NULL COMMENT '类型',
    create_time DATETIME     NOT NULL COMMENT '创建时间',
    INDEX idx_name(item_name),
    INDEX idx_price(price),
    INDEX idx_type(item_type)
);

INSERT INTO items_test (item_name, price, item_type, create_time) VALUES
('屠龙刀', 999.00, '武器', '2026-05-01 10:00:00'),
('倚天剑', 888.00, '武器', '2026-05-02 11:00:00'),
('金疮药', 10.00,  '药品', '2026-05-03 12:00:00'),
('回城卷', 50.00,  '消耗品','2026-05-04 13:00:00'),
('昆仑镜', 1200.00,'法宝', '2026-05-05 14:00:00');

-- ❌ 场景1：在索引列上使用函数
EXPLAIN SELECT * FROM items_test WHERE UPPER(item_name) = '屠龙刀';
-- type=ALL，索引失效！因为 MySQL 不认识 UPPER 后的值
-- ✅ 修复：函数放值那侧
EXPLAIN SELECT * FROM items_test WHERE item_name = UPPER('屠龙刀');

-- ❌ 场景2：隐式类型转换（字符串列用数字查）
EXPLAIN SELECT * FROM items_test WHERE item_name = 12345;
-- MySQL 会把字符串列全转成数字比较 → 索引失效！
-- ✅ 修复：保持类型一致
EXPLAIN SELECT * FROM items_test WHERE item_name = '12345';

-- ❌ 场景3：LIKE 前导模糊
EXPLAIN SELECT * FROM items_test WHERE item_name LIKE '%龙刀';
-- 索引失效，因为不知道前缀是什么
-- ✅ 修复：后模糊可以用索引
EXPLAIN SELECT * FROM items_test WHERE item_name LIKE '屠龙%';
-- ⚠️ 如果真的需要前后模糊，考虑 Elasticsearch 或 FULLTEXT 索引

-- ❌ 场景4：OR 条件中有一侧无索引
EXPLAIN SELECT * FROM items_test WHERE price = 999 OR item_type = '武器';
-- 虽然有 idx_price 和 idx_type，但 OR 可能导致全表扫描
-- ✅ 修复：改写为 UNION
EXPLAIN SELECT * FROM items_test WHERE price = 999
UNION
SELECT * FROM items_test WHERE item_type = '武器';

-- ❌ 场景5：WHERE 中使用 != 或 <>
EXPLAIN SELECT * FROM items_test WHERE item_type != '药品';
-- 否定条件通常不走索引
-- ✅ 修复：用 IN（如果已知所有合法值）
EXPLAIN SELECT * FROM items_test WHERE item_type IN ('武器','消耗品','法宝');

-- ❌ 场景6：IS NULL 和 IS NOT NULL
-- IS NULL 通常走索引，但 IS NOT NULL 大概率不走
EXPLAIN SELECT * FROM items_test WHERE item_name IS NOT NULL;
-- 如果大部分数据非 NULL，MySQL 认为全表扫描更快
-- ✅ 如果列几乎都有值，可以考虑加 NOT NULL 约束 + 默认值

-- ❌ 场景7：NOT IN 的子查询有 NULL
-- 危险场景，不仅不走索引，还可能返回空结果！
-- 见下方测试场景
```

### 示例 3：测试场景 —— 用 EXPLAIN 验证断言

```sql
-- ============================================
-- 测试场景：验证某个查询是否走了预期索引
-- 这是测试人员写数据库测试用例的核心技能
-- ============================================

-- 建游戏角色表
CREATE TABLE game_chars_test (
    id         INT PRIMARY KEY AUTO_INCREMENT,
    server_id  INT      NOT NULL COMMENT '区服ID',
    char_level INT      NOT NULL COMMENT '角色等级',
    fight_power INT     NOT NULL COMMENT '战力',
    INDEX idx_srv_level(server_id, char_level)
);

-- 插入5个区服，每区100个角色
-- （实际测试时用存储过程批量插入）
INSERT INTO game_chars_test (server_id, char_level, fight_power)
SELECT 
    (n % 5) + 1 AS server_id,
    10 + (n % 90) AS char_level,
    1000 + (n * 13 % 9000) AS fight_power
FROM (
    SELECT @row := @row + 1 AS n 
    FROM (SELECT 0 UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4) t1,
         (SELECT 0 UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4) t2,
         (SELECT 0 UNION SELECT 1 UNION SELECT 2 UNION SELECT 3) t3,
         (SELECT @row := -1) r
) nums;

-- 测试用例1：断言"按区服+等级查询必须走复合索引"
SET @test_name = '查询玩家必须使用 idx_srv_level 索引';

EXPLAIN SELECT * FROM game_chars_test 
WHERE server_id = 3 AND char_level = 50;

-- 验证：观察 type 和 key 字段
-- 期望：type = ref, key = idx_srv_level
-- 如果 key = NULL 或 type = ALL，说明索引失效，测试不通过！

-- 测试用例2：断言"仅按等级查询不走索引"（验证最左前缀）
EXPLAIN SELECT * FROM game_chars_test 
WHERE char_level = 50;
-- 期望：type = ALL, key = NULL
-- 因为跳过了最左列 server_id

-- 测试用例3：对比有索引和无索引的扫描行数差异
-- 无索引查询（IMPORTANT 不走索引）
EXPLAIN SELECT * FROM game_chars_test 
WHERE fight_power > 5000;
-- rows ≈ 500（全表）

-- 加索引后查询
CREATE INDEX idx_power ON game_chars_test(fight_power);
EXPLAIN SELECT * FROM game_chars_test 
WHERE fight_power > 5000;
-- rows 大幅减少！
```

### 示例 4：慢查询分析完整流程（从发现到优化）

```sql
-- ============================================
-- Step 1：确认慢查询日志已开启
-- ============================================
SHOW VARIABLES LIKE 'slow_query%';
-- 期望 slow_query_log = ON

SHOW VARIABLES LIKE 'long_query_time';
-- 开发/测试环境建议设 0.1，生产环境 1~2 秒

-- ============================================
-- Step 2：找一条慢查询
-- ============================================

-- 模拟一条慢查询（大表全表扫描）
-- 假设 items 表有 10 万条数据
EXPLAIN SELECT item_name, price, item_type
FROM items_test
WHERE price BETWEEN 100 AND 500
ORDER BY create_time DESC;

-- 观察 EXPLAIN 输出：
-- 如果 type=ALL, Extra 含 Using filesort → 性能差！

-- ============================================
-- Step 3：分析慢查询根因
-- ============================================
-- 根因分析框架：
-- ① type 是什么？ALL/index 说明没用好索引
-- ② key 被用到了吗？NULL = 没用上
-- ③ Extra 有 Using filesort/Using temporary 吗？
-- ④ rows 扫描了多少行？和实际返回行数差距大吗？

-- ============================================
-- Step 4：制定优化方案
-- ============================================
-- 方案A：加覆盖索引，避免回表
CREATE INDEX idx_price_time_name_type ON items_test(price, create_time, item_name, item_type);

-- 重新 EXPLAIN 验证优化效果
EXPLAIN SELECT item_name, price, item_type
FROM items_test
WHERE price BETWEEN 100 AND 500
ORDER BY create_time DESC;
-- 期望：type=range, key=idx_price_time_name_type, Extra含Using index

-- 方案B：如果只是统计数量，用 COUNT 替代 SELECT *
EXPLAIN SELECT COUNT(*) FROM items_test WHERE price BETWEEN 100 AND 500;
-- 扫描行数大幅减少

-- ============================================
-- Step 5：验证优化是否生效
-- ============================================
-- 对比优化前后的 rows 和 Extra
-- 把优化前后 EXPLAIN 结果保存到测试报告
```

---

## 【注意事项/易错点】

### 🔴 最常见的坑

| 错误行为 | 后果 | 正确做法 |
|---------|------|---------|
| 凭感觉加索引，不加 EXPLAIN 验证 | 索引不生效，还拖慢写入 | **每次建索引后必 EXPLAIN 验证** |
| 复合索引列顺序随意排 | 高频查询用不上索引 | 按区分度从高到低排列，等值条件在前 |
| 线上直接 CREATE INDEX | 大表加索引锁表几分钟 | 用 `ALGORITHM=INPLACE, LOCK=NONE`（MySQL 5.6+） |
| 索引越多越好 | 写入/更新/删除变慢，占磁盘 | 一个表 3-5 个索引够用，定期审查无用索引 |
| 忘记 MySQL 优化器会选错索引 | 明明有索引却全表扫描 | 用 `FORCE INDEX(idx_name)` 强制指定验证 |

### 🟡 性能提醒

- **覆盖索引**是银弹：查询列全在索引里，不用回表，Extra 显示 `Using index`
- **前缀索引**省空间：长字符串列可建 `INDEX(col(10))` 只索引前10个字符
- 单表索引建议 ≤ 5 个，避免索引维护开销超过收益
- 生产环境加索引：先用 `pt-online-schema-change`（Percona 工具），避免锁表

---

## 【今日练习题】

### 练习题 1：补全复合索引 + 验证最左前缀（必做）

建表并创建复合索引 `(area, occupation, login_days)`：

```sql
CREATE TABLE player_stats (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    area        VARCHAR(10) NOT NULL COMMENT '大区',
    occupation  VARCHAR(10) NOT NULL COMMENT '职业',
    login_days  INT         NOT NULL COMMENT '累计登录天数',
    nick        VARCHAR(20) NOT NULL
);
-- 🎯 你的任务：创建复合索引
-- 🎯 用 EXPLAIN 验证下面哪些查询能走索引：
-- ① WHERE area = '华东'
-- ② WHERE occupation = '战士'
-- ③ WHERE area = '华东' AND occupation = '战士'
-- ④ WHERE area = '华东' AND login_days > 30
-- ⑤ WHERE login_days = 30
```

<details>
<summary>参考答案（先自己做再看）</summary>

```sql
CREATE INDEX idx_area_occ_days ON player_stats(area, occupation, login_days);

-- ① ✅ 走索引，key_len = area 部分
-- ② ❌ 跳过最左列 area，全表扫描
-- ③ ✅ 走索引，key_len = area + occupation
-- ④ ✅ 走索引但 login_days 部分为 range 扫描
-- ⑤ ❌ 跳过最左列，全表扫描
```
</details>

### 练习题 2：找出并修复索引失效的 SQL

下面 SQL 哪些能走索引？不能的请写出修复方案：

```sql
-- 表 items 有索引 idx_name(item_name)
-- ①
SELECT * FROM items WHERE LEFT(item_name, 2) = '屠龙';
-- ②
SELECT * FROM items WHERE item_name LIKE '屠%';
-- ③
SELECT * FROM items WHERE item_name LIKE '%龙刀';
-- ④
SELECT * FROM items WHERE item_name IS NOT NULL;
-- ⑤
SELECT * FROM items WHERE item_name = '倚天剑' OR price = 888;
```

<details>
<summary>参考答案</summary>

```
① ❌ 索引列用了函数 LEFT()，失效
   修复：WHERE item_name LIKE '屠龙%'（如果能确定前缀）
   
② ✅ 后模糊可以走索引

③ ❌ 前导模糊，索引失效
   修复：如必须模糊搜索，用 Elasticsearch 或者 MySQL FULLTEXT 索引

④ ⚠️ 通常全表扫描（大部分行非 NULL）
   修复：如果这列确实极少为 NULL，加 NOT NULL 约束

⑤ ⚠️ OR 一边有索引一边没有，可能全表
   修复：改写为 UNION 两个分别走索引的查询
```
</details>

---

## 【一句话总结】

> **索引优化不是加索引，而是让 EXPLAIN 里的 type 远离 ALL、rows 尽量小、Extra 没有 filesort 和 temporary。**

---

*📅 2026-06-12 | Day 13/30 | 索引优化实战*
