🐬 今日MySQL学习 · Day 4/30
**主题**：查询进阶 - 条件与排序

**【学习目标】**
- 掌握 WHERE 子句的各种条件过滤写法
- 理解比较运算符、逻辑运算符的组合使用
- 学会用 ORDER BY 排序和 LIMIT 分页控制结果

---

**【核心语法】**

```sql
-- 1. WHERE 子句基础（从表里筛选符合条件的行）
SELECT 列名 FROM 表名 WHERE 条件;

-- 2. 比较运算符
-- =    等于
-- <>或!= 不等于
-- >    大于
-- <    小于
-- >=   大于等于
-- <=   小于等于

-- 3. 范围与集合运算符
-- BETWEEN 值1 AND 值2      在闭区间内（包含两端）
-- IN (值1, 值2, 值3)       在集合中匹配
-- NOT IN (值1, 值2)        不在集合中
-- LIKE '模式'              模糊匹配
-- IS NULL                  是空值
-- IS NOT NULL              不是空值

-- 4. LIKE 通配符
-- %  匹配任意长度字符（包括0个）
-- _  匹配单个字符

-- 5. 逻辑运算符
-- AND  两个条件同时满足
-- OR   两个条件满足其一
-- NOT  取反

-- 6. ORDER BY 排序
-- ASC   升序（默认，可省略）
-- DESC  降序

-- 7. LIMIT 分页
-- LIMIT N           返回前N条
-- LIMIT offset, N   从第offset+1条开始，返回N条
```

---

**【实战示例】**

### 示例1：基础过滤 —— 查询《山海之巅》中指定条件的玩家

```sql
-- 假设有玩家表 player
CREATE TABLE IF NOT EXISTS player (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL,
    level INT DEFAULT 1,
    gold DECIMAL(15,2) DEFAULT 0,
    vip_level INT DEFAULT 0,
    register_time DATETIME,
    last_login DATETIME
);

-- 插入测试数据
INSERT INTO player (username, level, gold, vip_level, register_time) VALUES
('张三丰', 85, 50000.00, 6, '2025-01-15 10:30:00'),
('独孤求败', 92, 120000.00, 8, '2024-12-01 08:00:00'),
('黄药师', 78, 30000.00, 4, '2025-03-20 14:00:00'),
('郭靖', 60, 8000.00, 2, '2025-06-10 20:00:00'),
('令狐冲', 95, 200000.00, 10, '2024-10-05 09:00:00'),
('段誉', 45, 500.00, 0, '2025-11-01 16:00:00'),
('小龙女', 70, 15000.00, 3, '2025-05-18 12:00:00'),
('杨过', 88, 75000.00, 7, '2025-02-14 11:00:00');

-- 查等级大于等于80的玩家
SELECT username, level, gold
FROM player
WHERE level >= 80;

-- 查VIP等级在4到7之间的玩家（BETWEEN是闭区间，包含4和7）
SELECT username, vip_level, gold
FROM player
WHERE vip_level BETWEEN 4 AND 7;

-- 查VIP等级是2、6或8的玩家（IN匹配集合）
SELECT username, vip_level
FROM player
WHERE vip_level IN (2, 6, 8);
```

### 示例2：模糊匹配与逻辑组合

```sql
-- LIKE模糊匹配：查名字里带"龙"的玩家
SELECT username, level
FROM player
WHERE username LIKE '%龙%';
-- 结果：小龙女（%匹配前后任意字符）

-- 查名字以"黄"开头、两个字的名字
SELECT username, level
FROM player
WHERE username LIKE '黄_';
-- 结果：黄药师（_精确匹配1个字符）

-- AND组合：等级>70 且 金币>20000
SELECT username, level, gold
FROM player
WHERE level > 70 AND gold > 20000;

-- OR组合：等级>90 或 VIP>=8
SELECT username, level, vip_level
FROM player
WHERE level > 90 OR vip_level >= 8;

-- NOT取反：非VIP玩家（vip_level=0）
SELECT username, level, gold
FROM player
WHERE vip_level NOT IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10);
-- 或者更简洁：
SELECT username, level, gold
FROM player
WHERE vip_level = 0;

-- IS NULL：查注册时间为空的玩家
SELECT username
FROM player
WHERE register_time IS NULL;
```

### 示例3：排序与分页（测试人员常用！）

```sql
-- ORDER BY：按金币从高到低排（TOP N查询）
SELECT username, level, gold
FROM player
ORDER BY gold DESC;

-- LIMIT：只取金币前3名
SELECT username, level, gold
FROM player
ORDER BY gold DESC
LIMIT 3;
-- 结果：令狐冲(200000)、独孤求败(120000)、杨过(75000)

-- 分页公式：LIMIT (页码-1)*每页条数, 每页条数
-- 第1页（每页3条）：LIMIT 0, 3
SELECT username, level, gold
FROM player
ORDER BY gold DESC
LIMIT 0, 3;

-- 第2页：LIMIT 3, 3
SELECT username, level, gold
FROM player
ORDER BY gold DESC
LIMIT 3, 3;

-- 多列排序：先按等级降序，等级相同再按金币降序
SELECT username, level, gold
FROM player
ORDER BY level DESC, gold DESC;

-- ⭐ 测试场景：验证排行榜接口返回的玩家顺序是否正确
-- 接口返回按战力排序的前10名，用SQL验证数据库中的真实排序
SELECT username, level
FROM player
ORDER BY level DESC
LIMIT 10;
-- 对比这个结果和接口返回的JSON数据，顺序必须一致
```

---

**【注意事项/易错点】**

1. **BETWEEN 是闭区间**：`BETWEEN 1 AND 10` 包含 1 和 10，不是开区间。如果业务需要开区间，用 `> 1 AND < 10`。

2. **AND 的优先级高于 OR**：`WHERE a = 1 OR b = 2 AND c = 3` 实际执行的是 `a = 1 OR (b = 2 AND c = 3)`。建议用括号明确优先级：`WHERE (a = 1 OR b = 2) AND c = 3`。

3. **LIKE 匹配区分大小写**：默认情况下 `LIKE 'abc'` 不会匹配 'ABC'。如果需要不区分大小写，搜索时可以用 `LOWER(username) LIKE LOWER('%abc%')` 或者查询前临时设置 `SET collation_connection = utf8mb4_general_ci;`。

4. **WHERE vs HAVING 的区别**（提前预告）：WHERE 过滤行（聚合前），HAVING 过滤分组（聚合后）。Day 5 会详细讲，现在别混淆。

5. **LIMIT 的 offset 从0开始**：`LIMIT 10, 5` 是从第11条开始取5条，不是从第10条。

---

**【今日练习题】**

**练习1（必做）：**
基于上面的 player 表，写出以下查询：
1. 查出所有非VIP（vip_level = 0）且等级小于50的玩家
2. 查出名字里包含"求"或"冲"的玩家，按等级从高到低排
3. 用分页语法查出按金币排第4到第6名的玩家

**练习2（扩展）：**
建一个物品表 `item`（物品名、品质颜色、价格、库存），然后：
1. 查出价格在100-500之间的物品（用BETWEEN）
2. 查出品质为"橙色"或"红色"的物品（用IN）
3. 按价格降序取前5个最贵物品

---

**【一句话总结】**
WHERE 是SQL的"过滤器"，帮你从海量数据中精准捞出想要的行；ORDER BY + LIMIT 则是"排序+截取"组合拳，排行榜和分页查询全靠它。
