# 🐬 每日MySQL学习 · Day 27/30

**主题**：Python + MySQL + pytest（数据库测试用例编写、测试数据清理、断言数据库状态）

---

## 【学习目标】

- 掌握 pytest + pymysql 构建数据库测试用例的标准模式（fixture 准备/清理、参数化用例）
- 学会**测试数据工厂**设计：每次测试用独立数据、测试结束自动清理
- 能在接口测试后**直接断言数据库状态**（订单创建/金币扣减/战力更新等）

---

## 【核心语法】

### 1. pytest fixture 准备/清理数据

```python
import pytest
import pymysql

@pytest.fixture(scope="function")  # 默认function级，每个用例独立
def db_conn():
    """获取数据库连接，测试结束自动关闭"""
    conn = pymysql.connect(
        host="127.0.0.1", port=3306, user="test", password="test123",
        database="dinosaur_island", charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,  # 返回字典方便取值
        autocommit=False  # 测试环境关掉自动提交，手动控制事务
    )
    yield conn  # 把conn交给测试用例
    conn.close()  # 用例结束关闭连接

@pytest.fixture
def test_player(db_conn):
    """造一个测试玩家，用完自动删除（清理）"""
    with db_conn.cursor() as cur:
        cur.execute("""
            INSERT INTO players (username, level, gold, created_at)
            VALUES (%s, %s, %s, NOW())
        """, ("test_player_001", 1, 1000))
        player_id = cur.lastrowid
    db_conn.commit()
    yield player_id  # 给用例
    # 清理：测试结束删除（不破坏其他数据）
    with db_conn.cursor() as cur:
        cur.execute("DELETE FROM players WHERE id = %s", (player_id,))
    db_conn.commit()
```

### 2. 断言数据库状态（核心！）

```python
def assert_db_state(cur, table, where_clause, expected_dict, where_params=()):
    """通用数据库断言：检查某行字段值是否等于预期
    示例：assert_db_state(cur, "players", "id=%s", {"level": 5, "gold": 2000}, (player_id,))
    """
    cur.execute(f"SELECT * FROM {table} WHERE {where_clause}", where_params)
    row = cur.fetchone()
    assert row is not None, f"❌ {table} 中找不到记录: {where_clause}"
    for key, expected in expected_dict.items():
        actual = row[key]
        assert actual == expected, f"❌ 字段 {key} 期望 {expected}，实际 {actual}"
    return True
```

### 3. pytest 参数化批量跑用例

```python
@pytest.mark.parametrize("level,expected_rank", [
    (1, "青铜"), (10, "白银"), (30, "黄金"), (60, "钻石"),
])
def test_player_rank(level, expected_rank, db_conn):
    """参数化：一次跑多组等级测试"""
    with db_conn.cursor() as cur:
        cur.execute("INSERT INTO players (username, level) VALUES (%s, %s)",
                    (f"player_{level}", level))
        pid = cur.lastrowid
        cur.execute("SELECT CASE WHEN level<10 THEN '青铜' WHEN level<30 THEN '白银' "
                    "WHEN level<60 THEN '黄金' ELSE '钻石' END AS r FROM players WHERE id=%s", (pid,))
        rank = cur.fetchone()["r"]
    db_conn.commit()
    assert rank == expected_rank
    db_conn.cursor().execute("DELETE FROM players WHERE id=%s", (pid,))
```

---

## 【实战示例】

### 示例 1：接口测试后核对数据库（订单+金币流水一致性）

```python
import requests
import pymysql

def test_buy_item_deducts_gold_and_creates_order():
    """测试购买道具：金币减少 + 订单生成 + 流水记录"""
    # 前置：造一个测试玩家，初始金币 1000
    conn = pymysql.connect(host="127.0.0.1", user="test", password="test123",
                            database="dinosaur_island", autocommit=False)
    with conn.cursor() as cur:
        cur.execute("INSERT INTO players (username, gold) VALUES ('buyer_001', 1000)")
        player_id = cur.lastrowid
    conn.commit()

    # 调用接口：买一个 100 金币的道具
    resp = requests.post("http://game-api/buy", json={
        "player_id": player_id, "item_id": 1001, "qty": 1
    })
    assert resp.status_code == 200
    assert resp.json()["code"] == 0

    # 数据库断言
    with conn.cursor(cursor=pymysql.cursors.DictCursor) as cur:
        # 玩家金币应该变成 900
        cur.execute("SELECT gold FROM players WHERE id=%s", (player_id,))
        assert cur.fetchone()["gold"] == 900, "金币扣减错误"

        # 订单表应该有一条
        cur.execute("SELECT * FROM orders WHERE player_id=%s AND item_id=1001", (player_id,))
        order = cur.fetchone()
        assert order is not None
        assert order["amount"] == 100
        assert order["status"] == "paid"

        # 金币流水表应该有一条 -100 记录
        cur.execute("SELECT * FROM gold_log WHERE player_id=%s AND type='spend'", (player_id,))
        log = cur.fetchone()
        assert log is not None
        assert log["change"] == -100

    # 清理
    with conn.cursor() as cur:
        cur.execute("DELETE FROM gold_log WHERE player_id=%s", (player_id,))
        cur.execute("DELETE FROM orders WHERE player_id=%s", (player_id,))
        cur.execute("DELETE FROM players WHERE id=%s", (player_id,))
    conn.commit()
    conn.close()
```

### 示例 2：批量造测试数据 + 自动清理（数据工厂模式）

```python
@pytest.fixture
def battle_records_factory(db_conn):
    """战斗记录数据工厂：批量插入N条 + 用完清理"""
    created_ids = []

    def _create(count=10, player_id=1, result="win"):
        with db_conn.cursor() as cur:
            for i in range(count):
                cur.execute("""
                    INSERT INTO battle_records (player_id, opponent_id, result, dmg_dealt, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                """, (player_id, 1000 + i, result, 100 * (i + 1)))
                created_ids.append(cur.lastrowid)
        db_conn.commit()
        return created_ids

    yield _create  # 把工厂函数给用例

    # 清理所有本次造的数据
    if created_ids:
        with db_conn.cursor() as cur:
            placeholders = ",".join(["%s"] * len(created_ids))
            cur.execute(f"DELETE FROM battle_records WHERE id IN ({placeholders})", created_ids)
        db_conn.commit()


def test_win_rate_calculation(battle_records_factory):
    """测试胜率统计：8胜2负 → 80%"""
    battle_records_factory(count=8, result="win")
    battle_records_factory(count=2, result="lose")

    with db_conn.cursor(cursor=pymysql.cursors.DictCursor) as cur:
        cur.execute("""
            SELECT 
                SUM(result='win') AS wins,
                SUM(result='lose') AS loses,
                ROUND(SUM(result='win') * 100.0 / COUNT(*), 1) AS win_rate
            FROM battle_records
        """)
        stats = cur.fetchone()
    assert stats["wins"] == 8
    assert stats["win_rate"] == 80.0
```

### 示例 3：数据库+接口双断言（数据一致性测试）

```python
def test_territory_capture_updates_db_consistently():
    """领地争夺：接口返回成功 + 数据库字段正确 + 战斗记录生成"""
    # 准备：玩家A、玩家B、3个恐龙
    conn = pymysql.connect(host="127.0.0.1", user="test", password="test123",
                            database="dinosaur_island", autocommit=False)
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO players (username) VALUES ('attacker')")
            attacker_id = cur.lastrowid
            cur.execute("INSERT INTO players (username) VALUES ('defender')")
            defender_id = cur.lastrowid
            cur.execute("INSERT INTO territories (name, owner_id) VALUES ('valley_1', %s)", (defender_id,))
            territory_id = cur.lastrowid
        conn.commit()

        # 调用接口：发起领地争夺
        resp = requests.post("http://game-api/territory/attack", json={
            "attacker_id": attacker_id,
            "territory_id": territory_id,
            "dino_team": [1, 2, 3]
        })
        assert resp.json()["code"] == 0

        # 验证 1：领地归属已变
        with conn.cursor(cursor=pymysql.cursors.DictCursor) as cur:
            cur.execute("SELECT owner_id FROM territories WHERE id=%s", (territory_id,))
            new_owner = cur.fetchone()["owner_id"]
            assert new_owner == attacker_id, "领地归属未更新"

        # 验证 2：战斗记录表新增了数据
        with conn.cursor(cursor=pymysql.cursors.DictCursor) as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM battle_records "
                        "WHERE attacker_id=%s AND territory_id=%s", (attacker_id, territory_id))
            assert cur.fetchone()["cnt"] >= 1, "战斗记录未生成"

        # 验证 3：玩家战功积分增加
        with conn.cursor(cursor=pymysql.cursors.DictCursor) as cur:
            cur.execute("SELECT battle_score FROM players WHERE id=%s", (attacker_id,))
            assert cur.fetchone()["battle_score"] > 0, "战功积分未增加"

    finally:
        # 清理：测试结束必删
        with conn.cursor() as cur:
            cur.execute("DELETE FROM battle_records WHERE attacker_id=%s", (attacker_id,))
            cur.execute("DELETE FROM territories WHERE id=%s", (territory_id,))
            cur.execute("DELETE FROM players WHERE id IN (%s, %s)", (attacker_id, defender_id))
        conn.commit()
        conn.close()
```

---

## 【注意事项/易错点】

1. **测试数据隔离是命根子**：每条数据必须有 `test_` 前缀或单独 ID，否则并发跑或重跑会污染真实库。**用完必须删**（teardown），不删等于埋雷。
2. **fixture 顺序问题**：依赖其他 fixture 的 fixture，要先声明再使用（pytest 按名字匹配），不要手动 import 顺序。`scope="function"` 是默认且最安全。
3. **autocommit=False 是双刃剑**：测试环境关掉自动提交，方便 rollback 重置数据；**但忘记 commit 也不会报错**（只是数据没写进去），调试时要多打印。
4. **数据库断言 vs 接口断言**：接口返回 `code=0` ≠ 数据库一定对。**接口测试必须配合数据库状态断言**，才能抓出"接口成功但 DB 没动"或"接口成功但 DB 写错值"这类隐藏 bug。
5. **不要在生产库跑测试**：`user="test"` 单独账号，只给测试库权限，**绝对不能用 root**——这是 20-21 讲的安全原则。

---

## 【今日练习题】

### 练习 1（必做）：升级奖励发放测试
写一个 pytest 用例：测试玩家升级到 10 级时，**金币+1000、背包解锁第2格**。要求：
- 用 fixture 造测试玩家
- 调用一个模拟的 `level_up(player_id)` 函数（你写一个简单 Python 函数，UPDATE level + INSERT gold_log + UPDATE bag_capacity）
- 断言三件事：玩家 level=10、金币+1000、bag_capacity=20
- 测试结束清理数据

### 练习 2（进阶）：并发抢购测试
用 `threading` 起 10 个线程，每个线程调用一个"抢购恐龙"的函数（UPDATE `player_dinosaurs` SET `owner_id=xxx` WHERE `id=N` AND owner_id IS NULL），要求：
- 1 只恐龙只能被 1 个玩家抢到
- 用 `SELECT COUNT(*) WHERE owner_id=xxx` 断言最终只有 1 条更新成功
- 思考：如果不查数据库只看函数返回值，能发现超卖问题吗？

---

## 【一句话总结】

**数据库测试三件套：fixture 准备数据 + 函数/接口执行 + 数据库断言验证状态，最后 teardown 清理——把这套流程封装成模板，从此告别"测试跑完数据库乱掉"。**
