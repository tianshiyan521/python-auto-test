🐬 今日MySQL学习 · Day 5/30
**主题**：查询进阶 - 聚合与分组

---

## 【学习目标】

- 掌握5大聚合函数（COUNT / SUM / AVG / MAX / MIN）的用法与区别
- 理解 GROUP BY 分组查询的原理和书写顺序
- 掌握 HAVING 子句对分组结果进行筛选（与 WHERE 的区别）

---

## 【核心语法】

### 1. 五大聚合函数

```sql
-- COUNT：统计行数
SELECT COUNT(*) FROM players;                -- 统计所有行（含NULL）
SELECT COUNT(level) FROM players;            -- 统计level非NULL的行数
SELECT COUNT(DISTINCT server_id) FROM players; -- 统计不同服务器数

-- SUM：求和
SELECT SUM(gold) FROM players;               -- 所有玩家金币总和

-- AVG：求平均值
SELECT AVG(level) FROM players;              -- 平均等级（含小数）

-- MAX / MIN：最大值 / 最小值
SELECT MAX(level), MIN(level) FROM players;  -- 最高等级和最低等级
```

### 2. GROUP BY 分组查询

```sql
-- 基本分组：按单个字段分组
SELECT server_id, COUNT(*) AS player_count
FROM players
GROUP BY server_id;

-- 按多个字段分组
SELECT server_id, vip_level, COUNT(*) AS player_count
FROM players
GROUP BY server_id, vip_level;

-- 分组 + 聚合
SELECT server_id, AVG(level) AS avg_level, SUM(gold) AS total_gold
FROM players
GROUP BY server_id;
```

### 3. HAVING 子句：对分组结果筛选

```sql
-- 查找玩家数超过100的服务器
SELECT server_id, COUNT(*) AS player_count
FROM players
GROUP BY server_id
HAVING player_count > 100;

-- WHERE + GROUP BY + HAVING 组合使用
SELECT server_id, COUNT(*) AS player_count, AVG(level) AS avg_level
FROM players
WHERE status = 'active'          -- 先筛选行（分组前）
GROUP BY server_id               -- 再分组
HAVING avg_level >= 30;          -- 最后筛选组（分组后）
```

### 4. SQL 子句执行顺序（重要！）

```sql
-- 书写顺序
SELECT → FROM → WHERE → GROUP BY → HAVING → ORDER BY → LIMIT

-- 执行顺序（MySQL实际处理顺序）
FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT

-- 记忆口诀：先找表( FROM ) → 再筛行( WHERE ) → 然后分组( GROUP BY )
-- → 再筛组( HAVING ) → 选列( SELECT ) → 排序( ORDER BY ) → 截取( LIMIT )
```

---

## 【实战示例】

### 示例1：基础 - 统计《山海之巅》各服务器玩家情况

```sql
-- 建表（如果还没建的话）
CREATE TABLE shanhai_players (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,
    server_id INT,
    level INT DEFAULT 1,
    gold DECIMAL(12,2) DEFAULT 0,
    vip_level INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active',
    register_date DATE
);

-- 统计每个服务器的玩家数、平均等级、总金币
SELECT
    server_id,
    COUNT(*) AS player_count,
    ROUND(AVG(level), 1) AS avg_level,
    SUM(gold) AS total_gold
FROM shanhai_players
WHERE status = 'active'
GROUP BY server_id
ORDER BY player_count DESC;
```

### 示例2：进阶 - HAVING 筛选 + 多字段分组

```sql
-- 找出平均等级 >= 40 且玩家数 >= 5 的服务器-VIP组合
SELECT
    server_id,
    vip_level,
    COUNT(*) AS player_count,
    ROUND(AVG(level), 1) AS avg_level,
    MAX(gold) AS richest_gold
FROM shanhai_players
WHERE status = 'active'
GROUP BY server_id, vip_level
HAVING avg_level >= 40 AND player_count >= 5
ORDER BY server_id, vip_level;
```

### 示例3：工作场景 - 游戏测试数据验证

```sql
-- 场景：测试"每日充值统计"功能，验证数据库中的充值记录是否正确

-- 假设有充值表
CREATE TABLE recharge_records (
    id INT PRIMARY KEY AUTO_INCREMENT,
    player_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    recharge_date DATE NOT NULL,
    channel VARCHAR(30)           -- 充值渠道：微信/支付宝/苹果内购
);

-- ① 按日期统计总充值金额和充值人数
SELECT
    recharge_date,
    COUNT(*) AS recharge_count,
    COUNT(DISTINCT player_id) AS unique_payers,
    SUM(amount) AS total_amount,
    ROUND(AVG(amount), 2) AS avg_amount
FROM recharge_records
GROUP BY recharge_date
ORDER BY recharge_date;

-- ② 找出单日充值总额超过 10000 的高峰日
SELECT
    recharge_date,
    SUM(amount) AS daily_total
FROM recharge_records
GROUP BY recharge_date
HAVING daily_total > 10000
ORDER BY daily_total DESC;

-- ③ 按渠道统计，只看大R玩家（充值总额 >= 1000）
SELECT
    channel,
    player_id,
    SUM(amount) AS total_paid
FROM recharge_records
GROUP BY channel, player_id
HAVING total_paid >= 1000
ORDER BY total_paid DESC;

-- ④ 测试验证：检查是否有重复充值记录（同一玩家同一天同渠道同金额）
SELECT
    recharge_date, player_id, channel, amount, COUNT(*) AS cnt
FROM recharge_records
GROUP BY recharge_date, player_id, channel, amount
HAVING cnt > 1;
```

---

## 【注意事项/易错点】

### 1. SELECT 中的非聚合列必须出现在 GROUP BY 中
```sql
-- ❌ 错误：name 没有在 GROUP BY 中，结果不确定
SELECT server_id, name, COUNT(*) FROM players GROUP BY server_id;

-- ✅ 正确：要么加进 GROUP BY，要么用聚合函数
SELECT server_id, COUNT(*) FROM players GROUP BY server_id;
SELECT server_id, MAX(name) FROM players GROUP BY server_id;
```

### 2. WHERE 和 HAVING 的区别（高频考点！）

| 对比项 | WHERE | HAVING |
|--------|-------|--------|
| 作用时机 | 分组**前**筛选行 | 分组**后**筛选组 |
| 能否用聚合函数 | ❌ 不能 | ✅ 可以 |
| 作用于 | 单行数据 | 分组后的结果 |

```sql
-- ❌ 错误：WHERE 里不能用聚合函数
SELECT server_id, COUNT(*) AS cnt FROM players WHERE cnt > 10 GROUP BY server_id;

-- ✅ 正确：HAVING 里才能用聚合函数
SELECT server_id, COUNT(*) AS cnt FROM players GROUP BY server_id HAVING cnt > 10;
```

### 3. COUNT(*) vs COUNT(列名) vs COUNT(DISTINCT 列名)
- `COUNT(*)` — 统计所有行，包括 NULL
- `COUNT(列名)` — 统计该列非 NULL 的行数
- `COUNT(DISTINCT 列名)` — 统计该列不同值的个数（去重）

### 4. 聚合函数自动忽略 NULL
```sql
-- 如果 gold 列有 NULL 值，AVG(gold) 会自动跳过 NULL 行
-- 这可能导致 AVG 结果 != SUM / COUNT(*)，而是 SUM / COUNT(非NULL行数)
```

---

## 【今日练习题】

### 练习1：基础分组统计
在 `shanhai_players` 表中，查询每个 VIP 等级的玩家数量和平均等级，按玩家数量降序排列。

```sql
-- 期待输出：vip_level | player_count | avg_level
-- 提示：GROUP BY vip_level，ORDER BY player_count DESC
```

### 练习2：HAVING 综合查询
在 `recharge_records` 表中，找出充值天数 >= 3 天的玩家（即在不同日期有充值记录的天数 >= 3），显示玩家ID、充值天数、总充值金额，按总金额降序。

```sql
-- 提示：GROUP BY player_id，用 COUNT(DISTINCT recharge_date) 算天数，HAVING 筛选
```

---

## 【一句话总结】

GROUP BY 把数据"分桶"，聚合函数在每个桶里做计算，HAVING 则负责把不合格的桶扔掉——记住"先筛行(WHERE) → 再分组(GROUP BY) → 最后筛组(HAVING)"的执行顺序就不会错。
