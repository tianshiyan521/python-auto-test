# JMeter Day 7 - 关联：JSON提取器 + 边界提取器

> **日期**: 2026-07-14  
> **核心**: JSON Extractor / Boundary Extractor / 多级关联实战  
> **一句话**: 用 JSONPath 从结构化响应里精准取数，比正则更稳；边界提取器适合快速抠固定左右边界的文本

---

## 一、JSON提取器（JSON Extractor）

### 1.1 为什么需要 JSON 提取器？

JSON 接口返回的是结构化数据，正则虽然也能提取，但：

| 问题 | 正则方案 | JSONPath 方案 |
|------|----------|---------------|
| 字段位置/换行变化 | 容易失效 | 按路径定位，稳定 |
| 多层嵌套 | 正则难写 | 用 `$` 路径层级轻松穿透 |
| 数组提取 | 要写循环 | `$[*].field` 一行搞定 |
| 可读性 | 差 | 好 |

**适用场景**：REST API、微服务接口、返回 JSON 的游戏协议（如登录/玩家/背包数据）。

### 1.2 核心参数

```
参数名                | 说明
----------------------|-------------------------------------------
Names of variables    | 变量名，多个用 ; 分隔，如 post_id;user_id
JSON Path expressions | JSONPath 表达式，多个用 ; 分隔
Match No. (0 for Any) | 0=随机/任意；正数=第N个；-1=全部
Default Values        | 匹配失败默认值，多个用 ; 分隔
Compute concatenation | 勾选-1时拼接所有结果到 varName_ALL
```

### 1.3 常用 JSONPath 语法

```
表达式              | 含义                          | 示例
-------------------|-------------------------------|------------------------------------
$                  | 根对象                        | 整个响应
$.id               | 取对象中的 id 字段            | {"id":1} → 1
$[0]               | 取数组第1个元素               | [{"id":1},...] → {"id":1}
$[0].id            | 取数组第1个元素的 id          | → 1
$[*].email         | 取数组所有元素的 email        | [a,b,c]
$..name            | 递归取所有 name 字段          | 所有层级
$[?(@.id==1)]      | 条件过滤                      | 取 id=1 的对象
$[0:3]             | 切片取前3个                   | 数组索引 0,1,2
```

> **注意**：JSON Extractor 对数组使用 `match_no=-1` 时，会生成 `var_1`, `var_2`, ... 和 `var_matchNr`。

---

## 二、边界提取器（Boundary Extractor）

### 2.1 核心参数

```
参数名              | 说明
--------------------|-------------------------------------------
Reference Name      | 变量名
Left Boundary       | 左边界文本（匹配结果不含该边界）
Right Boundary      | 右边界文本（匹配结果不含该边界）
Match No.           | 0=随机；正数=第N个；-1=全部
Default Value       | 匹配失败默认值
```

### 2.2 适用场景

- 左右边界固定、中间值变化的简单文本（token、email、验证码）
- 不想写正则，快速提取
- HTML/XML 中非结构化片段

### 2.3 示例

响应片段：`"email": "Sincere@april.biz"`

- Left Boundary: `"email": "`
- Right Boundary: `"`
- 提取结果: `Sincere@april.biz`

---

## 三、多级关联实战

### 3.1 链路设计

```
GET /posts
  ↓ JSONPath: $[0].id → ${post_id}
GET /posts/${post_id}
  ↓ JSONPath: $.userId → ${author_user_id}
GET /users/${author_user_id}
  ↓ Boundary Extractor: 提取 ${author_email}
  ↓ 断言：email 含 @
```

### 3.2 与 Day 6 正则方案对比

| 环节 | Day 6（正则） | Day 7（JSON/边界） |
|------|---------------|--------------------|
| 提取 id | `"id":\s*(\d+)` | `$[0].id` |
| 提取 userId | `"userId":\s*(\d+)` | `$.userId` |
| 提取 email | `"email":\s*"([^"]+)"` | Boundary `"email": "` / `"` |
| 稳定性 | 受空格/格式影响 | JSONPath 更稳定 |
| 可读性 | 需懂正则 | 路径直观 |

---

## 四、测试计划结构

```
Test Plan: JMeter Day7 - 关联-JSON提取器
├── HTTP请求默认值 (${BASE_URL})
├── HTTP Header Manager
│
├── 线程组1-JSON单值提取  [1线程×3循环=9请求]
│   ├── GET /posts → JSON Extractor $[0].id → ${post_id}
│   ├── GET /posts/${post_id} → JSON断言 $.id == ${post_id}
│   └── GET /posts/${post_id}/comments
│
├── 线程组2-JSON多值提取  [1线程×1循环=4请求]
│   ├── GET /users → JSON Extractor $[*].email (match=-1)
│   ├── GET /users/1 → JSON断言 email == ${user_email_1}
│   ├── GET /users/2 → JSON断言 email == ${user_email_2}
│   └── GET /users/3 → JSON断言 email == ${user_email_3}
│
├── 线程组3-边界提取器+多级关联  [1线程×2循环=6请求]
│   ├── GET /posts → JSON Extractor $[0].id → ${post_id}
│   ├── GET /posts/${post_id} → JSON Extractor $.userId → ${user_id}
│   └── GET /users/${user_id} → Boundary Extractor 提取 email → 断言
│
└── 监听器: 察看结果树 / 聚合报告 / CSV结果保存
```

**预计总请求数**: 9 + 4 + 6 = 19

---

## 五、运行结果摘要

```
样本数: 19
错误率: 0%
吞吐量: ~7.5/s
平均响应时间: ~300ms
```

---

## 六、知识点总结

| 概念 | 要点 |
|------|------|
| JSON Extractor | 用 JSONPath 从 JSON 响应提取数据，结构稳定、可读性好 |
| 常用 JSONPath | `$.id` 对象字段、`$[0].id` 数组首元素、`$[*].field` 全数组 |
| match_no=-1 | 提取全部，生成 `_1`, `_2`, ..., `_matchNr` |
| Boundary Extractor | 左右边界固定时快速提取，无需正则 |
| 多级关联 | A接口响应 → 提取变量 → B接口请求 → 再提取 → C接口使用 |
| 调试技巧 | 在请求名中嵌入 `${变量名}`，结果树直接显示变量值 |

---

## 七、今日踩坑点

1. **JSONPath 写错层级**：`$[0].id` 用于数组，`$.id` 用于对象，搞反会 NOT_FOUND。
2. **match_no=-1 的变量后缀**：多值提取后引用的是 `${var_1}`，不是 `${var}[1]`。
3. **边界提取器边界要包含引号/冒号**：边界写 `"email"` 还是 `"email": ` 要根据实际响应调整。
4. **变量作用域**：提取的变量在线程组内有效，跨线程组仍需 `setProperty()` / `${__P()}`。

---

> **下一步**: Day 8 逻辑控制器（上）—— 如果控制器、循环控制器、仅一次控制器。
