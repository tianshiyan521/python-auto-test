# -*- coding: utf-8 -*-
"""对照实验：不同账号密码 / 不同字段17取值，观察服务端错误码变化。"""
import requests

# 地址与账号从 config.json 读取
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from 启动器接口 import GATEWAY as GW, _cfg
ACC = _cfg.get('账号', 'test_account')
PWD = _cfg.get('密码', 'test_password')
HDR = {'CID': '1396', 'User-Agent': 'RaptorLauncher/0.1',
       'Content-Type': 'application/octet-stream'}

GUID = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
MAC = '001122334455'
GPU = 'OrayIddDriver Device (128G)'
CPU = '12th Gen Intel(R) Core(TM) i7-12700KF (12\u6838 @ 3600MHz)'
RAM = '32G'
OS = 'Microsoft Windows 10 \u4e13\u4e1a\u7248 10.0.19045'
BOARD = 'System Product Name'


def s(tag, v):
    d = v.encode('utf-8')
    return bytes([tag]) + bytes([len(d)]) + d


def build(acc, pwd, nick, f17=b'\x01'):
    b = bytearray()
    a = acc.encode('utf-8')
    b += bytes([len(a)]) + a
    b += s(0x12, pwd)
    b += s(0x1a, nick)
    b += b'\x22\x00' + b'\x28\x00'
    b += s(0x3a, GUID) + s(0x42, MAC)
    b += b'\x52\x00'
    b += s(0x62, GPU) + s(0x6a, CPU) + s(0x72, RAM) + s(0x7a, OS)
    b += s(0x82, BOARD)
    b += b'\x8a\x01\x01' + f17
    b += b'\x92\x01\x00'
    return bytes(b)


def probe(label, acc, pwd, f17=b'\x01'):
    body = build(acc, pwd, acc, f17)
    try:
        r = requests.post(GW, data=body, headers=HDR, timeout=8)
        c = r.content
        code = None
        if len(c) >= 2 and c[0] == 0x08:
            code = c[1]
        print('%-42s HTTP %s  %-4d字节  code=%s  hex=%s' % (
            label, r.status_code, len(c), code,
            ' '.join('%02x' % x for x in c[:24])))
        return c
    except Exception as e:
        print('%-42s 异常 %s' % (label, e))
        return None


print('=== 对照组：账号密码变化 ===')
probe('正确 账号/密码', ACC, PWD)
probe('密码错误', ACC, 'wrongpwd')
probe('账号不存在 nosuchuser00/pw', 'nosuchuser00', 'pw')
probe('空账号 /pw', '', 'pw')
probe('空密码', ACC, '')

print()
print('=== 字段17 取值变化（同账号）===')
for v in (0x00, 0x01, 0x02, 0x80, 0xff):
    probe('字段17 = 0x%02x' % v, ACC, PWD, bytes([v]))
