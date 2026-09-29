# -*- coding: utf-8 -*-
"""探测网关对不同 CID 的反应，判断 38 是"通用拒绝"还是"登录专用错误"。"""
import requests

# 地址与账号从 config.json 读取（见 启动器接口.py）
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from 启动器接口 import GATEWAY as GW, _cfg
ACC = _cfg.get('账号', 'test_account')
UA = 'RaptorLauncher/0.1'


def call(cid, body, label, extra=None):
    h = {'CID': str(cid), 'User-Agent': UA,
         'Content-Type': 'application/octet-stream'}
    if extra:
        h.update(extra)
    try:
        r = requests.post(GW, data=body, headers=h, timeout=8)
        c = r.content
        print('%-30s CID=%-5s -> HTTP %s  %-4d字节  hex=%s' % (
            label, cid, r.status_code, len(c),
            ' '.join('%02x' % x for x in c[:32])))
        return c
    except Exception as e:
        print('%-30s CID=%-5s -> 异常 %s' % (label, cid, e))
        return None


print('=== 用一个"已知能用"的请求体做探针 ===')
call(1527, b'\x08\x00', '公告类(08 00)')
call(1409, b'\x08\x00', '另一公告类(08 00)')
call(1401, b'\x2c' + b'A' * 44, '换access token(假token)')
call(1396, b'\x08' + ACC.encode(), '登录(只给账号)')
call(9999, b'\x08\x00', '不存在的CID')

print()
print('=== 换 HTTP 细节再试登录 ===')
body = b'\x08' + ACC.encode() + b'\x12\x08' + ACC.encode() + b'\x1a\x08' + ACC.encode() + b'\x22\x00\x28\x00'
call(1396, body, '登录(精简体)')
call(1396, body, '登录+Connection', {'Connection': 'close'})
call(1396, body, '登录+无UA', {})
call(1396, body, '登录+GET', {})

print()
print('=== 用 GET 试试 ===')
try:
    r = requests.get(GW, headers={'CID': '1396', 'User-Agent': UA}, timeout=8)
    print('GET ->', r.status_code, len(r.content),
          ' '.join('%02x' % x for x in r.content[:24]))
except Exception as e:
    print('GET 异常', e)
