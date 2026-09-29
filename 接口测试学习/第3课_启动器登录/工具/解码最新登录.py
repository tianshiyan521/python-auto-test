# -*- coding: utf-8 -*-
"""解码最新一次登录请求体，并用日志里其他账号做判别测试。"""
import os
import re
import glob
import requests

LOG_DIR = r'c:\Users\Administrator\AppData\Local\Raptor-Test\Logs'
# 地址从 config.json 读取
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from 启动器接口 import GATEWAY as GW


# ---------- 1. 取出最新日志里的登录请求体 ----------
def latest_login_raw():
    best = None
    for path in sorted(glob.glob(os.path.join(LOG_DIR, '*.log'))):
        txt = open(path, 'rb').read().decode('utf-8', 'ignore')
        lines = txt.split('\n')
        for i, line in enumerate(lines):
            if 'Request-Body:' not in line:
                continue
            win = '\n'.join(lines[max(0, i - 14):i + 1])
            urls = re.findall(r'URL:\s*(\S+)', win)
            cids = re.findall(r'CID:\s*(\d+)', win)
            if not urls or '9511' not in urls[-1] or not cids or cids[-1] != '1396':
                continue
            raw = line.split('Request-Body: ', 1)[1].rstrip('\r').encode('utf-8', 'ignore')
            best = (os.path.basename(path), i + 1, raw)
    return best


def decode(raw):
    """按 [无标签的 账号] + protobuf 字段 解析。"""
    out = []
    i = 0
    n = len(raw)
    # 第一个字段：长度 + 账号
    ln = raw[0]
    out.append(('字段1 账号?', raw[1:1 + ln].decode('utf-8', 'ignore')))
    i = 1 + ln
    while i < n:
        tag = raw[i]
        i += 1
        if tag & 7 == 2:                      # LEN
            if tag & 0x80:
                tag = ((tag & 0x7f) << 7) | (raw[i] & 0x7f)
                i += 1
            ln = raw[i]; i += 1
            data = raw[i:i + ln]; i += ln
            out.append(('字段%d' % (tag >> 3), data.decode('utf-8', 'ignore')))
        elif tag & 7 == 0:                    # varint
            v = 0; shift = 0
            while True:
                b = raw[i]; i += 1
                v |= (b & 0x7f) << shift
                if not b & 0x80:
                    break
                shift += 7
            out.append(('字段%d' % (tag >> 3), v))
        else:
            out.append(('未知 tag 0x%02x' % tag, ''))
            break
    return out


fn, lineno, raw = latest_login_raw()
print('最新登录请求: %s:%d   原始日志长度 %d' % (fn, lineno, len(raw)))
print('十六进制:')
for k in range(0, len(raw), 16):
    ch = raw[k:k + 16]
    print('  %04x  %-47s  %s' % (
        k, ' '.join('%02x' % b for b in ch),
        ''.join(chr(b) if 32 <= b < 127 else '.' for b in ch)))

print()
print('解码字段:')
for name, val in decode(raw):
    print('  %-14s = %r' % (name, val))
