# JMeter 性能测试 - Day 1：基础入门 + 第一个测试计划

> **日期**：2026-06-26  
> **JMeter版本**：5.6.3  
> **Java版本**：11.0.24  

---

## 一、JMeter 是什么？

JMeter 是 Apache 开源的**性能测试工具**，纯 Java 开发，主要用途：

| 能力 | 说明 |
|------|------|
| **接口性能测试** | 模拟多用户并发，测吞吐量(QPS/TPS)、响应时间 |
| **负载测试** | 逐步加压，找到系统瓶颈 |
| **压力测试** | 极限并发，测系统崩溃点 |
| **功能测试** | 也可以做接口自动化（但不如Postman/Requests方便） |

## 二、JMeter 核心架构（5层）

```
Test Plan（测试计划）
  └── Thread Group（线程组 = 虚拟用户）
        ├── Config Element（配置元件：HTTP默认值、CSV、Header Manager）
        ├── Sampler（采样器：HTTP Request、JDBC、TCP...）
        ├── Timer（定时器：固定定时、随机定时、吞吐量定时器）
        ├── Assertion（断言：响应断言、JSON断言、持续时间断言）
        ├── Post Processor（后置处理器：正则提取器、JSON提取器）
        └── Listener（监听器：查看结果树、聚合报告、汇总报告）
```

**关键理解**：
- **Thread Group** = 并发用户数，JMeter每个线程就是一个独立用户
- **Sampler** = 真正发请求的东西
- **Listener** = 收集结果的地方，不要在GUI模式下开太多监听器（吃内存）

## 三、GUI模式 vs CLI模式

| 模式 | 用途 | 命令 |
|------|------|------|
| **GUI** | 编写/调试脚本 | `jmeter.bat` |
| **CLI** | 执行性能测试 | `jmeter -n -t xxx.jmx -l result.jtl -e -o report/` |

**重要规则**：**用GUI写脚本，用CLI跑压测**。GUI本身吃资源，会干扰测试结果。

## 四、今日学习内容

### 4.1 测试计划结构

```
Test Plan: JMeter Day1 - HTTP基础请求入门
├── 用户定义变量: BASE_URL=httpbin.org, TEST_USER=jmeter_learner
├── Thread Group: 基础并发线程组
│   ├── 线程数: 5 (5个虚拟用户)
│   ├── Ramp-Up: 2秒 (2秒内全部启动)
│   ├── 循环次数: 2 (每个用户跑2遍)
│   └── 总请求: 5×2×3 = 30次
├── HTTP Request Defaults (base URL = httpbin.org)
├── HTTP Header Manager (Accept/User-Agent)
├── 【采样器1】GET /get — 基础GET
├── 【采样器2】GET /get?name=xxx — 带参数GET
├── 【采样器3】POST /post — JSON提交
├── 查看结果树 (实时查看)
├── 聚合报告 (统计分析)
└── 汇总报告 (简洁汇总)
```

### 4.2 关键参数解释

| 参数 | 含义 | 今日值 |
|------|------|--------|
| **线程数** | 并发用户数 | 5 |
| **Ramp-Up** | 启动间隔（秒） | 2s（每0.4s启动一个用户） |
| **循环次数** | 每个用户执行几遍 | 2 |
| **总采样数** | 线程数×循环×采样器数 | 5×2×3=30 |

### 4.3 JMeter 变量引用

JMeter 用 `${变量名}` 引用变量，跟 Shell 一样：
- `${BASE_URL}` → `httpbin.org`
- `${TEST_USER}` → `jmeter_learner`

## 五、CLI运行命令

```bash
# 基础运行（输出到控制台）
/c/tool/apache-jmeter-5.6.3/bin/jmeter -n -t jmeter学习/jmeter_day1.jmx

# 带结果文件 + HTML报告
/c/tool/apache-jmeter-5.6.3/bin/jmeter -n \
  -t jmeter学习/jmeter_day1.jmx \
  -l jmeter学习/day1_result.jtl \
  -e -o jmeter学习/day1_report/
```

**参数说明**：
- `-n`：非GUI模式
- `-t`：指定.jmx测试计划文件
- `-l`：结果输出为.jtl文件
- `-e -o`：生成HTML报告到指定目录

## 六、聚合报告字段含义

| 字段 | 含义 | 好/坏 |
|------|------|-------|
| **Samples** | 请求次数 | — |
| **Average** | 平均响应时间(ms) | 越小越好，<500ms算好 |
| **Median** | 中位数响应时间 | 比Average更能反映真实体验 |
| **90% Line** | 90%请求的响应时间 | 性能SLA通常看这个 |
| **95% Line** | 95%请求的响应时间 | — |
| **99% Line** | 99%请求的响应时间 | — |
| **Min/Max** | 最小/最大响应时间 | Max如果很大说明有抖动 |
| **Error%** | 错误率 | 必须0% |
| **Throughput** | 吞吐量(请求/秒) | 越大越好 |
| **Received KB/sec** | 接收速率 | — |
| **Sent KB/sec** | 发送速率 | — |

## 七、今日要点总结

1. ✅ JMeter架构：Test Plan > Thread Group > Sampler > Listener
2. ✅ 线程组 = 虚拟用户，控制并发
3. ✅ HTTP Request Defaults 统一配置，避免重复
4. ✅ 变量用 `${}` 引用
5. ✅ GUI写脚本，CLI跑压测
6. ✅ 聚合报告看：Average、90%Line、Error%、Throughput

## 八、明日预告

**Day 2: 监听器详解** — 聚合报告 / 汇总报告 / 图形结果 / 后端监听器 / 断言结果
