# -*- coding: utf-8 -*-
"""摸清登录接口各分支的真实返回码。"""
import sys
sys.path.insert(0, r'c:\Users\Administrator\WorkBuddy\Claw\接口测试学习\第3课_启动器登录')
from 启动器接口 import login, GW, CID_LOGIN, build_body
import requests

CASES = [
    ('正常：正确账号密码',        'test_account', 'test_account'),
    ('密码错误',                 'test_account', 'wrongpwd123'),
    ('密码为空',                 'test_account', ''),
    ('账号为空',                 '',         'test_account'),
    ('账号不存在',               'nosuchuser99', 'nosuchpwd'),
    ('账号超长(65位)',           'a' * 65,   'x'),
    ('账号含特殊字符',           'wuyan@233', 'test_account'),
    ('账号大小写(大寫WUYAN233)', 'WUYAN233', 'test_account'),
    ('账号前后空格',             ' test_account', 'test_account'),
]

print('%-28s %-8s %-8s %s' % ('用例', 'HTTP', 'code', '响应前 24 字节'))
print('-' * 78)
for name, acc, pwd in CASES:
    try:
        st, raw, d = login(acc, pwd)
        code = d.get(1)
        print('%-28s %-8s %-8s %s' % (
            name, st, code, ' '.join('%02x' % x for x in raw[:24])))
    except Exception as e:
        print('%-28s 异常 %s' % (name, e))

print()
print('=== 只给账号、不给密码字段（结构不完整）===')
try:
    body = b'\x0a\x08test_account'
    r = requests.post(GW, data=body, headers={
        'CID': CID_LOGIN, 'User-Agent': 'RaptorLauncher/0.1',
        'Content-Type': 'application/octet-stream'}, timeout=8)
    print('HTTP %s  %s' % (r.status_code, ' '.join('%02x' % x for x in r.content[:24])))
except Exception as e:
    print('异常', e)

print()
print('=== 空 body ===')
try:
    r = requests.post(GW, data=b'', headers={
        'CID': CID_LOGIN, 'User-Agent': 'RaptorLauncher/0.1',
        'Content-Type': 'application/octet-stream'}, timeout=8)
    print('HTTP %s  %s' % (r.status_code, ' '.join('%02x' % x for x in r.content[:24])))
except Exception as e:
    print('异常', e)
