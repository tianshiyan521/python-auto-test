# -*- coding: utf-8 -*-
"""在所有日志里找登录请求（各种账号），确认首字节语义。"""
import os
import re
import glob

LOG_DIR = r'c:\Users\Administrator\AppData\Local\Raptor-Test\Logs'

hits = []
for path in sorted(glob.glob(os.path.join(LOG_DIR, '*.log'))):
    txt = open(path, 'rb').read().decode('utf-8', 'ignore')
    lines = txt.split('\n')
    for i, line in enumerate(lines):
        if 'Request-Body:' not in line:
            continue
        window = '\n'.join(lines[max(0, i - 14):i + 1])
        urls = re.findall(r'URL:\s*(\S+)', window)
        cids = re.findall(r'CID:\s*(\d+)', window)
        if not urls or '9511' not in urls[-1]:
            continue
        if not cids or cids[-1] != '1396':
            continue
        body = line.split('Request-Body: ', 1)[1].rstrip('\r')
        raw = body.encode('utf-8', 'ignore')
        hits.append((os.path.basename(path), i + 1, raw))

print('登录请求(CID=1396) 共 %d 次\n' % len(hits))
seen_acc = set()
for fn, lineno, raw in hits:
    # 宽松提取：正文里的连续可读串
    acc = re.findall(r'[A-Za-z][A-Za-z0-9_]{3,}', raw.decode('utf-8', 'ignore'))
    acc = [a for a in acc if a not in ('OrayIddDriver', 'Device')]
    key = acc[0] if acc else '?'
    if key in seen_acc:
        continue
    seen_acc.add(key)
    print('账号=%-10s 首字节=0x%02x 总长=%-4d  %s:%d' % (
        key, raw[0], len(raw), fn, lineno))
    print('   前 16 字节: %s' % ' '.join('%02x' % b for b in raw[:16]))
    print('   第2-4字节 : %s' % ' '.join('%02x' % b for b in raw[1:4]))

print()
print('=== 首字节 vs 账号长度 对照（判定是标签还是长度）===')
for fn, lineno, raw in hits[:0]:
    pass
