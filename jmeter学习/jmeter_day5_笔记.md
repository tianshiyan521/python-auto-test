# JMeter Day5 - 参数化基础 学习笔记

> 📅 日期：2026-07-03 | 🎯 学习目标：CSV Data Set Config / 用户定义变量 / 函数助手

---

## 🧠 核心概念

**参数化 = 让同一测试计划用不同数据反复运行，避免硬编码**

为什么需要参数化？
- 真实场景：100个用户同时登录，每人账号不同 → 不能只测1个账号
- 数据驱动：测试数据与测试逻辑分离 → 改数据不用改脚本
- 场景覆盖：不同角色(admin/vip/guest) → 不同权限路径

JMeter参数化三大手段：
1. **CSV Data Set Config** — 外部文件驱动（最常用）
2. **用户定义变量** — 全局/局部常量管理
3. **函数助手** — 内置动态生成函数

---

## 📊 一、CSV Data Set Config（最核心）

### 基本配置

| 参数 | 说明 | 实战值 |
|------|------|--------|
| Filename | CSV文件路径（支持相对/绝对） | `测试数据/day5_param_pages.csv` |
| Variable Names | 列名映射，逗号分隔 | `page_id,page_title,expected_status` |
| Delimiter | 分隔符 | `,` |
| File Encoding | 编码 | `UTF-8` |
| Ignore First Line | 是否跳过标题行 | `TRUE`（跳过） |
| Recycle on EOF | 读完是否循环 | `TRUE`=循环 / `FALSE`=停止 |
| Stop Thread on EOF | 读完后是否停线程 | `TRUE`=停 / `FALSE`=继续（变量变`<EOF>`） |
| Sharing Mode | 线程间共享方式 | `all`=所有线程共享 / `thread`=每线程独立 |

### Sharing Mode 详解（⭐ 重点）

| 模式 | 行为 | 适用场景 |
|------|------|----------|
| `shareMode.all` | 所有线程共享同一迭代指针，轮流读不同行 | **每个虚拟用户读不同数据** |
| `shareMode.thread` | 每个线程独立迭代指针，各自从头读 | **所有用户用同一组数据** |
| `shareMode.currentGroup` | 当前线程组内共享 | 线程组隔离 |

> ⚠️ **常见踩坑**：设了 `all` 但线程数 > CSV行数 → 读完循环后重复数据，可能导致逻辑异常

### CSV参数化实战路径

```
CSV文件: day5_param_pages.csv
page_id,page_title,expected_status
1,Post One,200
2,Post Two,200
3,Post Three,200
4,Post Four,200
5,Post Five,200
```

JMeter引用方式：
- URL路径：`/posts/${page_id}` → 第1次循环请求 `/posts/1`
- 断言参数：`${expected_status}` → 动态期望状态码
- JSON断言：`${page_id}` → 动态期望JSON字段值

### 多列CSV实战

```
CSV文件: day5_param_users.csv
username,password,email,role
admin,admin123,admin@test.com,administrator
testuser1,pass111,user1@test.com,normal
```

POST请求体同时引用4列：
```json
{
  "title": "Post by ${username}(${role})",
  "body": "Email:${email} | Password:${password}",
  "userId": ${__Random(1,10,user_id)}
}
```

> 💡 CSV+函数助手可以混合使用，实现"文件数据+动态数据"的组合参数化

---

## 📊 二、用户定义变量（全局/局部）

### 两级作用域

| 级别 | 位置 | 作用域 | 优先级 |
|------|------|--------|--------|
| TestPlan级 | 测试计划 → 用户定义变量 | **所有线程组共享** | 低（可被覆盖） |
| 线程组级 | 线程组内 → Arguments元件 | **只在本线程组内可见** | 高（覆盖上级） |

### 本实战用到的变量

| 变量 | 值 | 级别 | 用途 |
|------|-----|------|------|
| `BASE_URL` | `jsonplaceholder.typicode.com` | TestPlan级 | 统一域名 |
| `PROTOCOL` | `http` | TestPlan级 | 统一协议 |
| `API_PREFIX` | `posts` | TestPlan级 | API路径前缀 |
| `TEST_TAG` | `Day5-ParamTest` | TestPlan级 | 测试标记 |
| `LOCAL_TAG` | `ThreadGroup2-FunctionDemo` | 线程组级 | 线程组2专用标记 |
| `RANDOM_POST_ID` | `${__Random(1,100,rand_post)}` | 线程组级 | 动态变量 |

> ⚠️ 变量作用域覆盖规则：子级覆盖父级，但**不能跨线程组**引用局部变量

### HTTP请求默认值 vs 用户定义变量

两者都能做"统一配置"，但本质不同：
- **HTTP请求默认值**：只影响HTTP采样器（domain/protocol/port/path/timeout），子请求设了就替换
- **用户定义变量**：通用变量，任何元件都能用`${VAR}`引用，但HTTP默认值不解析变量到子请求path

> ⚠️ **重要踩坑记录**：HTTP请求默认值的path设了`/posts`，子请求path设了`/${page_id}`
> 结果：子请求path**完全替换**默认path → 实际请求变成`/${page_id}`（丢失了`/posts`）
> **解决方案**：默认值path留空，子请求写完整路径`/posts/${page_id}`

---

## 📊 三、函数助手（内置动态函数）

### 常用函数速查表

| 函数 | 语法 | 返回值 | 本实战用途 |
|------|------|--------|-----------|
| `__Random` | `${__Random(min,max,varName)}` | min~max随机整数 | 随机帖子ID、请求体随机字段 |
| `__counter` | `${__counter(TRUE,varName)}` | 递增计数器 | UA标记、迭代编号 |
| `__threadNum` | `${__threadNum()}` | 当前线程号(1,2,...) | 区分不同线程的请求 |
| `__time` | `${__time(format,varName)}` | 时间戳 | 请求ID、日志标记 |
| `__UUID` | `${__UUID()}` | UUID字符串 | 唯一标识符 |

### __counter 参数详解

| 参数 | 含义 |
|------|------|
| `TRUE` (per-thread) | 每个线程独立计数，线程1:1,2,3... 线程2:1,2,3... |
| `FALSE` (global) | 全局共享计数，所有线程共用1,2,3,4,5,6... |

### __time 格式参数

| 格式 | 示例 | 说明 |
|------|------|------|
| 空或`time` | `1783041196150` | Unix时间戳（毫秒） |
| `YMDHMS` | `20260703091316` | 年月日时分秒 |
| `YMD` | `20260703` | 年月日 |
| `HMS` | `091316` | 时分秒 |

### 本实战函数组合案例

**POST请求体 - 4函数组合**：
```json
{
  "title": "${TEST_TAG}-Thread${__threadNum()}-Iter${__counter(TRUE,iter_cnt)}",
  "body": "Auto test at ${__time(YMDHMS,ts)} - randomId=${__Random(1,50,body_rand)}",
  "userId": ${__threadNum()}
}
```

每个请求body都独一无二：
- 线程1第1次：`Day5-ParamTest-Thread1-Iter1 / 20260703091316-3247 / userId=1`
- 线程2第2次：`Day5-ParamTest-Thread2-Iter2 / 20260703091322-8751 / userId=2`

**请求Header - 函数组合**：
```
X-Request-Id: ${__time(YMDHMS,)}-${__Random(1000,9999,req_rand)}
User-Agent: JMeter-Day5-Param/${__counter(FALSE,)}
```

---

## 🏃 四、运行结果摘要

### 整体结果

| 指标 | 值 |
|------|-----|
| 总样本数 | 44 |
| 错误率 | 0.00% |
| 吞吐量 | 7.3/s |
| 平均响应时间 | 438ms |
| 最小响应时间 | 242ms |
| 最大响应时间 | 1191ms |

### 各请求类型统计

| 请求标签 | 样本数 | 平均(ms) | 错误率 |
|----------|--------|----------|--------|
| GET /posts/${page_id} - CSV参数化 | 5 | 467 | 0% |
| GET /posts/${page_id}/comments - CSV嵌套 | 5 | 487 | 0% |
| GET /posts/${Random} - 随机帖子 | 6 | 560 | 0% |
| POST /posts - __time+__counter组合 | 6 | 392 | 0% |
| GET /posts?userId=${threadNum} - 线程号 | 6 | 269 | 0% |
| DELETE /posts/${Random} - 随机删除 | 6 | 355 | 0% |
| POST /posts - CSV用户数据驱动 | 5 | 371 | 0% |
| GET /posts?userId=_RND - 读取验证 | 5 | 528 | 0% |

### 3个线程组结构

| 线程组 | 配置 | 总请求 | 重点 |
|--------|------|--------|------|
| 线程组1-CSV参数化 | 1线程×5循环 | 10 | CSV Data Set Config驱动page_id |
| 线程组2-函数助手 | 2线程×3循环 | 24 | __Random/__counter/__time/__threadNum |
| 线程组3-CSV多列 | 1线程×5循环 | 10 | 4列CSV(username/password/email/role) |

---

## 🎯 五、踩坑记录与关键经验

### ⚠️ 踩坑1：HTTP默认值path被子请求完全替换

**问题**：HTTP默认值path设`/posts`，子请求path设`/${page_id}`
**结果**：实际URL变成`/${page_id}`，丢失`/posts`前缀 → 404错误

**规则**：JMeter中，子请求的path**完全替换**默认值path，不是追加！
**解决**：默认值path留空，子请求写完整路径`/posts/${page_id}`

### ⚠️ 踩坑2：HTTPS协议下jsonplaceholder返回404

**问题**：用户定义变量`PROTOCOL=https` → jsonplaceholder的HTTPS在某些JMeter/Java配置下异常
**解决**：改为`PROTOCOL=http`（沿用Day2经验，HTTP更稳定）

### ⚠️ 踩坑3：XML标签闭合错误

**问题**：`<requestHeaders>false</responseHeaders>` 标签不匹配
**解决**：改为`<requestHeaders>false</requestHeaders>` — 生成JMX时要仔细检查XML结构

### 💡 关键经验

1. **CSV参数化最适合**：大量预设数据（用户账号、测试数据集、配置项）
2. **函数助手最适合**：动态生成数据（随机数、时间戳、计数器）
3. **两者可以混合**：CSV提供基础数据 + 函数补充动态字段
4. **断言也能参数化**：`${expected_status}` 从CSV读取期望值，一个断言覆盖多种场景
5. **Sharing Mode选all**：让不同线程读不同行，模拟多用户并发

---

## 🔗 六、与游戏测试的关联

### 恐龙岛项目参数化场景

| 场景 | 参数化方式 | 数据来源 |
|------|-----------|----------|
| 多玩家登录 | CSV(账号/密码/设备ID) | 用户账号CSV |
| 不同恐龙品种测试 | CSV(恐龙ID/属性/等级) | 恐龙数据CSV |
| 不同领地争夺场景 | CSV(领地ID/攻击力/防守力) | 领地数据CSV |
| 随机匹配战斗 | __Random(对手ID) + CSV(战斗参数) | 函数+CSV混合 |
| 每日任务自动化 | __time(日期) + CSV(任务配置) | 函数+CSV混合 |

---

## 📚 七、Day5 → Day6 预习

Day6主题：**关联-正则提取器**

核心概念：A接口返回值 → 提取 → 作为B接口参数
- 正则表达式提取器（Regular Expression Extractor）
- 关联概念：接口之间的数据依赖链
- 实战：登录获取token → 用token请求用户信息

> 💡 CSV参数化是"预设数据驱动"，关联是"动态数据传递" — 两者配合才是完整的参数化体系！

---

*生成文件：jmeter_day5.jmx + jmeter_day5_笔记.md + day5_param_pages.csv + day5_param_users.csv*
*运行时间：2026-07-03 09:13:16 ~ 09:13:22（6秒）*
