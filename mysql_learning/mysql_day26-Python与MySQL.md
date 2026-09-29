# 🐬 今日MySQL学习 · Day 26/30

**主题**：实战：Python + MySQL（pymysql连接、执行SQL、事务管理、封装数据库操作类）

---

## 【学习目标】

- 用 pymysql 连接 MySQL，执行增删改查
- 掌握 Python 中事务管理（commit/rollback/with）
- 学会封装可复用的数据库操作类，写出干净的业务代码

---

## 【核心语法】

### 1. 安装与连接

```python
# 安装 pymysql
# pip install pymysql

import pymysql

# 创建连接
conn = pymysql.connect(
    host='localhost',
    port=3306,
    user='root',
    password='your_password',
    database='game_db',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor  # 返回字典而非元组
)

# 创建游标（用完后关闭）
cursor = conn.cursor()
```

### 2. 执行 SQL 的三种方式

```python
# 方式一：直接 execute（字符串拼接——危险！有SQL注入风险）
cursor.execute(f"SELECT * FROM players WHERE name = '{player_name}'")

# 方式二：参数化查询（推荐！防注入）
cursor.execute("SELECT * FROM players WHERE name = %s", (player_name,))

# 方式三：批量执行 executemany
data = [('Alice', 1), ('Bob', 2), ('Cindy', 3)]
cursor.executemany(
    "INSERT INTO players (name, level) VALUES (%s, %s)",
    data
)
```

### 3. 获取结果

```python
# 单行
row = cursor.fetchone()

# 多行（指定数量）
rows = cursor.fetchmany(10)

# 全部
all_rows = cursor.fetchall()

# 获取影响行数
affected = cursor.rowcount

# 获取最后插入的ID
last_id = cursor.lastrowid
```

### 4. 事务管理

```python
# 手动事务
try:
    conn.begin()  # 显式开始事务（也可省略，execute自动开始）
    cursor.execute("UPDATE accounts SET balance = balance - 100 WHERE id = 1")
    cursor.execute("UPDATE accounts SET balance = balance + 100 WHERE id = 2")
    conn.commit()  # 提交
except Exception as e:
    conn.rollback()  # 回滚
    print(f"事务失败: {e}")

# with 上下文管理器（推荐！自动提交/回滚）
with conn.cursor() as cursor:
    cursor.execute("UPDATE accounts SET balance = balance - 100 WHERE id = 1")
    cursor.execute("UPDATE accounts SET balance = balance + 100 WHERE id = 2")
conn.commit()  # with只管理cursor关闭，commit仍需手动

# 终极方案：自定义上下文管理器（见实战示例3）
```

### 5. 连接池（生产环境必备）

```python
# DBUtils 是常用连接池库
# pip install DBUtils

from dbutils.pooled_db import PooledDB

pool = PooledDB(
    creator=pymysql,
    maxconnections=10,       # 最大连接数
    mincached=2,             # 初始空闲连接数
    blocking=True,           # 连接耗尽时等待而非报错
    host='localhost',
    user='root',
    password='your_password',
    database='game_db',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

# 从池中获取连接
conn = pool.connection()
```

---

## 【实战示例】

### 示例1：基础 CRUD 操作

```python
import pymysql

conn = pymysql.connect(
    host='localhost', user='root', password='root',
    database='game_db', charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

with conn.cursor() as cursor:
    # ---- INSERT ----
    cursor.execute(
        "INSERT INTO players (name, level, gold) VALUES (%s, %s, %s)",
        ("战神阿瑞斯", 50, 10000.00)
    )
    new_id = cursor.lastrowid
    print(f"新增玩家ID: {new_id}")

    # ---- SELECT ----
    cursor.execute("SELECT id, name, level, gold FROM players WHERE id = %s", (new_id,))
    player = cursor.fetchone()
    print(f"查询结果: {player}")

    # ---- UPDATE ----
    cursor.execute(
        "UPDATE players SET gold = gold + %s WHERE id = %s",
        (5000, new_id)
    )
    print(f"更新行数: {cursor.rowcount}")

    # ---- DELETE ----
    cursor.execute("DELETE FROM players WHERE id = %s", (new_id,))
    print(f"删除行数: {cursor.rowcount}")

conn.commit()  # 提交所有变更
conn.close()
```

### 示例2：游戏战斗数据批量录入（executemany）

```python
import pymysql

conn = pymysql.connect(
    host='localhost', user='root', password='root',
    database='game_db', charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

# 模拟一场战斗：2个参战玩家 + 伤害统计
battle_data = [
    (1, 2, 3, 8500, 'WIN'),    # battle_id=3, attacker=1, defender=2, damage=8500, result=WIN
    (2, 1, 3, 6200, 'LOSE'),   # battle_id=3, attacker=2, defender=1, damage=6200, result=LOSE
]

sql = """
    INSERT INTO battle_records (attacker_id, defender_id, battle_id, damage, result)
    VALUES (%s, %s, %s, %s, %s)
"""

with conn.cursor() as cursor:
    cursor.executemany(sql, battle_data)
    print(f"批量插入 {cursor.rowcount} 条战斗记录")

conn.commit()
conn.close()
```

### 示例3：封装数据库操作类（含上下文管理器）⭐

```python
"""
game_db.py - 游戏数据库操作封装类
可直接用于恐龙岛项目的测试数据读写
"""
import pymysql
from typing import Optional, List, Dict, Any


class GameDB:
    """游戏数据库操作类"""

    def __init__(self, host='localhost', port=3306, user='root',
                 password='root', database='game_db', charset='utf8mb4'):
        self.config = {
            'host': host, 'port': port, 'user': user,
            'password': password, 'database': database,
            'charset': charset, 'cursorclass': pymysql.cursors.DictCursor
        }
        self._conn: Optional[pymysql.Connection] = None

    def connect(self):
        """建立连接"""
        if self._conn is None or not self._conn.open:
            self._conn = pymysql.connect(**self.config)
        return self

    def close(self):
        """关闭连接"""
        if self._conn and self._conn.open:
            self._conn.close()

    def execute(self, sql: str, params: tuple = None) -> int:
        """执行写操作（INSERT/UPDATE/DELETE），返回影响行数"""
        self.connect()
        with self._conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            self._conn.commit()
            return cursor.rowcount

    def fetchone(self, sql: str, params: tuple = None) -> Optional[Dict]:
        """查询单行"""
        self.connect()
        with self._conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchone()

    def fetchall(self, sql: str, params: tuple = None) -> List[Dict]:
        """查询多行"""
        self.connect()
        with self._conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchall()

    def fetchcol(self, sql: str, params: tuple = None, col: str = None) -> List:
        """查询单列"""
        rows = self.fetchall(sql, params)
        if col:
            return [row[col] for row in rows]
        return [list(row.values())[0] for row in rows]

    def insert(self, sql: str, params: tuple = None) -> int:
        """插入并返回新ID"""
        self.connect()
        with self._conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            self._conn.commit()
            return cursor.lastrowid

    def insertmany(self, sql: str, data: List[tuple]):
        """批量插入"""
        self.connect()
        with self._conn.cursor() as cursor:
            cursor.executemany(sql, data)
            self._conn.commit()

    def transaction(self, operations: list) -> bool:
        """
        事务：执行一组操作，全部成功才提交
        operations: [(sql, params), ...]
        返回：True成功 / False回滚
        """
        self.connect()
        try:
            with self._conn.cursor() as cursor:
                for sql, params in operations:
                    cursor.execute(sql, params or ())
            self._conn.commit()
            return True
        except Exception as e:
            self._conn.rollback()
            print(f"事务回滚: {e}")
            return False

    # --- 恐龙岛专用方法 ---

    def get_player(self, player_id: int) -> Optional[Dict]:
        """获取玩家信息"""
        return self.fetchone(
            "SELECT * FROM players WHERE id = %s", (player_id,)
        )

    def get_player_dinos(self, player_id: int) -> List[Dict]:
        """获取玩家的恐龙列表"""
        return self.fetchall("""
            SELECT pd.*, ds.name, ds.rarity, ds.base_attack, ds.base_defense
            FROM player_dinosaurs pd
            JOIN dino_species ds ON pd.species_id = ds.id
            WHERE pd.player_id = %s AND pd.is_deleted = 0
        """, (player_id,))

    def add_item(self, player_id: int, item_id: int, quantity: int = 1) -> int:
        """添加道具（存在则叠加，不存在则插入）"""
        return self.execute("""
            INSERT INTO player_items (player_id, item_id, quantity)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE quantity = quantity + VALUES(quantity)
        """, (player_id, item_id, quantity))

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self._conn.commit()
        else:
            self._conn.rollback()
        self.close()


# ===== 使用示例 =====
if __name__ == '__main__':
    db = GameDB(password='your_password')

    # 1. 查询玩家
    player = db.get_player(1)
    print(f"玩家: {player}")

    # 2. 查询玩家恐龙
    dinos = db.get_player_dinos(1)
    for d in dinos:
        print(f"恐龙: {d['name']} (稀有度: {d['rarity']})")

    # 3. 添加道具
    db.add_item(player_id=1, item_id=1001, quantity=5)

    # 4. 事务
    ok = db.transaction([
        ("UPDATE players SET gold = gold - 500 WHERE id = %s AND gold >= 500", (1,)),
        ("UPDATE players SET diamond = diamond + 50 WHERE id = %s", (1,)),
    ])
    print("金币换钻石" if ok else "交易失败")

    # 5. with 用法
    with GameDB(password='your_password') as db:
        player = db.get_player(1)
        print(player)

    db.close()
```

### 示例4：测试场景——接口操作后验证数据库状态

```python
"""
test_db_verify.py - 接口测试中验证数据库状态的典型用法
场景：玩家充值接口调用后，验证数据库是否正确写入
"""
from game_db import GameDB

db = GameDB(password='root')

# 假设接口已调用：POST /api/recharge {player_id: 1, amount: 100}


def test_recharge_db_consistency():
    """验证充值后数据库状态"""
    player_id = 1

    # 1. 查充值前余额
    before = db.fetchone(
        "SELECT gold FROM players WHERE id = %s", (player_id,)
    )
    gold_before = before['gold']

    # 2. 调用充值接口（这里用SQL模拟）
    db.execute(
        "UPDATE players SET gold = gold + 100 WHERE id = %s", (player_id,)
    )

    # 3. 查充值后余额
    after = db.fetchone(
        "SELECT gold FROM players WHERE id = %s", (player_id,)
    )
    gold_after = after['gold']

    # 4. 断言
    assert gold_after == gold_before + 100, \
        f"充值金额不一致！期望+100，实际 {gold_after} - {gold_before}"


def test_recharge_log_written():
    """验证充值日志是否正确记录"""
    player_id = 1

    log = db.fetchone("""
        SELECT * FROM recharge_logs
        WHERE player_id = %s
        ORDER BY created_at DESC
        LIMIT 1
    """, (player_id,))

    assert log is not None, "充值日志未写入！"
    assert log['amount'] == 100, f"日志金额错误: {log['amount']}"
    assert log['status'] == 'SUCCESS', f"日志状态异常: {log['status']}"


def test_item_duplicate_prevention():
    """验证道具唯一性——同一装备不能添加两次"""
    # 先加一个装备
    db.execute("""
        INSERT INTO player_dinosaurs (player_id, species_id, nickname, level)
        VALUES (%s, %s, %s, %s)
    """, (1, 5, '测试霸王龙', 1))

    # 再尝试重复加同一物种
    # 应该抛异常（如果有唯一约束）
    try:
        db.execute("""
            INSERT INTO player_dinosaurs (player_id, species_id, nickname, level)
            VALUES (%s, %s, %s, %s)
        """, (1, 5, '测试霸王龙2', 1))
        print("⚠️ 未拦截重复添加，需检查唯一约束")
    except pymysql.err.IntegrityError:
        print("✅ 正确拦截重复添加")

    # 清理
    db.execute("DELETE FROM player_dinosaurs WHERE nickname = '测试霸王龙'")


# 运行
test_recharge_db_consistency()
test_recharge_log_written()
test_item_duplicate_prevention()

db.close()
```

---

## 【注意事项/易错点】

### 常见错误

1. **忘记 commit —— 最容易被忽视**
   ```python
   cursor.execute("UPDATE players SET gold = 5000 WHERE id = 1")
   # ❌ 没写 conn.commit()，关闭连接后数据丢失！
   conn.commit()  # ✅ 必须提交
   ```
   > 注意：`autocommit=True` 会让每条 SQL 自动提交，但生产环境不推荐。

2. **连接没关闭 —— 连接泄漏**
   ```python
   # ❌ 每次操作都新建连接但不关，连接数打满
   for i in range(1000):
       conn = pymysql.connect(...)
       conn.cursor().execute(...)
       # 忘了 conn.close()

   # ✅ 用 with / 连接池 / try-finally
   ```

3. **参数化查询用 % 而非 format**
   ```python
   name = "O'Brien"  # 含单引号！
   # ❌ SQL注入 + 语法错误
   sql = f"SELECT * FROM players WHERE name = '{name}'"
   # ✅ 正确
   sql = "SELECT * FROM players WHERE name = %s"
   cursor.execute(sql, (name,))
   ```
   注意：pymysql 的占位符是 `%s` 不是 `?`，也不管类型都写 `%s`。

### 性能提醒

- `cursorclass=DictCursor` 方便但比默认 tuple cursor 稍慢，大批量数据考虑用 tuple
- 循环内逐条 INSERT 很慢 → 用 `executemany` 批量插入
- 查询用 `fetchall()` 时注意内存，百万级数据用 `fetchmany()` 分批取或用 SSCursor 流式读

---

## 【今日练习题】

### 题目1：封装分页查询方法

在 GameDB 类中补充一个 `paginate` 方法：

```python
def paginate(self, table: str, page: int = 1, page_size: int = 20,
             where: str = "", order_by: str = "id DESC") -> tuple:
    """
    通用分页查询
    返回: (数据列表, 总记录数, 总页数)
    """
    # 你的代码
    pass
```

要求：支持自定义 WHERE 条件和排序，返回当前页数据 + 分页信息。

### 题目2：用 Python 批量造测试数据

写一个脚本，向 `players` 表批量插入 100 个测试玩家：
- `name` 格式：`test_player_001` ~ `test_player_100`
- `level` 在 1~80 之间随机
- `gold` 在 0~100000 之间随机
- 用 `executemany` 一次性插入

完成后用 SQL 验证：查询 `level > 50` 的玩家数量，并用 Python 打印出来。

---

## 【一句话总结】

> Python 操作 MySQL 的核心三件事：pymysql 连接 + 参数化防注入 + commit 别忘，封装成类后业务代码干净利落，测试时就能在接口调用后秒查数据库验证落库是否准确。
