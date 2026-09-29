# -*- coding: utf-8 -*-
"""列出各日志里 9511 网关用到的 CID 及请求体特征，重点看 9/28 更新后的日志。"""
import os
import re
import glob

LOG_DIR = r'c:\Users\Administrator\AppData\Local\Raptor-Test\Logs'

for path in sorted(glob.glob(os.path.join(LOG_DIR, '*.log'))):
    name = os.path.basename(path)
    # 只看 9/28 10:48 之后的（exe 更新时间）
    if not (name >= 'launcher-20260928-104800' or name.startswith(('launcher-20260928-1',))):
        continue
    txt = open(path, 'rb').read().decode('utf-8', 'ignore')
    lines = txt.split('\n')
    found = []
    for i, line in enumerate(lines):
        if 'Request-Body:' not in line:
            continue
        window = '\n'.join(lines[max(0, i - 14):i + 1])
        urls = re.findall(r'URL:\s*(\S+)', window)
        cids = re.findall(r'CID:\s*(\d+)', window)
        if not urls or '9511' not in urls[-1]:
            continue
        body = line.split('Request-Body: ', 1)[1].rstrip('\r')
        raw = body.encode('utf-8', 'ignore')
        # 是否是登录体（含账号+密码特征）
        readable = raw.decode('utf-8', 'ignore')
        is_login = ('wuyan' in readable or 'CS1' in readable) and len(raw) > 100
        found.append((cids[-1] if cids else '?', len(raw), raw[:24], is_login))

    if not found:
        continue
    print('%-32s 请求 %d 次' % (name, len(found)))
    seen = set()
    for cid, ln, head, is_login in found:
        key = (cid, ln)
        if key in seen:
            continue
        seen.add(key)
        mark = '  ★登录?' if is_login else ''
        print('    CID=%-6s len=%-5d %s%s' % (
            cid, ln, ' '.join('%02x' % b for b in head), mark))
    print()
