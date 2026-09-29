# 山海之巅 — 接口测试报告 Day 13

> 报告生成时间：2026-05-28 09:19

## 执行摘要

| 指标 | 数值 |
|------|------|
| 总用例数 | 10 |
| ✅ 通过 | 8 |
| ❌ 失败 | 0 |
| ⏭️ 跳过 | 2 |
| 通过率 | 80.0% |
| 总耗时 | 0.00s |

## 用例详情

| # | 用例名称 | 状态 | 耗时(s) | 描述 |
|---|---------|------|---------|------|
| 1 | test_login_normal | ✅ PASS | 0.32 | 正常登录流程 |
| 2 | test_login_wrong_password | ✅ PASS | 0.28 | 错误密码返回401 |
| 3 | test_login_sql_injection | ✅ PASS | 0.41 | SQL注入防护 |
| 4 | test_player_info | ✅ PASS | 0.35 | 获取玩家信息 |
| 5 | test_player_update_nickname | ✅ PASS | 0.29 | 更新昵称 |
| 6 | test_combat_start | ✅ PASS | 0.38 | 开始战斗 |
| 7 | test_combat_skill | ✅ PASS | 0.31 | 使用技能 |
| 8 | test_combat_settlement | ✅ PASS | 0.44 | 战斗结算 |
| 9 | test_admin_ban_user | ⏭️ SKIP | 0.00 | 管理员封号（权限不足，跳过） |
| 10 | test_server_maintenance | ⏭️ SKIP | 0.00 | 维护期测试（环境限制） |

---
*报告由 Day 13 自动化测试框架生成*