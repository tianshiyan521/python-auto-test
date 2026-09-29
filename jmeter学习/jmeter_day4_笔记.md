# JMeter Day4 - 断言（Assertion）

**日期**: 2026-07-02  
**主题**: 响应断言 / JSON断言 / 持续时间断言 / 大小断言 / BeanShell断言  
**文件**: `jmeter_day4.jmx` + `day4_result.jtl` + `day4_report/`  

---

## 一、今日学习目标

1. 理解断言在性能测试中的作用：验证接口返回是否符合预期，不只看状态码。
2. 掌握 JMeter 5.6.3 中 5 种常用断言的配置方法。
3. 学会根据场景选择断言类型。
4. 通过实战体会"断言失败如何影响样本成功率"。

---

## 二、断言核心概念

### 2.1 什么是断言？

断言 = **对响应结果的自动检查**。JMeter 默认不会仅因 HTTP 4xx/5xx 就把样本标记为失败（除非接口抛异常），所以必须靠断言来明确判定请求是否成功。

### 2.2 断言在哪里生效？

- 断言挂在 **Sampler 的子节点**下，只对该 Sampler 生效。
- 一个 Sampler 可以挂多个断言，**任一断言失败则该样本失败**。
- 断言结果会写入聚合报告、察看结果树、断言结果监听器。

### 2.3 断言失败 vs 采样器失败

| 情况 | 样本状态 | 示例 |
|------|----------|------|
| 接口返回 200，断言通过 | ✅ success=true | /get 返回正确 JSON |
| 接口返回 200，断言失败 | ❌ success=false | /status/200 断言期望 404 |
| 接口返回 404，断言通过 | ✅ success=true | /status/404 断言期望 404 |
| 接口返回 404，断言期望 200（未忽略状态）| ❌ success=false | 状态码本身也会触发失败 |
| 接口返回 404，断言期望 200（勾选忽略状态）| ❌ success=false | 仅断言失败，便于观察断言效果 |

> 💡 **关键点**：Response Assertion 勾选 **"Ignore status"**（XML 中 `Assertion.assume_success=true`）后，JMeter 会先把 4xx/5xx 强制视为成功，再执行断言判断。本日实战的请求 7 就使用了这个技巧。

---

## 三、5 种断言类型详解

### 3.1 响应断言（Response Assertion）

**适用场景**：检查响应码、响应消息、响应体、响应头、请求 URL 等文本内容。

**核心字段**：

| XML 属性 | 含义 | 常用值 |
|----------|------|--------|
| `Assertion.test_field` | 检查对象 | `Assertion.response_code` / `Assertion.response_message` / `Assertion.response_data` / `Assertion.response_headers` |
| `Assertion.test_type` | 匹配方式 | **1=Matches**, **2=Contains**, **4=Not**, **8=Equals**, **16=Substring** |
| `Assertion.assume_success` | 忽略状态 | `true` 表示 4xx/5xx 先强制成功 |

> ⚠️ **JMeter 5.6.3 常量值容易搞混**：`EQUALS=8`、`CONTAINS=2`、`SUBSTRING=16`，不是直观的 1/2/4/8。本日踩坑记录见下文。

**本日配置示例（请求 2：/status/200）**：

```xml
<ResponseAssertion testname="响应断言-状态码200">
  <collectionProp name="Asserion.test_strings">
    <stringProp name="49586">200</stringProp>
  </collectionProp>
  <stringProp name="Assertion.test_field">Assertion.response_code</stringProp>
  <boolProp name="Assertion.assume_success">false</boolProp>
  <intProp name="Assertion.test_type">8</intProp>  <!-- 8 = Equals -->
</ResponseAssertion>
```

---

### 3.2 JSON 断言（JSON Path Assertion）

**适用场景**：RESTful 接口返回 JSON，需要校验具体字段值。

**核心字段**：

| XML 属性 | 含义 |
|----------|------|
| `JSON_PATH` | JSON Path 表达式，如 `$.url`、`$.data[0].id` |
| `EXPECTED_VALUE` | 期望值，可开启正则匹配 |
| `ISREGEX` | 是否把期望值当正则表达式 |
| `JSONVALIDATION` | 是否启用校验 |
| `EXPECT_NULL` | 是否期望值为 null |
| `INVERT` | 是否反转结果（不匹配才通过） |

**本日配置示例（请求 1：/get）**：

```xml
<JSONPathAssertion testname="JSON断言-$.url包含httpbin.org">
  <stringProp name="JSON_PATH">$.url</stringProp>
  <stringProp name="EXPECTED_VALUE">.*httpbin\.org.*</stringProp>
  <boolProp name="JSONVALIDATION">true</boolProp>
  <boolProp name="ISREGEX">true</boolProp>
</JSONPathAssertion>
```

> 💡 JSON Path Assertion 的 `ISREGEX=true` 时是 **完整匹配**（`String.matches()`），所以写 `httpbin.org` 会失败，必须写成 `.*httpbin\.org.*`。

---

### 3.3 持续时间断言（Duration Assertion）

**适用场景**：对接口响应时间做硬性上限约束，例如"登录接口必须在 1 秒内返回"。

**核心字段**：

```xml
<DurationAssertion testname="持续时间断言-小于3000毫秒">
  <stringProp name="DurationAssertion.duration">3000</stringProp>
</DurationAssertion>
```

> 注意：持续时间断言的单位是 **毫秒**。如果请求本身已经因为 `response_timeout` 超时，会先触发 SocketTimeoutException，再触发持续时间断言。

---

### 3.4 大小断言（Size Assertion）

**适用场景**：校验响应体、响应头、响应消息、网络传输大小是否满足条件，常用于下载文件、图片、批量数据接口。

**核心字段**：

| XML 属性 | 含义 | 常用值 |
|----------|------|--------|
| `SizeAssertion.operator` | 比较运算符 | 1=EQUAL, 2=NOT EQUAL, 3=GREATER THAN, 4=LESS THAN, 5=GREATER/EQUAL, 6=LESS/EQUAL |
| `SizeAssertion.size` | 目标大小 | 字节数 |
| `Assertion.test_field` | 检查对象 | `SizeAssertion.response_data`（响应体）/ `SizeAssertion.response_headers` / `SizeAssertion.response_network_size` |

**本日配置示例（请求 4：/bytes/2048）**：

```xml
<SizeAssertion testname="大小断言-响应体大于1000字节">
  <intProp name="SizeAssertion.operator">3</intProp>  <!-- 3 = Greater Than -->
  <stringProp name="SizeAssertion.size">1000</stringProp>
  <stringProp name="Assertion.test_field">SizeAssertion.response_data</stringProp>
</SizeAssertion>
```

> ⚠️ 大小断言的属性名不是 `Assertion.test_type` 和 `Assertion.size`，而是 `SizeAssertion.operator` 和 `SizeAssertion.size`。

---

### 3.5 BeanShell 断言（BeanShell Assertion）

**适用场景**：上面 4 种断言都无法满足的复杂校验，例如：

- 正则匹配复杂格式（UUID、手机号、身份证号）
- 多字段联合校验
- 把校验结果写入 JMeter 变量供后续使用
- 调用 Java 方法做加密/签名验证

**内置变量**：

| 变量 | 含义 |
|------|------|
| `prev` | 当前 SampleResult 对象 |
| `vars` | JMeterVariables，可读写变量 |
| `props` | JMeterProperties |
| `Failure` | 布尔值，设置为 true 表示断言失败 |
| `FailureMessage` | 断言失败时的提示信息 |

**本日配置示例（请求 6：/uuid）**：

```java
String response = prev.getResponseDataAsString().trim();
String uuidPattern = "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$";

if (response == null || response.isEmpty()) {
    Failure = true;
    FailureMessage = "响应为空，无法校验UUID";
} else if (!response.matches(uuidPattern)) {
    Failure = true;
    FailureMessage = "响应不是标准UUID格式，实际内容: " + response;
} else {
    vars.put("extracted_uuid", response);
}
```

---

## 四、实战测试计划结构

```
Test Plan: JMeter Day4 - 断言实战
├── 用户定义变量：BASE_URL / PROTOCOL / CUSTOM_HEADER_VALUE
├── HTTP 请求默认值（httpbin.org / https / 30s 超时）
├── HTTP Header Manager
├── 线程组：2 线程 × 2 循环 = 4 次迭代
│   ├── 01-GET /get - 响应断言 + JSON断言
│   ├── 02-GET /status/200 - 响应断言
│   ├── 03-GET jsonplaceholder/posts/1 - 持续时间断言（覆盖默认值）
│   ├── 04-GET /bytes/2048 - 大小断言
│   ├── 05-GET /response-headers - 响应头断言
│   ├── 06-GET /uuid - BeanShell断言
│   └── 07-GET /status/404 - 断言失败演示（assume_success=true + 期望 200）
├── 察看结果树
├── 聚合报告
├── 断言结果
└── CSV 结果保存
```

---

## 五、运行结果

### 5.1 CLI 运行命令

```powershell
$env:JAVA_HOME="C:\Program Files\Java\jdk-11"
$env:PATH="$env:JAVA_HOME\bin;$env:PATH"
& "C:\tool\apache-jmeter-5.6.3\bin\jmeter.bat" `
  -n -t "jmeter学习\jmeter_day4.jmx" `
  -l "jmeter学习\day4_result.jtl" `
  -e -o "jmeter学习\day4_report"
```

### 5.2 聚合报告摘要

| 指标 | 数值 |
|------|------|
| 总样本数 | **28** |
| 错误数 / 错误率 | **4 / 14.29%** |
| 吞吐量 | **1.8/s** |
| 平均响应时间 | **846 ms** |
| 最小响应时间 | **214 ms** |
| 最大响应时间 | **10,007 ms** |

> 说明：4 个错误全部来自 **07-GET /status/404 - 断言失败演示**。该请求实际返回 404，但断言期望 200，因此断言失败。其他 6 个请求的所有断言均通过。

### 5.3 各请求断言结果

| 请求 | 断言类型 | 结果 |
|------|----------|------|
| 01 /get | 响应断言（code=200）+ JSON断言（`$.url` 包含 httpbin.org） | ✅ 通过 |
| 02 /status/200 | 响应断言（code=200） | ✅ 通过 |
| 03 jsonplaceholder/posts/1 | 持续时间断言（< 3000ms） | ✅ 通过 |
| 04 /bytes/2048 | 大小断言（> 1000 bytes） | ✅ 通过 |
| 05 /response-headers | 响应断言（响应头包含自定义值） | ✅ 通过 |
| 06 /uuid | BeanShell 断言（UUID 格式） | ✅ 通过 |
| 07 /status/404 | 响应断言（故意期望 200） | ❌ 失败（演示用） |

---

## 六、踩坑记录

### 6.1 Response Assertion 的 test_type 常量值

JMeter 5.6.3 源码中的常量：

```java
MATCH     = 1
CONTAINS  = 2
NOT       = 4
EQUALS    = 8
SUBSTRING = 16
OR        = 32
```

不是常见的 1=Contains / 2=Equals，写错会导致断言逻辑完全相反。本日第一次运行就因为把 `EQUALS` 写成 4（实际是 `NOT`），导致状态码 200 的断言失败。

### 6.2 Size Assertion 的属性名

大小断言的运算符和大小属性名分别是：

- `SizeAssertion.operator`
- `SizeAssertion.size`

不是 `Assertion.test_type` / `Assertion.size`。写错会导致 `NumberFormatException: For input string: ""`。

### 6.3 JSON Path Assertion 的 ISREGEX 是完整匹配

当 `ISREGEX=true` 时，JMeter 使用 `String.matches()`，要求整个字段值匹配正则。如果想做子串包含，必须写 `.*目标字符串.*`。

### 6.4 HTTP 4xx/5xx 默认会影响样本状态

要让断言独立决定样本成败，需要勾选 **Ignore status**（`assume_success=true`）。本日请求 7 使用该技术，否则 404 会直接让样本失败，无法单独观察断言效果。

### 6.5 httpbin.org 公共接口存在 502/超时

`/delay` 等接口在网络繁忙时不稳定，本日前几次运行出现 502 Bad Gateway 和 SocketTimeoutException。最终方案是把持续时间断言请求切换到更稳定的 `jsonplaceholder.typicode.com/posts/1`。

---

## 七、今日总结

| 断言类型 | 核心能力 | 典型场景 |
|----------|----------|----------|
| 响应断言 | 文本/状态码/头匹配 | 检查返回码、返回消息、页面关键字 |
| JSON 断言 | JSON Path 字段校验 | REST 接口字段值、嵌套对象校验 |
| 持续时间断言 | 响应时间上限 | SLA 约束、接口性能基线 |
| 大小断言 | 响应体/头大小 | 文件下载、图片返回、批量数据 |
| BeanShell 断言 | 自定义 Java 脚本 | 复杂规则、正则、多字段联合校验 |

**一句话总结**：断言是性能测试的"判官"，它告诉 JMeter 哪些请求算成功、哪些算失败。只会发请求不会加断言，等于只做了半个测试。

---

## 八、明日预告

**Day 5 - 参数化基础**：CSV Data Set Config、用户定义变量、函数助手。学习如何把固定值抽离成参数，让脚本更接近真实用户场景。
