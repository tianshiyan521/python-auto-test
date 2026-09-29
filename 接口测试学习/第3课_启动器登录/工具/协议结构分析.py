# -*- coding: utf-8 -*-
"""对比 9511 网关上的所有请求体，判断协议结构。"""
import os
import re
import glob

LOG_DIR = r'c:\Users\Administrator\AppData\Local\Raptor-Test\Logs'

seen = {}
total = 0
for path in sorted(glob.glob(os.path.join(LOG_DIR, '*.log'))):
    txt = open(path, 'rb').read().decode('utf-8', 'ignore')
    lines = txt.split('\n')
    for i, line in enumerate(lines):
        if 'Request-Body:' not in line:
            continue
        total += 1
        window = '\n'.join(lines[max(0, i - 14):i + 1])
        urls = re.findall(r'URL:\s*(\S+)', window)
        cids = re.findall(r'CID:\s*(\d+)', window)
        if not urls or '9511' not in urls[-1]:
            continue
        cid = cids[-1] if cids else '?'
        body = line.split('Request-Body: ', 1)[1].rstrip('\r')
        raw = body.encode('utf-8', 'ignore')
        key = (cid, raw[:40])
        if key in seen:
            continue
        seen[key] = (os.path.basename(path), i + 1, raw)

print('含 Request-Body 的行 %d 条；9511 网关上的不同请求 %d 种\n' % (total, len(seen)))
for (cid, _), (fn, lineno, raw) in seen.items():
    hexs = ' '.join('%02x' % b for b in raw[:56])
    txts = ''.join(chr(b) if 32 <= b < 127 else '.' for b in raw[:56])
    readable = re.sub(r'[^\x20-\x7e]+', ' | ', raw.decode('utf-8', 'ignore'))
    print('CID=%-6s 总长=%-5d  %s:%d' % (cid, len(raw), fn, lineno))
    print('   hex : %s' % hexs)
    print('   txt : %s' % txts)
    print('   可读: %s' % readable[:160])
    print()
