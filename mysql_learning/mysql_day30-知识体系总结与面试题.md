# 🐬 今日MySQL学习 · Day 30/30（最终回）

**主题**：MySQL知识体系总结与面试题

> 🎉 恭喜！今天是30天MySQL学习之旅的最后一站。经过29天的系统学习，你已经从零基础走到了能独立完成数据库设计、复杂查询、性能优化和测试验证的水平。今天我们做一次全面的知识盘点，把散落的知识串成体系，再配上10道高频面试题，为这趟旅程画上完美句号。

---

## 【学习目标】

- **梳理30天知识体系**：从基础CRUD到高级优化，建立完整的MySQL知识图谱
- **攻克10道高频面试题**：每道题都是面试真实出现率80%+的考点，附带标准答案+加分话术
- **明确进阶学习路线**：知道接下来该学什么，避免盲目摸索

---

## 【一、30天知识体系总图谱】

### 基础篇（Day 1-7）：会写SQL

```
MySQL知识体系
│
├── 基础操作层
│   ├── Day 1: 安装与连接（mysqld/DBeaver/SHOW/USE/DESC）
│   ├── Day 2: 建库建表（CREATE DATABASE/TABLE、数据类型选型）
│   ├── Day 3: CRUD基础（INSERT/SELECT/UPDATE/DELETE）
│   ├── Day 4: 条件与排序（WHERE/AND/OR/ORDER BY/LIMIT）
│   ├── Day 5: 聚合与分组（COUNT/SUM/AVG/GROUP BY/HAVING）
│   ├── Day 6: 多表关联（INNER/LEFT/RIGHT/CROSS JOIN）
│   └── Day 7: 子查询（WHERE/FROM/SELECT子查询、EXISTS、ANY/ALL）
│
├── 进阶技能层
│   ├── Day 8: 集合操作（UNION/UNION ALL/交集/差集）
│   ├── Day 9: 函数库（字符串14个+数学11个）
│   ├── Day 10: 日期时间（NOW/DATE_FORMAT/DATEDIFF/DATE_ADD/TIMESTAMPDIFF）
│   ├── Day 11: 视图VIEW（创建/修改/WITH CHECK OPTION/可更新视图）
│   ├── Day 12: 索引基础（B+树/主键/唯一/普通索引/EXPLAIN）
│   ├── Day 13: 索引优化（复合索引/最左前缀/索引失效/慢查询）
│   └── Day 14: 事务与锁（ACID/隔离级别/脏读不可重复读幻读/行锁表锁/死锁）
│
├── 高级管理层
│   ├── Day 15: 存储过程（PROCEDURE/IN/OUT/INOUT/IF/CASE/WHILE/游标）
│   ├── Day 16: 触发器（BEFORE/AFTER × INSERT/UPDATE/DELETE/NEW/OLD/SIGNAL）
│   ├── Day 17: 权限管理（CREATE USER/GRANT/REVOKE/4级权限/最小权限原则）
│   ├── Day 18: 表设计进阶（外键/CHECK/DEFAULT/AUTO_INCREMENT/ON UPDATE）
│   ├── Day 19: 设计范式（1NF/2NF/3NF/反范式设计）
│   ├── Day 20: SQL注入安全（5种注入/预编译/参数化/检测方法）
│   └── Day 21: 备份恢复（mysqldump/binlog/增量恢复/备份策略）
│
├── 实战应用层
│   ├── Day 22: 电商数据库设计（7张表/关联设计/金额快照）
│   ├── Day 23: 电商CRUD全流程（注册/上架/购物车/下单/取消）
│   ├── Day 24: 游戏数据库设计（恐龙岛5张表/分区/双表分离）
│   ├── Day 25: 游戏复杂查询（排行榜/战力统计/留存分析）
│   ├── Day 26: Python+MySQL（pymysql/GameDB封装类）
│   ├── Day 27: Python+pytest（数据库测试用例/数据工厂/双断言）
│   └── Day 28: 慢查询优化（3个真实案例/EXPLAIN/四步法）
│
└── 测试专项层
    ├── Day 29: MySQL与测试开发（接口后DB验证/一致性检查/数据工厂）
    └── Day 30: 知识总结与面试题 ← 📍 你在这里
```

### 核心知识关联图

```
                    ┌──────────────┐
                    │   SQL注入安全  │◄──── 权限管理(最小权限)
                    └──────┬───────┘
                           │ 参数化查询
                    ┌──────▼───────┐
                    │  Python+MySQL │◄──── 事务管理(commit/rollback)
                    └──────┬───────┘
                           │ pytest
                    ┌──────▼───────┐
     备份恢复 ◄─────►│  测试开发     │◄────► 数据一致性验证
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼─────┐ ┌───▼────┐ ┌────▼─────┐
        │ 索引优化   │ │ 表设计  │ │ 复杂查询  │
        │ EXPLAIN   │ │ 范式    │ │ JOIN     │
        │ 最左前缀   │ │ 外键    │ │ 子查询    │
        └─────┬─────┘ └───┬────┘ └────┬─────┘
              │            │            │
              └────────────┼────────────┘
                           │
                    ┌──────▼───────┐
                    │   CRUD 基础   │
                    │  增 删 改 查   │
                    └──────────────┘
```

---

## 【二、高频面试题 10 道】

### 面试题 1：MySQL 索引底层是什么数据结构？为什么选 B+ 树而不是 B 树或 Hash？

**标准答案：**

MySQL InnoDB 引擎的索引底层是 **B+ 树**（B+ Tree）。

选择 B+ 树的原因：

| 对比项 | B+ 树 | B 树 | Hash |
|--------|-------|------|------|
| 范围查询 | ✅ 叶子节点链表，范围扫描极快 | ❌ 需中序遍历，效率低 | ❌ 完全不支持 |
| 等值查询 | ✅ 快（3-4层即可存千万级数据） | ✅ 快 | ✅ 最快 O(1) |
| 排序 | ✅ 叶子节点有序 | ❌ 数据散落各节点 | ❌ 无序 |
| 磁盘IO | ✅ 少（非叶子节点不存数据，扇出大） | ❌ 多（每个节点存数据，扇出小） | - |
| 数据稳定性 | ✅ 查询路径长度固定（都到叶子） | ❌ 不固定（数据可能在非叶子节点） | - |

**加分话术：**
> "B+ 树的非叶子节点只存索引 key 不存数据，所以一个节点能存更多 key，树更矮，3-4 层就能覆盖千万级数据。而且叶子节点通过双向链表连接，范围查询和排序效率远高于 B 树。Hash 索引虽然等值查询快，但不支持范围查询和排序，所以 InnoDB 选择 B+ 树。"

---

### 面试题 2：MySQL 事务的四大特性（ACID）分别是什么？InnoDB 是怎么实现的？

**标准答案：**

| 特性 | 含义 | InnoDB 实现机制 |
|------|------|----------------|
| **A**tomicity（原子性） | 事务要么全部成功，要么全部回滚 | **undo log**（回滚日志）：记录修改前的数据，ROLLBACK 时用 undo log 恢复 |
| **C**onsistency（一致性） | 事务前后数据保持一致状态 | 由 A、I、D 共同保证 + 应用层约束（外键/CHECK等） |
| **I**solation（隔离性） | 并发事务之间互不干扰 | **MVCC + 锁机制**：读用 MVCC（多版本并发控制），写用行锁 |
| **D**urability（持久性） | 事务提交后数据永久保存 | **redo log**（重做日志）：先写 redo log 再写磁盘（WAL机制），崩溃后可恢复 |

**关键记忆点：**
- 原子性靠 **undo log**
- 持久性靠 **redo log**
- 隔离性靠 **MVCC + 锁**
- 一致性是最终目标，由其他三个保证

**加分话术：**
> "InnoDB 用 WAL（Write-Ahead Logging）机制，先写 redo log 再写数据页，保证崩溃恢复。undo log 不仅用于回滚，还支撑了 MVCC 的快照读。这四个特性中，一致性是目的，AID 是手段。"

---

### 面试题 3：MySQL 的四种隔离级别分别解决了什么问题？

**标准答案：**

| 隔离级别 | 脏读 | 不可重复读 | 幻读 | 性能 |
|----------|------|-----------|------|------|
| READ UNCOMMITTED（读未提交） | ❌ 可能 | ❌ 可能 | ❌ 可能 | 最高 |
| READ COMMITTED（读已提交） | ✅ 避免 | ❌ 可能 | ❌ 可能 | 高 |
| REPEATABLE READ（可重复读） | ✅ 避免 | ✅ 避免 | ❌ 可能* | 中 |
| SERIALIZABLE（串行化） | ✅ 避免 | ✅ 避免 | ✅ 避免 | 最低 |

> *MySQL InnoDB 的 REPEATABLE READ 通过 **Next-Key Lock**（间隙锁+行锁）在很大程度上也解决了幻读问题，这是 MySQL 区别于其他数据库的地方。

**三个并发问题解释：**
- **脏读**：事务A读到了事务B未提交的数据，B回滚后A读到的就是脏数据
- **不可重复读**：事务A两次读同一行，中间事务B修改了，两次结果不同（侧重修改）
- **幻读**：事务A两次范围查询，中间事务B插入/删除了数据，结果集行数变了（侧重增删）

**加分话术：**
> "MySQL 默认隔离级别是 REPEATABLE READ，不像 Oracle/PostgreSQL 默认是 READ COMMITTED。MySQL 的 RR 级别通过 MVCC 实现快照读避免不可重复读，通过 Next-Key Lock 实现当前读避免幻读，所以实际上 MySQL 的 RR 已经很接近 Serializable 了。"

---

### 面试题 4：什么是聚簇索引和非聚簇索引（二级索引）？什么是回表？

**标准答案：**

**聚簇索引（Clustered Index）：**
- 叶子节点存储的是**完整数据行**，索引和数据存在一起
- InnoDB 的主键就是聚簇索引
- 一张表只能有一个聚簇索引
- 查主键不需要额外IO，直接拿到数据

**非聚簇索引 / 二级索引（Secondary Index）：**
- 叶子节点存储的是**索引列值 + 主键值**
- 需要先查到主键，再回聚簇索引查完整数据 → 这个过程叫**回表**
- 一张表可以有多个二级索引

**回表示意图：**
```
二级索引（idx_name）              聚簇索引（PRIMARY）
┌──────────────┐                ┌──────────────────────┐
│ name='张三'   │───找到PK=5──→  │ PK=5, name='张三',    │
│ → PK=5       │                │      level=10, gold=..│
└──────────────┘                └──────────────────────┘
     第一次查                        第二次查（回表）
```

**覆盖索引优化：**
如果查询的列都在索引中，就不需要回表：
```sql
-- name列有索引，且只查name → 覆盖索引，无需回表
SELECT name FROM players WHERE name = '张三';

-- 需要回表：查了level，但索引只有name
SELECT name, level FROM players WHERE name = '张三';
```

**加分话术：**
> "InnoDB 的聚簇索引就是主键索引，数据和索引一体。非聚簇索引存的是主键值，需要回表。所以面试常问的'为什么主键建议用自增INT'——因为自增主键插入时B+树叶子节点顺序写入，不会频繁页分裂，写入性能好。"

---

### 面试题 5：复合索引的最左前缀原则是什么？以下查询能否命中索引？

假设有复合索引：`idx_abc (a, b, c)`

**标准答案：**

最左前缀原则：查询条件必须从索引最左列开始，才能使用该复合索引。

| 查询条件 | 是否命中索引 | 说明 |
|----------|-------------|------|
| `WHERE a = 1` | ✅ 命中 | 最左列 |
| `WHERE a = 1 AND b = 2` | ✅ 命中 | 连续最左前缀 |
| `WHERE a = 1 AND b = 2 AND c = 3` | ✅ 命中 | 完整匹配 |
| `WHERE b = 2` | ❌ 不命中 | 缺少最左列a |
| `WHERE b = 2 AND c = 3` | ❌ 不命中 | 缺少最左列a |
| `WHERE a = 1 AND c = 3` | ⚠️ 部分命中 | 只用到a，c无法利用索引（中间断了b） |
| `WHERE a = 1 AND b > 2 AND c = 3` | ⚠️ 部分命中 | a和b命中，但b是范围查询后c无法用索引 |

**范围查询是分界线：** 范围查询（>、<、BETWEEN、LIKE 'xxx%'）之后的列无法使用索引。

```sql
-- idx_abc (a, b, c)
-- a用索引，b用索引，但b>2是范围查询，c无法用索引
WHERE a = 1 AND b > 2 AND c = 3
--     ✅        ✅         ❌
```

**加分话术：**
> "建复合索引时，列的顺序很重要。通用原则是：等值查询的列放前面，范围查询的列放后面。比如 `WHERE status = 1 AND create_time > '2026-01-01'`，索引应该建 `(status, create_time)` 而不是反过来。"

---

### 面试题 6：MySQL 中 CHAR 和 VARCHAR 有什么区别？怎么选？

**标准答案：**

| 对比项 | CHAR(n) | VARCHAR(n) |
|--------|---------|------------|
| 存储方式 | 固定长度，不足n用空格填充 | 变长存储，实际长度+1~2字节长度前缀 |
| n的含义 | 字符数 | 字符数 |
| 存储'ab'（CHAR(5) vs VARCHAR(5)） | 'ab   '（5字节） | 'ab'（3字节：1长度+2数据） |
| 空间浪费 | 可能浪费 | 几乎不浪费 |
| 检索效率 | 略快（定长） | 略慢（需计算偏移） |
| 尾部空格 | 存储时去除，检索时补回 | 存储时保留 |
| 适用场景 | 定长数据（MD5、手机号、状态码） | 变长数据（用户名、昵称、地址） |

**选择原则：**
- 长度固定 → CHAR（如 `CHAR(32)` 存MD5，`CHAR(11)` 存手机号）
- 长度不定 → VARCHAR（如 `VARCHAR(50)` 存用户名）
- 经常变更的列 → CHAR（避免页分裂）

**加分话术：**
> "VARCHAR(5) 和 VARCHAR(255) 存储 'ab' 的磁盘空间是一样的，都是3字节。但 MySQL 在内存排序时会按定义长度分配缓冲区，所以 VARCHAR(255) 会占用更多内存。建议按实际需要设长度，不要无脑 255。"

---

### 面试题 7：什么情况下索引会失效？列举至少5种场景。

**标准答案：**

```sql
-- 假设 players 表有索引：idx_name(name)、idx_create_time(create_time)、idx_status_level(status, level)
```

| # | 失效场景 | 示例 | 原因 |
|---|---------|------|------|
| 1 | **对索引列使用函数** | `WHERE DATE_FORMAT(create_time, '%Y-%m') = '2026-07'` | 函数破坏了B+树的有序性 |
| 2 | **隐式类型转换** | `WHERE phone = 13800138000`（phone是VARCHAR） | MySQL做了隐式CAST，等价于对列加函数 |
| 3 | **LIKE以%开头** | `WHERE name LIKE '%三'` | B+树无法定位前缀 |
| 4 | **不满足最左前缀** | `WHERE level = 10`（idx_status_level需要先有status） | 复合索引从左到右匹配 |
| 5 | **OR连接非索引列** | `WHERE name = '张三' OR age = 25`（age无索引） | 必须全表扫描满足OR条件 |
| 6 | **!= 或 NOT IN** | `WHERE status != 1` | 否定条件无法走索引（扫描范围太大） |
| 7 | **索引列做运算** | `WHERE id + 1 = 100` | 等价于 `WHERE id = 99`，但优化器不一定能识别 |
| 8 | **IS NOT NULL** | `WHERE name IS NOT NULL` | 取决于数据分布和MySQL版本 |

**正确写法 vs 错误写法：**

```sql
-- ❌ 索引失效
SELECT * FROM players WHERE DATE(create_time) = '2026-07-13';

-- ✅ 改写为范围查询
SELECT * FROM players
WHERE create_time >= '2026-07-13 00:00:00'
  AND create_time <  '2026-07-14 00:00:00';
```

**加分话术：**
> "面试时不要只背场景，要能说出原因。核心就是一条：B+ 树依赖有序性，任何破坏索引列有序性比较的操作都会导致索引失效。函数、类型转换、运算都是在列上做了'变换'，让B+树无法直接二分查找。"

---

### 面试题 8：MySQL 中 DELETE、TRUNCATE、DROP 的区别？

**标准答案：**

| 对比项 | DELETE | TRUNCATE | DROP |
|--------|--------|----------|------|
| 操作对象 | 行（DML） | 表（DDL） | 表/数据库（DDL） |
| WHERE条件 | ✅ 支持 | ❌ 不支持 | ❌ 不支持 |
| 事务 | ✅ 可回滚 | ❌ 隐式提交，不可回滚 | ❌ 不可回滚 |
| 自增列 | 不重置 | 重置为1 | 表都没了 |
| 触发器 | ✅ 触发 | ❌ 不触发 | ❌ 不触发 |
| 速度 | 慢（逐行删除+写undo log） | 快（直接释放数据页） | 最快（删除表定义+数据） |
| 返回值 | 返回删除行数 | 返回0 | 无 |
| 空间 | 不立即释放 | 立即释放 | 立即释放 |

```sql
-- DELETE：可条件删除，可回滚
BEGIN;
DELETE FROM battle_records WHERE server_id = 1;  -- 只删1服数据
ROLLBACK;  -- 数据回来了

-- TRUNCATE：清空全表，不可回滚，自增重置
TRUNCATE TABLE battle_records;  -- 表空了，AUTO_INCREMENT归零

-- DROP：连表结构一起删
DROP TABLE battle_records;  -- 表没了
```

**加分话术：**
> "生产环境清表千万别用 TRUNCATE，因为它不可回滚且不触发触发器。DELETE 虽然慢，但安全。另外 TRUNCATE 是 DDL 语句，会隐式提交当前事务，所以你就算包在 BEGIN...ROLLBACK 里也救不回来。"

---

### 面试题 9：COUNT(*)、COUNT(1)、COUNT(列名) 有什么区别？

**标准答案：**

| 写法 | 含义 | 是否统计NULL | 性能 |
|------|------|-------------|------|
| `COUNT(*)` | 统计行数（包括NULL行） | ✅ 统计 | InnoDB优化过，优先选最小索引扫描 |
| `COUNT(1)` | 统计行数（1是常量，每行都有） | ✅ 统计 | 与COUNT(*)几乎一样 |
| `COUNT(列名)` | 统计该列非NULL的行数 | ❌ 不统计NULL | 需要读取列值判断NULL |

**关键结论：**
- `COUNT(*)` 和 `COUNT(1)` 结果完全相同，性能也几乎一样
- `COUNT(列名)` 语义不同——它不统计 NULL 值
- InnoDB 对 `COUNT(*)` 做了专门优化，会选择最小的二级索引来扫描（而不是全表扫描）
- **面试推荐用 `COUNT(*)`**，这是 SQL 标准写法

```sql
-- 假设 players 有100行，其中10行的 guild_id 为 NULL

SELECT COUNT(*) FROM players;        -- 结果：100（统计所有行）
SELECT COUNT(1) FROM players;        -- 结果：100（和COUNT(*)一样）
SELECT COUNT(guild_id) FROM players; -- 结果：90  （不统计NULL）
```

**为什么 InnoDB 的 COUNT(*) 不精确？**
> InnoDB 的 MVCC 机制下，不同事务看到的行数可能不同，所以 `COUNT(*)` 不能像 MyISAM 那样维护一个全局计数器，必须实际扫描。这也是大表 COUNT(*) 慢的原因。

**加分话术：**
> "面试官如果追问'COUNT(*)慢怎么办'，回答：1) 业务上用估算值 `SHOW TABLE STATUS` 的 rows 字段；2) 维护单独的计数表；3) 用 Redis 缓存计数。不要用 `COUNT(1)` 以为更快，这是误区。"

---

### 面试题 10：如何排查 MySQL 慢查询？完整流程是什么？

**标准答案：**

**四步法：**

```
发现慢查询 → EXPLAIN分析 → 定位根因 → 优化执行
```

### Step 1：开启慢查询日志

```sql
-- 查看是否开启
SHOW VARIABLES LIKE 'slow_query_log%';
-- 开启
SET GLOBAL slow_query_log = ON;
-- 设置阈值（超过1秒记录）
SET GLOBAL long_query_time = 1;
-- 记录未使用索引的查询
SET GLOBAL log_queries_not_using_indexes = ON;
```

### Step 2：用 EXPLAIN 分析

```sql
EXPLAIN SELECT * FROM battle_records WHERE server_id = 1 ORDER BY create_time DESC;
```

重点关注：

| 列 | 关注点 | 理想值 | 危险信号 |
|----|--------|--------|---------|
| **type** | 访问类型 | `const`/`eq_ref`/`ref`/`range` | `ALL`（全表扫描） |
| **key** | 实际使用的索引 | 索引名 | `NULL`（没用索引） |
| **rows** | 估算扫描行数 | 越小越好 | 接近全表行数 |
| **Extra** | 额外信息 | `Using index`（覆盖索引） | `Using filesort`（文件排序）/ `Using temporary`（临时表） |

### Step 3：定位根因

常见根因：
- 全表扫描 → 缺索引
- 索引失效 → 函数/类型转换/LIKE %开头/违反最左前缀
- 临时表+filesort → 多表JOIN+ORDER BY+GROUP BY
- 扫描行数过多 → 索引选择性差

### Step 4：优化

```sql
-- 原始慢查询（全表扫描）
SELECT * FROM battle_records WHERE DATE(create_time) = '2026-07-13';

-- 优化1：改写SQL避免函数（命中索引）
SELECT * FROM battle_records
WHERE create_time >= '2026-07-13 00:00:00'
  AND create_time <  '2026-07-14 00:00:00';

-- 优化2：添加索引
CREATE INDEX idx_create_time ON battle_records(create_time);

-- 优化3：只查需要的列（减少回表）
SELECT id, server_id, result FROM battle_records
WHERE create_time >= '2026-07-13 00:00:00'
  AND create_time <  '2026-07-14 00:00:00';
```

**加分话术：**
> "排查慢查询我有一套固定流程：先看 slow_query_log 找到慢SQL，然后 EXPLAIN 看 type 和 Extra，type=ALL 说明全表扫描，Extra 有 Using filesort 或 Using temporary 说明有排序和临时表。然后对症下药：缺索引加索引，索引失效改SQL，JOIN 太多考虑拆查询或加冗余字段。优化后再用 EXPLAIN 验证效果。"

---

## 【三、30天学习成果速查表】

### SQL 语法速查

```sql
-- ========== 基础 CRUD ==========
INSERT INTO players (name, level) VALUES ('张三', 1);
UPDATE players SET level = level + 1 WHERE id = 1;
DELETE FROM players WHERE id = 1;
SELECT id, name, level FROM players WHERE level >= 10 ORDER BY level DESC LIMIT 20;

-- ========== 聚合与分组 ==========
SELECT server_id, COUNT(*) AS player_count, AVG(level) AS avg_level
FROM players
GROUP BY server_id
HAVING COUNT(*) > 100;

-- ========== 多表关联 ==========
SELECT p.name, d.species_name, pd.level
FROM players p
JOIN player_dinosaurs pd ON p.id = pd.player_id
JOIN dino_species d ON pd.species_id = d.id
WHERE p.level >= 50;

-- ========== 子查询 ==========
SELECT name, level FROM players
WHERE level > (SELECT AVG(level) FROM players);

-- ========== 窗口函数 ==========
SELECT name, level,
       RANK() OVER (ORDER BY level DESC) AS rank_no
FROM players;

-- ========== 事务 ==========
BEGIN;
UPDATE players SET gold = gold - 100 WHERE id = 1;
INSERT INTO gold_log (player_id, amount, reason) VALUES (1, -100, 'buy_item');
COMMIT;  -- 或 ROLLBACK;

-- ========== 索引 ==========
CREATE INDEX idx_name ON players(name);
CREATE UNIQUE INDEX idx_phone ON players(phone);
CREATE INDEX idx_status_level ON players(status, level);  -- 复合索引

-- ========== 执行计划 ==========
EXPLAIN SELECT * FROM players WHERE name = '张三';

-- ========== 视图 ==========
CREATE VIEW v_player_summary AS
SELECT id, name, level, gold FROM players WHERE status = 1;

-- ========== 存储过程 ==========
DELIMITER //
CREATE PROCEDURE GetPlayerInfo(IN p_id INT, OUT p_level INT)
BEGIN
  SELECT level INTO p_level FROM players WHERE id = p_id;
END //
DELIMITER ;

-- ========== 触发器 ==========
CREATE TRIGGER trg_after_battle
AFTER INSERT ON battle_records
FOR EACH ROW
BEGIN
  UPDATE players SET total_battles = total_battles + 1 WHERE id = NEW.player_id;
END;

-- ========== 备份 ==========
-- 命令行：mysqldump -u root -p game_db > backup.sql
-- 恢复：mysql -u root -p game_db < backup.sql
```

### Python + MySQL 速查

```python
import pymysql

# 连接
conn = pymysql.connect(host='localhost', user='root', password='xxx',
                       database='game_db', charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

# 参数化查询（防SQL注入）
with conn.cursor() as cursor:
    cursor.execute("SELECT * FROM players WHERE level >= %s", (50,))
    rows = cursor.fetchall()

# 事务
try:
    with conn.cursor() as cursor:
        cursor.execute("UPDATE players SET gold = gold - %s WHERE id = %s", (100, 1))
        cursor.execute("INSERT INTO gold_log (player_id, amount) VALUES (%s, %s)", (1, -100))
    conn.commit()
except:
    conn.rollback()
finally:
    conn.close()
```

---

## 【四、进阶学习路线】

30天只是入门，以下是根据不同方向的进阶路线：

### 方向 A：测试开发（推荐，契合你的职业）

```
当前位置 ──► 接口自动化测试框架（pytest + requests + pymysql）
         │
         ├── 性能测试：JMeter + MySQL 监控（SHOW PROCESSLIST / Performance Schema）
         ├── 数据工厂：自动生成测试数据 + 数据隔离方案
         ├── CI/CD：Jenkins/GitLab CI 中集成数据库测试
         └── 数据库迁移测试：Flyway/Liquibase 验证
```

### 方向 B：数据库管理员（DBA）

```
当前位置 ──► MySQL 高可用（主从复制 / 读写分离）
         │
         ├── MHA / Orchestrator 故障切换
         ├── MySQL Shell / MySQL Router
         ├── 分库分表（ShardingSphere / MyCAT）
         ├── Performance Schema / sys 库深度监控
         └── MySQL 8.0 新特性（窗口函数 / CTE / JSON增强 / 不可见索引）
```

### 方向 C：后端开发

```
当前位置 ──► ORM 框架（SQLAlchemy / Django ORM / MyBatis）
         │
         ├── 连接池（Druid / HikariCP）
         ├── 读写分离中间件
         ├── 分布式事务（XA / TCC / Saga）
         └── 缓存策略（Redis + MySQL 数据一致性）
```

### 推荐学习资源

| 资源 | 说明 |
|------|------|
| MySQL 8.0 官方文档 | https://dev.mysql.com/doc/refman/8.0/en/ |
| 《高性能MySQL》第三版 | 索引优化/查询优化/架构设计的圣经 |
| 《MySQL是怎样运行的》 | 底层原理通俗易懂，推荐入门后读 |
| MySQL Performance Blog | Percona团队的博客，实战性强 |
| LeetCode 数据库题 | SQL练习，按难度刷 |

---

## 【五、30天学习回顾——你的成长轨迹】

| 阶段 | 天数 | 你学会了什么 |
|------|------|-------------|
| **入门** | Day 1-3 | 安装MySQL、建库建表、增删改查基础 |
| **查询** | Day 4-7 | 条件排序、聚合分组、多表关联、子查询 |
| **进阶** | Day 8-14 | 集合操作、函数库、视图、索引、事务与锁 |
| **高级** | Day 15-21 | 存储过程、触发器、权限、表设计、范式、安全、备份 |
| **实战** | Day 22-28 | 电商库设计、游戏库设计、Python操作、pytest测试、慢查询优化 |
| **测试** | Day 29-30 | 接口后DB验证、数据一致性、数据工厂、知识总结 |

> 这30天你从"SELECT *是什么"走到了能分析EXPLAIN执行计划、能写pytest数据库测试用例、能做慢查询优化。对一个游戏测试人员来说，这个数据库能力已经超过90%的同行了。

---

## 【注意事项/易错点】

### 面试中常见误区

1. **"索引越多越好"** → ❌ 索引提升读性能但降低写性能，且占用磁盘空间。OLTP系统建议单表索引不超过5个。

2. **"COUNT(1) 比 COUNT(*) 快"** → ❌ 这是老版本MyISAM的遗留误区，InnoDB下两者性能几乎一样，且MySQL优化器对COUNT(*)做了专门优化。

3. **"MySQL 默认隔离级别是 READ COMMITTED"** → ❌ MySQL InnoDB 默认是 **REPEATABLE READ**，这是MySQL区别于Oracle/PostgreSQL的地方。

4. **"有了索引就不会全表扫描"** → ❌ 索引可能失效（函数、类型转换、LIKE %开头等），必须用EXPLAIN验证。

5. **"TRUNCATE 和 DELETE 一样，都能ROLLBACK"** → ❌ TRUNCATE是DDL，隐式提交，不可回滚。

### 面试加分技巧

- **主动画图**：讲到B+树、事务隔离时，主动在纸上画图，展示你的理解深度
- **结合项目**：回答时结合恐龙岛项目的真实场景，比如"在我们项目里，战斗记录表用了RANGE分区..."
- **承认不知道**：遇到不会的，说"这个我还没深入研究，但我的理解是...，回去我会确认"，比胡编好
- **反问**：回答后问"你们项目中遇到的最复杂的SQL优化场景是什么？"展示学习意愿

---

## 【今日练习题】

### 练习1：模拟面试自测

不看上面的答案，尝试用自己的话回答以下5个问题，每个限时2分钟：

1. MySQL InnoDB 的索引是什么数据结构？为什么？
2. ACID 四大特性分别靠什么机制实现的？
3. 什么情况下索引会失效？举3个例子。
4. DELETE、TRUNCATE、DROP 的区别？
5. 如何排查一条慢查询？说完整流程。

> 对比答案，看哪些点漏了，查漏补缺。

### 练习2：综合SQL实战

基于恐龙岛项目，写一条SQL：**查询每个服务器战力前10的玩家，显示玩家名、恐龙种类名、恐龙等级、战斗力，并标注排名。**

要求：
- 用到多表 JOIN（players + player_dinosaurs + dino_species）
- 用到窗口函数（RANK()）
- 用到子查询或 CTE

```sql
-- 你的答案写在这里，然后对比下面的参考答案
```

<details>
<summary>📝 参考答案（先自己写再看）</summary>

```sql
WITH ranked_dinos AS (
  SELECT
    p.server_id,
    p.name AS player_name,
    d.species_name,
    pd.level AS dino_level,
    pd.combat_power,
    RANK() OVER (
      PARTITION BY p.server_id
      ORDER BY pd.combat_power DESC
    ) AS server_rank
  FROM players p
  JOIN player_dinosaurs pd ON p.id = pd.player_id
  JOIN dino_species d ON pd.species_id = d.id
  WHERE p.status = 1
)
SELECT * FROM ranked_dinos
WHERE server_rank <= 10
ORDER BY server_id, server_rank;
```
</details>

---

## 【一句话总结】

> **30天MySQL之旅，从"SELECT *"到"EXPLAIN优化"，从"建表"到"设计游戏数据库"——你已经具备了测试工程师需要的全部数据库能力，面试中能答、工作中能写、出问题能查。剩下的就是在实战中不断打磨。**

---

## 🎉 30天MySQL学习毕业证书

```
╔══════════════════════════════════════════════════╗
║                                                  ║
║          🏆 MySQL 30天系统学习                    ║
║                                                  ║
║            毕 业 证 书                            ║
║                                                  ║
║    涂伟富 同学：                                   ║
║                                                  ║
║    已完成30天MySQL系统学习全部课程，                ║
║    内容涵盖基础CRUD、进阶查询、索引优化、           ║
║    事务锁机制、存储过程触发器、数据库设计、         ║
║    SQL注入安全、Python+pytest自动化测试、          ║
║    慢查询优化等30个主题。                          ║
║                                                  ║
║    具备以下能力：                                  ║
║    ✅ 独立设计游戏/电商数据库                       ║
║    ✅ 编写复杂多表关联查询与窗口函数                 ║
║    ✅ 使用EXPLAIN分析并优化慢查询                   ║
║    ✅ Python+pytest编写数据库自动化测试             ║
║    ✅ 应对MySQL面试高频问题                         ║
║                                                  ║
║    完成日期：2026-07-13                            ║
║                                                  ║
╚══════════════════════════════════════════════════╝
```

> 🚀 接下来该做什么？把30天学到的知识用在恐龙岛项目测试中——写接口测试的数据库断言、做性能测试的数据准备、排查慢查询。**知识不用就会忘，用了才是你的。**
