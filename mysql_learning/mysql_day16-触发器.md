🐬 今日MySQL学习 · Day 16/30
**主题**：触发器（Trigger）

---

## 【学习目标】
- 理解触发器的本质：一种在表发生 **INSERT / UPDATE / DELETE** 时自动执行的存储程序
- 掌握 6 种触发器组合：`BEFORE/AFTER × INSERT/UPDATE/DELETE`
- 学会用 `NEW` 和 `OLD` 伪记录访问被操作行的数据

---

## 【核心语法】

```sql
-- ==================== 1. 创建触发器 ====================
DELIMITER $$

CREATE TRIGGER 触发器名
    {BEFORE | AFTER} {INSERT | UPDATE | DELETE}   -- 时机 × 事件
    ON 表名
    FOR EACH ROW                                  -- 行级触发器（MySQL只支持这个）
BEGIN
    -- 触发器逻辑（可以用 NEW.列名 和 OLD.列名）
END$$

DELIMITER ;

-- ==================== 2. 查看触发器 ====================
SHOW TRIGGERS;                           -- 查看当前库所有触发器
SHOW TRIGGERS LIKE '表名';               -- 按表名过滤
SHOW CREATE TRIGGER 触发器名;            -- 查看触发器定义

-- 从系统表查
SELECT * FROM information_schema.TRIGGERS
WHERE TRIGGER_SCHEMA = '数据库名';

-- ==================== 3. 删除触发器 ====================
DROP TRIGGER IF EXISTS 触发器名;

-- ==================== 4. NEW 和 OLD 使用规则 ====================
-- INSERT 触发器: NEW 可用（新插入的行数据），OLD 无意义（全是NULL）
-- UPDATE 触发器: NEW 可用（修改后的值），OLD 可用（修改前的值）
-- DELETE 触发器: OLD 可用（被删的行数据），NEW 无意义（全是NULL）
```

---

## 【实战示例】

### 示例 1：日志自动记录 — 玩家注册时自动写入日志表

```sql
-- 建玩家表
CREATE TABLE players (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    nickname  VARCHAR(50) NOT NULL,
    level     INT DEFAULT 1,
    gold      DECIMAL(10,2) DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 建日志表（触发器写入目标）
CREATE TABLE player_logs (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    player_id  INT,
    action     VARCHAR(20),
    log_time   DATETIME DEFAULT CURRENT_TIMESTAMP,
    detail     VARCHAR(200)
);

DELIMITER $$

CREATE TRIGGER trg_player_insert
    AFTER INSERT ON players
    FOR EACH ROW
BEGIN
    INSERT INTO player_logs(player_id, action, detail)
    VALUES (NEW.id, '注册',
            CONCAT('新玩家 ', NEW.nickname, ' 加入游戏，初始金币 ', NEW.gold));
END$$

DELIMITER ;

-- 测试：插入一个玩家，自动生成日志
INSERT INTO players(nickname, gold) VALUES ('阿克', 1000);

SELECT * FROM players;
SELECT * FROM player_logs;  -- 会看到一条自动生成的日志
```

**执行结果**：
```
players:  | 1 | 阿克 | 1 | 1000.00 | 2026-06-17 12:00:00 |
player_logs: | 1 | 1 | 注册 | 2026-06-17 12:00:00 | 新玩家 阿克 加入游戏，初始金币 1000.00 |
```

---

### 示例 2：BEFORE UPDATE + OLD vs NEW — 装备升级时校验和自动修正

```sql
-- 建装备表
CREATE TABLE equipment (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(50),
    level       INT DEFAULT 1,
    attack      INT DEFAULT 0,
    max_level   INT DEFAULT 20
);

DELIMITER $$

CREATE TRIGGER trg_equip_upgrade
    BEFORE UPDATE ON equipment
    FOR EACH ROW
BEGIN
    -- 校验1：等级不能超过上限
    IF NEW.level > NEW.max_level THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = '装备等级不能超过最大等级上限';
    END IF;

    -- 校验2：等级不能倒退（防止测试数据异常）
    IF NEW.level < OLD.level THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = '装备等级不能降低';
    END IF;

    -- 自动修正：每升一级攻击力+10
    IF NEW.level > OLD.level THEN
        SET NEW.attack = OLD.attack + (NEW.level - OLD.level) * 10;
    END IF;
END$$

DELIMITER ;

-- 测试
INSERT INTO equipment(name, level, attack) VALUES ('龙骨之剑', 1, 50);

-- 正常升级：level 1→3，攻击自动从50→70
UPDATE equipment SET level = 3 WHERE id = 1;
SELECT * FROM equipment;  -- level=3, attack=70 ✅

-- 异常1：等级倒退 → 报错
UPDATE equipment SET level = 1 WHERE id = 1;  -- ❌ 装备等级不能降低

-- 异常2：超过上限 → 报错
UPDATE equipment SET level = 99 WHERE id = 1; -- ❌ 装备等级不能超过最大等级上限
```

---

### 示例 3：BEFORE DELETE — 防止误删核心数据（测试环境常用）

```sql
-- 建VIP玩家表
CREATE TABLE vip_players (
    id       INT AUTO_INCREMENT PRIMARY KEY,
    nickname VARCHAR(50),
    vip_level INT DEFAULT 0
);

INSERT INTO vip_players(nickname, vip_level) VALUES
    ('氪金大佬', 10),
    ('普通玩家', 1);

DELIMITER $$

CREATE TRIGGER trg_prevent_vip_delete
    BEFORE DELETE ON vip_players
    FOR EACH ROW
BEGIN
    IF OLD.vip_level >= 5 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = CONCAT('禁止删除VIP', OLD.vip_level, '级玩家: ', OLD.nickname);
    END IF;
END$$

DELIMITER ;

-- 测试
DELETE FROM vip_players WHERE id = 2;  -- ✅ 普通玩家可以删
DELETE FROM vip_players WHERE id = 1;  -- ❌ 禁止删除VIP10级玩家: 氪金大佬
```

---

### 示例 4：实战场景 — 恐龙岛金币变动自动审计（测试数据校验用）

```sql
-- 建金币变动审计表
CREATE TABLE gold_audit (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    player_id   INT,
    change_type VARCHAR(20),     -- 任务奖励/购买装备/GM发放/战斗掉落
    old_gold    DECIMAL(10,2),
    new_gold    DECIMAL(10,2),
    change_amount DECIMAL(10,2),
    change_time DATETIME DEFAULT CURRENT_TIMESTAMP
);

DELIMITER $$

CREATE TRIGGER trg_gold_change_audit
    AFTER UPDATE ON players
    FOR EACH ROW
BEGIN
    -- 只在金币发生变化时记录
    IF NEW.gold <> OLD.gold THEN
        INSERT INTO gold_audit(player_id, old_gold, new_gold, change_amount, change_type)
        VALUES (NEW.id, OLD.gold, NEW.gold, NEW.gold - OLD.gold,
                CASE
                    WHEN NEW.gold > OLD.gold THEN '收入'
                    WHEN NEW.gold < OLD.gold THEN '支出'
                    ELSE '不变'
                END);
    END IF;
END$$

DELIMITER ;

-- 测试：模拟金币变动
UPDATE players SET gold = gold + 500 WHERE id = 1;   -- 获得任务奖励
UPDATE players SET gold = gold - 200 WHERE id = 1;   -- 购买装备
UPDATE players SET gold = gold + 1000 WHERE id = 1;  -- GM发放补偿

SELECT * FROM gold_audit;
```

**输出**：
```
| id | player_id | change_type | old_gold | new_gold | change_amount |
|----|-----------|-------------|----------|----------|---------------|
|  1 |         1 | 收入        |  1000.00 |  1500.00 |        500.00 |
|  2 |         1 | 支出        |  1500.00 |  1300.00 |       -200.00 |
|  3 |         1 | 收入        |  1300.00 |  2300.00 |       1000.00 |
```

> 🔧 **作为测试人员，这种审计触发器是你的利器**：测试时执行操作 → 查审计表 → 一行 SQL 验证数据变更是否正确，不用眼睛盯着几十个字段对比。

---

## 【注意事项 / 易错点】

### ❌ 易错 1：触发器里不能对本表做 DML
```sql
-- 这个会报错！触发器里不能再 INSERT/UPDATE/DELETE 同一张表
CREATE TRIGGER trg_bad
    AFTER INSERT ON players
    FOR EACH ROW
BEGIN
    UPDATE players SET level = 99 WHERE id = NEW.id;  -- ❌ Can't update table 'players' in stored function/trigger
END$$
```
**正确做法**：用 `BEFORE INSERT` + `SET NEW.level = 99` 直接修改行数据。

### ❌ 易错 2：SIGNAL 只能用在 5.5+，旧版本用别的方法
```sql
-- MySQL 5.5 之前不支持 SIGNAL，只能用 hack 方式抛错
-- 比如故意对不存在的表操作（不推荐）
-- 建议升级到 MySQL 5.7+，生产环境主流版本
```

### ❌ 易错 3：FOR EACH ROW 是强制的，批量操作每一行都触发
```sql
-- 批量 UPDATE 1000 行 → 触发器执行 1000 次！
UPDATE players SET gold = gold + 10 WHERE level > 50;  -- 如果匹配1000行，触发器跑1000次

-- 不要把重逻辑放触发器里（比如查大数据量表、调外部API等）
-- 触发器逻辑越轻越好
```

### ⚠️ 性能提醒
- 一张表每种事件（INSERT/UPDATE/DELETE）每种时机（BEFORE/AFTER）只能有一个触发器
- 触发器是**同步执行**的——触发器不跑完，原 DML 不返回，所以逻辑要轻量
- 不要在触发器里放耗时操作（如调用存储过程做复杂计算）

---

## 【今日练习题】

### 练习题 1：背包容量校验触发器
为玩家背包表 `backpack` 创建 BEFORE INSERT 触发器：
- 表结构：`id, player_id, item_id, quantity, capacity_limit`
- 当玩家当前背包物品数量 + 新插入的数量 > `capacity_limit` 时，拒绝插入
- 错误提示：`背包已满，当前X件，容量上限Y件`

```sql
-- 先建表
CREATE TABLE backpack (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    player_id      INT,
    item_id        INT,
    quantity       INT DEFAULT 1,
    capacity_limit INT DEFAULT 50   -- 默认容量50
);

-- 你的任务是写出 CREATE TRIGGER ...
```

### 练习题 2：装备绑定状态保护
为装备表 `equipment` 创建 BEFORE UPDATE 触发器：
- 新增字段 `is_bound TINYINT DEFAULT 0`（0=未绑定, 1=已绑定）
- 已绑定的装备（is_bound=1）不允许修改 attack 和 level
- 未绑定的装备可以自由修改

---

## 【一句话总结】
> **触发器是"表的事件监听器"——当 INSERT/UPDATE/DELETE 发生时，自动执行你预设的逻辑；NEW 看新值，OLD 看旧值，逻辑要轻量。**

---

📁 文件已保存至：`mysql_learning/mysql_day16-触发器.md`
