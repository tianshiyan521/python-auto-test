# 🐬 今日MySQL学习 · Day 15/30

**主题**：存储过程（CREATE PROCEDURE、参数类型 IN/OUT/INOUT、流程控制 IF/CASE/WHILE）

---

## 【学习目标】

- 理解存储过程的本质：**预编译的SQL代码块**，存于数据库服务端，可重复调用
- 掌握三种参数模式：`IN`（输入）、`OUT`（输出）、`INOUT`（输入输出）
- 掌握流程控制语句：`IF/ELSEIF`、`CASE`、`WHILE`、`REPEAT`、`LOOP`

---

## 【核心语法】

```sql
-- ============================================
-- 1. 创建存储过程（基本语法）
-- ============================================
-- ⚠️ 先改分隔符，因为存储过程体内含分号，不改会导致语句提前结束
DELIMITER $$

CREATE PROCEDURE 过程名(参数列表)
BEGIN
    -- 过程体：变量声明放最前面
    DECLARE 变量名 数据类型 DEFAULT 默认值;
    -- SQL 语句 + 流程控制
END$$

DELIMITER ;

-- ============================================
-- 2. 三种参数类型
-- ============================================
-- IN：调用者传入值，过程内只读（默认类型，可省略 IN 关键字）
CREATE PROCEDURE demo_in(IN p_id INT)
BEGIN
    SELECT * FROM players WHERE id = p_id;
END$$

-- OUT：过程内赋值，调用者拿结果
CREATE PROCEDURE demo_out(OUT p_count INT)
BEGIN
    SELECT COUNT(*) INTO p_count FROM players;
END$$

-- INOUT：传入且传出
CREATE PROCEDURE demo_inout(INOUT p_val INT)
BEGIN
    SET p_val = p_val + 100;  -- 基于传入值修改后返回
END$$

-- ============================================
-- 3. 变量声明与赋值
-- ============================================
DECLARE v_name VARCHAR(50) DEFAULT '未命名';   -- 声明+默认值
SET v_name = '张三';                            -- SET 赋值
SELECT col INTO v_name FROM t WHERE id=1;       -- SELECT INTO 赋值

-- ============================================
-- 4. IF 分支
-- ============================================
IF 条件1 THEN
    语句1;
ELSEIF 条件2 THEN
    语句2;
ELSE
    语句3;
END IF;

-- ============================================
-- 5. CASE 分支（两种写法）
-- ============================================
-- 写法A：简单CASE（等值比较）
CASE 变量
    WHEN 值1 THEN 语句1;
    WHEN 值2 THEN 语句2;
    ELSE 语句3;
END CASE;

-- 写法B：搜索CASE（条件判断）
CASE
    WHEN 条件1 THEN 语句1;
    WHEN 条件2 THEN 语句2;
    ELSE 语句3;
END CASE;

-- ============================================
-- 6. 循环
-- ============================================
-- WHILE：先判断再执行（可能0次）
WHILE 条件 DO
    语句;
END WHILE;

-- REPEAT：先执行再判断（至少1次）
REPEAT
    语句;
UNTIL 条件 END REPEAT;

-- LOOP：无限循环，需 LEAVE 退出
label: LOOP
    IF 条件 THEN
        LEAVE label;
    END IF;
    语句;
END LOOP label;

-- ============================================
-- 7. 调用、查看、删除
-- ============================================
CALL 过程名(参数);                           -- 调用
SHOW PROCEDURE STATUS WHERE Db='数据库名';    -- 查看所有过程
SHOW CREATE PROCEDURE 过程名;                 -- 查看创建语句
DROP PROCEDURE IF EXISTS 过程名;             -- 删除
```

---

## 【实战示例】

### 示例1：基础——带 IN 参数查询玩家信息

```sql
-- 创建一个按ID查玩家的存储过程
DELIMITER $$

CREATE PROCEDURE get_player(IN p_id INT)
BEGIN
    SELECT player_name, level, power, gold
    FROM players
    WHERE id = p_id;
END$$

DELIMITER ;

-- 调用
CALL get_player(1001);
```

### 示例2：进阶——IN/OUT/INOUT + IF 流程（战力评级）

```sql
DELIMITER $$

CREATE PROCEDURE rate_player_power(
    IN  p_player_id INT,          -- 输入：玩家ID
    OUT p_level_name VARCHAR(20)  -- 输出：战力等级
)
BEGIN
    DECLARE v_power INT DEFAULT 0;

    -- 查战力值存入变量
    SELECT power INTO v_power FROM players WHERE id = p_player_id;

    -- IF 评级
    IF v_power >= 10000 THEN
        SET p_level_name = 'SSR';
    ELSEIF v_power >= 5000 THEN
        SET p_level_name = 'SR';
    ELSEIF v_power >= 1000 THEN
        SET p_level_name = 'R';
    ELSE
        SET p_level_name = 'N';
    END IF;
END$$

DELIMITER ;

-- 调用并获取 OUT 值
CALL rate_player_power(1001, @result);
SELECT @result AS power_level;  -- 查看输出
```

### 示例3：WHILE 批量生成测试数据（工作场景🌟）

```sql
-- 批量生成 100 条测试玩家记录，适合接口/性能测试造数据
DELIMITER $$

CREATE PROCEDURE batch_insert_players(IN p_count INT)
BEGIN
    DECLARE i INT DEFAULT 1;
    DECLARE v_random_server INT;
    DECLARE v_random_power INT;

    WHILE i <= p_count DO
        SET v_random_server = FLOOR(1 + RAND() * 10);     -- 1~10区
        SET v_random_power  = FLOOR(500 + RAND() * 9500); -- 500~10000战力

        INSERT INTO players(player_name, server_id, level, power, gold, created_at)
        VALUES (
            CONCAT('测试玩家_', LPAD(i, 4, '0')),
            v_random_server,
            FLOOR(1 + RAND() * 60),         -- 1~60级
            v_random_power,
            FLOOR(RAND() * 50000),           -- 0~50000金币
            NOW()
        );

        SET i = i + 1;
    END WHILE;

    SELECT CONCAT('成功生成 ', p_count, ' 条测试数据') AS result;
END$$

DELIMITER ;

-- 执行
CALL batch_insert_players(100);
```

### 示例4：CASE + 游标——更新装备品质分类

```sql
-- 给装备表批量打上品质标签
DELIMITER $$

CREATE PROCEDURE classify_equipment()
BEGIN
    DECLARE done INT DEFAULT 0;
    DECLARE v_id INT;
    DECLARE v_score INT;
    DECLARE v_quality VARCHAR(10);

    -- 声明游标
    DECLARE cur CURSOR FOR SELECT id, score FROM equipment WHERE quality IS NULL;
    -- 声明异常处理：游标读完时设置 done=1
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

    OPEN cur;

    read_loop: LOOP
        FETCH cur INTO v_id, v_score;
        IF done THEN
            LEAVE read_loop;
        END IF;

        -- CASE 分类
        SET v_quality = CASE
            WHEN v_score >= 90 THEN '传说'
            WHEN v_score >= 70 THEN '史诗'
            WHEN v_score >= 50 THEN '稀有'
            ELSE '普通'
        END;

        UPDATE equipment SET quality = v_quality WHERE id = v_id;
    END LOOP;

    CLOSE cur;
    SELECT '装备品质分类完成' AS result;
END$$

DELIMITER ;

CALL classify_equipment();
```

---

## 【注意事项/易错点】

| 易错点 | 说明 |
|---|---|
| **DELIMITER 忘改回来** | 存储过程内含 `;`，必须先用 `DELIMITER $$` 切换，写完再 `DELIMITER ;` 切回 |
| **变量名与列名冲突** | `SELECT col INTO col FROM t` 会导致歧义。变量加 `v_` 前缀，参数加 `p_` 前缀区分 |
| **SELECT INTO 必须返回单行** | 如果查询返回多行，`SELECT ... INTO` 会报错，多行用游标 |
| **OUT 参数调用后必须取** | `CALL proc(@x); SELECT @x;` —— 别忘了第二步看结果 |
| **游标用完要 CLOSE** | 忘记关闭不会立即报错，但游标数量有上限（默认 max_open_files） |
| **存储过程无法用 EXPLAIN** | 优化存储过程要靠 `SHOW PROFILE` 或单独取 SQL 出来测试 |

---

## 【今日练习题】

**题1：写一个存储过程 `get_server_stats`**
- 输入：`IN p_server_id INT`
- 输出：`OUT p_avg_power DECIMAL(10,2)`、`OUT p_total_players INT`
- 功能：统计指定服务器玩家的平均战力和总人数
- 提示：用 `SELECT ... INTO` 把聚合结果赋给 OUT 参数

**题2（挑战）：写一个 `batch_update_gold` 存储过程**
- 输入：`IN p_days INT`（注册天数阈值）
- 功能：给所有注册天数 ≥ p_days 的**老玩家**每人发放 1000 金币登录奖励
- 要求：使用 `DATEDIFF(NOW(), created_at) >= p_days` 条件
- 最后用 `SELECT ROW_COUNT()` 返回影响行数

---

## 【一句话总结】

> 存储过程 = 把一堆 SQL + 流程逻辑打包成数据库内置函数，减少网络开销、提升可维护性，测试同学用它批量造数据、跑数据校验脚本超好用。
