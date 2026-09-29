# 🐬 今日MySQL学习 · Day 23/30

**主题**：实战：电商数据库 CRUD 操作（模拟用户注册、商品上架、下单、支付全流程SQL）

---

## 【学习目标】

- 掌握电商场景中 INSERT / SELECT / UPDATE / DELETE 的完整使用，覆盖用户、商品、购物车、订单四大模块
- 学会用事务把「下单 + 扣库存 + 生成订单」封装成原子操作，避免数据不一致
- 站在测试角度设计 CRUD 验证点，能用 SQL 快速构造测试数据、核对接口返回值与数据库状态

---

## 【核心语法】

```sql
-- 1. 用户注册：INSERT 插入单条/多条
INSERT INTO users(username, email, phone, password_hash, status, created_at)
VALUES ('test_user', 'test@example.com', '13800138000', MD5('123456'), 'active', NOW());

-- 2. 商品上架：INSERT + 同时返回自增主键
INSERT INTO products(category_id, product_name, price, stock, status, created_at)
VALUES (1, '机械键盘 K8', 399.00, 100, 'on_sale', NOW());
SELECT LAST_INSERT_ID();  -- 获取刚插入的商品 ID

-- 3. 加入购物车：INSERT ... ON DUPLICATE KEY UPDATE 防止重复插入
INSERT INTO shopping_cart(user_id, product_id, quantity, updated_at)
VALUES (1, 5, 2, NOW())
ON DUPLICATE KEY UPDATE
  quantity = quantity + VALUES(quantity),
  updated_at = NOW();

-- 4. 下单：事务内完成扣库存 + 创建订单 + 创建订单明细
START TRANSACTION;
  -- 4.1 校验库存
  SELECT stock FROM products WHERE product_id = 5 FOR UPDATE;
  -- 4.2 扣库存
  UPDATE products SET stock = stock - 2 WHERE product_id = 5 AND stock >= 2;
  -- 4.3 生成订单
  INSERT INTO orders(user_id, total_amount, status, created_at)
  VALUES (1, 798.00, 'paid', NOW());
  SET @order_id = LAST_INSERT_ID();
  -- 4.4 写入订单明细（快照价格，避免后续改价纠纷）
  INSERT INTO order_items(order_id, product_id, product_name, unit_price, quantity)
  SELECT @order_id, product_id, product_name, price, 2
  FROM products WHERE product_id = 5;
COMMIT;

-- 5. 支付后改订单状态：UPDATE
UPDATE orders SET status = 'paid', paid_at = NOW() WHERE order_id = @order_id;

-- 6. 查询某用户全部订单及明细：多表 JOIN
SELECT o.order_id, o.total_amount, o.status, o.created_at,
       oi.product_id, oi.product_name, oi.unit_price, oi.quantity
FROM orders o
INNER JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.user_id = 1
ORDER BY o.created_at DESC;

-- 7. 取消未支付订单：先恢复库存，再删/改订单状态
START TRANSACTION;
  UPDATE products p
  INNER JOIN order_items oi ON p.product_id = oi.product_id
  SET p.stock = p.stock + oi.quantity
  WHERE oi.order_id = 1;

  UPDATE orders SET status = 'cancelled', updated_at = NOW()
  WHERE order_id = 1 AND status = 'pending';
COMMIT;

-- 8. 软删除用户（不真删，改状态）
UPDATE users SET status = 'inactive', updated_at = NOW() WHERE user_id = 1;
```

---

## 【实战示例】

### 1. 基础示例：用户注册 + 商品上架

```sql
-- 假设已使用 Day 22 的电商库表结构
USE ecommerce;

-- 注册测试用户
INSERT INTO users(username, email, phone, password_hash, status, created_at)
VALUES
  ('user_001', 'u1@test.com', '13800000001', MD5('pass001'), 'active', NOW()),
  ('user_002', 'u2@test.com', '13800000002', MD5('pass002'), 'active', NOW());

-- 上架商品
INSERT INTO categories(category_name, parent_id) VALUES ('数码外设', 0);
SET @cat_id = LAST_INSERT_ID();

INSERT INTO products(category_id, product_name, price, stock, status, created_at)
VALUES
  (@cat_id, '无线鼠标 M2', 129.00, 200, 'on_sale', NOW()),
  (@cat_id, 'Type-C 扩展坞', 259.00,  50, 'on_sale', NOW());

-- 验证插入结果
SELECT * FROM users WHERE username LIKE 'user_%';
SELECT * FROM products WHERE category_id = @cat_id;
```

### 2. 进阶示例：购物车 → 下单 → 扣库存 事务流程

```sql
USE ecommerce;

-- 构造购物车
INSERT INTO shopping_cart(user_id, product_id, quantity, updated_at)
VALUES (1, 1, 2, NOW()),   -- 买 2 个无线鼠标
       (1, 2, 1, NOW());   -- 买 1 个扩展坞

-- 查看购物车明细
SELECT c.cart_id, c.user_id, p.product_name, p.price, c.quantity,
       p.price * c.quantity AS subtotal
FROM shopping_cart c
INNER JOIN products p ON c.product_id = p.product_id
WHERE c.user_id = 1;

-- 把购物车转成订单（事务）
START TRANSACTION;
  -- 步骤1：计算总金额
  SELECT SUM(p.price * c.quantity) INTO @total
  FROM shopping_cart c
  INNER JOIN products p ON c.product_id = p.product_id
  WHERE c.user_id = 1;

  -- 步骤2：扣库存（使用库存充足条件，防止超卖）
  UPDATE products p
  INNER JOIN shopping_cart c ON p.product_id = c.product_id
  SET p.stock = p.stock - c.quantity
  WHERE c.user_id = 1 AND p.stock >= c.quantity;

  -- 步骤3：如果库存不足，上面 UPDATE 影响行数 < 购物车商品数，可回滚
  -- 这里为了演示，假设库存充足

  -- 步骤4：创建主订单
  INSERT INTO orders(user_id, total_amount, status, created_at)
  VALUES (1, @total, 'pending', NOW());
  SET @new_order_id = LAST_INSERT_ID();

  -- 步骤5：写入订单明细，快照商品名和价格
  INSERT INTO order_items(order_id, product_id, product_name, unit_price, quantity)
  SELECT @new_order_id, p.product_id, p.product_name, p.price, c.quantity
  FROM shopping_cart c
  INNER JOIN products p ON c.product_id = p.product_id
  WHERE c.user_id = 1;

  -- 步骤6：清空该用户购物车
  DELETE FROM shopping_cart WHERE user_id = 1;
COMMIT;

-- 查看刚生成的订单
SELECT * FROM orders WHERE order_id = @new_order_id;
SELECT * FROM order_items WHERE order_id = @new_order_id;
SELECT product_id, stock FROM products WHERE product_id IN (1, 2);
```

### 3. 工作 / 测试场景示例：接口测试后核对数据库状态

**场景**：你测试的下单接口返回 `{"order_id": 1001, "status": "paid", "total": 388.00}`，需要核对订单、库存、订单明细三张表是否一致。

```sql
-- 测试断言 1：订单存在且金额正确
SELECT order_id, user_id, total_amount, status
FROM orders
WHERE order_id = 1001;
-- 期望：total_amount = 388.00，status = 'paid'

-- 测试断言 2：订单明细条数、单价、数量与请求一致
SELECT product_id, product_name, unit_price, quantity,
       unit_price * quantity AS line_total
FROM order_items
WHERE order_id = 1001;
-- 期望：SUM(line_total) = 订单 total_amount

-- 测试断言 3：库存正确扣减（接口请求前 vs 请求后）
-- 请求前记录 stock_before
-- 请求后执行
SELECT product_id, stock FROM products WHERE product_id IN (1, 2);
-- 期望：stock_after = stock_before - 购买数量

-- 测试断言 4：购物车已清空（如果是购物车下单流程）
SELECT COUNT(*) AS remain_cart
FROM shopping_cart
WHERE user_id = 1;
-- 期望：remain_cart = 0

-- 一键核对脚本
SELECT
  o.order_id,
  o.total_amount AS order_total,
  SUM(oi.unit_price * oi.quantity) AS item_total,
  o.status,
  COUNT(oi.item_id) AS item_count
FROM orders o
LEFT JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_id = 1001
GROUP BY o.order_id, o.total_amount, o.status;
-- 期望：order_total = item_total
```

---

## 【注意事项 / 易错点】

1. **价格 / 金额必须存 `DECIMAL`，不要用 `FLOAT` 或 `DOUBLE`**
   - `DECIMAL(10,2)` 精确到分；`FLOAT` 会出现 388.0000001 这类误差，导致对账失败。

2. **下单扣库存要把 UPDATE 条件写成 `stock >= 购买数量`**
   - 否则并发时两个会话同时读到 stock=1，都执行 `stock - 1`，导致超卖。

3. **订单明细要存价格快照（product_name、unit_price）**
   - 商品后续改价不应影响历史订单金额，否则财务对账会乱。

4. **`LAST_INSERT_ID()` 只在同一会话有效**
   - 测试框架里如果用连接池，要确保取自增 ID 和后续 INSERT 用同一个 connection。

5. **删除操作优先用软删除**
   - 用户注销、订单取消不建议 `DELETE`，改 status 更安全，方便审计和数据分析。

---

## 【今日练习题】

### 练习 1：本地跑通完整购物流程

1. 创建 1 个新用户。
2. 上架 2 件商品，库存分别设置为 10 和 5。
3. 用户把两件商品各买 1 件加入购物车。
4. 用事务完成：扣库存 → 创建订单 → 写订单明细 → 清空购物车。
5. 查询订单总金额，并核对 `orders.total_amount` 是否等于 `order_items` 的 `SUM(unit_price * quantity)`。

### 练习 2：写一个测试核对 SQL

假设接口下单请求参数为：

```json
{
  "user_id": 3,
  "items": [
    {"product_id": 1, "quantity": 2},
    {"product_id": 2, "quantity": 1}
  ]
}
```

接口返回订单号 `order_id = 1002`。请写出一条 SQL，一次性返回以下字段，供自动化测试断言：

- 订单状态
- 订单总金额
- 订单明细总金额
- 购买的商品种类数
- 各商品库存是否 >= 0

提示：用 `LEFT JOIN` + `GROUP BY` + `HAVING` 组合。

---

## 【一句话总结】

电商 CRUD 的核心是 **「价格快照保对账、事务扣库存防超卖、软删除留审计」**，测试人员写 SQL 时要同时校验业务结果和数据库状态一致性。
