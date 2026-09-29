# 🐬 今日MySQL学习 · Day 24/30

**主题**：实战：设计一个游戏数据库（结合恐龙岛项目：玩家表、恐龙表、背包表、战斗记录表）

---

## 【学习目标】

- 掌握游戏业务的核心实体抽象：玩家（Players）、恐龙（Dinosaurs）、背包（Inventory）、战斗记录（Battle Records）的表结构设计
- 学会处理游戏业务特有的复杂关系：一对多（玩家拥有多只恐龙）、多对多（恐龙与技能/装备）、层级结构（恐龙进化树、领地树）
- 结合你正在测试的"恐龙岛"项目，输出可直接套用的建表 SQL 与测试验证点

---

## 【核心语法】

### 1. 游戏数据库的四大设计原则

```sql
-- 游戏数据库与电商数据库的核心差异：
-- (1) 高频读写：玩家状态/背包更新非常频繁（每秒可能多次）
-- (2) 数据规模大：百万级玩家 + 千万级战斗记录
-- (3) 数值精确：金币、经验、属性加成必须用 INT/DECIMAL，禁止 FLOAT
-- (4) 时序数据多：战斗记录、日志需要按时间分表或分区

-- 推荐引擎：InnoDB（支持事务、行锁、外键）
-- 推荐字符集：utf8mb4（兼容玩家昵称里的 emoji）
```

### 2. 玩家表 Players（账号体系）

```sql
CREATE TABLE players (
    player_id     BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT    COMMENT '玩家ID',
    username      VARCHAR(50)  NOT NULL UNIQUE                  COMMENT '账号',
    nickname      VARCHAR(50)  NOT NULL                         COMMENT '游戏内昵称',
    password_hash VARCHAR(128) NOT NULL                        COMMENT '密码哈希',
    phone         VARCHAR(20)                                  COMMENT '手机号',
    email         VARCHAR(100)                                 COMMENT '邮箱',
    level         INT UNSIGNED NOT NULL DEFAULT 1              COMMENT '玩家等级',
    exp           BIGINT UNSIGNED NOT NULL DEFAULT 0           COMMENT '经验值',
    gold          BIGINT NOT NULL DEFAULT 0                    COMMENT '金币（有正有负用BIGINT）',
    diamond       INT UNSIGNED NOT NULL DEFAULT 0              COMMENT '钻石（充值货币）',
    vip_level     TINYINT UNSIGNED NOT NULL DEFAULT 0          COMMENT 'VIP等级',
    server_id     INT UNSIGNED NOT NULL DEFAULT 1              COMMENT '所在服务器ID',
    guild_id      INT UNSIGNED                                  COMMENT '所属公会ID',
    status        TINYINT NOT NULL DEFAULT 1                   COMMENT '状态:1正常/0封禁/2已注销',
    last_login_at DATETIME                                     COMMENT '最后登录时间',
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_server_level (server_id, level),                 -- 按服务器查排行榜
    INDEX idx_guild (guild_id),
    INDEX idx_last_login (last_login_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='玩家表';
```

### 3. 恐龙表 Dinosaurs（恐龙图鉴 + 玩家恐龙实例）

游戏里"恐龙"通常是双表设计：图鉴（dino_species）+ 玩家拥有（player_dinosaurs）。

```sql
-- 3.1 恐龙图鉴：所有恐龙种类的基础信息（只读静态数据）
CREATE TABLE dino_species (
    species_id     INT UNSIGNED PRIMARY KEY AUTO_INCREMENT     COMMENT '恐龙种类ID',
    species_name   VARCHAR(50) NOT NULL UNIQUE                 COMMENT '恐龙名称（霸王龙/三角龙...）',
    rarity         TINYINT UNSIGNED NOT NULL                   COMMENT '稀有度:1普通/2稀有/3史诗/4传说/5神话',
    dino_type      VARCHAR(20) NOT NULL                        COMMENT '属性:火/水/草/雷/土',
    base_hp        INT UNSIGNED NOT NULL                       COMMENT '基础生命',
    base_atk       INT UNSIGNED NOT NULL                       COMMENT '基础攻击',
    base_def       INT UNSIGNED NOT NULL                       COMMENT '基础防御',
    base_speed     INT UNSIGNED NOT NULL                       COMMENT '基础速度',
    evolve_to_id   INT UNSIGNED                                 COMMENT '可进化为的种类ID',
    description    TEXT                                         COMMENT '描述',
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_rarity (rarity),
    INDEX idx_type (dino_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='恐龙图鉴';

-- 3.2 玩家恐龙表：每个玩家实际拥有的恐龙
CREATE TABLE player_dinosaurs (
    instance_id    BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT   COMMENT '实例ID',
    player_id      BIGINT UNSIGNED NOT NULL                    COMMENT '所属玩家',
    species_id     INT UNSIGNED NOT NULL                       COMMENT '恐龙种类ID',
    nickname       VARCHAR(50)                                  COMMENT '玩家给恐龙起的名字',
    level          INT UNSIGNED NOT NULL DEFAULT 1             COMMENT '等级',
    exp            BIGINT UNSIGNED NOT NULL DEFAULT 0          COMMENT '经验',
    hp             INT UNSIGNED NOT NULL                       COMMENT '当前生命值',
    skill_1        SMALLINT UNSIGNED                            COMMENT '技能1',
    skill_2        SMALLINT UNSIGNED                            COMMENT '技能2',
    skill_3        SMALLINT UNSIGNED                            COMMENT '技能3',
    is_locked      TINYINT NOT NULL DEFAULT 0                  COMMENT '是否锁定（防止误卖）',
    obtain_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '获得时间',
    
    FOREIGN KEY (player_id) REFERENCES players(player_id) ON DELETE CASCADE,
    FOREIGN KEY (species_id) REFERENCES dino_species(species_id),
    INDEX idx_player (player_id),
    INDEX idx_species (species_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='玩家拥有的恐龙';
```

### 4. 装备/背包表 Player_Items

```sql
-- 装备/道具统一用一张表，用 item_type 区分
CREATE TABLE player_items (
    item_id        BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT  COMMENT '物品实例ID',
    player_id      BIGINT UNSIGNED NOT NULL                    COMMENT '持有玩家',
    item_type      VARCHAR(20) NOT NULL                        COMMENT '类型:equip/consumable/material/gem',
    item_subtype   VARCHAR(20)                                  COMMENT '子类型:weapon/armor/hat/shoe...',
    item_name      VARCHAR(50) NOT NULL                        COMMENT '物品名',
    quantity       INT UNSIGNED NOT NULL DEFAULT 1             COMMENT '数量（装备为1，道具可堆叠）',
    quality        TINYINT UNSIGNED NOT NULL DEFAULT 1         COMMENT '品质:1白/2绿/3蓝/4紫/5橙',
    level          INT UNSIGNED NOT NULL DEFAULT 1             COMMENT '强化等级',
    attack_bonus   INT NOT NULL DEFAULT 0                      COMMENT '攻击加成',
    defense_bonus  INT NOT NULL DEFAULT 0                      COMMENT '防御加成',
    hp_bonus       INT NOT NULL DEFAULT 0                      COMMENT '生命加成',
    is_equipped    TINYINT NOT NULL DEFAULT 0                  COMMENT '是否已装备',
    equipped_by_dino BIGINT UNSIGNED                            COMMENT '装备在哪只恐龙身上',
    obtained_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (player_id) REFERENCES players(player_id) ON DELETE CASCADE,
    INDEX idx_player_type (player_id, item_type),
    INDEX idx_equipped (equipped_by_dino)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='玩家物品/装备表';
```

### 5. 战斗记录表 Battle_Records（时序大数据量）

```sql
-- 战斗记录属于"写多读少"的时序数据，要考虑未来分表
CREATE TABLE battle_records (
    battle_id      BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    attacker_id    BIGINT UNSIGNED NOT NULL                    COMMENT '发起方玩家',
    defender_id    BIGINT UNSIGNED NOT NULL                    COMMENT '防守方玩家',
    battle_type    TINYINT UNSIGNED NOT NULL                   COMMENT '战斗类型:1领地战/2PVP/3世界BOSS',
    territory_id   INT UNSIGNED                                 COMMENT '领地ID（领地战时填）',
    attacker_dinos JSON                                         COMMENT '参战恐龙ID列表',
    defender_dinos JSON                                         COMMENT '防守方恐龙ID列表',
    winner_side    TINYINT NOT NULL                             COMMENT '胜利方:1攻击/2防守/3平局',
    battle_log     TEXT                                         COMMENT '战斗过程（json或文本）',
    reward_gold    BIGINT NOT NULL DEFAULT 0                   COMMENT '奖励金币',
    reward_exp     INT UNSIGNED NOT NULL DEFAULT 0             COMMENT '奖励经验',
    started_at     DATETIME NOT NULL                           COMMENT '战斗开始时间',
    ended_at       DATETIME                                     COMMENT '战斗结束时间',
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_attacker_time (attacker_id, started_at),
    INDEX idx_defender_time (defender_id, started_at),
    INDEX idx_territory (territory_id, started_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='战斗记录表'
  PARTITION BY RANGE (TO_DAYS(started_at)) (
    PARTITION p202604 VALUES LESS THAN (TO_DAYS('2026-05-01')),
    PARTITION p202605 VALUES LESS THAN (TO_DAYS('2026-06-01')),
    PARTITION p202606 VALUES LESS THAN (TO_DAYS('2026-07-01')),
    PARTITION p_max    VALUES LESS THAN MAXVALUE
  );
```

---

## 【实战示例】

### 示例 1：完整建库脚本（含恐龙岛测试数据）

```sql
-- 1. 创建数据库
DROP DATABASE IF EXISTS dino_island;
CREATE DATABASE dino_island DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE dino_island;

-- 2. 造几条恐龙图鉴
INSERT INTO dino_species (species_name, rarity, dino_type, base_hp, base_atk, base_def, base_speed) VALUES
('霸王龙', 5, '火', 1500, 320, 180, 95),
('三角龙', 4, '土', 1800, 220, 280, 70),
('迅猛龙', 3, '雷', 900,  280, 120, 130),
('翼龙',   2, '风', 800,  200, 100, 150),
('剑龙',   3, '草', 1200, 180, 220, 60);

-- 3. 造3个测试玩家
INSERT INTO players (username, nickname, level, gold, diamond, vip_level, server_id) VALUES
('tu001', '涂伟富', 30, 50000, 200, 3, 1),
('test002', '小恐龙', 25, 30000, 50,  1, 1),
('test003', '萌新',   10,  5000,  0,  0, 1);

-- 4. 给玩家1分配3只恐龙
INSERT INTO player_dinosaurs (player_id, species_id, nickname, level, exp, hp) VALUES
(1, 1, '炎牙',  20, 12000, 1500),
(1, 2, '铁甲',  15,  6000, 1800),
(1, 3, '闪电',  10,  2000,  900);

-- 5. 给玩家1的背包加装备
INSERT INTO player_items (player_id, item_type, item_subtype, item_name, quantity, quality, level, attack_bonus, defense_bonus) VALUES
(1, 'equip',     'weapon', '烈焰之剑',  1, 5, 10, 150, 0),
(1, 'equip',     'armor',  '龙鳞铠甲',  1, 4, 8,  20, 120),
(1, 'consumable','potion', '小型血瓶', 99, 1, 1,  0,  0);
```

### 示例 2：测试场景验证 SQL

```sql
-- 测试点1：玩家1的恐龙数量是否正确（应该是3）
SELECT player_id, COUNT(*) AS dino_count
FROM player_dinosaurs
WHERE player_id = 1
GROUP BY player_id;

-- 测试点2：哪个玩家的战斗力最强（按恐龙等级+数量综合）
SELECT 
    p.player_id, p.nickname,
    COUNT(pd.instance_id) AS dino_count,
    SUM(pd.level) AS total_level,
    SUM(pd.level * ds.base_atk) AS combat_power  -- 简化的战斗力公式
FROM players p
JOIN player_dinosaurs pd ON p.player_id = pd.player_id
JOIN dino_species ds     ON pd.species_id = ds.species_id
WHERE p.status = 1
GROUP BY p.player_id, p.nickname
ORDER BY combat_power DESC
LIMIT 10;

-- 测试点3：验证外键级联删除（删除玩家时恐龙/物品也被删）
-- 注意：测试环境操作！
DELETE FROM players WHERE player_id = 3;
SELECT COUNT(*) FROM player_dinosaurs WHERE player_id = 3;  -- 应为0
SELECT COUNT(*) FROM player_items     WHERE player_id = 3;  -- 应为0

-- 测试点4：装备关联恐龙（背包 → 恐龙）
SELECT 
    pi.item_name, pi.attack_bonus, pi.defense_bonus,
    pd.nickname AS dino_nickname
FROM player_items pi
LEFT JOIN player_dinosaurs pd ON pi.equipped_by_dino = pd.instance_id
WHERE pi.player_id = 1 AND pi.item_type = 'equip';
```

### 示例 3：分区表战斗记录 + 领地争夺查询（你的项目场景）

```sql
-- 场景：测试"领地争夺"玩法，统计某玩家最近7天的战斗胜负
SELECT 
    battle_type,
    COUNT(*) AS total,
    SUM(CASE WHEN winner_side = 1 AND attacker_id = 1 THEN 1 ELSE 0 END) AS my_win,
    SUM(CASE WHEN winner_side = 2 AND defender_id = 1 THEN 1 ELSE 0 END) AS be_attacked_win,
    SUM(reward_gold) AS total_gold
FROM battle_records
WHERE (attacker_id = 1 OR defender_id = 1)
  AND started_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY battle_type;

-- 验证自动挂机期间战斗数据是否正常入库
SELECT 
    DATE(started_at) AS battle_date,
    COUNT(*) AS daily_count,
    AVG(TIMESTAMPDIFF(SECOND, started_at, ended_at)) AS avg_duration_sec
FROM battle_records
WHERE attacker_id IN (SELECT player_id FROM players WHERE vip_level >= 2)
  AND started_at >= '2026-06-23'
GROUP BY DATE(started_at)
ORDER BY battle_date;
```

---

## 【注意事项/易错点】

### 1. 业务设计陷阱

- **不要用 FLOAT 存金币/经验**：精度丢失会导致玩家对账异常，必须用 `BIGINT`（整数）或 `DECIMAL(18,2)`（带小数）。例：玩家充了 100 元变成 99.9999999，财务就乱了。
- **昵称长度预留足够**：玩家昵称常见 50-100 字节，且必须 `utf8mb4` 才能存 emoji（霸王龙🦖 4 字节）。
- **状态字段用 TINYINT 而非 VARCHAR**：节省空间、查询更快，注释里写明每个值含义。

### 2. 性能陷阱

- **战斗记录表一定要分区或分表**：单表 1000 万行后查询会明显变慢。RANGE 分区按时间切片是好选择。
- **JSON 字段谨慎使用**：MySQL 5.7+ 支持 JSON 索引（生成列），但读写性能不如规范化表。建议：非查询条件用 JSON，查条件用独立列。
- **外键不是越多越好**：高并发写场景下外键检查会拖慢性能，很多生产环境的"分库分表"会去掉外键用应用层保证一致性。

### 3. 测试特别提醒

- **删除玩家验证级联**：先确认业务上"删玩家"到底要不要级联删恐龙/装备？不同项目策略不同，可能要求玩家"封禁"而非"删除"。
- **装备加成计算要边界测试**：超过 INT 范围会溢出（攻击力 INT 上限 21 亿），高等级装备要切到 BIGINT。
- **自动挂机测试**：验证离线期间的战斗/收益数据是否完整入库，对账时 COUNT(*) 必须和日志匹配。

---

## 【今日练习题】

### 练习 1：完整建库 + 测试查询

任务：把上面的 `dino_island` 库跑起来，执行建表 + 测试数据插入，然后写一个 SQL 查出：
- "玩家 1 拥有的所有恐龙，按等级从高到低排序"
- "全服务器拥有 3 只以上传说道话（rarity=4 或 5）的玩家昵称和数量"

### 练习 2（结合你的恐龙岛项目）

任务：在你的测试环境数据库里跑 `SHOW TABLES` 看现有结构，挑出 3 张表用 `SHOW CREATE TABLE` 看完整建表语句，回答：
- 哪些字段用了 `utf8mb4`？哪些还是 `utf8`？（utf8 不支持 emoji，玩家昵称可能乱码）
- 哪些是事务核心表（有外键、InnoDB）？哪些是日志表（MyISAM 或无索引）？
- 哪些大表（数据量 > 100 万行）需要加索引？把 `EXPLAIN` 截图保存，作为今天的产出物。

---

## 【一句话总结】

**游戏数据库设计的核心是"双表分离 + 时序分区"：图鉴表存静态数据，玩家实例表存动态属性；战斗日志用时间分区；金额用 `BIGINT/DECIMAL`；昵称用 `utf8mb4`——这四点是避免线上事故的底线。**
