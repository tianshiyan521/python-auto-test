# JMeter Day 6 - 关联：正则表达式提取器

> **日期**: 2026-07-07  
> **核心**: 正则表达式提取器 + 关联概念 + A接口返回值→B接口参数  
> **一句话**: 关联就是"把上一个请求的返回值掏出来，喂给下一个请求"

---

## 一、什么是关联（Correlation）

### 1.1 为什么需要关联？

HTTP是无状态的。在真实项目中，很多动态数据无法写死：

| 场景 | 动态值 | 例子 |
|------|--------|------|
| 登录后拿token | session_id / token | 每次登录不同 |
| 创建订单后查详情 | order_id | 服务端生成 |
| 列表页点进详情 | 帖子/商品ID | 列表返回 |
| 分页翻页 | 下一页的URL | 响应中返回 |

**关联做的事**：从响应中提取这些动态值，存成JMeter变量，给后面的请求用。

### 1.2 关联 vs 参数化

| | 参数化 | 关联 |
|------|--------|------|
| 数据来源 | 外部（CSV/函数/变量） | 上一个请求的响应 |
| 数据特点 | 预先准备好 | 运行时动态生成 |
| 典型工具 | CSV Data Set Config | 正则/JSON提取器 |
| 关系 | 输入驱动 | 输出驱动输入 |

**实际项目两者都用**：CSV参数化提供测试账号，关联提取登录返回的token。

---

## 二、正则表达式提取器（Regex Extractor）

### 2.1 核心参数

```
参数名              | 说明
--------------------|-------------------------------------------
Apply to (scope)    | 搜索范围：ALL/body/headers/URL/response_code等
Reference Name      | 变量名，后续用 ${变量名} 引用
Regular Expression  | 正则表达式，括号()是捕获组
Template            | 模板，$1$=第1组, $2$=第2组, $1$$2$=拼接
Match No.           | 0=随机, 正数=第N次匹配, -1=全部
Default Value       | 匹配失败时的默认值（建议设成 NOT_FOUND 方便排查）
Use empty default   | 勾选后默认值为空字符串
```

### 2.2 match_number 详解

| 值 | 含义 | 生成变量 | 适用场景 |
|----|------|----------|----------|
| 1 | 第1次匹配 | `${refname}` | 只要第一个结果 |
| 2,3,... | 第N次匹配 | `${refname}` | 指定位置 |
| 0 | 随机 | `${refname}` | 模拟随机点击 |
| -1 | 所有匹配 | `${refname}_1`, `${refname}_2`, ... `${refname}_matchNr` | 遍历所有结果 |

**match_number=-1 会额外生成**：
- `${refname}_matchNr` = 匹配到的总数
- `${refname}_1`, `${refname}_2`, `${refname}_3` ... = 每个匹配结果

### 2.3 正则表达式写法（针对JSON）

```
场景                      | 正则表达式                      | 说明
--------------------------|---------------------------------|--------------------------
提取数字id                | "id":\s*(\d+)                  | \s*容忍空格，\d+匹配数字
提取字符串email           | "email":\s*"([^"]+)"           | \s*容忍空格，[^"]+匹配非引号字符
提取多行                  | "body": "([\s\S]*?)"           | [\s\S]匹配所有字符包括换行
提取URL                   | "href": "(https?://[^"]+)"     | 提取超链接
```

> **注意**：JMeter中正则表达式写 `"` 需要用 `&quot;` 或 `"` 都可以，`.jmx` XML中必须用 `&quot;`

---

## 三、关联链路实战

### 线程组1：关联基础（单值提取）

```
GET /posts (返回100条帖子)
  ↓ 正则提取: "id": (\d+),  match_number=1 → ${post_id}
GET /posts/${post_id} (查详情)
  ↓ 断言: $.id == ${post_id}
GET /posts/${post_id}/comments (查评论)
```

**关键点**：
- `${post_id}` 变量在线程组内所有后续请求都可用
- 同一个变量可以被多个请求复用

### 线程组2：关联进阶（多值提取）

```
GET /users (返回10个用户)
  ↓ 正则提取: "email": "([^"]+)"  match_number=-1 → ${user_email_1}...${user_email_10}
GET /users/1 → 断言 email == ${user_email_1}
GET /users/2 → 断言 email == ${user_email_2}
GET /users/3 → 断言 email == ${user_email_3}
```

**关键点**：
- `match_number=-1` 一次性提取所有匹配
- 生成的变量带编号后缀 `_1`, `_2`, `_3`...
- `${user_email_matchNr}` 告诉你一共匹配了多少个

### 线程组3：关联实战（三级关联链路）

```
GET /posts
  ↓ 正则提取post id (match_number=0随机)
GET /posts/${random_post_id}
  ↓ 正则提取userId
GET /users/${author_user_id}
  ↓ 正则提取email
  ↓ 断言验证email含@
```

**关键点**：
- 多级关联：A→提取→B→提取→C→提取→断言
- 每一级的提取结果都可以给后续所有请求使用
- `match_number=0` 随机选择，模拟真实用户行为

---

## 四、常见问题 & 调试技巧

### 4.1 提取不到值？

1. 加 **察看结果树** 看原始响应，确认正则能匹配到
2. 检查 `match_number` 是否合理（比如只匹配到3个但设了5）
3. 看 `Default Value` 是否生效（请求里出现 NOT_FOUND 就说明没匹配到）
4. 在下一个请求的 **Sampler 名称里加 `${变量名}`**，运行后在结果树里看变量值

### 4.2 正则怎么写才对？

- 用 [regex101.com](https://regex101.com) 在线测试
- 从响应中复制一段原文，先在外面验证正则能匹配
- JMeter的 `template=$1$` 取的是**捕获组**，不是整个匹配

### 4.3 正则提取器放错位置？

- 正则提取器是**后置处理器**（虽然是独立元件），但必须放在**采样器的子节点**下
- 它只对父级采样器的响应生效
- 如果放在 TestPlan 下对所有采样器都生效（一般不这样做）

### 4.4 变量作用域

- 正则提取器提取的变量在**当前线程组内全局有效**
- 跨线程组需要用 `setProperty()` / `${__P()}` 传值
- 同一线程组内，后执行的请求可以引用前面任何提取器产生的变量

---

## 五、Day 6 测试计划结构

```
Test Plan: JMeter Day6 - 关联-正则提取器
├── HTTP请求默认值 (${BASE_URL})
├── HTTP Header Manager
│
├── 线程组1-关联基础(单值提取)  [1线程×3循环=9请求]
│   ├── GET /posts → 正则提取post_id(match=1)
│   ├── GET /posts/${post_id} → JSON断言$.id==${post_id}
│   └── GET /posts/${post_id}/comments
│
├── 线程组2-关联进阶(多值提取)  [1线程×1循环=4请求]
│   ├── GET /users → 正则提取所有email(match=-1)
│   ├── GET /users/1 → JSON断言email==${user_email_1}
│   ├── GET /users/2 → JSON断言email==${user_email_2}
│   └── GET /users/3 → JSON断言email==${user_email_3}
│
├── 线程组3-关联实战(三级链路)  [1线程×2循环=6请求]
│   ├── GET /posts → 正则提取random_post_id(match=0)
│   ├── GET /posts/${random_post_id} → 正则提取author_user_id
│   └── GET /users/${author_user_id} → 正则提取author_email → 断言含@
│
└── 监听器: 察看结果树 / 聚合报告 / CSV结果保存
```

**预计总请求数**: 9 + 4 + 6 = 19

---

## 六、知识点总结

| 概念 | 要点 |
|------|------|
| 关联 | 从响应提取动态数据 → 存变量 → 后续请求使用 |
| 正则提取器参数 | refname/regex/template/match_number/default/scope |
| match_number=1 | 取第一个匹配 |
| match_number=0 | 随机取一个匹配 |
| match_number=-1 | 取所有匹配，生成 `_1`, `_2`, `_matchNr` |
| template | `$1$`=第1个捕获组, `$0$`=整个匹配 |
| 默认值 | 建议设 `NOT_FOUND`，便于排查问题 |
| 调试方法 | 在请求名中嵌入 `${变量名}`，运行后在结果树中直接看到变量值 |
