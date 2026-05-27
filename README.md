# Python+Requests 自动化测试实战

> 14天从零到实战的接口自动化测试学习项目

## 学习进度

| 天数 | 主题 | 状态 |
|------|------|------|
| Day 1 | HTTP基础 + 第一个GET请求 | Done |
| Day 2 | POST/PUT/DELETE请求（增删改查） | Done |
| Day 3 | Postman基本操作 | Done |
| Day 4 | Requests + JSON处理 | Done |
| Day 5 | 接口断言（状态码/JSON字段/pytest断言） | Done |
| Day 6 | 接口依赖处理（A接口返回值作为B接口参数） | Done |
| Day 7 | 接口依赖处理进阶 | Done |
| Day 8 | pytest框架入门（安装/用例编写规范） | Done |
| Day 9 | pytest框架进阶（fixture） | Done |
| Day 10 | pytest + 数据驱动测试（CSV/Excel） | Done |
| Day 11 | 项目实战：Auth认证 + Monster怪物模块 | Done |
| Day 12 | 项目实战：Player玩家模块 + Combat战斗模块 | Done |
| Day 13 | 项目实战：Item道具 + Ranking排行榜模块 | TODO |
| Day 14 | 项目实战：完整测试套件 + Allure报告 | TODO |

## 技术栈

- Python 3.10
- requests - HTTP请求库
- pytest - 测试框架
- Allure - 测试报告
- CSV / Excel - 数据驱动测试

## 运行方式

```bash
# 安装依赖
pip install requests pytest allure-pytest

# 运行某一天的测试
python requests_day1.py
python requests_day12.py

# 运行所有测试并生成 Allure 报告
pytest requests_day*.py --alluredir=./allure-results
allure serve ./allure-results
```

## 项目说明

本项目基于《山海之巅》游戏接口文档编写真实测试用例，涵盖：
- 用户认证（登录/注册）
- 怪物系统（查询/战斗）
- 玩家系统（信息/背包/升级）
- 战斗系统（PVE/PVP）
- 道具系统（使用/购买/装备）
- 排行榜系统

## 作者

tianshiyan521
