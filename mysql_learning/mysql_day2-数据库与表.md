# 🐬 MySQL学习 · Day 2/30 — 数据库与表的基本操作

## 【学习目标】
- 掌握 CREATE DATABASE、USE、DROP 等数据库级操作
- 学会 CREATE TABLE 建表，理解常用数据类型
- 能独立设计简单的表结构

## 【核心语法】

```sql
-- ========== 数据库操作 ==========

-- 创建数据库（规范写法：指定字符集防乱码）
CREATE DATABASE game_test
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- 查看所有数据库
SHOW DATABASES;

-- 进入数据库
USE game_test;

-- 查看当前在哪个库
SELECT DATABASE();

-- 安全删除
DROP DATABASE IF EXISTS game_test;

-- ========== 表操作 ==========

-- 建表
CREATE TABLE player (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    username    VARCHAR(50) NOT NULL,
    level       INT DEFAULT 1,
    gold        DECIMAL(10,2) DEFAULT 0.00,
    email       VARCHAR(100),
    created_at  DATETIME DEFAULT NOW()
);

-- 查看表
SHOW TABLES;
DESC player;
SHOW CREATE TABLE player;

-- 删除表
DROP TABLE IF EXISTS player;
```

## 【常用数据类型速查】

| 类型 | 用法 | 说明 | 常用度 |
|------|------|------|:--:|
| INT | `INT` | 整数，约±21亿 | ⭐⭐⭐⭐⭐ |
| VARCHAR(n) | `VARCHAR(50)` | 变长字符串 | ⭐⭐⭐⭐⭐ |
| TEXT | `TEXT` | 长文本，不能设默认值 | ⭐⭐⭐ |
| DECIMAL(m,d) | `DECIMAL(10,2)` | 精确小数，金额专用 | ⭐⭐⭐⭐ |
| DATETIME | `DATETIME` | 日期+时间 | ⭐⭐⭐⭐⭐ |
| BOOLEAN | `BOOLEAN` | 0/1真假 | ⭐⭐⭐ |

> 💡 金币/金额用 DECIMAL 不用 FLOAT！FLOAT 有精度误差。

## 【实战示例】

### 1. 创建游戏测试库
```sql
CREATE DATABASE game_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE game_test;
SELECT DATABASE();  -- 确认进对库
```

### 2. 建完整玩家表
```sql
CREATE TABLE player (
    id          INT PRIMARY KEY AUTO_INCREMENT COMMENT '玩家ID',
    username    VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    level       INT DEFAULT 1 COMMENT '等级',
    gold        DECIMAL(10,2) DEFAULT 0.00 COMMENT '金币',
    email       VARCHAR(100) COMMENT '邮箱',
    vip         BOOLEAN DEFAULT FALSE COMMENT '是否VIP',
    created_at  DATETIME DEFAULT NOW() COMMENT '创建时间'
) COMMENT '玩家信息表';
DESC player;
```

### 3. 数据类型选错演示
```sql
-- ❌ VARCHAR存年龄
CREATE TABLE bad (name VARCHAR(20), age VARCHAR(10));
INSERT INTO bad VALUES ('张三', '二十');
SELECT * FROM bad ORDER BY age;  -- 字符串排序结果错误！
```

## 【注意事项/易错点】
- ❌ 金额用 FLOAT → 必须用 DECIMAL
- ❌ 建表不设 CHARACTER SET → 中文乱码
- ⚠️ DROP DATABASE 要加 IF EXISTS 防报错

## 【今日练习题】
1. 建 learn_day2 库 → 建 student 表 → DESC 查看结构
2. 设计一张 equipment 装备表（ID/名称/类型/攻击力/售价/创建时间）

## 【一句话总结】
> 数据库=文件夹，表=表格——先建库再建表，选对数据类型，SQL就成功了一半。
