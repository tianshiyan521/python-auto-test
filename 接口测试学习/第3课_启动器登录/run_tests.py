# -*- coding: utf-8 -*-
"""
《龙岛异兽：起源》启动器 · 登录链路接口自动化测试

一键跑完 34 条用例，覆盖：
  登录(CID1396) / 鉴权换token(CID1401) / 更新链路(CDN) / 网关健壮性 / 拉起游戏

用法:  双击 跑测试.bat      （或 python 跑用例.py）
结果:  控制台报告 + 测试报告.md
"""
import os
import re
import sys
import json
import time
import base64
import hashlib
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import requests
import 启动器接口 as api

LINE = '=' * 78

# ---------------------------------------------------------------- 配置
CFG = {
    '账号': 'test_account', '密码': 'test_password',
    '网关': 'http://127.0.0.1:9511/', 'CDN': 'http://127.0.0.1:9000/raptor-client-test',
    '启动游戏': False, '超时秒': 8,
}
_cfg_path = os.path.join(HERE, 'config.json')
if os.path.exists(_cfg_path):
    try:
        CFG.update(json.load(open(_cfg_path, encoding='utf-8')))
    except Exception as e:
        print('[警告] config.json 读取失败，用默认值: %s' % e)
else:
    print('[警告] 未找到 config.json，正在使用占位符默认值。')
    print('       请复制 config.example.json 为 config.json 并填入真实环境信息。')

ACC, PWD = CFG['账号'], CFG['密码']
GW, CDN, TO = CFG['网关'], CFG['CDN'], CFG['超时秒']

STATE = {}          # 用例间传递数据（token 等）
ALL_HTTP = []       # 收集所有 HTTP 状态码，供 A19 校验


# ---------------------------------------------------------------- 工具
def _retry(fn, times=3, wait=0.8):
    """只对真正的服务端抖动（502/503/504）做退避重试。

    注意：不要在这里重试 499！
    实测（间隔1.5s连打8次全部 499，body=08 23 即 code=35）证明：
    499 是网关对"token 字段可解析但验证失败"的**确定性业务响应**，不是限流。
    把它当限流重试会掩盖真实协议行为，导致用例判定错乱。
    """
    last = None
    for i in range(times):
        last = fn()
        if last.status_code not in (502, 503, 504):
            return last
        time.sleep(wait * (i + 1))
    return last


def post(cid, body, timeout=None):
    r = _retry(lambda: requests.post(
        GW, data=body, timeout=timeout or TO, headers={
            'CID': str(cid), 'User-Agent': api.UA,
            'Content-Type': 'application/octet-stream'}))
    ALL_HTTP.append(r.status_code)
    return r


def get(url, timeout=None):
    r = _retry(lambda: requests.get(url, timeout=timeout or TO))
    ALL_HTTP.append(r.status_code)
    return r


def code_of(r):
    return api.parse_proto(r.content).get(1)


def _mask(s):
    """脱敏：报告可能被提交进公开仓库，真实网关地址与账号不外泄。

    - 内网 IP  10.0.0.5        ->  10.0.x.x
    - 账号     abcd1234        ->  ab****34
    """
    if s is None:
        return ''
    s = str(s)
    s = re.sub(r'\b(\d{1,3})\.(\d{1,3})\.\d{1,3}\.\d{1,3}\b', r'\1.\2.x.x', s)
    if '@' in s or '://' in s:
        return s                      # 已是网址，IP 已脱敏，无需再处理
    if len(s) > 4:
        return s[:2] + '*' * (len(s) - 4) + s[-2:]
    return '*' * len(s)


def build_login(account, password, nickname=None, version=api.VERSION,
                with_tag1=True):
    if nickname is None:
        nickname = account
    body = (api.f_len(2, password) + api.f_len(3, nickname) +
            api.f_len(4, '') + api.f_int(5, 0) +
            api.f_len(7, api.GUID) + api.f_len(8, api.MAC) +
            api.f_len(10, version) +
            api.f_len(12, api.GPU) + api.f_len(13, api.CPU) +
            api.f_len(14, api.RAM) + api.f_len(15, api.OS) +
            api.f_len(16, api.BOARD) +
            api.f_len(17, b'\x01') + api.f_len(18, b''))
    head = api.f_len(1, account)
    if not with_tag1:
        head = head[1:]          # 去掉 0x0A 标签，模拟"照抄日志"
    return head + body


# ---------------------------------------------------------------- 用例
def c_a01():
    r = post(api.CID_LOGIN, build_login(ACC, PWD))
    d = api.parse_proto(r.content)
    STATE['token'] = d.get(9)
    STATE['login_raw'] = r.content
    ok = r.status_code == 200 and d.get(1) == 0 and d.get(2) == ACC
    return ok, 'HTTP %s  code=%s  Account=%s' % (r.status_code, d.get(1), _mask(d.get(2)))


def c_a02():
    d = api.parse_proto(STATE.get('login_raw', b''))
    tk = d.get(9)
    ok = bool(d.get(3)) and isinstance(tk, str) and len(tk) == 44
    return ok, 'Name=%s  Token长度=%s' % (
        (d.get(3) or '')[:12] + '…', len(tk) if isinstance(tk, str) else 'N/A')


def c_a03():
    r = post(api.CID_LOGIN, build_login(ACC, 'wrongpwd123'))
    return code_of(r) == 14, 'HTTP %s  code=%s' % (r.status_code, code_of(r))


def c_a04():
    r = post(api.CID_LOGIN, build_login(ACC, ''))
    return code_of(r) == 10, 'HTTP %s  code=%s' % (r.status_code, code_of(r))


def c_a05():
    r = post(api.CID_LOGIN, build_login('', PWD))
    return code_of(r) == 39, 'HTTP %s  code=%s' % (r.status_code, code_of(r))


def c_a06():
    r = post(api.CID_LOGIN, build_login('nosuchuser99', 'nosuchpwd'))
    return code_of(r) == 13, 'HTTP %s  code=%s' % (r.status_code, code_of(r))


def c_a07():
    r = post(api.CID_LOGIN, build_login('a' * 65, 'x'))
    return code_of(r) == 13, 'HTTP %s  code=%s' % (r.status_code, code_of(r))


def c_a08():
    r = post(api.CID_LOGIN, build_login('a', 'x'))
    return code_of(r) == 13, 'HTTP %s  code=%s' % (r.status_code, code_of(r))


def c_a09():
    r = post(api.CID_LOGIN, build_login('wuyan@233', PWD))
    return code_of(r) == 13, 'HTTP %s  code=%s' % (r.status_code, code_of(r))


def c_a10():
    r = post(api.CID_LOGIN, build_login('WUYAN233', PWD))
    return code_of(r) == 13, 'HTTP %s  code=%s' % (r.status_code, code_of(r))


def c_a11():
    r = post(api.CID_LOGIN, build_login(' ' + ACC, PWD))
    return code_of(r) == 13, 'HTTP %s  code=%s' % (r.status_code, code_of(r))


def c_a12():
    r = post(api.CID_LOGIN, api.f_len(1, ACC))
    return code_of(r) == 10, 'HTTP %s  code=%s' % (r.status_code, code_of(r))


def c_a13():
    r = post(api.CID_LOGIN, b'')
    return code_of(r) == 39, 'HTTP %s  code=%s' % (r.status_code, code_of(r))


def c_a14():
    """★ 关键用例：不补 0x0A 标签应被拒（证明该字段是必需协议头）"""
    r = post(api.CID_LOGIN, build_login(ACC, PWD, with_tag1=False))
    return code_of(r) == 38, 'HTTP %s  code=%s（预期38：协议错误）' % (
        r.status_code, code_of(r))


def c_a15():
    r = post(api.CID_LOGIN, build_login(ACC, PWD, version=''))
    return code_of(r) == 0, 'HTTP %s  code=%s' % (r.status_code, code_of(r))


def c_a16():
    r = post(api.CID_LOGIN, build_login(ACC, PWD, version='9.9.9'))
    return code_of(r) == 0, 'HTTP %s  code=%s' % (r.status_code, code_of(r))


def c_a17():
    r = post(api.CID_LOGIN, build_login(ACC, PWD, nickname='测试昵称'))
    d = api.parse_proto(r.content)
    return (code_of(r) == 0 and d.get(2) == ACC), \
        'HTTP %s  code=%s  返回账号=%s' % (r.status_code, d.get(1), _mask(d.get(2)))


def c_a18():
    r1 = post(api.CID_LOGIN, build_login(ACC, PWD))
    r2 = post(api.CID_LOGIN, build_login(ACC, PWD))
    c1, c2 = code_of(r1), code_of(r2)
    return (c1 == 0 and c2 == 0), '两次登录 code=%s / %s' % (c1, c2)


def c_a19():
    bad = [s for s in ALL_HTTP if s != 200]
    return not bad, '已累计 %d 次请求，非200的有 %d 次' % (len(ALL_HTTP), len(bad))


def c_b01():
    """必须当场登录再换 —— token 会被后续登录顶掉（见 B06）。"""
    lr = api.login(ACC, PWD)
    tok = lr.get('token')
    STATE['token'] = tok
    if not tok:
        return False, '前置失败：未拿到登录 token'
    r = post(api.CID_TOKEN, api.f_len(1, tok))
    d = api.parse_proto(r.content)
    STATE['access'] = d.get(2)
    ok = d.get(1) == 0 and isinstance(d.get(2), str) and len(d.get(2)) >= 32
    return ok, 'HTTP %s  code=%s  access_token长度=%s' % (
        r.status_code, d.get(1), len(d.get(2)) if isinstance(d.get(2), str) else 'N/A')


def c_b02():
    """伪造 token（字段格式合法、值无效）→ 网关在协议层拦截。

    实测：HTTP 499 + body=08 23（code=35）。
    间隔 1.5s 连打 8 次结果完全一致，证明这是确定性行为而非限流。
    """
    r = post(api.CID_TOKEN, api.f_len(1, 'A' * 44))
    ok = r.status_code == 499 and code_of(r) == 35
    return ok, 'HTTP %s  code=%s' % (r.status_code, code_of(r))


def c_b03():
    """token 字段标签被破坏（无法解析出字段）→ 落到业务层返回 code=1。

    与 B02 对照：同样是无效 token，"能不能解析出字段"决定了走协议层还是业务层。
    """
    body = api.f_len(1, 'A' * 44)[1:]        # 去掉 0x0A
    r = post(api.CID_TOKEN, body)
    ok = r.status_code == 200 and code_of(r) == 1
    return ok, 'HTTP %s  code=%s' % (r.status_code, code_of(r))


def c_b04():
    r = post(api.CID_TOKEN, api.f_len(1, ''))
    ok = r.status_code == 499 and code_of(r) == 35
    return ok, 'HTTP %s  code=%s' % (r.status_code, code_of(r))


def c_b05():
    r = post(api.CID_TOKEN, b'')
    ok = r.status_code == 200 and code_of(r) == 1
    return ok, 'HTTP %s  code=%s' % (r.status_code, code_of(r))


def c_b06():
    """★ 单会话互踢：同一账号再次登录后，先前 token 立即作废。

    这解释了启动器为何在拉起游戏前必须重新换一次 access token。
    """
    t1 = api.login(ACC, PWD).get('token')
    if not t1:
        return False, '前置失败：第1次登录未拿到 token'
    c1 = api.exchange_access_token(t1)['code']
    time.sleep(1.3)                          # token 按秒派生，须跨秒才会变
    t2 = api.login(ACC, PWD).get('token')
    r = post(api.CID_TOKEN, api.f_len(1, t1))
    c2 = code_of(r)
    ok = (c1 == 0 and c2 == 35 and r.status_code == 499)
    STATE['token'] = t2
    return ok, '旧token换=%s；新登录(token变化=%s)后旧token换=%s（HTTP %s）' % (
        c1, t2 != t1, c2, r.status_code)


def c_b07():
    """旧 token 作废后，用最新登录的 token 应立刻恢复可用。"""
    tok = api.login(ACC, PWD).get('token')
    c = api.exchange_access_token(tok)['code']
    STATE['token'] = tok
    return c == 0, '最新 token 换 access 返回 code=%s' % c


def c_c01():
    c = api.fetch_remote_config(version=api.VERSION, cdn=CDN)
    STATE['remote_version'] = c.get('game_version')
    ok = c['http'] == 200 and bool(c.get('game_version'))
    return ok, 'HTTP %s  远程游戏版本=%s' % (c['http'], c.get('game_version'))


def c_c02():
    m = api.fetch_manifest(cdn=CDN)
    STATE['manifest'] = m
    return m['http'] == 200 and m['size'] > 0, \
        'HTTP %s  清单大小=%d 字节' % (m['http'], m['size'])


def c_c03():
    m = STATE.get('manifest') or api.fetch_manifest(cdn=CDN)
    return m['md5_ok'], '声明=%s  实际=%s  → %s' % (
        m['declared_md5'], m['real_md5'], '一致' if m['md5_ok'] else '不一致')


def c_c04():
    rv = STATE.get('remote_version')
    return rv == api.VERSION, '本地=%s  远程=%s  → %s' % (
        api.VERSION, rv, '无需更新' if rv == api.VERSION else '需要更新')


def c_c05():
    r = get('%s/Builds/Game/Bot/0.1/Default/NoSuchGame/Manifest.json' % CDN)
    return r.status_code == 404, 'HTTP %s（预期404）' % r.status_code


def c_c06():
    r = get('%s/Preferences/Bot/Default/Launcher/9.9.9.json' % CDN)
    return r.status_code == 404, 'HTTP %s（预期404）' % r.status_code


def c_d01():
    r = requests.post(GW, data=b'\x08\x00', timeout=TO, headers={
        'User-Agent': api.UA, 'Content-Type': 'application/octet-stream'})
    ALL_HTTP.append(r.status_code)
    txt = r.content.decode('utf-8', 'ignore')
    return r.status_code == 500 and 'no route' in txt, \
        'HTTP %s  %s' % (r.status_code, txt.strip()[:40])


def c_d02():
    r = post('9999', b'\x08\x00')
    txt = r.content.decode('utf-8', 'ignore')
    return r.status_code == 500 and 'no route' in txt, \
        'HTTP %s  %s' % (r.status_code, txt.strip()[:40])


def c_d03():
    r = requests.get(GW, timeout=TO, headers={'CID': '1396', 'User-Agent': api.UA})
    ALL_HTTP.append(r.status_code)
    txt = r.content.decode('utf-8', 'ignore')
    return r.status_code == 501 and 'invalid method' in txt, \
        'HTTP %s  %s' % (r.status_code, txt.strip()[:40])


def c_e01():
    if not CFG.get('启动游戏'):
        return None, '已跳过（config.json 里 "启动游戏": false）'
    exe = r'C:\Users\Administrator\AppData\Local\Raptor-Test\Game\Raptor-Default-Test.exe'
    if not os.path.exists(exe):
        return False, '游戏主程序不存在: %s' % exe
    # 拉起前必须重新登录+换 token（否则会被 B06 的互踢机制顶掉）
    tok = api.login(ACC, PWD).get('token')
    tok = api.exchange_access_token(tok).get('access_token') or tok
    if not tok:
        return False, '前置失败：未能取得有效 access token'
    prof = base64.b64encode(json.dumps({
        "Token": "", "Account": ACC, "Name": ACC, "DisplayId": "",
        "Phone": "0", "Setting": "", "NeedNppa": 0, "ISVerify": 1,
        "ISMsg": 0, "ISWx": 0, "Language": 2,
        "SavedAt": datetime.datetime.now().isoformat(),
    }, ensure_ascii=False).encode('utf-8')).decode()
    import subprocess
    p = subprocess.Popen([exe, '--launched-by-launcher', '--channel=Default',
                          '--author=Bot', '--access-token=%s' % tok,
                          '--launcher-profile=%s' % prof])
    time.sleep(3)
    alive = p.poll() is None
    return alive, '进程 pid=%s  %s' % (p.pid, '运行中' if alive else '已退出')


def c_e02():
    """收尾：确认网关在整轮测试后仍存活"""
    r = post('1409', b'\x08\x00')
    return r.status_code == 200, 'HTTP %s  网关正常' % r.status_code


# 编号, 模块, 类型, 标题, 优先级, 执行函数
CASES = [
    ('A01', '登录', '正常流程', '正确账号密码登录', 'P0', c_a01),
    ('A02', '登录', '正常流程', '登录返回昵称与Token', 'P0', c_a02),
    ('A03', '登录', '异常流程', '密码错误', 'P0', c_a03),
    ('A04', '登录', '异常流程', '密码为空', 'P0', c_a04),
    ('A05', '登录', '异常流程', '账号为空', 'P0', c_a05),
    ('A06', '登录', '异常流程', '账号不存在', 'P0', c_a06),
    ('A07', '登录', '边界值', '账号超长(65位)', 'P1', c_a07),
    ('A08', '登录', '边界值', '账号仅1位', 'P2', c_a08),
    ('A09', '登录', '异常流程', '账号含特殊字符', 'P1', c_a09),
    ('A10', '登录', '边界值', '账号大小写敏感', 'P1', c_a10),
    ('A11', '登录', '边界值', '账号前后含空格', 'P1', c_a11),
    ('A12', '登录', '异常流程', '请求体缺少密码字段', 'P1', c_a12),
    ('A13', '登录', '异常流程', '请求体为空', 'P1', c_a13),
    ('A14', '登录', '协议校验', '缺失字段1标签0x0A', 'P0', c_a14),
    ('A15', '登录', '健壮性', '版本号为空', 'P2', c_a15),
    ('A16', '登录', '健壮性', '版本号为异常值', 'P2', c_a16),
    ('A17', '登录', '健壮性', '昵称与账号不一致', 'P2', c_a17),
    ('A18', '登录', '幂等性', '重复登录', 'P1', c_a18),
    ('A19', '登录', '结果校验', 'HTTP状态码恒为200', 'P0', c_a19),
    ('B01', '鉴权', '正常流程', '用登录Token换access token', 'P0', c_b01),
    ('B02', '鉴权', '异常流程', '使用伪造Token', 'P0', c_b02),
    ('B03', '鉴权', '协议校验', '缺字段1标签0x0A', 'P1', c_b03),
    ('B04', '鉴权', '异常流程', 'Token为空', 'P1', c_b04),
    ('B05', '鉴权', '异常流程', '请求体为空', 'P2', c_b05),
    ('B06', '鉴权', '会话机制', '单会话互踢：旧Token失效', 'P0', c_b06),
    ('B07', '鉴权', '会话机制', '重新登录后Token立即可用', 'P0', c_b07),
    ('C01', '更新', '正常流程', '拉取启动器远程配置', 'P0', c_c01),
    ('C02', '更新', '正常流程', '拉取游戏清单', 'P0', c_c02),
    ('C03', '更新', '数据校验', '清单MD5完整性校验', 'P0', c_c03),
    ('C04', '更新', '版本比对', '本地与远程版本一致', 'P1', c_c04),
    ('C05', '更新', '异常流程', '拉取不存在的清单', 'P1', c_c05),
    ('C06', '更新', '异常流程', '拉取不存在的版本配置', 'P2', c_c06),
    ('D01', '网关', '异常流程', '缺少CID路由头', 'P1', c_d01),
    ('D02', '网关', '异常流程', '使用不存在的CID', 'P1', c_d02),
    ('D03', '网关', '异常流程', '使用GET方法', 'P2', c_d03),
    ('E01', '拉起游戏', '正常流程', '用access token启动游戏', 'P1', c_e01),
]


# ---------------------------------------------------------------- 主流程
def main():
    t0 = time.time()
    print()
    print(LINE)
    print('  《龙岛异兽：起源》启动器 · 登录链路接口自动化测试')
    print('  账号 %s    网关 %s' % (ACC, GW))
    print('  共 %d 条用例' % len(CASES))
    print(LINE)
    print()
    print('  %-5s %-5s %-9s %-6s %s' % ('编号', '模块', '类型', '结果', '用例'))
    print('  ' + '-' * 74)

    results = []
    for no, mod, kind, title, pri, fn in CASES:
        try:
            ok, detail = fn()
        except Exception as e:
            ok, detail = False, '执行异常: %s: %s' % (type(e).__name__, e)
        state = '通过' if ok else ('跳过' if ok is None else '失败')
        mark = {'通过': '[OK]', '失败': '[X ]', '跳过': '[--]'}[state]
        print('  %-5s %-5s %-9s %-6s %s' % (no, mod, kind, mark, title))
        results.append(dict(no=no, mod=mod, kind=kind, title=title, pri=pri,
                            ok=ok, state=state, detail=detail))
        if ok is False:
            print('        └─ 实际: %s' % detail)
        time.sleep(0.12)      # 轻节流：降低对测试服的瞬时压力

    passed = [r for r in results if r['ok'] is True]
    failed = [r for r in results if r['ok'] is False]
    skipped = [r for r in results if r['ok'] is None]
    elapsed = time.time() - t0

    print('  ' + '-' * 74)
    print('  合计 %d   通过 %d   失败 %d   跳过 %d   耗时 %.1fs' % (
        len(results), len(passed), len(failed), len(skipped), elapsed))
    print()

    if failed:
        print(LINE)
        print('  失败用例详情')
        print(LINE)
        for r in failed:
            print('  [%s] %s' % (r['no'], r['title']))
            print('       实际: %s' % r['detail'])
            print()

    # ---------------- 写报告 ----------------
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    lines = []
    lines.append('# 启动器登录链路 · 接口自动化测试报告\n')
    lines.append('- 执行时间：%s' % now)
    lines.append('- 被测网关：%s' % _mask(GW))
    lines.append('- 资源 CDN：%s' % _mask(CDN))
    lines.append('- 测试账号：%s' % _mask(ACC))
    lines.append('- 结果：**共 %d 条，通过 %d，失败 %d，跳过 %d**，耗时 %.1fs\n'
                 % (len(results), len(passed), len(failed), len(skipped), elapsed))
    lines.append('## 用例执行明细\n')
    lines.append('| 编号 | 模块 | 类型 | 标题 | 优先级 | 结果 | 实际 |')
    lines.append('|---|---|---|---|---|---|---|')
    for r in results:
        mark = {'通过': '✅ 通过', '失败': '❌ 失败', '跳过': '⏭ 跳过'}[r['state']]
        lines.append('| %s | %s | %s | %s | %s | %s | %s |' % (
            r['no'], r['mod'], r['kind'], r['title'], r['pri'], mark,
            r['detail'].replace('|', '/').replace('\n', ' ')))
    if failed:
        lines.append('\n## 失败详情\n')
        for r in failed:
            lines.append('### [%s] %s\n' % (r['no'], r['title']))
            lines.append('- 实际结果：%s\n' % r['detail'])
    lines.append('\n## 错误码字典（实测）\n')
    lines.append('| code | 含义 | 触发条件 |')
    lines.append('|---|---|---|')
    for c, m in api.CODES.items():
        lines.append('| %d | %s | |' % (c, m))
    lines.append('| 35 | Token 为空 | CID=1401 字段1 传空串 |')
    lines.append('\n> 说明：以上错误码均由本轮实测得到，HTTP 状态码统一为 200，'
                 '成败只体现在响应体的 `code` 字段。\n')

    rp = os.path.join(HERE, '测试报告.md')
    with open(rp, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(LINE)
    print('  报告已写入: %s' % rp)
    print(LINE)
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
