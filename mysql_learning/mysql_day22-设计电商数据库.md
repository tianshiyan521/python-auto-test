🐬 今日MySQL学习 · Day 22/30
**主题**：实战：设计一个电商数据库（用户表、商品表、订单表、关联设计、完整建表语句）

---

## 【学习目标】
- 从零设计一个完整电商数据库，理解表与表之间的关联关系（一对多、多对多）
- 掌握外键约束、索引设计、字段类型选择的实战决策
- 写出可直接在MySQL中运行的完整建表脚本

---

## 【核心语法】

```sql
-- ========== 1. 创建数据库并指定字符集 ==========
CREATE DATABASE ecommerce
  CHARACTER SET utf8mb4          -- 支持emoji和中文
  COLLATE utf8mb4_unicode_ci;    -- 大小写不敏感排序
USE ecommerce;

-- ========== 2. 一对多关系：用户 → 订单 ==========
-- 多方（订单）存外键，指向一方（用户）主键
CREATE TABLE orders (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,                    -- 外键列
  FOREIGN KEY (user_id) REFERENCES users(id)  -- 外键约束
    ON DELETE RESTRICT                         -- 有订单不能删用户
    ON UPDATE CASCADE                          -- 用户ID变了自动同步
);

-- ========== 3. 多对多关系：订单 ↔ 商品（通过中间表）==========
CREATE TABLE order_items (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  order_id BIGINT NOT NULL,
  product_id BIGINT NOT NULL,
  quantity INT NOT NULL DEFAULT 1,
  unit_price DECIMAL(10,2) NOT NULL,          -- 下单时价格（快照）
  FOREIGN KEY (order_id) REFERENCES orders(id),
  FOREIGN KEY (product_id) REFERENCES products(id),
  UNIQUE KEY uk_order_product (order_id, product_id)  -- 同一订单不重复
);

-- ========== 4. 常用字段默认值与约束 ==========
CREATE TABLE products (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(200) NOT NULL COMMENT '商品名',
  price DECIMAL(10,2) NOT NULL DEFAULT 0 COMMENT '售价',
  stock INT NOT NULL DEFAULT 0 COMMENT '库存',
  status TINYINT NOT NULL DEFAULT 1 COMMENT '1上架 0下架',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_status (status),
  INDEX idx_category (category_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品表';
```

---

## 【实战示例】

### 示例 1：完整的电商数据库建表（共 7 张核心表）

```sql
-- ============================================
-- 电商数据库完整建表脚本（可直接运行）
-- ============================================
CREATE DATABASE IF NOT EXISTS ecommerce
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ecommerce;

-- ① 用户表
CREATE TABLE users (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
  password_hash CHAR(60) NOT NULL COMMENT '密码哈希(bcrypt)',
  nickname VARCHAR(50) DEFAULT '' COMMENT '昵称',
  phone CHAR(11) DEFAULT '' COMMENT '手机号',
  email VARCHAR(100) DEFAULT '' COMMENT '邮箱',
  balance DECIMAL(12,2) NOT NULL DEFAULT 0.00 COMMENT '账户余额',
  user_level TINYINT NOT NULL DEFAULT 0 COMMENT '0普通 1VIP 2超级VIP',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_phone (phone),
  INDEX idx_level (user_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- ② 商品分类表（自关联，支持无限级分类）
CREATE TABLE categories (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(50) NOT NULL COMMENT '分类名',
  parent_id INT DEFAULT NULL COMMENT '父分类ID，NULL=顶级分类',
  sort_order INT NOT NULL DEFAULT 0 COMMENT '排序',
  FOREIGN KEY (parent_id) REFERENCES categories(id)
    ON DELETE SET NULL,
  INDEX idx_parent (parent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品分类表';

-- ③ 商品表
CREATE TABLE products (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  category_id INT NOT NULL COMMENT '分类ID',
  name VARCHAR(200) NOT NULL COMMENT '商品名称',
  description TEXT COMMENT '商品描述',
  price DECIMAL(10,2) NOT NULL COMMENT '原价',
  discount_price DECIMAL(10,2) DEFAULT NULL COMMENT '折扣价，NULL=无折扣',
  stock INT NOT NULL DEFAULT 0 COMMENT '库存',
  sales_volume INT NOT NULL DEFAULT 0 COMMENT '销量',
  status TINYINT NOT NULL DEFAULT 1 COMMENT '1上架 2下架 3缺货',
  main_image VARCHAR(500) DEFAULT '' COMMENT '主图URL',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (category_id) REFERENCES categories(id),
  INDEX idx_category (category_id),
  INDEX idx_status (status),
  INDEX idx_price (price),
  INDEX idx_name (name(50))          -- 前缀索引，节省空间
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品表';

-- ④ 收货地址表
CREATE TABLE addresses (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  receiver_name VARCHAR(50) NOT NULL COMMENT '收货人',
  phone CHAR(11) NOT NULL COMMENT '电话',
  province VARCHAR(30) NOT NULL,
  city VARCHAR(30) NOT NULL,
  district VARCHAR(30) NOT NULL COMMENT '区/县',
  detail VARCHAR(200) NOT NULL COMMENT '详细地址',
  is_default TINYINT NOT NULL DEFAULT 0 COMMENT '1=默认地址',
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX idx_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='收货地址表';

-- ⑤ 购物车表（用户-商品多对多）
CREATE TABLE shopping_cart (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  product_id BIGINT NOT NULL,
  quantity INT NOT NULL DEFAULT 1 COMMENT '数量',
  added_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
  UNIQUE KEY uk_user_product (user_id, product_id),  -- 同一用户同一商品不重复
  INDEX idx_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='购物车';

-- ⑥ 订单表
CREATE TABLE orders (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  order_no VARCHAR(32) NOT NULL UNIQUE COMMENT '订单号(业务唯一)',
  user_id BIGINT NOT NULL,
  address_id BIGINT DEFAULT NULL COMMENT '收货地址ID（下单时快照）',
  total_amount DECIMAL(12,2) NOT NULL COMMENT '订单总金额',
  discount_amount DECIMAL(12,2) NOT NULL DEFAULT 0.00 COMMENT '优惠金额',
  pay_amount DECIMAL(12,2) NOT NULL COMMENT '实付金额',
  order_status TINYINT NOT NULL DEFAULT 1 COMMENT '1待支付 2已支付 3已发货 4已完成 5已取消 6已退款',
  pay_time DATETIME DEFAULT NULL COMMENT '支付时间',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (address_id) REFERENCES addresses(id) ON DELETE SET NULL,
  INDEX idx_user (user_id),
  INDEX idx_order_no (order_no),
  INDEX idx_status (order_status),
  INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单表';

-- ⑦ 订单明细表（订单-商品多对多中间表）
CREATE TABLE order_items (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  order_id BIGINT NOT NULL,
  product_id BIGINT NOT NULL,
  product_name VARCHAR(200) NOT NULL COMMENT '商品名称快照',
  product_image VARCHAR(500) DEFAULT '' COMMENT '商品图片快照',
  unit_price DECIMAL(10,2) NOT NULL COMMENT '下单时单价',
  quantity INT NOT NULL COMMENT '数量',
  sub_total DECIMAL(12,2) NOT NULL COMMENT '小计 = unit_price * quantity',
  FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(id),
  INDEX idx_order (order_id),
  INDEX idx_product (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单明细表';
```

### 示例 2：设计思路拆解——为什么这样设计？

```
【表关系图谱】

users (1) ──────< addresses (N)      一个用户多个收货地址
users (1) ──────< orders (N)          一个用户多个订单
users (1) >───── shopping_cart >──── (1) products    多对多：用户↔商品
orders (1) ──────< order_items (N)   一个订单多个明细
products (1) >─── order_items >─── (1) orders        多对多：订单↔商品
categories (1) ──< categories (N)    自关联：分类树
categories (1) ──< products (N)      一个分类多个商品

【设计决策要点】
1. order_items 快照了 product_name / unit_price：
   → 即使商品后来改名或涨价，历史订单看到的还是下单时的数据
2. order_no 是业务唯一键，id 是物理主键：
   → 对外暴露 order_no（防遍历），内部用 id 做关联（效率高）
3. categories 用 parent_id 自关联：
   → 一个表搞定无限级分类：手机 → 苹果 → iPhone 15
4. 金额用 DECIMAL(12,2) 不用 FLOAT/DOUBLE：
   → 避免浮点精度问题（0.1 + 0.2 != 0.3）
```

### 示例 3：生成测试数据并验证设计

```sql
-- 插入测试分类
INSERT INTO categories (name, parent_id, sort_order) VALUES
('电子产品', NULL, 1),
('服装', NULL, 2),
('手机', 1, 1),
('笔记本', 1, 2),
('男装', 2, 1),
('女装', 2, 2);

-- 插入测试用户（密码是 bcrypt 哈希的 "123456"）
INSERT INTO users (username, password_hash, nickname, phone, email, balance, user_level) VALUES
('zhangsan', '$2b$12$LJ3m4ys3Lk0TsIqYxKdDVeUv3RqRZ5fM2bP8nKcSxXwOuO0iVvNYu', '张三', '13800001001', 'zhangsan@test.com', 5000.00, 1),
('lisi',     '$2b$12$LJ3m4ys3Lk0TsIqYxKdDVeUv3RqRZ5fM2bP8nKcSxXwOuO0iVvNYu', '李四', '13800001002', 'lisi@test.com', 1000.00, 0);

-- 插入测试商品
INSERT INTO products (category_id, name, description, price, discount_price, stock) VALUES
(3, 'iPhone 15 Pro', '苹果最新旗舰手机', 8999.00, 8499.00, 100),
(3, '华为Mate 60 Pro', '华为旗舰手机', 6999.00, NULL, 50),
(4, 'MacBook Air M3', '苹果轻薄笔记本', 8999.00, 8499.00, 30),
(5, '纯棉T恤-白色', '100%纯棉，舒适透气', 129.00, 99.00, 500);

-- 插入收货地址
INSERT INTO addresses (user_id, receiver_name, phone, province, city, district, detail, is_default) VALUES
(1, '张三', '13800001001', '广东省', '深圳市', '南山区', '科技园路1号', 1),
(1, '张三', '13800001001', '广东省', '广州市', '天河区', '天河路100号', 0);

-- 加入购物车
INSERT INTO shopping_cart (user_id, product_id, quantity) VALUES
(1, 1, 1),   -- 张三买了1台iPhone
(1, 3, 1),   -- 张三买了1台MacBook
(1, 4, 2);   -- 张三买了2件T恤

-- 创建订单（模拟下单流程）
INSERT INTO orders (order_no, user_id, address_id, total_amount, pay_amount, order_status)
VALUES ('ORD20260626001', 1, 1, 17997.00, 17497.00, 1);

INSERT INTO order_items (order_id, product_id, product_name, unit_price, quantity, sub_total) VALUES
(1, 1, 'iPhone 15 Pro', 8499.00, 1, 8499.00),
(1, 3, 'MacBook Air M3', 8499.00, 1, 8499.00),
(1, 4, '纯棉T恤-白色', 99.00, 2, 198.00);

-- 验证：订单总金额是否与明细小计一致
SELECT
  o.order_no,
  o.total_amount AS '订单总金额',
  SUM(oi.sub_total) AS '明细合计',
  o.total_amount - SUM(oi.sub_total) AS '差额'
FROM orders o
JOIN order_items oi ON o.id = oi.order_id
WHERE o.id = 1
GROUP BY o.id, o.order_no, o.total_amount;

-- 验证：库存是否充足（测试视角）
SELECT
  p.id,
  p.name,
  p.stock,
  p.sales_volume,
  SUM(COALESCE(oi.quantity, 0)) AS '待发货数量'
FROM products p
LEFT JOIN order_items oi ON p.id = oi.product_id
LEFT JOIN orders o ON oi.order_id = o.id AND o.order_status IN (1,2,3)  -- 未完成订单
GROUP BY p.id, p.name, p.stock, p.sales_volume
HAVING p.stock < SUM(COALESCE(oi.quantity, 0));  -- 库存不足的商品
```

---

## 【注意事项/易错点】

1. **金额永远用 DECIMAL，不要用 FLOAT/DOUBLE**
   ```sql
   -- ❌ 错误：FLOAT 精度丢失
   price FLOAT;
   -- ✅ 正确
   price DECIMAL(10,2);
   ```
   原因：`0.1 + 0.2 = 0.30000000000000004` 在浮点数中是真实存在的。

2. **order_items 要存商品快照，不要只存 product_id 然后去 JOIN**
   ```sql
   -- ❌ 只存 product_id：商品涨价后历史订单金额会变
   -- ✅ 同时存 product_name + unit_price：历史数据不改
   ```
   这是"反范式"在实际项目中的经典应用——历史数据不能被当前数据影响。

3. **外键列类型必须与被引用列完全一致（含 UNSIGNED）**
   ```sql
   -- ❌ 主表 id 是 BIGINT，外键用 INT → 报错
   -- ✅ 类型、长度、UNSIGNED 都要一模一样
   ```

4. **索引设计原则：高频查询列 + 外键列 + 排序列**
   ```sql
   -- 外键必须加索引（否则每次删改都要全表扫）
   -- 经常 WHERE 的列加索引
   -- 经常 ORDER BY / GROUP BY 的列加索引
   ```

5. **ON DELETE 选择要慎重**
   - `CASCADE`：级联删除（购物车可以，订单慎用）
   - `RESTRICT`：有子记录禁止删（订单保护用户）
   - `SET NULL`：置空（分类删了商品还在，分类变 NULL）

---

## 【今日练习题】

### 练习题 1：补充缺失的表

当前数据库少了**支付记录表(payments)**，请设计它。

要求：
- 一条订单可以有多笔支付记录（支持部分退款场景）
- 记录支付金额、支付方式（微信/支付宝/余额）、支付流水号
- 记录支付时间、支付状态（成功/失败/退款）
- 写出完整 CREATE TABLE 语句

### 练习题 2：在本地 MySQL 中跑通建表

把示例1的 7 张表在本地 MySQL 中全部建出来，然后：
1. 插入示例 3 的测试数据
2. 用 `SHOW CREATE TABLE 表名` 查看每张表的完整定义
3. 用 `SELECT * FROM information_schema.TABLE_CONSTRAINTS WHERE TABLE_SCHEMA='ecommerce'` 查看所有外键

---

## 【一句话总结】

> **电商数据库设计的核心是：用外键表达业务关系，用快照保护历史数据，用 DECIMAL 守护金钱精度。**

---

📌 进度：Day 22/30 | 实战篇 · 第1天 | 下一篇：电商数据库 CRUD 操作
