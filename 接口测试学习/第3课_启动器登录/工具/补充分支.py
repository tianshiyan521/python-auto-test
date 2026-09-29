# -*- coding: utf-8 -*-
"""补充分支：版本号、昵称、重复登录、token 后续可用性。"""
import sys
sys.path.insert(0, r'c:\Users\Administrator\WorkBuddy\Claw\接口测试学习\第3课_启动器登录')
from 启动器接口 import login, build_body, parse_proto, GW, CID_LOGIN
import requests

HDR = {'CID': CID_LOGIN, 'User-Agent': 'RaptorLauncher/0.1',
       'Content-Type': 'application/octet-stream'}


def call(label, body, hdr=None, cid=None):
    h = dict(hdr or HDR)
    if cid:
        h['CID'] = cid
    try:
        r = requests.post(GW, data=body, headers=h, timeout=8)
        d = parse_proto(r.content)
        print('%-34s HTTP %-4s code=%-6s 长度=%d' % (
            label, r.status_code, d.get(1), len(r.content)))
        return d, r.content
    except Exception as e:
        print('%-34s 异常 %s' % (label, e))
        return {}, b''


print('=== 版本号相关 ===')
call('版本=0.1(正常)', build_body('test_account', 'test_account'))
call('版本=空', build_body('test_account', 'test_account', version=''))
call('版本=9.9.9', build_body('test_account', 'test_account', version='9.9.9'))
call('版本=abc', build_body('test_account', 'test_account', version='abc'))

print()
print('=== 昵称相关 ===')
call('昵称=账号(正常)', build_body('test_account', 'test_account', nickname='test_account'))
call('昵称=其他值', build_body('test_account', 'test_account', nickname='测试昵称'))
call('昵称=空', build_body('test_account', 'test_account', nickname=''))

print()
print('=== 重复/并发登录 ===')
d1, r1 = call('第1次登录', build_body('test_account', 'test_account'))
d2, r2 = call('第2次登录', build_body('test_account', 'test_account'))
t1, t2 = d1.get(9), d2.get(9)
print('   token1 = %s' % t1)
print('   token2 = %s' % t2)
print('   两次 token 是否相同: %s' % (t1 == t2))
print('   第1次的 token 在第2次登录后是否仍可用（下一个测试验证）')

print()
print('=== token 可用性验证：用 token 拉公告(CID=1527) ===')
tk = d2.get(9)
try:
    r = requests.post(GW, data=b'\x08\x00',
                      headers={'CID': '1527', 'User-Agent': 'RaptorLauncher/0.1',
                               'Content-Type': 'application/octet-stream'},
                      timeout=8)
    print('   不带 token -> HTTP %s %d 字节' % (r.status_code, len(r.content)))
except Exception as e:
    print('   异常', e)

print()
print('=== 用 token 换 access token (CID=1401) ===')
for label, tok in (('第2次登录的 token', tk), ('第1次登录的 token', t1), ('伪造 token', 'A' * 44)):
    if not tok:
        continue
    body = bytes([len(tok)]) + tok.encode()
    try:
        r = requests.post(GW, data=body,
                          headers={'CID': '1401', 'User-Agent': 'RaptorLauncher/0.1',
                                   'Content-Type': 'application/octet-stream'},
                          timeout=8)
        d = parse_proto(r.content)
        print('   %-18s HTTP %-4s code=%-4s 长度=%-4d' % (
            label, r.status_code, d.get(1), len(r.content)))
    except Exception as e:
        print('   %-18s 异常 %s' % (label, e))

print()
print('=== 头部/CID 异常 ===')
call('缺少 CID 头', build_body('test_account', 'test_account'),
     hdr={'User-Agent': 'RaptorLauncher/0.1',
          'Content-Type': 'application/octet-stream'})
call('CID 用 1401', build_body('test_account', 'test_account'), cid='1401')
call('CID 用 9999', build_body('test_account', 'test_account'), cid='9999')
