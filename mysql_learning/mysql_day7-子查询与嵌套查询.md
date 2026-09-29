# 🐬 今日MySQL学习 · Day 7/30

**主题**：子查询与嵌套查询

---

## 【学习目标】

- 理解什么是子查询，掌握子查询在 WHERE、FROM、SELECT 三种位置的使用方式
- 掌握 EXISTS / NOT EXISTS 的用法及其与 IN 的区别
- 学会 ANY / ALL 运算符与比较运算符的组合使用
- 能在游戏测试场景中用子查询做数据验证

---

## 【核心语法】

### 1. WHERE 子查询（最常用）

```sql
-- 基础写法：子查询在 WHERE 中作为条件值
SELECT 列名
FROM 表名
WHERE 列名 = (SELECT 子查询返回单个值);      -- 单值子查询
WHERE 列名 IN (SELECT 子查询返回一列多行);   -- 多值子查询（用IN）
```

### 2. FROM 子查询（派生表）

```sql
-- 子查询的结果作为一张"虚拟表"供外层查询使用
SELECT 别名.列名, ...
FROM (SELECT ... FROM ...) AS 别名
WHERE 条件;
```

### 3. SELECT 子查询（标量子查询）

```sql
-- 子查询出现在 SELECT 列表中，每次外层查一行就执行一次
SELECT
    玩家名,
    战力,
    (SELECT AVG(战力) FROM 玩家表) AS 全服平均战力
FROM 玩家表;
```

### 4. EXISTS / NOT EXISTS

```sql
-- EXISTS：子查询返回至少一行时为 TRUE
SELECT * FROM 玩家表 p
WHERE EXISTS (
    SELECT 1 FROM 装备表 e
    WHERE e.玩家ID = p.id AND e.品质 = 'SSR'
);

-- NOT EXISTS：子查询返回空时为 TRUE（常用于"没有..."的场景）
SELECT * FROM 玩家表 p
WHERE NOT EXISTS (
    SELECT 1 FROM 战斗记录表 b
    WHERE b.玩家ID = p.id AND DATE(b.时间) = '2026-06-04'
);
```

### 5. ANY / ALL

```sql
-- ANY：满足任意一个即可（等价于 IN 的场景）
SELECT * FROM 玩家表
WHERE 战力 > ANY (SELECT 战力 FROM 玩家表 WHERE 等级 >= 50);
-- 意思：战力大于"等级>=50的玩家中任意一个"

-- ALL：必须满足所有
SELECT * FROM 玩家表
WHERE 战力 > ALL (SELECT 战力 FROM 玩家表 WHERE 等级 < 30);
-- 意思：战力大于"等级<30的玩家中所有人"（即比最弱的小号还强）
```

---

## 【实战示例】

### 示例1：基础 WHERE 子查询 — 查找战斗力高于平均值的玩家

```sql
-- 先看全服平均战力
SELECT AVG(战力) AS 平均战力 FROM player;

-- 用子查询：找出战力高于全服平均的玩家
SELECT id, 玩家名, 等级, 战力
FROM player
WHERE 战力 > (SELECT AVG(战力) FROM player)
ORDER BY 战力 DESC;
```

> **要点**：子查询必须用括号 `()` 包裹。当子查询返回单个值（AVG/SUM/MAX/MIN）时，外层用 `=`、`>`、`<` 等比较运算符。

### 示例2：FROM 子查询 — 各等级段战力排行 TOP 3

```sql
-- 用派生表先算每个等级的最高战力，再找出各等级段的前3名
SELECT
    等级,
    玩家名,
    战力
FROM (
    SELECT 等级, 玩家名, 战力,
           ROW_NUMBER() OVER (PARTITION BY 等级 ORDER BY 战力 DESC) AS 排名
    FROM player
) AS 等级排名
WHERE 排名 <= 3
ORDER BY 等级, 排名;
```

> **要点**：FROM 子查询结果必须起别名（`AS 等级排名`），否则 MySQL 会报错。这种写法相当于把查询结果当成临时表再用一次。

### 示例3：测试场景 — 用 EXISTS 验证数据一致性

```sql
-- 测试需求：找出"背包里有SSR装备但装备表里没记录"的异常数据
-- 即：玩家背包表有，但装备定义表没有 → 可能是刷装备bug
SELECT bp.玩家ID, bp.装备ID, bp.数量
FROM backpack bp
WHERE NOT EXISTS (
    SELECT 1 FROM equipment e
    WHERE e.id = bp.装备ID
);
```

```sql
-- 测试需求：找出今天登录过但没有任何战斗记录的玩家（可能是挂机异常）
SELECT p.id, p.玩家名, p.最后登录时间
FROM player p
WHERE DATE(p.最后登录时间) = '2026-06-04'
  AND NOT EXISTS (
      SELECT 1 FROM battle_log b
      WHERE b.玩家ID = p.id
        AND DATE(b.创建时间) = '2026-06-04'
  );
```

> **要点**：EXISTS 只关心"有没有"，不关心"有多少"，所以子查询里写 `SELECT 1`（或 `SELECT *`）效率一样。EXISTS 遇到第一条匹配就停，比 IN 更高效（尤其是子集大时）。

### 示例4：ANY / ALL — 分层对比

```sql
-- 找出"战力比任意一个VIP玩家都高"的非VIP玩家（潜在的鲸鱼用户）
SELECT id, 玩家名, VIP等级, 战力
FROM player
WHERE VIP等级 = 0
  AND 战力 > ANY (SELECT 战力 FROM player WHERE VIP等级 >= 3);

-- 找出"战力比所有新手村玩家都高"的玩家（用来校验新手村数据合理性）
SELECT id, 玩家名, 战力, 新手村完成时间
FROM player
WHERE 新手村完成时间 IS NOT NULL
  AND 战力 > ALL (SELECT 战力 FROM player WHERE 新手村完成时间 IS NULL);
```

---

## 【注意事项/易错点】

### 1. 子查询返回多行时不能用单值比较
```sql
-- ❌ 错误：子查询返回多行，不能用 = 比较
SELECT * FROM player WHERE 等级 = (SELECT 等级 FROM player WHERE 战力 > 10000);

-- ✅ 正确：多行用 IN
SELECT * FROM player WHERE 等级 IN (SELECT 等级 FROM player WHERE 战力 > 10000);
```

### 2. EXISTS vs IN 的选择
| 场景 | 推荐 | 原因 |
|------|------|------|
| 子集数据量大 | EXISTS | 短路求值，找到即停 |
| 子集数据量小 | IN 都可以 | IN 会先把子查询结果加载到内存 |
| 两表都很大 | EXISTS | 性能优势明显 |

### 3. FROM 子查询必须起别名
```sql
-- ❌ 错误：缺少别名
SELECT * FROM (SELECT id, 玩家名 FROM player);

-- ✅ 正确
SELECT * FROM (SELECT id, 玩家名 FROM player) AS t;
```

### 4. 相关子查询 vs 非相关子查询
- **非相关子查询**：子查询独立执行一次，结果给外层用（如 `WHERE 战力 > (SELECT AVG(战力) FROM player)`）
- **相关子查询**：子查询引用外层表的列，外层每查一行子查询就执行一次（如 EXISTS 场景）。注意性能，数据量大时相关子查询可能很慢

---

## 【今日练习题】

### 练习1（必做）
```sql
-- 建测试数据
CREATE TABLE IF NOT EXISTS student (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50),
    score INT
);
INSERT INTO student (name, score) VALUES
('张三', 85), ('李四', 92), ('王五', 78),
('赵六', 95), ('钱七', 60), ('孙八', 88);

-- 题目：用子查询找出"分数高于所有学生平均分"的学生
-- 提示：SELECT AVG(score) FROM student 得到平均分
```

### 练习2（进阶）
```sql
-- 用 EXISTS 写法完成：找出"没有成绩低于80分"的学生
-- 即：该学生不存在任何一条 <80 的成绩记录
-- 提示：NOT EXISTS (SELECT 1 FROM student s2 WHERE s2.id = s1.id AND s2.score < 80)
```

---

## 【一句话总结】

子查询就是把一个查询嵌套在另一个查询里，WHERE 里做条件过滤、FROM 里造临时表、EXISTS 里做存在性判断——掌握这三个位置，复杂查询基本都难不倒你。
