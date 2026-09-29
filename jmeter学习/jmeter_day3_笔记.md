# JMeter Day 3 - HTTP配置元件详解

> **学习日期**：2026-07-01  
> **测试计划**：`jmeter_day3.jmx`  
> **目标接口**：httpbin.org

---

## 一、今日学习概览

| 配置元件 | 作用 | 典型场景 |
|----------|------|----------|
| HTTP请求默认值 | 统一域名/协议/端口/超时 | 避免每个请求重复配置 |
| HTTP Header Manager | 统一请求头 | Content-Type、Auth Token、UA |
| HTTP Cookie Manager | 自动管理Cookie | 登录态保持、Session传递 |
| HTTP缓存管理器 | 模拟浏览器缓存 | 静态资源压测、缓存命中率 |

---

## 二、HTTP请求默认值（HTTP Request Defaults）

### 核心功能
为同一作用域下的所有 HTTP Request 提供默认配置，子级 Sampler 可覆盖。

### 配置参数
| 参数 | 示例值 | 说明 |
|------|--------|------|
| 协议(Protocol) | https | http/https，空则继承jmeter.properties |
| 服务器名称/IP | httpbin.org | 域名或IP |
| 端口号 | (空) | 80(http)/443(https) 默认 |
| 路径(Path) | (空) | 公共路径前缀 |
| 实现(Implementation) | HttpClient4 | Java/HttpClient4（推荐4） |
| 连接超时 | 5000ms | 建立连接的最大等待时间 |
| 响应超时 | 10000ms | 等待响应的最大时间 |

### 作用域规则
```
Test Plan
  ├── HTTP请求默认值-A  ← 影响子级所有请求
  │   ├── Thread Group 1
  │   │   ├── Request 1  → 使用默认值-A
  │   │   └── Request 2  → 使用默认值-A
  │   └── Thread Group 2
  │       ├── HTTP请求默认值-B  ← 覆盖！只影响TG2
  │       └── Request 3  → 使用默认值-B
```

### 实战要点
- ✅ 一个 Test Plan 可放多个 HTTP请求默认值，作用域隔离
- ✅ 子级 Sampler 的配置会覆盖默认值（就近原则）
- ✅ 适合管理多环境（开发/测试/生产各自一套默认值）
- ⚠️ 路径留空，在具体请求中写完整路径，避免路径拼接混淆

---

## 三、HTTP Header Manager

### 核心功能
为请求统一添加 HTTP 头，支持全局头和局部头。

### 常用请求头配置

```yaml
User-Agent: JMeter-Day3-Test/5.6.3
Accept: application/json, text/plain, */*
Accept-Language: zh-CN,zh;q=0.9
Accept-Encoding: gzip, deflate, br
Connection: keep-alive
```

### 实战场景

| 场景 | Header 配置 |
|------|------------|
| JSON API | `Content-Type: application/json` |
| 表单提交 | `Content-Type: application/x-www-form-urlencoded` |
| Bearer Token | `Authorization: Bearer eyJhbG...` |
| 模拟移动端 | `User-Agent: Mozilla/5.0 (iPhone; ...)` |
| 模拟微信 | `User-Agent: MicroMessenger/8.0...` |
| 反爬测试 | `Referer: https://xxx.com` |
| API版本 | `X-API-Version: v2` |

### 注意事项
- ⚠️ Header Manager 可放在多个层级，下层会合并（不是覆盖）上层
- ⚠️ 如果同一 Header 名称在多层出现，下层的值优先
- ⚠️ `Content-Type` 配合 POST 请求使用时，Header Manager 会自动设置，但也可能被 Sampler 的 Content-Type 覆盖
- ⚠️ `Accept-Encoding: gzip` — 如果响应是压缩的，查看结果树会自动解压展示

---

## 四、HTTP Cookie Manager

### 核心功能
像浏览器一样自动管理 Cookie：发送预设 Cookie → 接收 Set-Cookie → 后续请求自动携带。

### 关键参数

| 参数 | 可选值 | 说明 |
|------|--------|------|
| Cookie策略 | standard/compatibility/rfc2109/netscape/ignore | standard 推荐 |
| clearEachIteration | true/false | 每次迭代清空Cookie？默认false |
| 预设Cookie | Name/Value/Domain/Path | 模拟已登录态 |

### Cookie 策略对比

| 策略 | 行为 |
|------|------|
| **standard**（推荐） | 严格遵循 RFC 6265，最接近现代浏览器 |
| compatibility | 兼容模式，宽松处理 |
| rfc2109 | 旧标准，少用 |
| netscape | 最早的Cookie草案 |
| ignore | 忽略所有Cookie（=禁用Cookie管理器） |

### 实战流程

```
步骤1: Cookie Manager 预设 session_token=abc123
       ↓
步骤2: 请求 /api/login → 服务器返回 Set-Cookie: auth=xyz789
       ↓ (Cookie Manager 自动保存 auth=xyz789)
步骤3: 请求 /api/user/info → 自动携带 session_token + auth
       ↓
步骤4: 请求 /api/logout → 服务器返回 Set-Cookie: auth=; expires=过去
       ↓ (Cookie Manager 自动删除 auth)
```

### 验证方法
- 用 httpbin.org/cookies 查看服务器收到的 Cookie
- 用 httpbin.org/cookies/set?name=value 模拟服务器下发 Cookie
- 在察看结果树中查看 Request 的 Cookie 头

### 注意事项
- ⚠️ `clearEachIteration=true` 每次迭代重置Cookie，适合独立用户场景
- ⚠️ `clearEachIteration=false` 跨迭代保持Cookie，适合同一用户多步操作
- ⚠️ 不同 Thread Group 的 Cookie Manager 互相隔离
- ⚠️ 预设Cookie的Domain必须与请求域名匹配，否则不会发送

---

## 五、HTTP缓存管理器（HTTP Cache Manager）

### 核心功能
模拟浏览器缓存行为，处理 HTTP 缓存头（Cache-Control、Expires、ETag、Last-Modified）。

### 关键参数

| 参数 | 说明 |
|------|------|
| clearEachIteration | 每次迭代清空缓存？默认false |
| useExpires | 是否遵循Cache-Control/Expires头？默认true |
| 最大缓存条目 | 默认5000 |

### 缓存行为逻辑

```
请求资源
  ↓
检查本地缓存是否存在？
  ├─ 否 → 发送HTTP请求 → 服务器返回200 + Cache-Control
  └─ 是 → 检查是否过期？
         ├─ 已过期 → 发送条件请求(If-Modified-Since/If-None-Match)
         │           ├─ 304 Not Modified → 使用本地缓存（节省带宽）
         │           └─ 200 → 使用新响应，更新缓存
         └─ 未过期 → 直接使用本地缓存（不发HTTP请求！）
```

### 对性能测试的影响

| 场景 | 无缓存管理器 | 有缓存管理器 |
|------|-------------|-------------|
| 静态资源（图片/CSS/JS） | 每次都请求 | 第2次起用缓存 |
| 吞吐量 | 接近真实带宽压力 | 模拟真实用户行为 |
| 服务器压力 | 偏大（不真实） | 更真实 |
| 适用场景 | 接口压测 | Web页面压测 |

### 注意事项
- ⚠️ 缓存管理器**只在虚拟用户内部生效**，不同线程独立
- ⚠️ `useExpires=false` 时忽略服务器缓存头，每次都发请求（=禁用缓存）
- ⚠️ 仅对 GET/HEAD 请求生效，POST/PUT/DELETE 不走缓存
- ⚠️ 如果服务器不返回缓存头（Cache-Control等），缓存管理器不生效

---

## 六、Day3 测试计划说明

### 场景设计
模拟浏览器访问 httpbin.org，验证4个配置元件：

```
用户定义变量: BASE_URL=httpbin.org, PROTOCOL=https

【配置元件层】─────────────────────
├── HTTP请求默认值 → 统一域名/协议/超时
├── Header Manager  → 统一User-Agent/Accept等
├── Cookie Manager  → 预设 session_token + 自动接收
└── 缓存管理器      → 模拟浏览器缓存

【线程组】3线程 × 2循环 = 6迭代 ──
  ├── 01 GET /headers       → 验证Header Manager发送的请求头
  ├── 02 GET /cookies       → 验证Cookie Manager预设Cookie
  ├── 03 GET /cookies/set   → 验证Set-Cookie自动接收
  ├── 04 GET /cookies       → 验证Cookie自动传递（含服务器下发的）
  └── 05 GET /cache         → 验证缓存管理器行为

【监听器】察看结果树 + 聚合报告 + CSV保存
```

### 预期结果
- 请求1：响应包含 User-Agent=JMeter-Day3-Test/5.6.3
- 请求2：响应 cookies 字段包含 session_token
- 请求3：服务器下发 server_cookie
- 请求4：响应 cookies 包含 session_token + server_cookie
- 请求5：第2次迭代时可能返回304或使用缓存

---

## 七、配置元件对比总结

| 维度 | HTTP请求默认值 | Header Manager | Cookie Manager | 缓存管理器 |
|------|--------------|----------------|----------------|-----------|
| 作用对象 | 域名/协议/端口/超时 | HTTP请求头 | Cookie | GET请求的响应 |
| 自动继承 | ✅ 子级可覆盖 | ✅ 多层合并 | ❌ 作用域隔离 | ❌ 线程隔离 |
| 主要场景 | 统一环境配置 | 鉴权/UA/格式 | 登录态保持 | 静态资源 |
| 是否必须 | 推荐但非必须 | 推荐但非必须 | Web场景必须 | Web页面压测推荐 |
| 影响性能 | 否 | 否 | 否（内存开销小） | 是（减少实际请求） |

---

## 八、常见坑与最佳实践

### ❌ 常见坑
1. **HTTP请求默认值路径拼接问题**：默认值里写 `/api`，请求里写 `/users`，结果访问 `/api/users`（可能不是你想要的）
2. **Header Manager Content-Type 冲突**：POST Sampler 自带 Content-Type 会覆盖 Header Manager 的设置
3. **Cookie Domain 不匹配**：预设Cookie的Domain与请求域名不一致，Cookie不会发送
4. **缓存管理器在接口测试中启用**：POST请求不走缓存，但GET接口可能因缓存导致数据不更新

### ✅ 最佳实践
1. HTTP请求默认值 → 只配置域名和协议，路径留空
2. Header Manager → 全局的放 Test Plan 下，接口特定的放 Thread Group 或 Sampler 下
3. Cookie Manager → 使用 `standard` 策略，Web场景放在 Thread Group 下
4. 缓存管理器 → 仅在 Web 页面压测时启用，接口测试禁用
5. 使用"用户定义变量"管理环境相关值（域名、Token等），方便切换环境

---

*Day3 完成 ✅ | 下一站：Day4 - 断言*
