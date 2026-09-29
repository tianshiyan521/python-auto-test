# -*- coding: utf-8 -*-
"""修正版：带上 字段10=客户端版本"0.1"，并穷举结尾字段。"""
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


def s2(tag, v):
    """字段号 >15 的双字节标签。"""
    d = v.encode('utf-8')
    t = (tag << 3) | 2
    out = b''
    while True:
        b = t & 0x7f
        t >>= 7
        out += bytes([b | (0x80 if t else 0)])
        if not t:
            break
    return out + bytes([len(d)]) + d


def build(acc, pwd, nick, version='0.1', tail=b'\x8a\x01\x01\x01\x92\x01\x00',
          lead_tag=False):
    b = bytearray()
    if lead_tag:
        b += b'\x0a'
    a = acc.encode('utf-8')
    b += bytes([len(a)]) + a
    b += s(0x12, pwd)
    b += s(0x1a, nick)
    b += b'\x22\x00' + b'\x28\x00'
    b += s(0x3a, GUID) + s(0x42, MAC)
    b += s(0x52, version)
    b += s(0x62, GPU) + s(0x6a, CPU) + s(0x72, RAM) + s(0x7a, OS)
    b += s2(16, BOARD)
    b += tail
    return bytes(b)


def probe(label, body):
    try:
        r = requests.post(GW, data=body, headers=HDR, timeout=8)
        c = r.content
        code = c[1] if len(c) >= 2 and c[0] == 0x08 else None
        tag = '★' if code != 38 else ' '
        print('%s %-44s %-4d字节 code=%-6s hex=%s' % (
            tag, label, len(c), code, ' '.join('%02x' % x for x in c[:20])))
        return c
    except Exception as e:
        print('  %-44s 异常 %s' % (label, e))
        return None


print('=== 加上版本号后再试 ===')
probe('版本=0.1 (基准)', build(ACC, PWD, ACC))
probe('版本=0.1 + 0x0A前导', build(ACC, PWD, ACC, lead_tag=True))
probe('版本=空', build(ACC, PWD, ACC, version=''))

print()
print('=== 结尾字段穷举（版本=0.1）===')
tails = {
    '8a01 01 xx 92 01 00': b'\x8a\x01\x01\x01\x92\x01\x00',
    '8a 01 01 xx': b'\x8a\x01\x01\x01',
    '8a 01 00': b'\x8a\x01\x00',
    '92 01 00': b'\x92\x01\x00',
    '无': b'',
    '01 00': b'\x01\x00',
    '8a0101xx 0100': b'\x8a\x01\x01\x01\x01\x00',
    '8a0101xx 920100 880100': b'\x8a\x01\x01\x01\x92\x01\x00\x88\x01\x00',
}
for name, t in tails.items():
    probe(name, build(ACC, PWD, ACC, tail=t))
