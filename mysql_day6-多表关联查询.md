# 🐬 今日MySQL学习 · Day 6/30

**主题**：多表关联查询（INNER JOIN、LEFT JOIN、RIGHT JOIN、CROSS JOIN、多表关联原理）

---

## 【学习目标】
- 理解为什么需要多表关联 — 实际项目中数据几乎不会只存在一张表里
- 掌握四种 JOIN 类型及其核心区别（谁为主表、匹配不到怎么处理）
- 学会多表关联的写法（2表、3表及以上），避免写出错误的笛卡尔积

---

## 【核心语法】

### 1. INNER JOIN（内连接）— 取交集
```sql
-- 只返回两张表中都匹配到的行
-- 结果 = 两表交集
SELECT a.player_name, b.item_name
FROM player a
INNER JOIN backpack b ON a.player_id = b.player_id;
-- 说明：只查出有背包物品的玩家，没物品的玩家不出现
```

### 2. LEFT JOIN（左连接）— 左表全保留
```sql
-- 左表（FROM后面的表）所有行都保留
-- 右表匹配不到的行用 NULL 填充
SELECT a.player_name, b.item_name
FROM player a
LEFT JOIN backpack b ON a.player_id = b.player_id;
-- 说明：所有玩家都显示，没物品的玩家 item_name 为 NULL
```

### 3. RIGHT JOIN（右连接）— 右表全保留
```sql
-- 右表（JOIN后面的表）所有行都保留
-- 左表匹配不到的行用 NULL 填充
SELECT a.player_name, b.item_name
FROM player a
RIGHT JOIN backpack b ON a.player_id = b.player_id;
-- 说明：所有背包物品都显示，如果物品的玩家已删除，player_name 为 NULL
-- 实际开发中 RIGHT JOIN 较少用，通常用 LEFT JOIN 换一下表顺序即可
```

### 4. CROSS JOIN（交叉连接）— 笛卡尔积
```sql
-- 每行 × 每行，结果行数 = 左表行数 × 右表行数
-- 一般不单独用，除非确实需要全排列
SELECT a.player_name, b.skin_name
FROM player a
CROSS JOIN skin b;
-- 如果有 100 个玩家、50 款皮肤 → 结果 5000 行 → 小心数据爆炸！
```

### 5. 多表关联（3表及以上）
```sql
-- 查：玩家名 + 装备名 + 装备属性
SELECT p.player_name, e.equip_name, e.attack_power, e.defense_power
FROM player p
INNER JOIN backpack bp ON p.player_id = bp.player_id
INNER JOIN equipment e ON bp.equip_id = e.equip_id
WHERE e.attack_power > 100;
-- 链条：player → backpack（中间表） → equipment
```

### 6. 自连接（同一张表自己 JOIN 自己）
```sql
-- 查每个玩家的推荐人是谁（推荐人也在同一张 player 表里）
SELECT p1.player_name AS '玩家', p2.player_name AS '推荐人'
FROM player p1
LEFT JOIN player p2 ON p1.referrer_id = p2.player_id;
```

---

## 【实战示例】

### 示例1：基础 INNER JOIN — 查有装备的玩家
```sql
-- 场景：查拥有装备的玩家及其装备名称
-- 表结构：
-- player(player_id, player_name, level)
-- equipment(equip_id, equip_name, attack_power)
-- backpack(backpack_id, player_id, equip_id, quantity)

SELECT p.player_name, e.equip_name, bp.quantity
FROM player p
INNER JOIN backpack bp ON p.player_id = bp.player_id
INNER JOIN equipment e ON bp.equip_id = e.equip_id
ORDER BY p.level DESC;

-- 预期结果：只有背包里真的有装备的玩家才出现
```

### 示例2：LEFT JOIN — 找出没装备的"白板"玩家（测试常用！）
```sql
-- 场景：测试需要验证新玩家初始状态是否真的是空背包
SELECT p.player_id, p.player_name, bp.equip_id
FROM player p
LEFT JOIN backpack bp ON p.player_id = bp.player_id
WHERE bp.equip_id IS NULL;

-- 结果就是所有背包为空的玩家
-- 这是测试数据验证的常用模式！
```

### 示例3：工作场景 — 验证充值记录与订单表的一致性
```sql
-- 场景：《山海之巅》项目中，检查充值流水表(recharge)和订单表(orders)是否一致
-- 找出 "有充值记录但没有对应订单" 的异常数据

SELECT r.recharge_id, r.player_id, r.amount, r.recharge_time, o.order_id
FROM recharge r
LEFT JOIN orders o ON r.order_id = o.order_id
WHERE o.order_id IS NULL;

-- 如果查出数据 → 说明有 bug：充值成功但订单没生成
-- 这就是多表关联在测试工作中的典型应用！
```

### 示例4：多表关联 — 排行榜综合查询
```sql
-- 场景：查战力前10的玩家，同时显示他们的装备数和公会名
SELECT 
    p.player_name,
    p.combat_power,
    COUNT(bp.backpack_id) AS equip_count,
    g.guild_name
FROM player p
LEFT JOIN backpack bp ON p.player_id = bp.player_id
LEFT JOIN guild g ON p.guild_id = g.guild_id
GROUP BY p.player_id, p.player_name, p.combat_power, g.guild_name
ORDER BY p.combat_power DESC
LIMIT 10;
-- 注意：用了 LEFT JOIN 而不是 INNER JOIN，即使没公会/没装备也显示
```

---

## 【注意事项/易错点】

### 易错点1：JOIN 条件写错 → 笛卡尔积灾难
```sql
-- ❌ 错误：忘记写 ON 条件
SELECT * FROM player, backpack;  -- 产生所有组合，数据爆炸

-- ✅ 正确：必须写 ON 或 USING
SELECT * FROM player p INNER JOIN backpack bp ON p.player_id = bp.player_id;
```

### 易错点2：LEFT JOIN 时 WHERE 条件位置错 — 把外连接"退化"成内连接
```sql
-- ❌ 错误：在 WHERE 里过滤右表 NULL 不可为的行
SELECT p.player_name, bp.equip_id
FROM player p
LEFT JOIN backpack bp ON p.player_id = bp.player_id
WHERE bp.equip_id = 1001;  -- 这会把没有装备的玩家全干掉，退化成 INNER JOIN

-- ✅ 正确：右表条件写在 ON 里
SELECT p.player_name, bp.equip_id
FROM player p
LEFT JOIN backpack bp ON p.player_id = bp.player_id AND bp.equip_id = 1001;
-- 这样所有玩家保留，只有 equip_id=1001 的行才匹配
```

### 易错点3：INNER JOIN 多表时，中间表缺失导致整个链条断裂
```sql
-- 如果某个玩家在 backpack 里没记录，
-- 那即使有 equipment，这条连查也会被 INNER JOIN 吞掉
-- 解决方案：核心路径用 LEFT JOIN，再用 WHERE IS NOT NULL 类逻辑兜底
```

### 性能提醒
- JOIN 字段必须有索引！player_id、equip_id 这类关联键一定要建索引
- 多表 JOIN 时先过滤再关联，减少临时表大小
- 能用 INNER JOIN 就别用 LEFT JOIN，驱动表更小

---

## 【JOIN 类型速查图】

```
INNER JOIN：   A ∩ B         — 只取交集
LEFT JOIN：    A + (A ∩ B)   — A全要，B匹配不到就NULL
RIGHT JOIN：   B + (A ∩ B)   — B全要，A匹配不到就NULL
CROSS JOIN：   A × B         — 笛卡尔积，每行配每行
```

---

## 【今日练习题】

### 练习题1：刷怪记录统计
假设有两张表：
- `player(player_id, player_name, level)` — 玩家表
- `battle_log(log_id, player_id, monster_name, kill_time, damage)` — 战斗记录表

请写出SQL：**查出所有玩家最近一次击杀的怪物名称和伤害值**。

> 提示：可能需要子查询或先理解"最近一次"怎么取。

### 练习题2：数据完整性检查（测试实战）
还是上面的表结构，请写出SQL：**找出"存在战斗记录但没有对应玩家信息"的异常数据**。这种数据在删号后可能出现。

---

## 【一句话总结】
> **多表关联就是"通过共同字段把分散在不同表里的数据串起来"，核心是分清"谁是主表、匹配不到咋办"，LEFT JOIN 保留主表全部、INNER JOIN 只取交集、WHERE 条件写在 ON 里还是 ON 外效果完全不同。**
