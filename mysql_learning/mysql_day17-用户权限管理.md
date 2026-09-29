# 🐬 今日MySQL学习 · Day 17/30

**主题**：用户权限管理（CREATE USER、GRANT/REVOKE、权限级别、安全最佳实践）

---

## 【学习目标】

- 掌握 MySQL 用户创建与删除的完整语法
- 理解 GRANT/REVOKE 权限授予与收回机制
- 区分全局级、数据库级、表级、列级四个权限层次
- 了解测试人员视角下的数据库安全实践

---

## 【核心语法】

### 1. 创建用户

```sql
-- 创建本地用户，设置密码
CREATE USER 'testuser'@'localhost' IDENTIFIED BY 'Test123!';

-- 创建允许远程连接的用户
CREATE USER 'devuser'@'192.168.1.%' IDENTIFIED BY 'DevPass456!';

-- 创建用户并设置密码过期策略（90天过期）
CREATE USER 'appuser'@'localhost' IDENTIFIED BY 'AppPwd789!' PASSWORD EXPIRE INTERVAL 90 DAY;

-- 查看已有用户
SELECT user, host FROM mysql.user;
```

### 2. 授予权限 GRANT

```sql
-- 授予某个用户对特定数据库的全部权限
GRANT ALL PRIVILEGES ON game_db.* TO 'devuser'@'192.168.1.%';

-- 只授予 SELECT 和 INSERT 权限（适合测试读+写入数据）
GRANT SELECT, INSERT ON game_db.player TO 'testuser'@'localhost';

-- 授予列级权限（只允许查看指定列）
GRANT SELECT (player_id, nickname) ON game_db.player TO 'reportuser'@'localhost';

-- 授权并允许该用户继续授权给别人（WITH GRANT OPTION）
GRANT SELECT ON game_db.* TO 'teamlead'@'localhost' WITH GRANT OPTION;

-- 刷新权限（修改后建议执行）
FLUSH PRIVILEGES;
```

### 3. 收回权限 REVOKE

```sql
-- 收回全部权限
REVOKE ALL PRIVILEGES ON game_db.* FROM 'devuser'@'192.168.1.%';

-- 只收回 INSERT 权限（保留 SELECT）
REVOKE INSERT ON game_db.player FROM 'testuser'@'localhost';

-- 收回 GRANT OPTION 权限
REVOKE GRANT OPTION ON game_db.* FROM 'teamlead'@'localhost';
```

### 4. 查看权限 SHOW GRANTS

```sql
-- 查看指定用户的权限
SHOW GRANTS FOR 'testuser'@'localhost';

-- 查看当前登录用户的权限
SHOW GRANTS FOR CURRENT_USER();
```

### 5. 修改用户与删除用户

```sql
-- 修改密码
ALTER USER 'testuser'@'localhost' IDENTIFIED BY 'NewPwd2026!';

-- 锁定/解锁用户账号
ALTER USER 'testuser'@'localhost' ACCOUNT LOCK;
ALTER USER 'testuser'@'localhost' ACCOUNT UNLOCK;

-- 重命名用户
RENAME USER 'testuser'@'localhost' TO 'qauser'@'localhost';

-- 删除用户
DROP USER 'testuser'@'localhost';
```

---

## 【实战示例】

### 示例1：基础 —— 创建测试专用用户并授权

```sql
-- 场景：测试团队需要一个只读用户来验证数据库数据

-- Step1: 创建测试只读用户
CREATE USER 'qa_readonly'@'localhost' IDENTIFIED BY 'QaReadOnly2026!';

-- Step2: 只授予 SELECT 权限（只读，不能改数据）
GRANT SELECT ON game_db.* TO 'qa_readonly'@'localhost';

-- Step3: 验证权限
SHOW GRANTS FOR 'qa_readonly'@'localhost';
-- 输出: GRANT SELECT ON `game_db`.* TO 'qa_readonly'@'localhost'

-- Step4: 用该用户登录测试
-- mysql -u qa_readonly -p
-- 尝试 INSERT 会报错：INSERT command denied
```

### 示例2：进阶 —— 按权限级别分层授权

```sql
-- 场景：一个游戏项目中，不同角色需要不同权限

-- 运维人员：全局级权限（可管理所有数据库）
CREATE USER 'dba_admin'@'localhost' IDENTIFIED BY 'DbaAdmin!2026';
GRANT ALL PRIVILEGES ON *.* TO 'dba_admin'@'localhost' WITH GRANT OPTION;

-- 开发人员：数据库级权限（只操作 game_db）
CREATE USER 'game_dev'@'192.168.1.%' IDENTIFIED BY 'GameDev2026!';
GRANT ALL PRIVILEGES ON game_db.* TO 'game_dev'@'192.168.1.%';

-- 数据分析师：表级权限（只读特定表）
CREATE USER 'analyst'@'localhost' IDENTIFIED BY 'Analyst2026!';
GRANT SELECT ON game_db.player TO 'analyst'@'localhost';
GRANT SELECT ON game_db.battle_log TO 'analyst'@'localhost';

-- 客服人员：列级权限（只能看玩家昵称和状态，不能看密码/余额）
CREATE USER 'support'@'localhost' IDENTIFIED BY 'Support2026!';
GRANT SELECT (player_id, nickname, status, last_login) ON game_db.player TO 'support'@'localhost';

-- 查看所有用户的权限概览
SELECT user, host,
       IF(Select_priv='Y','全局SELECT','受限') AS select_level
FROM mysql.user
WHERE user NOT IN ('root','mysql.sys','mysql.session');
```

### 示例3：工作/测试场景 —— 测试环境中权限管理最佳实践

```sql
-- 场景：测试人员需要验证接口测试后数据库数据是否正确

-- Step1: 创建测试专用用户（读写但不能删库）
CREATE USER 'qa_tester'@'localhost' IDENTIFIED BY 'QaTest2026!';
GRANT SELECT, INSERT, UPDATE, DELETE ON game_db.* TO 'qa_tester'@'localhost';
-- 注意：没有 DROP, ALTER, CREATE 权限，防止误删表

-- Step2: 创建测试数据清理专用用户（有 TRUNCATE 权限）
CREATE USER 'qa_cleanup'@'localhost' IDENTIFIED BY 'QaClean2026!';
GRANT SELECT, INSERT, DELETE ON game_db.* TO 'qa_cleanup'@'localhost';

-- Step3: 用 qa_tester 登录验证
-- mysql -u qa_tester -pQaTest2026! game_db
-- 能做：SELECT/INSERT/UPDATE/DELETE
-- 不能做：DROP TABLE, ALTER TABLE, CREATE TABLE → 报权限不足

-- Step4: 测试完成后用 qa_cleanup 清理测试数据
DELETE FROM game_db.player WHERE nickname LIKE 'test_%';
DELETE FROM game_db.battle_log WHERE player_id IN (SELECT player_id FROM game_db.player WHERE nickname LIKE 'test_%');

-- Step5: 定期审计：查看谁有危险权限
SELECT user, host,
       IF(Drop_priv='Y','可DROP','无DROP') AS drop_ability,
       IF(Grant_priv='Y','可授权','无授权') AS grant_ability,
       IF(Super_priv='Y','SUPER','无') AS super_priv
FROM mysql.user
WHERE user NOT IN ('root','mysql.sys','mysql.session');
```

---

## 【注意事项/易错点】

### ❗ 常见错误

1. **忘记指定 host 部分**
   - `CREATE USER 'testuser'` 不等于 `CREATE USER 'testuser'@'localhost'`
   - MySQL 用户标识是 `用户名@主机` 组合，两者是不同用户
   - `'testuser'@'%'` 允许任何主机连接，`'testuser'@'localhost'` 只允许本地

2. **GRANT 创建用户 vs CREATE USER**
   - MySQL 8.0 之前：`GRANT ... TO 'newuser'@'localhost'` 会自动创建用户（已废弃）
   - MySQL 8.0+：必须先 `CREATE USER` 再 `GRANT`，否则报错
   - **务必先 CREATE USER 再 GRANT！**

3. **权限修改后未刷新**
   - 虽然 MySQL 8.0 中 GRANT/REVOKE 会自动更新内存，但某些场景仍需 `FLUSH PRIVILEGES`
   - 直接修改 mysql.user 表后，必须 FLUSH PRIVILEGES 才生效

### 🔒 安全提醒

- **生产环境绝不用 root 账号做日常操作**——为每个角色创建独立用户
- **密码必须复杂**——至少8位，包含大小写+数字+特殊字符
- **遵循最小权限原则**——只给需要的权限，不给 ALL
- **定期审计权限**——`SHOW GRANTS` 检查是否有权限过大用户
- **禁止 WITH GRANT OPTION 在生产使用**——防止权限链式传播
- **远程访问限制 host**——用 `192.168.1.%` 代替 `%`，缩小允许范围

---

## 【今日练习题】

### 练习1：创建权限分层用户体系

在你的本地 MySQL 中完成以下操作：

```sql
-- 1. 创建4个用户（密码自己设定，要符合复杂度要求）
--    dba_admin@localhost, game_dev@localhost, qa_readonly@localhost, support@localhost

-- 2. 分别授权：
--    dba_admin → game_db 的全部权限
--    game_dev  → game_db 的 SELECT, INSERT, UPDATE, DELETE
--    qa_readonly → game_db 的 SELECT
--    support   → game_db.player 表的 SELECT (player_id, nickname, status)

-- 3. 用 SHOW GRANTS 验证每个用户的权限

-- 4. 尝试用 qa_readonly 执行 INSERT，观察报错信息

-- 5. 收回 game_dev 的 DELETE 权限，再次查看权限变化
```

### 练习2：权限审计实战

```sql
-- 查询所有非系统用户，列出它们的危险权限级别
-- 判断标准：有 Drop_priv 或 Super_priv 的用户需要重点关注

SELECT user, host,
       Drop_priv, Super_priv, Grant_priv,
       Create_priv, Alter_priv
FROM mysql.user
WHERE user NOT IN ('root','mysql.sys','mysql.session','mysql.infoschema');
```

---

## 【一句话总结】

**权限管理的核心是"最小权限原则"——先 CREATE USER 再 GRANT，按需授权，定期审计，生产环境绝不给 ALL 和 WITH GRANT OPTION。**

---

> 📌 明天预告：Day 18 —— 表设计进阶（外键约束、CHECK约束、DEFAULT值、AUTO_INCREMENT、ON UPDATE）
