# 🐬 MySQL学习 · Day 1/30 — MySQL安装与入门

## 【学习目标】
- 了解MySQL是什么、能干什么、在你工作中的价值
- 掌握MySQL的安装方式和客户端工具（Workbench / DBeaver）
- 成功连接到数据库并执行人生第一条SQL查询

## 【MySQL是什么】
MySQL 是全球最流行的开源关系型数据库。游戏玩家数据、装备数据、战斗记录，大概率就存在MySQL里。

作为测试人员，学会MySQL意味着：
- 能直接查数据库验证接口返回的数据是否正确
- 能自己构造测试数据，不依赖开发给账号
- 能看懂慢查询日志，发现性能问题

## 【核心语法】

```sql
-- 连接到MySQL服务器
-- mysql -h localhost -P 3306 -u root -p

-- 查看当前有哪些数据库
SHOW DATABASES;

-- 选择数据库
USE mysql;

-- 查看当前库有哪些表
SHOW TABLES;

-- 查看表结构
DESC user;

-- 第一个查询：看版本
SELECT VERSION();

-- 看当前时间
SELECT NOW();

-- 看当前用户
SELECT USER();
```

## 【实战示例】

### 1. 安装MySQL
- 下载 mysql-installer-community 离线完整版(565MB)
- 安装时选择 "Developer Default"
- 设置root密码（务必记住）
- 或用 XAMPP / phpStudy 集成环境

### 2. 使用DBeaver连接MySQL
- 下载 DBeaver Community 版
- 新建连接 → MySQL
- Host=localhost, Port=3306, User=root
- 测试连接，自动下载驱动

### 3. 测试工作场景
```sql
USE game_db;
SELECT * FROM player WHERE id = 1001;
-- 接口返回的玩家数据，去数据库验证是否一致
```

## 【注意事项/易错点】
- ❌ 忘记分号 `;` → SQL语句必须分号结尾
- ❌ root密码忘了 → 重置很麻烦，建议存记事本
- ⚠️ 生产环境严禁直接操作

## 【今日练习题】
1. 安装MySQL + DBeaver连接，执行 `SELECT VERSION(), NOW(), USER();`
2. 创建测试库 `test_learn`，建一张 students 表

## 【一句话总结】
> MySQL是测试工程师的第二双眼睛——接口告诉你"数据对了"，但只有亲手查过数据库，你才知道真的对了。
