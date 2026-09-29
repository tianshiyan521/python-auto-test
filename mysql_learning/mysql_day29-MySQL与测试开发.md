# 🐬 今日MySQL学习 · Day 29/30

**主题**：MySQL与测试开发

---

## 【学习目标】

- 学会在接口测试中验证数据库状态，做到“接口返回 + 数据库”双断言
- 掌握测试数据一致性检查的常用SQL与Python封装方法
- 理解测试数据工厂（Data Factory）的设计思路：造数据 → 跑测试 → 自动清理

---

## 【核心语法】

### 1. 接口测试后核对数据库的常用SQL

```sql
-- 根据业务流水号查单条记录
SELECT * FROM orders WHERE order_no = 'O202507070001';

-- 多表一致性核对：订单金额 = 支付金额
SELECT o.order_id, o.total_amount, p.pay_amount
FROM orders o
JOIN payments p ON o.order_id = p.order_id
WHERE o.order_id = 1001;

-- 状态机校验：下单后订单状态应为 'paid'
SELECT status FROM orders WHERE order_no = 'O202507070001';

-- 金币/钻石变动核对：玩家充值前后余额差 = 充值金额
SELECT player_id, currency_type, amount
FROM currency_log
WHERE player_id = 2001 AND currency_type = 'gold'
ORDER BY created_at DESC LIMIT 1;
```

### 2. Python + pytest 数据库断言常用封装

```python
# assert_db_state.py：通用数据库断言函数
import pymysql

def assert_db_state(conn, sql, expected, params=None, msg="数据库状态断言失败"):
    """
    执行SQL，断言返回结果与期望值一致
    expected: list[dict] 或 list[tuple]
    """
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute(sql, params)
        actual = cur.fetchall()
        assert actual == expected, f"{msg}\n实际: {actual}\n期望: {expected}"

# 使用示例：充值成功后断言玩家金币
assert_db_state(
    conn,
    "SELECT gold FROM players WHERE player_id = %s",
    [{"gold": 1150}],
    params=(2001,),
    msg="充值后玩家金币未正确到账"
)
```

### 3. 测试数据工厂核心思想

```python
# data_factory.py：统一造数据 + 自动回滚/清理
class DataFactory:
    def __init__(self, conn):
        self.conn = conn

    def create_player(self, nickname="测试玩家", gold=1000, diamonds=0):
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO players (nickname, gold, diamonds) VALUES (%s, %s, %s)",
                (nickname, gold, diamonds)
            )
            self.conn.commit()
            return cur.lastrowid  # 返回玩家ID

    def create_dinosaur(self, player_id, species_id, level=1):
        # 省略具体SQL
        pass

    def cleanup(self, table, pk_list):
        # 测试结束后删除测试数据
        placeholders = ",".join(["%s"] * len(pk_list))
        sql = f"DELETE FROM {table} WHERE id IN ({placeholders})"
        with self.conn.cursor() as cur:
            cur.execute(sql, tuple(pk_list))
            self.conn.commit()
```

---

## 【实战示例】

### 示例1：基础示例 — 接口登录后核对最后登录时间

```python
import requests
import pymysql

# 1. 调接口：登录
resp = requests.post("/api/login", json={"username": "test001", "password": "123456"})
assert resp.status_code == 200

# 2. 查数据库：验证 last_login_time 被更新
conn = pymysql.connect(host="localhost", user="root", password="123456", database="game_db")
with conn.cursor(pymysql.cursors.DictCursor) as cur:
    cur.execute(
        "SELECT last_login_time FROM players WHERE username = %s",
        ("test001",)
    )
    row = cur.fetchone()
    assert row["last_login_time"] is not None, "登录后未更新最后登录时间"
conn.close()
```

### 示例2：进阶示例 — 充值到账一致性检查（订单 + 金币流水 + 玩家余额）

```python
# 测试用例：充值 100 元购买 1000 金币
order_no = "PAY20250707120001"
resp = requests.post("/api/recharge", json={
    "player_id": 2001,
    "amount": 100,
    "order_no": order_no
})
assert resp.json()["code"] == 0

# 数据库三表一致性校验
sql = """
SELECT p.player_id,
       p.gold AS player_gold,
       o.order_no,
       o.amount AS recharge_amount,
       l.amount AS log_amount
FROM players p
JOIN orders o ON p.player_id = o.player_id
JOIN currency_log l ON o.order_no = l.related_order_no
WHERE o.order_no = %s
"""
with conn.cursor(pymysql.cursors.DictCursor) as cur:
    cur.execute(sql, (order_no,))
    row = cur.fetchone()
    assert row is not None, "充值订单未写入数据库"
    assert row["log_amount"] == 1000, f"金币流水应为+1000，实际{row['log_amount']}"
    assert row["player_gold"] >= 1000, "玩家金币余额未增加"
```

### 示例3：工作/测试场景示例 — 恐龙岛领地争夺战接口后验证数据库

```python
# 场景：玩家A进攻玩家B领地，接口返回胜利，验证数据库
# 1. 调用接口
resp = requests.post("/api/territory/battle", json={
    "attacker_id": 3001,
    "defender_id": 3002,
    "territory_id": 5001
})
result = resp.json()
assert result["code"] == 0

winner_id = result["data"]["winner_id"]

# 2. 验证战斗记录表
sql = """
SELECT winner_id, territory_id, battle_time
FROM battle_records
WHERE attacker_id = %s AND defender_id = %s
ORDER BY battle_time DESC LIMIT 1
"""
with conn.cursor(pymysql.cursors.DictCursor) as cur:
    cur.execute(sql, (3001, 3002))
    row = cur.fetchone()
    assert row["winner_id"] == winner_id, "战斗记录表胜者ID与接口返回不一致"

# 3. 验证领地归属更新
sql = "SELECT owner_id FROM territories WHERE territory_id = %s"
with conn.cursor(pymysql.cursors.DictCursor) as cur:
    cur.execute(sql, (5001,))
    row = cur.fetchone()
    assert row["owner_id"] == winner_id, "领地归属未更新为胜者"

# 4. 验证双方战损/奖励记录
sql = """
SELECT player_id, reward_gold, reward_exp
FROM battle_rewards
WHERE battle_id = (SELECT MAX(battle_id) FROM battle_records)
"""
with conn.cursor(pymysql.cursors.DictCursor) as cur:
    cur.execute(sql)
    rows = cur.fetchall()
    assert len(rows) >= 1, "战斗奖励未写入"
```

---

## 【注意事项/易错点】

1. **只断言接口返回不够**：很多Bug是接口返回成功但数据库没写入或写错，必须做“接口 + 数据库”双断言。
2. **测试数据一定要隔离**：每个用例造的数据最好带唯一标识（如UUID、时间戳），避免多测试并发时互相污染。
3. **清理必须finally**：用pytest的`yield` fixture或`try...finally`保证即使断言失败也会删除脏数据。
4. **不要直接删生产库**：测试脚本里的数据库连接必须是测试环境，配置文件和环境变量要严格区分。
5. **时间字段不要精确到秒断言**：用`BETWEEN`或只比较日期部分，避免毫秒级差异导致用例不稳定。

```sql
-- 推荐：时间断言用范围
SELECT * FROM orders
WHERE order_no = 'O202507070001'
  AND created_at BETWEEN '2025-07-07 11:54:00' AND '2025-07-07 11:56:00';
```

---

## 【今日练习题】

### 练习1：手动验证一次登录接口

在本地MySQL中建一张`players`表，字段包含`player_id`、`username`、`last_login_time`。写一个Python脚本：
1. 调用模拟登录接口（或直接执行UPDATE模拟登录）
2. 查询`last_login_time`是否被更新
3. 断言时间不为NULL

### 练习2：设计测试数据工厂

为恐龙岛项目设计一个`GameDataFactory`类，至少包含：
- `create_player()`：创建玩家，返回player_id
- `create_dinosaur(player_id, species_id)`：给玩家创建恐龙
- `cleanup_players(player_ids)`：批量删除测试玩家及其关联数据

要求：造数据使用独立账号连接测试库，数据带`test_`前缀便于识别，测试结束后必须能清理。

---

## 【一句话总结】

测试开发的核心不是“接口通了”，而是“接口通了之后，数据库里的数据真的对了吗？”——用SQL做数据库断言，用数据工厂保证测试隔离，才算真正的自动化测试。

---

_今日学习完毕，明天 Day 30 将进行30天知识体系总结与高频面试题复习。_
