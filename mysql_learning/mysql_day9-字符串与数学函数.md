# 🐬 今日MySQL学习 · Day 9/30
## 主题：字符串与数学函数

> MySQL 内置函数就像游戏里的辅助技能——会用了事半功倍，不会用只能写出又长又丑的 SQL。

---

## 【学习目标】

1. **掌握常用字符串处理函数**：拼接、截取、替换、去空格、大小写转换等
2. **掌握常用数学计算函数**：四舍五入、向上向下取整、绝对值、随机数等
3. **理解函数在实战中的组合用法**：测试数据清洗、报表格式化、模糊匹配预处理

---

## 【核心语法】

### 一、字符串函数

```sql
-- ========== 拼接 ==========
-- CONCAT(str1, str2, ...) 拼接多个字符串，任一为NULL则结果为NULL
SELECT CONCAT('Hello', ' ', 'World');                    -- Hello World
SELECT CONCAT('玩家', player_name, ' 等级:', player_level); -- 玩家张三 等级:50

-- CONCAT_WS(separator, str1, str2, ...)  带分隔符拼接，自动处理NULL
SELECT CONCAT_WS('-', '2026', '06', '08');               -- 2026-06-08
SELECT CONCAT_WS('，', item1, item2, item3);              -- 用逗号分隔，NULL值会被跳过

-- ========== 截取 ==========
-- SUBSTRING(str, start, length)  从第start个字符开始截取length个（从1开始计数）
SELECT SUBSTRING('Hello World', 1, 5);                    -- Hello
SELECT SUBSTRING('Hello World', 7);                       -- World（省略length则截到末尾）
SELECT SUBSTRING('13800138000', 1, 3);                    -- 138（取手机号前3位）

-- LEFT(str, n) / RIGHT(str, n)  取左/右n个字符
SELECT LEFT('2026-06-08', 4);                             -- 2026
SELECT RIGHT('13800138000', 4);                           -- 8000（取手机号后4位）

-- ========== 查找与替换 ==========
-- REPLACE(str, from_str, to_str)  替换字符串
SELECT REPLACE('山海之巅_测试服', '_测试服', '');           -- 山海之巅
SELECT REPLACE('138-0013-8000', '-', '');                 -- 13800138000（去短横线）

-- INSTR(str, substr)  返回substr在str中首次出现的位置，找不到返回0
SELECT INSTR('player_id=10086', '=');                     -- 11

-- LOCATE(substr, str)  同INSTR，参数顺序不同
SELECT LOCATE('@', 'test@qq.com');                        -- 5

-- ========== 大小写与空格 ==========
-- UPPER(str) / LOWER(str)  转大/小写
SELECT UPPER('hello');                                    -- HELLO
SELECT LOWER('ITEM_SWORD');                               -- item_sword

-- TRIM(str)  去除首尾空格
SELECT TRIM('   张三   ');                                 -- 张三

-- LTRIM(str) / RTRIM(str)  去左/右侧空格
SELECT LTRIM('   张三');                                   -- 张三

-- ========== 长度 ==========
-- CHAR_LENGTH(str)  返回字符数（推荐，中英文都算1个字符）
SELECT CHAR_LENGTH('Hello世界');                           -- 7

-- LENGTH(str)  返回字节数（中文每字3字节 UTF-8）
SELECT LENGTH('Hello世界');                                -- 11（5 + 3×2）

-- ========== 填充 ==========
-- LPAD(str, len, padstr) / RPAD(str, len, padstr)  左/右填充到指定长度
SELECT LPAD('99', 5, '0');                                -- 00099（编号补零）
SELECT RPAD('VIP', 8, '*');                               -- VIP*****
```

### 二、数学函数

```sql
-- ========== 取整 ==========
-- ROUND(x, d)  四舍五入，保留d位小数
SELECT ROUND(3.14159, 2);                                 -- 3.14
SELECT ROUND(3.14159, 0);                                 -- 3（保留0位小数 → 整数）
SELECT ROUND(12345, -2);                                  -- 12300（精确到百位）

-- CEIL(x) / CEILING(x)  向上取整（天花板）
SELECT CEIL(3.1);                                         -- 4
SELECT CEIL(-3.1);                                        -- -3

-- FLOOR(x)  向下取整（地板）
SELECT FLOOR(3.9);                                        -- 3
SELECT FLOOR(-3.9);                                       -- -4

-- TRUNCATE(x, d)  直接截断，不四舍五入
SELECT TRUNCATE(3.14159, 2);                              -- 3.14
SELECT TRUNCATE(3.149, 2);                                -- 3.14（不会进位到3.15！）

-- ========== 数学运算 ==========
-- ABS(x)  绝对值
SELECT ABS(-100);                                         -- 100
SELECT ABS(attack_diff);                                  -- 攻击力差值取绝对值

-- MOD(x, y)  取模（求余数）
SELECT MOD(17, 5);                                        -- 2
SELECT MOD(player_id, 10);                                -- 按ID分10个桶（分库分表常用）

-- POW(x, y) / POWER(x, y)  x的y次方
SELECT POW(2, 10);                                        -- 1024

-- SQRT(x)  平方根
SELECT SQRT(100);                                         -- 10

-- ========== 随机与符号 ==========
-- RAND()  返回0到1之间的随机数
SELECT RAND();                                            -- 0.683427...（每次不同）
SELECT FLOOR(RAND() * 100);                               -- 0~99的随机整数（抽奖、随机排序）

-- SIGN(x)  返回参数符号（-1/0/1）
SELECT SIGN(-50);                                         -- -1
SELECT SIGN(0);                                           -- 0
SELECT SIGN(200);                                         -- 1
```

---

## 【实战示例】

### 示例1：基础篇 — 玩家昵称格式化与脱敏

```sql
-- 场景：用户列表需要统一格式并脱敏展示
-- 原始数据：nickname 可能前后有空格、混有大小写

-- 建测试表
CREATE TABLE test_players (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nickname VARCHAR(50),
    phone VARCHAR(20),
    reg_date DATE
);

INSERT INTO test_players (nickname, phone, reg_date) VALUES
('  暗夜猎手  ', '13800138001', '2026-03-15'),
('SwordMaster', '13912345678', '2026-05-20'),
('  dark_hunter  ', '15678901234', '2026-01-01');

-- 格式化查询：去空格 + 首字母大写（简单处理）+ 手机号脱敏
SELECT 
    id,
    TRIM(nickname) AS clean_nickname,                          -- 去空格
    CONCAT(LEFT(phone, 3), '****', RIGHT(phone, 4)) AS masked_phone,  -- 脱敏: 138****8001
    reg_date
FROM test_players;
```

**结果：**

| id | clean_nickname | masked_phone | reg_date |
|----|---------------|-------------|----------|
| 1 | 暗夜猎手 | 138****8001 | 2026-03-15 |
| 2 | SwordMaster | 139****5678 | 2026-05-20 |
| 3 | dark_hunter | 156****1234 | 2026-01-01 |

---

### 示例2：进阶篇 — 装备属性统计与格式化输出

```sql
-- 场景：装备表包含基础属性、强化属性，需要计算总值并按格式输出
CREATE TABLE test_equipment (
    id INT PRIMARY KEY AUTO_INCREMENT,
    equip_name VARCHAR(50),
    base_atk INT,          -- 基础攻击
    base_def INT,          -- 基础防御
    enhance_rate DECIMAL(4,2) -- 强化加成比例(如1.25=125%)
);

INSERT INTO test_equipment (equip_name, base_atk, base_def, enhance_rate) VALUES
('屠龙刀', 150, 30, 1.35),
('玄铁剑', 120, 50, 1.20),
('破甲弓', 130, 20, 1.15);

-- 计算强化后属性 + 格式化面板展示
SELECT 
    equip_name AS '装备名',
    CONCAT('攻击:', base_atk, '→', FLOOR(base_atk * enhance_rate)) AS '攻击力(强化后)',
    CONCAT('防御:', base_def, '→', FLOOR(base_def * enhance_rate)) AS '防御力(强化后)',
    CONCAT(ROUND((enhance_rate - 1) * 100, 0), '%') AS '强化加成',
    FLOOR((base_atk + base_def) * enhance_rate) AS '综合战力'
FROM test_equipment
ORDER BY FLOOR((base_atk + base_def) * enhance_rate) DESC;
```

**结果：**

| 装备名 | 攻击力(强化后) | 防御力(强化后) | 强化加成 | 综合战力 |
|-------|-------------|-------------|---------|---------|
| 屠龙刀 | 攻击:150→202 | 防御:30→40 | 35% | 243 |
| 玄铁剑 | 攻击:120→144 | 防御:50→60 | 20% | 204 |
| 破甲弓 | 攻击:130→149 | 防御:20→23 | 15% | 172 |

---

### 示例3：测试场景 — 数据比对与清洗

```sql
-- 场景：测试时经常要比较两个数据源（如接口返回 vs 数据库）的差异
-- 用字符串/数学函数做数据标准化后再比对

CREATE TABLE api_result (
    id INT,
    player_name VARCHAR(50),
    damage VARCHAR(20)   -- 注意：接口返回是字符串类型！
);

CREATE TABLE db_record (
    id INT,
    player_name VARCHAR(50),
    damage INT           -- 数据库存的是整数
);

INSERT INTO api_result VALUES
(1, '  ShadowKnight  ', ' 12,560 '),
(2, 'Phoenix123', '10.0'),
(3, '  dragon_emperor', 'NULL');

INSERT INTO db_record VALUES
(1, 'ShadowKnight', 12560),
(2, 'Phoenix123', 10),
(3, 'dragon_emperor', NULL);

-- 测试验证：比对两个数据源是否一致
SELECT 
    a.id,
    TRIM(a.player_name) AS api_name,
    b.player_name AS db_name,
    CASE WHEN TRIM(a.player_name) = b.player_name THEN '一致' ELSE '不一致' END AS name_match,
    REPLACE(TRIM(a.damage), ',', '') AS api_damage_raw,
    b.damage AS db_damage,
    CASE 
        WHEN REPLACE(TRIM(a.damage), ',', '') = 'NULL' AND b.damage IS NULL THEN '一致(空值)'
        WHEN CAST(REPLACE(TRIM(a.damage), ',', '') AS SIGNED) = b.damage THEN '一致'
        ELSE '不一致'
    END AS damage_match
FROM api_result a
LEFT JOIN db_record b ON a.id = b.id;
```

**输出：** 这条 SQL 模拟了真实测试场景——API 返回的字符串数据（可能有空格、千分位逗号、"NULL"字符串），需要清洗后与数据库比对。`REPLACE` 去逗号、`TRIM` 去空格、`CAST(...AS SIGNED)` 转整数，一气呵成。

---

### 示例4：进阶篇 — 随机抽样与分桶

```sql
-- 场景：从10万条玩家记录中随机抽100条做抽查审计
SELECT * FROM test_players
ORDER BY RAND()
LIMIT 100;

-- 场景：按玩家ID分10个桶（模拟分库分表路由）
SELECT 
    id,
    nickname,
    MOD(id, 10) AS bucket_id,        -- 分桶编号0~9
    CONCAT('player_db_', MOD(id, 10)) AS target_db   -- 对应数据库
FROM test_players;

-- 场景：计算等级区间分布（向上取整到10的倍数）
SELECT 
    FLOOR(player_level / 10) * 10 AS level_tier,     -- 0-9→0, 10-19→10
    CONCAT(FLOOR(player_level / 10) * 10, '-', FLOOR(player_level / 10) * 10 + 9) AS level_range,
    COUNT(*) AS player_count
FROM test_players
GROUP BY FLOOR(player_level / 10) * 10;
```

---

## 【注意事项 / 易错点】

| # | 错误点 | 说明 |
|---|-------|------|
| 1 | **CONCAT 遇 NULL 返回 NULL** | `CONCAT('a', NULL)` → `NULL`！用 `CONCAT_WS` 或 `COALESCE` 兜底 |
| 2 | **SUBSTRING 从1开始** | SQL 字符串索引从 **1** 开始，不是 0（和 Python/JS 不同！） |
| 3 | **ROUND vs TRUNCATE** | `ROUND(3.149, 2)` = `3.15`（四舍五入），`TRUNCATE(3.149, 2)` = `3.14`（截断） |
| 4 | **CHAR_LENGTH vs LENGTH** | 中文环境用 `CHAR_LENGTH`，`LENGTH` 返回字节数会让你怀疑人生 |
| 5 | **RAND() 计算列** | `ORDER BY RAND()` 大表性能极差，生产环境慎用（可用 `WHERE id >= FLOOR(RAND()*MAX_ID)` 代替） |

---

## 【今日练习题】

### 题1（必做）：背包物品格式化报表

在本地 MySQL 中创建如下表并插入数据，按要求写出查询：

```sql
-- 建表
CREATE TABLE backpack (
    id INT PRIMARY KEY AUTO_INCREMENT,
    item_name VARCHAR(50),
    item_type VARCHAR(20),   -- weapon/armor/potion
    quantity INT,
    unit_price DECIMAL(10,2)
);

INSERT INTO backpack VALUES
(1, '  破军之刃  ', 'weapon', 1, 5800.00),
(2, '龙鳞护甲', 'armor', 2, 3200.50),
(3, ' 生命药水 ', 'potion', 99, 12.80),
(4, 'blade_of_eternity', 'weapon', 1, 15000.00);

-- 需求：写一条SQL，输出如下格式的背包清单
-- | 物品 | 类型 | 数量 | 单价 | 总价(格式化) | 大类型 |
-- | 破军之刃 | 武器 | 1 | 5800.00 | ¥5,800.00 | WEAPON |
-- | 龙鳞护甲 | 防具 | 2 | 3200.50 | ¥6,401.00 | ARMOR  |
-- | 生命药水 | 药水 | 12 | 12.80  | ¥153.60  | POTION |
-- | Blade Of Eternity | 武器 | 1 | 15000.00 | ¥15,000.00 | WEAPON |
-- 要求：item_name去空格+英文首字母大写、总价带上千分位¥符号、大类型转大写
```

### 题2（选做）：战力区间分组统计

还是用上面的 backpack 表，写 SQL 按单件价值把物品分到不同档位，统计每档的数量：

```
档位规则：
- '廉价'：单价 < 100
- '普通'：100 ≤ 单价 < 1000
- '稀有'：1000 ≤ 单价 < 5000
- '史诗'：5000 ≤ 单价 < 10000
- '传说'：单价 ≥ 10000
```

---

## 【一句话总结】

> **字符串函数处理"脏数据"，数学函数搞定"计算题"——掌握这两套内置函数，SQL 才能从"能跑"变成"好用"。**

---

*Day 9 完成！明天进入 Day 10：日期时间函数 —— 比字符串函数更容易踩坑。*
