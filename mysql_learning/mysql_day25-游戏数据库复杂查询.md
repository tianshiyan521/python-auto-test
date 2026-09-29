# 🐬 今日MySQL学习 · Day 25/30

**主题**：实战：游戏数据库复杂查询（排行榜、战力统计、装备分布、玩家留存分析SQL）

---

## 【学习目标】
- 掌握游戏项目常见复杂查询场景：排行榜、战力统计、装备分布、玩家留存。
- 熟练使用 `JOIN`、`GROUP BY`、`窗口函数`、`子查询`、`CASE WHEN` 组合解决业务问题。
- 结合《恐龙岛》项目背景，写出可直接运行的复杂业务查询 SQL。

---

## 【核心语法】

### 1. 排行榜查询（RANK / DENSE_RANK / ROW_NUMBER）
```sql
-- 三种排名窗口函数区别
SELECT
    player_id,
    power,
    RANK()       OVER (ORDER BY power DESC) AS rank_gap,      -- 并列跳号：1,1,3
    DENSE_RANK() OVER (ORDER BY power DESC) AS rank_no_gap,   -- 并列不跳号：1,1,2
    ROW_NUMBER() OVER (ORDER BY power DESC) AS row_num        -- 强制唯一：1,2,3
FROM player_dinosaurs;
```

### 2. 战力统计（聚合 + 分组 + HAVING）
```sql
-- 按服务器统计玩家战力分布
SELECT
    server_id,
    COUNT(*)                    AS player_count,
    SUM(total_power)            AS server_power,
    AVG(total_power)            AS avg_power,
    MAX(total_power)            AS top_power,
    MIN(total_power)            AS min_power
FROM players
GROUP BY server_id
HAVING COUNT(*) > 10
ORDER BY server_power DESC;
```

### 3. 装备分布统计（多表关联 + 分组）
```sql
-- 统计各品质装备持有数量
SELECT
    i.quality,
    COUNT(*)              AS total_count,
    COUNT(DISTINCT p.player_id) AS owner_count,
    ROUND(AVG(i.item_level), 1) AS avg_level
FROM player_items i
JOIN players p ON i.player_id = p.player_id
GROUP BY i.quality
ORDER BY FIELD(i.quality, 'SSR', 'SR', 'R', 'N');
```

### 4. 玩家留存分析（日期函数 + 自连接）
```sql
-- 次日留存：注册后第2天仍有登录的玩家占比
SELECT
    DATE(create_time) AS register_date,
    COUNT(DISTINCT p.player_id) AS register_count,
    COUNT(DISTINCT l2.player_id) AS retain_1d_count,
    ROUND(
        COUNT(DISTINCT l2.player_id) * 100.0 / COUNT(DISTINCT p.player_id),
        2
    ) AS retention_1d_rate
FROM players p
LEFT JOIN login_log l1
    ON p.player_id = l1.player_id
    AND DATE(l1.login_time) = DATE(p.create_time)
LEFT JOIN login_log l2
    ON p.player_id = l2.player_id
    AND DATE(l2.login_time) = DATE_ADD(DATE(p.create_time), INTERVAL 1 DAY)
GROUP BY DATE(create_time)
ORDER BY register_date DESC;
```

### 5. 窗口函数分桶 / 占比
```sql
-- 战力前10%玩家识别
SELECT
    player_id,
    total_power,
    NTILE(10) OVER (ORDER BY total_power DESC) AS power_decile
FROM players;
```

---

## 【实战示例】

### 示例 1：基础示例 — 玩家战力 TOP 100 排行榜

基于 Day 24 创建的 `players` 表：

```sql
SELECT
    p.player_id,
    p.nickname,
    p.server_id,
    p.total_power,
    p.vip_level,
    RANK() OVER (ORDER BY p.total_power DESC) AS power_rank
FROM players p
WHERE p.status = 'active'
ORDER BY p.total_power DESC
LIMIT 100;
```

输出说明：
- 用 `RANK()` 处理并列战力；并列玩家排名相同，后续跳号。
- 如需连续排名（1,1,2），改用 `DENSE_RANK()`。
- 适合游戏内“全服排行榜”或“领地争夺排名”。

---

### 示例 2：进阶示例 — 恐龙战力分布与服务器占比

```sql
-- 各服务器 SSR 恐龙平均战力、最高战力、占比
WITH server_stats AS (
    SELECT
        p.server_id,
        COUNT(pd.dinosaur_id) AS ssr_count,
        AVG(pd.power)         AS avg_ssr_power,
        MAX(pd.power)         AS max_ssr_power
    FROM players p
    JOIN player_dinosaurs pd ON p.player_id = pd.player_id
    WHERE pd.quality = 'SSR'
      AND pd.status = 'active'
    GROUP BY p.server_id
),
total AS (
    SELECT SUM(ssr_count) AS total_ssr FROM server_stats
)
SELECT
    s.server_id,
    s.ssr_count,
    ROUND(s.avg_ssr_power, 0) AS avg_ssr_power,
    s.max_ssr_power,
    ROUND(s.ssr_count * 100.0 / t.total_ssr, 2) AS ssr_ratio_pct
FROM server_stats s
CROSS JOIN total t
ORDER BY s.avg_ssr_power DESC;
```

业务价值：
- 快速识别哪个服务器高战恐龙集中，辅助合服或运营活动决策。
- 窗口函数 + CTE 组合可读性高，避免多层嵌套。

---

### 示例 3：工作/测试场景示例 — 领地争夺战斗胜率 + 装备持有交叉分析

```sql
-- 领地争夺中胜率前20的玩家，及其装备品质分布
WITH win_rate AS (
    SELECT
        attacker_id AS player_id,
        COUNT(*) AS total_battle,
        SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) AS win_count,
        ROUND(
            SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
            2
        ) AS win_rate_pct
    FROM battle_records
    WHERE battle_type = 'territory'
    GROUP BY attacker_id
    HAVING COUNT(*) >= 5
),
top_players AS (
    SELECT player_id, win_rate_pct
    FROM win_rate
    ORDER BY win_rate_pct DESC, total_battle DESC
    LIMIT 20
)
SELECT
    tp.player_id,
    p.nickname,
    tp.win_rate_pct,
    SUM(CASE WHEN i.quality = 'SSR' THEN 1 ELSE 0 END) AS ssr_count,
    SUM(CASE WHEN i.quality = 'SR'  THEN 1 ELSE 0 END) AS sr_count,
    SUM(CASE WHEN i.quality = 'R'   THEN 1 ELSE 0 END) AS r_count,
    ROUND(AVG(i.item_level), 1) AS avg_item_level
FROM top_players tp
JOIN players p ON tp.player_id = p.player_id
LEFT JOIN player_items i ON tp.player_id = i.player_id
GROUP BY tp.player_id, p.nickname, tp.win_rate_pct
ORDER BY tp.win_rate_pct DESC;
```

测试关注点：
- `battle_records` 表数据量可能巨大，确认 `battle_type` + `attacker_id` 有复合索引。
- `HAVING COUNT(*) >= 5` 过滤“低场次”玩家，避免 1 场 100% 胜率拉偏排名。
- 可用 EXPLAIN 检查是否走索引，避免全表扫描。

---

### 示例 4：留存分析扩展 — 7日留存与流失玩家名单

```sql
-- 按注册日期计算次日、7日留存率
SELECT
    DATE(p.create_time) AS register_date,
    COUNT(DISTINCT p.player_id) AS register_count,
    COUNT(DISTINCT IF(DATE(l.login_time) = DATE_ADD(DATE(p.create_time), INTERVAL 1 DAY), p.player_id, NULL)) AS d1_retained,
    COUNT(DISTINCT IF(DATE(l.login_time) = DATE_ADD(DATE(p.create_time), INTERVAL 7 DAY), p.player_id, NULL)) AS d7_retained,
    ROUND(
        COUNT(DISTINCT IF(DATE(l.login_time) = DATE_ADD(DATE(p.create_time), INTERVAL 1 DAY), p.player_id, NULL))
        * 100.0 / COUNT(DISTINCT p.player_id),
        2
    ) AS d1_retention_rate,
    ROUND(
        COUNT(DISTINCT IF(DATE(l.login_time) = DATE_ADD(DATE(p.create_time), INTERVAL 7 DAY), p.player_id, NULL))
        * 100.0 / COUNT(DISTINCT p.player_id),
        2
    ) AS d7_retention_rate
FROM players p
LEFT JOIN login_log l ON p.player_id = l.player_id
GROUP BY DATE(p.create_time)
ORDER BY register_date DESC;
```

> 注：需要已存在 `login_log(player_id, login_time)` 表。如未创建，可参考 Day 24 补充。

---

## 【注意事项/易错点】

- **窗口函数 `ORDER BY` 与最终 `ORDER BY` 混淆**：窗口函数内的 `ORDER BY` 仅决定排名顺序，最终查询结果仍需外层 `ORDER BY` 排序。
- **留存分析自连接容易产⽣笛卡尔积**：对 `login_log` 按日期去重后再连接，避免同一玩家一天多次登录导致重复计算。
- **分组字段必须与 SELECT 中非聚合字段一致**：MySQL 默认模式下允许 `ONLY_FULL_GROUP_BY` 关闭，但测试环境建议开启，避免隐藏 Bug。
- **百分比除零**：`COUNT(*)` 为 0 时直接除会报错，先用 `NULLIF` 或 `HAVING` 过滤。
- **排行榜并列处理**：`RANK()` 跳号、`DENSE_RANK()` 不跳号、`ROW_NUMBER()` 唯一，根据发奖规则选择。

---

## 【今日练习题】

1. **排行榜练习**：在本地 `players` 表中，写出查询“每个服务器战力前 10 名”的 SQL，要求相同战力并列排名且不跳号（用 `DENSE_RANK()`）。

2. **留存练习**：基于 `players` 和 `login_log` 表，计算最近 7 天每天的注册人数、次日留存率、3日留存率，并找出 3 日未登录的玩家名单（流失预警）。

3. **装备分布练习**：统计每个玩家拥有的 SSR 装备数量，并按 SSR 装备数量降序输出前 50 名，结合玩家昵称与服务器。

---

## 【一句话总结】

游戏复杂查询的核心是“业务指标 = 正确的聚合 + 合理的窗口函数 + 精准的日期/关联条件”，写完后务必用 EXPLAIN 验证执行计划。
