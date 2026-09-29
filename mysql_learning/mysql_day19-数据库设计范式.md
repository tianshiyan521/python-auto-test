# 🐬 今日MySQL学习 · Day 19/30
**主题**：数据库设计范式

---

## 【学习目标】

- 理解第一、二、三范式的定义与判断方法，能识别表设计中的范式违规
- 掌握反范式设计的适用场景——什么时候故意"违反范式"反而更优
- 结合游戏项目，在实际表设计中做出范式与性能的取舍决策

---

## 【核心语法】

范式不是"语法"，而是**设计原则**。这里用表格对比展示三种范式：

### 第一范式（1NF）—— 属性不可再分

```
-- ❌ 违反1NF：equipment字段存了多个值（逗号分隔）
CREATE TABLE players_bad (
    player_id INT,
    name VARCHAR(50),
    equipment VARCHAR(200)  -- "剑,盾,头盔,铠甲" → 不是原子值！
);

-- ✅ 满足1NF：每个字段只存一个值，多装备拆到关联表
CREATE TABLE players (
    player_id INT PRIMARY KEY,
    name VARCHAR(50),
    level INT
);

CREATE TABLE player_equipment (
    id INT PRIMARY KEY AUTO_INCREMENT,
    player_id INT,
    equip_name VARCHAR(50),
    equip_level INT
);
```

### 第二范式（2NF）—— 消除部分依赖

```
-- ❌ 违反2NF：order_detail表中，product_name只依赖product_id，不依赖联合主键(order_id + product_id)
CREATE TABLE order_details_bad (
    order_id INT,           -- 联合主键的一部分
    product_id INT,         -- 联合主键的一部分
    product_name VARCHAR(100),  -- 只依赖product_id → 部分依赖！
    quantity INT,
    price DECIMAL(10,2),
    PRIMARY KEY (order_id, product_id)
);

-- ✅ 满足2NF：product_name拆到独立的商品表
CREATE TABLE products (
    product_id INT PRIMARY KEY,
    product_name VARCHAR(100),
    base_price DECIMAL(10,2)
);

CREATE TABLE order_items (
    order_id INT,
    product_id INT,
    quantity INT,
    price DECIMAL(10,2),     -- 下单时的实际价格
    PRIMARY KEY (order_id, product_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);
```

### 第三范式（3NF）—— 消除传递依赖

```
-- ❌ 违反3NF：server_name依赖server_id，而server_id依赖player_id → 传递依赖
CREATE TABLE players_bad (
    player_id INT PRIMARY KEY,
    name VARCHAR(50),
    server_id INT,
    server_name VARCHAR(50)  -- 通过server_id→server_name，间接依赖player_id
);

-- ✅ 满足3NF：server_name拆到独立的服务器表
CREATE TABLE servers (
    server_id INT PRIMARY KEY,
    server_name VARCHAR(50),
    region VARCHAR(20)
);

CREATE TABLE players (
    player_id INT PRIMARY KEY,
    name VARCHAR(50),
    server_id INT,
    FOREIGN KEY (server_id) REFERENCES servers(server_id)
);
```

---

## 【实战示例】

### 1. 基础示例：识别一张表的范式违规

```sql
-- 原始"糟糕"的学生表，逐步拆解到3NF

-- ❌ 违反1NF：hobbies存了多个值
-- ❌ 违反2NF：college_name和college_address只依赖college_id
-- ❌ 违反3NF：college_address通过college_id传递依赖student_id
CREATE TABLE students_bad (
    student_id INT PRIMARY KEY,
    name VARCHAR(50),
    college_id INT,
    college_name VARCHAR(100),
    college_address VARCHAR(200),
    hobbies VARCHAR(500)  -- "篮球,编程,摄影"
);

-- ✅ 拆解后的3NF设计
CREATE TABLE colleges (
    college_id INT PRIMARY KEY,
    college_name VARCHAR(100),
    college_address VARCHAR(200)
);

CREATE TABLE students (
    student_id INT PRIMARY KEY,
    name VARCHAR(50),
    college_id INT,
    FOREIGN KEY (college_id) REFERENCES colleges(college_id)
);

CREATE TABLE student_hobbies (
    student_id INT,
    hobby VARCHAR(30),
    PRIMARY KEY (student_id, hobby),
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);
```

### 2. 进阶示例：恐龙岛项目——从"大杂烩表"到范式化设计

```sql
-- ❌ 游戏初期常见的"一张大表"（违反1NF+2NF+3NF）
CREATE TABLE dinosaur_records_bad (
    record_id INT PRIMARY KEY AUTO_INCREMENT,
    player_id INT,
    player_name VARCHAR(50),
    server_id INT,
    server_name VARCHAR(50),
    dino_ids VARCHAR(200),     -- "101,205,333" → 1NF违规
    dino_names VARCHAR(500),   -- "霸王龙,三角龙,翼龙" → 1NF违规
    battle_date DATE,
    battle_result VARCHAR(20),
    territory_name VARCHAR(50),  -- 只依赖territory_id → 2NF违规
    territory_id INT             -- 通过territory_id→territory_name → 3NF违规
);

-- ✅ 范式化拆解（3NF）
CREATE TABLE servers (
    server_id INT PRIMARY KEY,
    server_name VARCHAR(50),
    region VARCHAR(20)
);

CREATE TABLE territories (
    territory_id INT PRIMARY KEY,
    territory_name VARCHAR(50),
    territory_type VARCHAR(20),
    server_id INT,
    FOREIGN KEY (server_id) REFERENCES servers(server_id)
);

CREATE TABLE players (
    player_id INT PRIMARY KEY,
    player_name VARCHAR(50),
    server_id INT,
    FOREIGN KEY (server_id) REFERENCES servers(server_id)
);

CREATE TABLE dinosaurs (
    dino_id INT PRIMARY KEY,
    dino_name VARCHAR(50),
    dino_type VARCHAR(20),
    base_power INT
);

CREATE TABLE player_dinos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    player_id INT,
    dino_id INT,
    level INT,
    current_power INT,
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    FOREIGN KEY (dino_id) REFERENCES dinosaurs(dino_id)
);

CREATE TABLE battle_records (
    record_id INT PRIMARY KEY AUTO_INCREMENT,
    player_id INT,
    territory_id INT,
    battle_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    battle_result VARCHAR(20),
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    FOREIGN KEY (territory_id) REFERENCES territories(territory_id)
);
```

### 3. 工作/测试场景示例：反范式设计——排行榜查询性能优化

```sql
-- 纯3NF设计：查排行榜需要JOIN多表，高并发下性能差
-- 排行榜每次请求都要：
SELECT p.player_name, s.server_name, SUM(pd.current_power) AS total_power
FROM player_dinos pd
JOIN players p ON pd.player_id = p.player_id
JOIN servers s ON p.server_id = s.server_id
GROUP BY pd.player_id, p.player_name, s.server_name
ORDER BY total_power DESC
LIMIT 100;
-- 3表JOIN + 聚合 + 排序 → 高频访问时压力巨大

-- ✅ 反范式优化：创建排行榜快照表，冗余存储server_name和total_power
CREATE TABLE power_ranking (
    rank_id INT PRIMARY KEY AUTO_INCREMENT,
    player_id INT,
    player_name VARCHAR(50),      -- 冗余！本应从players表取
    server_name VARCHAR(50),      -- 冗余！本应从servers表取
    total_power INT,              -- 冗余！本应实时聚合计算
    rank_position INT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_rank (rank_position),
    INDEX idx_player (player_id)
);

-- 定时刷新排行榜（每5分钟或每次战斗结束后）
INSERT INTO power_ranking (player_id, player_name, server_name, total_power, rank_position)
SELECT pd.player_id, p.player_name, s.server_name,
       SUM(pd.current_power) AS total_power,
       RANK() OVER (ORDER BY SUM(pd.current_power) DESC) AS rank_position
FROM player_dinos pd
JOIN players p ON pd.player_id = p.player_id
JOIN servers s ON p.server_id = s.server_id
GROUP BY pd.player_id, p.player_name, s.server_name
ORDER BY total_power DESC
LIMIT 100;

-- 排行榜查询变成单表直查——快！
SELECT rank_position, player_name, server_name, total_power
FROM power_ranking
ORDER BY rank_position ASC
LIMIT 100;
-- 单表 + 索引 → 毫秒级响应

-- ⚠️ 反范式代价：
-- 1. player改名需要同步更新power_ranking
-- 2. 数据有延迟（不是实时）
-- 3. 占用更多存储空间

-- 测试人员验证点：
-- 1. 排行榜数据与原始聚合数据一致性校验
SELECT pr.player_id, pr.total_power AS ranking_power,
       SUM(pd.current_power) AS actual_power,
       pr.total_power - SUM(pd.current_power) AS diff
FROM power_ranking pr
JOIN player_dinos pd ON pr.player_id = pd.player_id
GROUP BY pr.player_id
HAVING ABS(diff) > 0;  -- 差值不为0说明快照过期

-- 2. 玩家改名后排行榜是否同步更新
UPDATE players SET player_name = '新名字' WHERE player_id = 1001;
-- 检查 power_ranking 中该玩家的 name 是否也更新了
SELECT player_name FROM power_ranking WHERE player_id = 1001;
-- 如果没更新 → 数据不一致BUG！

-- 3. 排行榜刷新时间戳验证
SELECT MAX(updated_at) FROM power_ranking;
-- 与预期刷新周期对比，判断是否超时未更新
```

---

## 【注意事项/易错点】

### 常见错误

1. **盲目追求3NF导致过度拆表**
   - 不是所有表都需要拆到3NF。比如配置表（只有几行数据）完全可以冗余字段
   - 判断标准：冗余字段是否**频繁变更**？如果几乎不变（如服务器名称），冗余存储成本低

2. **混淆"部分依赖"和"传递依赖"**
   - 2NF是针对**联合主键**的——某个非主键字段只依赖主键的一部分
   - 3NF是针对**单主键**的——某个非主键字段通过另一个非主键字段间接依赖主键
   - 如果表已经是单列主键，满足1NF就自动满足2NF（没有联合主键就没有部分依赖）

3. **反范式 ≠ 不设计**
   - 反范式是**有意识地冗余**，不是随意乱建。必须明确：
     - 冗余哪些字段、为什么冗余
     - 数据同步机制（触发器/定时任务/应用层双写）
     - 冗余数据的验证/校验方案

### 性能提醒

- **写多读少**的场景 → 坚持范式化（减少更新代价）
- **读多写少**的场景 → 适度反范式（减少JOIN代价）
- **高频查询+低频更新** → 最适合反范式快照表（如排行榜、统计报表）
- 游戏项目中：玩家基础信息 → 范式化；排行榜/日志统计 → 反范式化

---

## 【今日练习题】

### 练习1：判断并修正范式违规

下面这张"公会表"违反了哪些范式？请指出并修正：

```sql
CREATE TABLE guilds_bad (
    guild_id INT PRIMARY KEY,
    guild_name VARCHAR(50),
    leader_id INT,
    leader_name VARCHAR(50),        -- ???
    leader_level INT,               -- ???
    member_ids VARCHAR(1000),       -- ???
    member_count INT,               -- ???
    server_id INT,
    server_region VARCHAR(20)       -- ???
);
```

提示：逐个标注???的字段违反了1NF/2NF/3NF中的哪个，然后写出修正后的表设计。

### 练习2：为恐龙岛项目设计反范式快照

场景：运营需要实时查看"各服务器今日充值总额"仪表盘，纯3NF查询如下：

```sql
SELECT s.server_name, SUM(p.amount) AS today_total
FROM payments p
JOIN players pl ON p.player_id = pl.player_id
JOIN servers s ON pl.server_id = s.server_id
WHERE p.pay_time >= CURDATE()
GROUP BY s.server_name;
```

要求：
1. 设计一张反范式的日充值快照表 `daily_recharge_snapshot`
2. 写出刷新快照的SQL
3. 写出验证快照与原始数据一致性的校验SQL

---

## 【一句话总结】

**范式保一致性，反范式保性能——设计不是追求"最规范"，而是在正确性和速度之间找平衡。**

---

*进度：Day 19/30 · 下次预告：Day 20 SQL注入与安全*
