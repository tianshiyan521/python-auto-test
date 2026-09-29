# 🐬 今日MySQL学习 · Day 10/30

**主题**：日期时间函数

---

## 【学习目标】
- 掌握 MySQL 核心日期时间函数：获取当前时间、格式化、计算时间差、日期加减
- 理解 TIMESTAMPDIFF vs DATEDIFF 的区别和适用场景
- 能在游戏测试中运用日期函数做数据验证（留存分析、活动时间校验、日志时间筛选）

---

## 【核心语法】

```sql
-- ========== 1. 获取当前时间 ==========
SELECT NOW();              -- 当前日期+时间：2026-06-09 12:00:00
SELECT CURDATE();          -- 当前日期：2026-06-09
SELECT CURTIME();          -- 当前时间：12:00:00
SELECT CURRENT_TIMESTAMP();-- 同 NOW()，标准SQL写法
SELECT SYSDATE();          -- 函数执行时的实时时间（NOW()是语句开始时）

-- ========== 2. 日期格式化 ==========
SELECT DATE_FORMAT(NOW(), '%Y-%m-%d');           -- 2026-06-09
SELECT DATE_FORMAT(NOW(), '%Y年%m月%d日');       -- 2026年06月09日
SELECT DATE_FORMAT(NOW(), '%Y-%m-%d %H:%i:%s'); -- 2026-06-09 12:00:00
-- 常用占位符：%Y(4位年) %y(2位) %m(月) %d(日) %H(24时) %h(12时) %i(分) %s(秒) %W(周几英文)

-- 字符串 → 日期
SELECT STR_TO_DATE('2026-06-09', '%Y-%m-%d');    -- 字符串转日期
SELECT STR_TO_DATE('06/09/2026', '%m/%d/%Y');    -- 美式格式转日期

-- ========== 3. 提取日期分量 ==========
SELECT YEAR(NOW()), MONTH(NOW()), DAY(NOW());    -- 2026, 6, 9
SELECT HOUR(NOW()), MINUTE(NOW()), SECOND(NOW());
SELECT DAYOFWEEK(NOW());     -- 星期几（1=周日，7=周六）
SELECT DAYOFYEAR(NOW());     -- 一年中第几天
SELECT WEEK(NOW());          -- 第几周（0-53）
SELECT QUARTER(NOW());       -- 季度（1-4）

-- ========== 4. 日期加减 ==========
SELECT DATE_ADD(NOW(), INTERVAL 7 DAY);           -- 7天后
SELECT DATE_ADD(NOW(), INTERVAL -1 MONTH);        -- 1个月前（等价于 DATE_SUB）
SELECT DATE_SUB(NOW(), INTERVAL 1 HOUR);          -- 1小时前
-- INTERVAL 单位：MICROSECOND, SECOND, MINUTE, HOUR, DAY, WEEK, MONTH, QUARTER, YEAR

SELECT ADDDATE('2026-06-09', 7);                  -- 简化版：加7天
SELECT SUBDATE('2026-06-09', 7);                  -- 简化版：减7天

-- ========== 5. 日期差值计算（重要！）==========
SELECT DATEDIFF('2026-06-09', '2026-06-01');      -- 8（只算日期差，忽略时间）
SELECT TIMESTAMPDIFF(DAY, '2026-06-01', '2026-06-09');    -- 8（天）
SELECT TIMESTAMPDIFF(HOUR, '2026-06-01 08:00', '2026-06-01 18:00'); -- 10（小时）
SELECT TIMESTAMPDIFF(MINUTE, '2026-06-01 08:00', '2026-06-01 08:30'); -- 30（分钟）
-- TIMESTAMPDIFF 支持：MICROSECOND, SECOND, MINUTE, HOUR, DAY, WEEK, MONTH, QUARTER, YEAR

-- ========== 6. 时间戳转换 ==========
SELECT UNIX_TIMESTAMP(NOW());                      -- 当前Unix时间戳（秒）
SELECT FROM_UNIXTIME(1750000000);                  -- 时间戳转日期时间
SELECT FROM_UNIXTIME(1750000000, '%Y-%m-%d');      -- 格式化转换

-- ========== 7. 其他实用函数 ==========
SELECT LAST_DAY(NOW());           -- 本月最后一天
SELECT DAYNAME(NOW());            -- 星期几英文名
SELECT MONTHNAME(NOW());          -- 月份英文名
SELECT MAKEDATE(2026, 160);       -- 2026年第160天 → 2026-06-09
SELECT PERIOD_DIFF(202606, 202601); -- 月份差 → 5
```

---

## 【实战示例】

### 示例1：基础 - 获取当前时间并格式化

```sql
-- 测试场景：记录一条战斗日志，需要记录精确到秒的时间
CREATE TABLE battle_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    player_name VARCHAR(50),
    event_desc VARCHAR(200),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP   -- 插入时自动填当前时间
);

INSERT INTO battle_log (player_name, event_desc) VALUES ('阿克', '进入山海之巅战场');
INSERT INTO battle_log (player_name, event_desc) VALUES ('阿克', '击败Boss青龙');

-- 查看日志，格式化时间显示
SELECT 
    player_name,
    event_desc,
    created_at AS 原始时间,
    DATE_FORMAT(created_at, '%m月%d日 %H:%i') AS 格式化时间
FROM battle_log;
```

### 示例2：进阶 - 计算玩家注册天数与活跃度

```sql
-- 测试场景：计算玩家注册后活跃了多少天，以及距离上次登录过了多久
CREATE TABLE players (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50),
    register_date DATE,
    last_login DATETIME
);

INSERT INTO players VALUES 
(1, '玩家A', '2026-05-01', '2026-06-09 10:30:00'),
(2, '玩家B', '2026-06-01', '2026-06-07 18:00:00'),
(3, '玩家C', '2026-06-08', '2026-06-09 08:00:00');

SELECT 
    name,
    register_date,
    -- 注册了多少天
    DATEDIFF(CURDATE(), register_date) AS 注册天数,
    -- 距上次登录过了多少小时
    TIMESTAMPDIFF(HOUR, last_login, NOW()) AS 离线小时数,
    -- 今天是否登录过（用 DATE 比较）
    DATE(last_login) = CURDATE() AS 今日是否活跃
FROM players;
-- 结果：玩家A注册39天/离线~1h/今日活跃；玩家B注册8天/离线约42h；玩家C注册1天/离线约4h
```

### 示例3：工作场景 - 活动时间校验（测试必备）

```sql
-- 测试场景：验证"端午限时活动"是否在正确的时间窗口内生效
-- 运营配置：2026-06-08 00:00:00 ~ 2026-06-10 23:59:59
-- 作为测试人员，你需要验证活动开启/关闭的边界条件

-- 1）查询活动表并格式化显示
SELECT 
    activity_name,
    DATE_FORMAT(start_time, '%Y-%m-%d %H:%i:%s') AS 开始时间,
    DATE_FORMAT(end_time, '%Y-%m-%d %H:%i:%s') AS 结束时间,
    -- 活动持续天数
    DATEDIFF(end_time, start_time) + 1 AS 持续天数,
    -- 还剩多少天
    DATEDIFF(end_time, NOW()) AS 剩余天数,
    -- 当前是否在活动期间
    NOW() BETWEEN start_time AND end_time AS 活动中_当前
FROM activities;

-- 2）验证活动开启边界：在 2026-06-08 00:00:00 前不应参与
SELECT * FROM player_activity 
WHERE activity_id = 1 
  AND join_time < '2026-06-08 00:00:00';  
-- 预期：返回0行（活动未开启时不应有参与记录）

-- 3）验证活动结束边界：在 2026-06-10 23:59:59 后不应有新的参与
SELECT * FROM player_activity 
WHERE activity_id = 1 
  AND join_time > '2026-06-10 23:59:59';
-- 预期：返回0行

-- 4）统计活动期间每天参与人数（按日期分组）
SELECT 
    DATE(join_time) AS 日期,
    DATE_FORMAT(join_time, '%W') AS 星期,
    COUNT(DISTINCT player_id) AS 参与人数
FROM player_activity
WHERE activity_id = 1
GROUP BY DATE(join_time)
ORDER BY 日期;
```

### 示例4：综合 - 留存分析（游戏核心指标）

```sql
-- 测试场景：计算用户次日留存率、7日留存率
-- 思路：找到用户的注册日，然后看第N天是否还在登录

-- 第1步：构造测试数据
CREATE TABLE login_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    player_id INT,
    login_time DATETIME
);

INSERT INTO login_log (player_id, login_time) VALUES
(1, '2026-06-01 10:00:00'), (1, '2026-06-02 11:00:00'),  -- 次日登录 ✅
(1, '2026-06-03 09:00:00'), (1, '2026-06-08 10:00:00'),  -- 7日登录 ✅
(2, '2026-06-01 14:00:00'),                                -- 只有注册日
(3, '2026-06-01 16:00:00'), (3, '2026-06-08 15:00:00'),  -- 7日登录 ✅
(4, '2026-06-08 08:00:00'), (4, '2026-06-09 09:00:00');  -- 次日登录 ✅

-- 第2步：计算次日留存（第1天注册，第2天登录）
-- 使用 TIMESTAMPDIFF 按天比较
SELECT 
    reg.player_id,
    MIN(reg.login_time) AS 注册时间,
    -- 判断是否有次日登录
    IF(SUM(TIMESTAMPDIFF(DAY, reg.login_time, login.login_time) = 1) > 0, 
       '是', '否') AS 次日留存
FROM login_log reg
LEFT JOIN login_log login 
    ON reg.player_id = login.player_id 
    AND login.login_time > reg.login_time  -- 登录在注册之后
GROUP BY reg.player_id;
```

---

## 【注意事项/易错点】

| 易错点 | 说明 |
|--------|------|
| **DATEDIFF vs TIMESTAMPDIFF** | `DATEDIFF(a, b)` 只比较日期部分，忽略时分秒，结果是 `a - b` 的天数。`TIMESTAMPDIFF(unit, b, a)` 按实际时间差计算，精确到指定的单位（小时/分钟等），**参数顺序是老的在前、新的在后**！ |
| **NOW() vs SYSDATE()** | `NOW()` 在一条SQL语句中始终返回语句开始的时间（即使语句执行了很久）；`SYSDATE()` 返回函数执行那一刻的实时时间。做一致性校验时注意这个差异。 |
| **DATE_FORMAT 大小写敏感** | `%Y` 是4位年(2026)，`%y` 是2位(26)；`%M` 是全称月份(June)，`%m` 是数字(06)。写错了结果完全不对。 |
| **STR_TO_DATE 容错差** | 如果字符串格式和模板不匹配，返回 NULL，不会报错。调试时记得先 `SELECT STR_TO_DATE(...)` 确认转换成功。 |
| **INTERVAL 单位的坑** | `INTERVAL 1 MONTH` 在 1月31日执行 → 结果是 2月28/29日（MySQL会自动处理月末），但不等于 `INTERVAL 30 DAY`！ |
| **时区问题** | `NOW()` 取的是 MySQL 服务器时区。如果游戏服务器和数据库服务器时区不同，时间比较可能出错。用 `SELECT @@global.time_zone;` 查看时区。 |

---

## 【今日练习题】

### 练习题1：活动倒计时
某游戏"五一劳动节活动"配置时间为 `2026-05-01 00:00:00` ~ `2026-05-07 23:59:59`。

写一条 SQL，输出：
- 活动已过多少天（从结束时间到现在的天数）
- 格式化显示活动开始和结束时间为 `5月1日 00:00` 格式

### 练习题2：玩家等级升级速度分析
表 `level_up_log(player_id, from_level, to_level, upgrade_time)` 记录了每次升级。

写一条 SQL，找出从1级升到10级**用时最短**的玩家，输出玩家ID和总用时（小时）。

---

## 【一句话总结】
> 日期时间函数的核心就两件事——**格式化显示给人看**（DATE_FORMAT）和**计算时间差拿来做分析**（TIMESTAMPDIFF），游戏测试中验证活动时间窗口、计算留存率、分析升级速度，全离不开它们。
