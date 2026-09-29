# 🐬 今日MySQL学习 · Day 18/30
**主题**：表设计进阶（外键约束、CHECK约束、DEFAULT值、AUTO_INCREMENT、ON UPDATE）

---

## 【学习目标】

- 掌握5种表级约束的语法与作用：外键（FOREIGN KEY）、CHECK、DEFAULT、AUTO_INCREMENT、ON UPDATE
- 理解外键的级联操作（CASCADE / SET NULL / RESTRICT）及实际取舍
- 能在游戏测试场景中设计符合业务规则的建表语句

---

## 【核心语法】

### 1. 外键约束 FOREIGN KEY

```sql
-- 创建表时定义外键
CREATE TABLE orders (
    order_id   INT PRIMARY KEY AUTO_INCREMENT,
    user_id    INT NOT NULL,
    total_price DECIMAL(10,2),
    -- 外键：user_id 必须在 users 表中存在
    CONSTRAINT fk_order_user 
        FOREIGN KEY (user_id) 
        REFERENCES users(user_id)
        ON DELETE RESTRICT      -- 删父行时阻止（不允许删有订单的用户）
        ON UPDATE CASCADE       -- 父行 user_id 变了，子表自动跟着变
);

-- 单独添加外键（表已存在时）
ALTER TABLE orders
    ADD CONSTRAINT fk_order_user
    FOREIGN KEY (user_id) REFERENCES users(user_id)
    ON DELETE SET NULL ON UPDATE CASCADE;

-- 删除外键
ALTER TABLE orders DROP FOREIGN KEY fk_order_user;
```

> **级联选项一览**：
> | 选项 | ON DELETE 含义 | ON UPDATE 含义 |
> |------|---------------|---------------|
> | CASCADE | 父行删了，子行也删 | 父键改了，子键跟着改 |
> | SET NULL | 父行删了，子键设NULL | 父键改了，子键设NULL（子列须允许NULL） |
> | RESTRICT / NO ACTION | 阻止删除（默认） | 阻止修改 |
> | SET DEFAULT | 设为默认值（MySQL忽略此选项） | 同上 |

### 2. CHECK 约束

```sql
-- MySQL 8.0.16+ 才真正生效！8.0.16之前只是"写了但不检查"
CREATE TABLE players (
    player_id INT PRIMARY KEY AUTO_INCREMENT,
    nickname  VARCHAR(50) NOT NULL,
    level     INT CHECK (level >= 1 AND level <= 100),   -- 等级范围限制
    hp        INT CHECK (hp > 0),                         -- 血量必须正数
    gender    ENUM('M','F','O') CHECK (gender IN ('M','F','O')),
    -- 表级 CHECK（组合条件）
    CONSTRAINT chk_power CHECK (attack_power + defense_power <= 10000)
);

-- 单独添加 CHECK
ALTER TABLE players ADD CONSTRAINT chk_level CHECK (level BETWEEN 1 AND 100);

-- 删除 CHECK
ALTER TABLE players DROP CHECK chk_level;
```

### 3. DEFAULT 默认值

```sql
CREATE TABLE player_stats (
    stat_id     INT PRIMARY KEY AUTO_INCREMENT,
    player_id   INT NOT NULL,
    status      VARCHAR(20) DEFAULT 'online',       -- 默认在线
    login_time  DATETIME DEFAULT CURRENT_TIMESTAMP, -- 默认当前时间
    vip_level   INT DEFAULT 0,                      -- 默认非VIP
    gold        DECIMAL(12,2) DEFAULT 0.00          -- 默认0金币
);

-- 修改默认值
ALTER TABLE player_stats ALTER COLUMN status SET DEFAULT 'offline';

-- 删除默认值
ALTER TABLE player_stats ALTER COLUMN status DROP DEFAULT;
```

### 4. AUTO_INCREMENT 自增

```sql
CREATE TABLE battle_log (
    log_id      INT PRIMARY KEY AUTO_INCREMENT,  -- 自增主键
    player_id   INT NOT NULL,
    enemy_id    INT,
    damage      INT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
) AUTO_INCREMENT = 1000;  -- 指定起始值（默认从1开始）

-- 查看当前自增值
SHOW TABLE STATUS LIKE 'battle_log';  -- Auto_increment 列

-- 修改自增起始值
ALTER TABLE battle_log AUTO_INCREMENT = 5000;

-- 获取刚插入的自增ID
INSERT INTO battle_log (player_id, enemy_id, damage) VALUES (1, 2, 300);
SELECT LAST_INSERT_ID();  -- 返回本次插入的自增ID
```

### 5. ON UPDATE CURRENT_TIMESTAMP

```sql
CREATE TABLE player_records (
    player_id   INT PRIMARY KEY,
    nickname    VARCHAR(50),
    -- created_at：只在 INSERT 时自动填
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    -- updated_at：INSERT 自动填，UPDATE 时也自动刷新！
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 注意：一个表只能有一个 DATETIME/TIMESTAMP 列用 ON UPDATE
-- 多个时间列要用 DATETIME（不带自动更新）+ 触发器手动维护
```

---

## 【实战示例】

### 示例1：基础 — 游戏背包表设计（外键 + CHECK + DEFAULT + AUTO_INCREMENT）

```sql
-- 先建主表
CREATE TABLE players (
    player_id   INT PRIMARY KEY AUTO_INCREMENT,
    nickname    VARCHAR(50) NOT NULL UNIQUE,
    level       INT DEFAULT 1 CHECK (level >= 1 AND level <= 200),
    vip_level   INT DEFAULT 0 CHECK (vip_level BETWEEN 0 AND 15),
    gold        DECIMAL(12,2) DEFAULT 0.00 CHECK (gold >= 0),
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 再建子表（背包），引用主表
CREATE TABLE inventory (
    inv_id      INT PRIMARY KEY AUTO_INCREMENT,
    player_id   INT NOT NULL,
    item_id     INT NOT NULL,
    quantity    INT DEFAULT 1 CHECK (quantity BETWEEN 1 AND 999),
    slot_pos    INT CHECK (slot_pos BETWEEN 1 AND 50),    -- 背包格子位置
    is_bound    TINYINT(1) DEFAULT 0 CHECK (is_bound IN (0, 1)),
    acquired_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_inv_player 
        FOREIGN KEY (player_id) REFERENCES players(player_id)
        ON DELETE CASCADE     -- 玩家删了，背包也删
        ON UPDATE CASCADE,
    CONSTRAINT chk_unique_slot UNIQUE (player_id, slot_pos)  -- 每个格子只能放一件
);
```

### 示例2：进阶 — 订单-商品多表关联（外键级联对比 + 组合CHECK）

```sql
-- 商品表
CREATE TABLE products (
    product_id  INT PRIMARY KEY AUTO_INCREMENT AUTO_INCREMENT=100,
    name        VARCHAR(100) NOT NULL,
    category    VARCHAR(30) DEFAULT 'uncategorized',
    price       DECIMAL(10,2) NOT NULL CHECK (price > 0),
    stock       INT DEFAULT 0 CHECK (stock >= 0),
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 用户表
CREATE TABLE users (
    user_id     INT PRIMARY KEY AUTO_INCREMENT,
    username    VARCHAR(50) NOT NULL UNIQUE,
    balance     DECIMAL(10,2) DEFAULT 0.00 CHECK (balance >= 0),
    status      ENUM('active','banned','suspended') DEFAULT 'active'
);

-- 订单表 — SET NULL级联：商品删了订单保留但商品字段留空
CREATE TABLE orders (
    order_id    INT PRIMARY KEY AUTO_INCREMENT,
    user_id     INT NOT NULL,
    product_id  INT,
    quantity    INT DEFAULT 1 CHECK (quantity BETWEEN 1 AND 100),
    total_price DECIMAL(10,2),
    order_time  DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_order_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_order_product
        FOREIGN KEY (product_id) REFERENCES products(product_id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    -- 组合CHECK：总价格 = 单价 × 数量（近似校验）
    CONSTRAINT chk_total CHECK (total_price >= price * quantity * 0.9)
);

-- 订单日志 — ON UPDATE自动记录修改时间
CREATE TABLE order_logs (
    log_id      INT PRIMARY KEY AUTO_INCREMENT,
    order_id    INT NOT NULL,
    action      VARCHAR(20) CHECK (action IN ('create','pay','cancel','refund')),
    note        TEXT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### 示例3：工作/测试场景 — 恐龙岛项目核心表设计（约束全覆盖 + 测试验证点）

```sql
-- 恐龙表
CREATE TABLE dinosaurs (
    dino_id     INT PRIMARY KEY AUTO_INCREMENT,
    name        VARCHAR(50) NOT NULL CHECK (CHAR_LENGTH(name) >= 2),
    species     VARCHAR(30) NOT NULL DEFAULT 'unknown',
    hp          INT DEFAULT 100 CHECK (hp BETWEEN 10 AND 50000),
    attack      INT DEFAULT 10 CHECK (attack BETWEEN 1 AND 10000),
    defense     INT DEFAULT 5 CHECK (defense BETWEEN 0 AND 5000),
    speed       DECIMAL(5,2) DEFAULT 1.00 CHECK (speed > 0),
    rarity      ENUM('common','rare','epic','legendary') DEFAULT 'common',
    is_owned    TINYINT(1) DEFAULT 0 CHECK (is_owned IN (0,1)),
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 玩家恐龙存储（领地 + 背包）
CREATE TABLE player_dinos (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    player_id   INT NOT NULL,
    dino_id     INT NOT NULL,
    level       INT DEFAULT 1 CHECK (level BETWEEN 1 AND 100),
    hp_current  INT CHECK (hp_current > 0),
    location    ENUM('territory','bag','battle') DEFAULT 'bag',
    slot_index  INT CHECK (slot_index BETWEEN 1 AND 20),
    acquired_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_pd_player
        FOREIGN KEY (player_id) REFERENCES players(player_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_pd_dino
        FOREIGN KEY (dino_id) REFERENCES dinosaurs(dino_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    -- 独占约束：每只恐龙只能被一个玩家拥有
    CONSTRAINT chk_unique_dino UNIQUE (dino_id, player_id)
);

-- 战斗记录表
CREATE TABLE battle_records (
    record_id   INT PRIMARY KEY AUTO_INCREMENT,
    attacker_id INT NOT NULL,
    defender_id INT NOT NULL,
    result      ENUM('win','lose','draw') NOT NULL,
    territory_id INT,
    damage_total INT DEFAULT 0 CHECK (damage_total >= 0),
    duration_sec INT DEFAULT 0 CHECK (duration_sec >= 0),
    battle_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_br_attacker
        FOREIGN KEY (attacker_id) REFERENCES players(player_id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_br_defender
        FOREIGN KEY (defender_id) REFERENCES players(player_id)
        ON DELETE SET NULL ON UPDATE CASCADE
);

-- ===== 测试验证点 =====
-- 1. CHECK 约束验证：插入非法数据应报错
INSERT INTO dinosaurs (name, hp) VALUES ('Rex', 0);    -- 应失败，hp 必须 > 10
INSERT INTO dinosaurs (name, hp) VALUES ('Rex', 60000); -- 应失败，hp 必须 <= 50000

-- 2. 外键验证：引用不存在的主键应报错
INSERT INTO player_dinos (player_id, dino_id) VALUES (9999, 1); -- 应失败，player_id=9999 不存在

-- 3. DEFAULT 验证：省略字段看默认值
INSERT INTO dinosaurs (name, species, hp, attack) VALUES ('Trex', 'T-Rex', 5000, 800);
SELECT rarity, defense, speed, is_owned FROM dinosaurs WHERE name='Trex';
-- 期望：common | 5 | 1.00 | 0

-- 4. AUTO_INCREMENT 验证
INSERT INTO dinosaurs (name) VALUES ('Dino1');
INSERT INTO dinosaurs (name) VALUES ('Dino2');
SELECT LAST_INSERT_ID();  -- 应为第2条的自增ID

-- 5. ON UPDATE 验证
UPDATE dinosaurs SET attack = 900 WHERE name = 'Trex';
SELECT updated_at FROM dinosaurs WHERE name = 'Trex';  -- updated_at 应已刷新
```

---

## 【注意事项/易错点】

### 1. 外键的"坑"

- **存储引擎必须是 InnoDB**：MyISAM 不支持外键，建了也静默忽略！
  ```sql
  -- 确认引擎
  SHOW TABLE STATUS LIKE 'players';  -- Engine 列应为 InnoDB
  ```
- **外键列和被引用列的类型必须完全一致**：INT 对 INT，VARCHAR(50) 对 VARCHAR(50)，连长度都要匹配，否则报错
- **被引用列必须有索引**（通常是 PRIMARY KEY 或 UNIQUE）
- **级联删很危险**：ON DELETE CASCADE 一删父表就连锁删子表，生产环境慎用！测试环境可以大胆用

### 2. CHECK 约束版本差异

- **MySQL 8.0.16 之前**：写了 CHECK 但不检查，任何值都能插入（相当于摆设）
- **MySQL 8.0.16+**：CHECK 真正生效
- 如果你的 MySQL 版本较低，用触发器代替 CHECK 做数据校验

### 3. AUTO_INCREMENT 注意

- 一个表只能有一个 AUTO_INCREMENT 列，且必须是主键或唯一键的一部分
- 删除最大自增ID后，下一个ID不会回填（空洞是正常的，不要纠结）
- LAST_INSERT_ID() 是连接级别的，多并发不会互相干扰

### 4. ON UPDATE CURRENT_TIMESTAMP 限制

- **每个表只能有一个 DATETIME 列自动更新**（MySQL 5.6.5+ 放宽了 TIMESTAMP 限制）
- TIMESTAMP 比 DATETIME 更省空间（4字节 vs 8字节），但 TIMESTAMP 范围窄（1970~2038）
- 如果需要多个"最后修改时间"列，用触发器手动维护

### 5. 外键 vs 应用层校验的取舍

- **优点**：数据库层面强制一致性，不管什么客户端都不会被绕过
- **缺点**：批量操作慢（逐行检查）、级联操作可能意外删数据、迁移困难
- **游戏项目常见做法**：核心表用外键（玩家-订单），高频表不用外键（战斗日志），一致性靠代码保证

---

## 【今日练习题】

### 练习1：设计恐龙岛领地争夺表（必做）

根据恐龙岛项目需求，设计一张 `territories` 表，要求：
- 领地ID自增
- 领地名称不能空，长度 ≥ 2
- 领地等级 1~10，默认1
- 占领者 player_id 外键引用 players 表，ON DELETE SET NULL（玩家走了领地变空）
- 占领时间默认当前时间
- 领地状态：vacant / occupied / contested，默认 vacant
- 防御值 ≥ 0，默认 100

**提示**：写完建表语句后，用 INSERT 测试 CHECK 约束是否生效（故意插入非法数据看报错）

### 练习2：外键级联行为对比（扩展）

创建3张表模拟：玩家 → 装备 → 装备强化记录
- 装备表外键引用玩家，分别用 CASCADE / SET NULL / RESTRICT 三种方式建3个版本的装备表
- 对比：删除一个玩家时，3张装备表的行为有何不同？

```sql
-- 版本A：ON DELETE CASCADE
-- 版本B：ON DELETE SET NULL  
-- 版本C：ON DELETE RESTRICT
-- 各建一张表，插入同样的数据，然后 DELETE 一个玩家，看差异
```

---

## 【一句话总结】

**表设计进阶 = 5种约束保驾护航**：外键保关联一致性、CHECK 保数据合法性、DEFAULT 简化插入、AUTO_INCREMENT 管主键生成、ON UPDATE 自动追踪修改时间——但外键和CHECK在性能与灵活性之间需要权衡取舍。

---

*明天 Day 19：数据库设计范式（第一/二/三范式、反范式设计、实际项目中的取舍）*
