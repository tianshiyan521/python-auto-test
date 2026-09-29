# -*- coding: utf-8 -*-
"""
登录接口 · 频率限制/风控探测

目的：确认登录接口有没有独立于"协议可复现"之外的第二道防线。
      若完全没有限流，弱口令撞库就是可枚举的，相关缺陷等级需要上调。

三组实验：
  实验1  连续错误密码      —— 看是否触发账号锁定 / 延迟 / 验证码
  实验2  同秒高频正确登录  —— 看是否有并发数限制
  实验3  换不同账号错误密码 —— 看限流是按账号还是按 IP

安全边界：只打测试环境(<网关地址>)与测试账号，只做登录，不碰注册/改密/支付。
"""
import sys
import time
import statistics

sys.path.insert(0, r'c:\Users\Administrator\WorkBuddy\Claw\接口测试学习\第3课_启动器登录')
import requests
import 启动器接口 as api

GW = api.GATEWAY
HDR_BASE = {'User-Agent': api.UA, 'Content-Type': 'application/octet-stream'}


def login_raw(account, password, nickname=None):
    """返回 (http状态码, code, 耗时秒)。"""
    body = api.build_login_body(account, password, nickname)
    t = time.time()
    try:
        r = requests.post(GW, data=body, timeout=10,
                          headers=dict(HDR_BASE, CID=api.CID_LOGIN))
    except Exception as e:
        return 'ERR', str(e), time.time() - t
    dt = time.time() - t
    return r.status_code, api.parse_proto(r.content).get(1), dt


def show(label, st, code, dt):
    print('  %-34s HTTP %-5s code=%-5s %.3fs' % (label, st, code, dt))


# ================================================================ 实验 1
print('=' * 78)
print('  实验 1：连续错误密码（同一账号 test_account，40 次）')
print('  观察点：错误码是否变化（14→账号锁定？）、响应是否变慢、是否要求验证码')
print('=' * 78)

N1 = 40
codes, times = [], []
for i in range(1, N1 + 1):
    st, code, dt = login_raw('test_account', 'wrongpw%d' % i)
    codes.append(code)
    times.append(dt)
    if i <= 5 or i % 10 == 0 or code != 14:
        show('第 %d 次错误密码' % i, st, code, dt)

print()
print('  错误码分布: %s' % {c: codes.count(c) for c in set(codes)})
print('  响应耗时: 首次 %.3fs | 末次 %.3fs | 平均 %.3fs | 最大 %.3fs'
      % (times[0], times[-1], statistics.mean(times), max(times)))
first5 = statistics.mean(times[:5])
last5 = statistics.mean(times[-5:])
print('  前5次均值 %.3fs → 后5次均值 %.3fs （增幅 %.0f%%）'
      % (first5, last5, (last5 / first5 - 1) * 100 if first5 else 0))
print('  >> 结论: %s' % (
    '出现锁定/验证码/延迟，有限流' if (set(codes) - {14} or last5 > first5 * 2)
    else '错误码恒为14、耗时无增长 → 未发现限流'))

time.sleep(2)

# ================================================================ 实验 2
print()
print('=' * 78)
print('  实验 2：同秒高频正确登录（30 次）')
print('  观察点：是否有并发限制；token 是否随秒变化')
print('=' * 78)

N2 = 30
codes2, times2, toks = [], [], set()
for i in range(1, N2 + 1):
    st, code, dt = login_raw('test_account', 'test_account')
    codes2.append(code)
    times2.append(dt)
    if code == 0:
        # 重新取一次拿 token
        body = api.build_login_body('test_account', 'test_account')
        r = requests.post(GW, data=body, headers=dict(HDR_BASE, CID=api.CID_LOGIN),
                          timeout=10)
        toks.add(api.parse_proto(r.content).get(9))
    if i <= 3 or i % 10 == 0:
        show('第 %d 次正确登录' % i, st, code, dt)

print()
print('  错误码分布: %s' % {c: codes2.count(c) for c in set(codes2)})
print('  平均耗时 %.3fs  最大 %.3fs' % (statistics.mean(times2), max(times2)))
print('  观测到的不同 token 数: %d（反映 token 按秒派生）' % len(toks))
print('  >> 结论: %s' % (
    '高频正确登录未被限制' if set(codes2) == {0} else '出现非0返回码：%s' % set(codes2)))

time.sleep(2)

# ================================================================ 实验 3
print()
print('=' * 78)
print('  实验 3：换不同账号连续错误密码（15 个不存在的账号）')
print('  观察点：限流是按账号维度还是按来源 IP 维度')
print('=' * 78)

codes3, times3 = [], []
for i in range(1, 16):
    st, code, dt = login_raw('probe_acct_%02d' % i, 'x')
    codes3.append(code)
    times3.append(dt)
    show('第 %2d 个不同账号' % i, st, code, dt)

print()
print('  错误码分布: %s' % {c: codes3.count(c) for c in set(codes3)})
print('  >> 结论: %s' % (
    '不同账号同样畅通 → 未发现按账号或按IP的风控拦截'
    if set(codes3) == {13} else '出现变化，可能有限流：%s' % set(codes3)))

# ================================================================ 总结
print()
print('=' * 78)
print('  总结')
print('=' * 78)
total = N1 + N2 + 15
all_codes = codes + codes2 + codes3
expected = {14, 0, 13}
unexpected = set(all_codes) - expected
print('  共发送登录请求 %d 次' % total)
print('  出现的响应码: %s' % {c: all_codes.count(c) for c in set(all_codes)})
if not unexpected:
    print('  未出现任何锁定 / 验证码 / 限流类响应码')
    print()
    print('  ⚠️  判断：登录接口没有可观测的频率限制。')
    print('     结合"协议可从客户端日志零门槛复现"，弱口令/撞库具备可枚举条件。')
else:
    print('  出现预期外的响应码: %s（说明存在风控，需进一步确认触发阈值）' % unexpected)
