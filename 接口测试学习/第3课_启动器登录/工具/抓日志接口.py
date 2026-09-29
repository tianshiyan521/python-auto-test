# -*- coding: utf-8 -*-
"""
把 Raptor 启动器日志里"录播"的 HTTP 请求/响应全部扒出来。

启动器在 [DETAIL] 级别把每个请求的 Method / URL / Headers / Body
和响应的 Status / Headers / Body 都写进了 Logs/launcher-*.log，
所以不需要抓包工具也能拿到接口全貌。

用法:
    python 抓日志接口.py              # 汇总所有日志里的不同接口
    python 抓日志接口.py --dump 3     # 打印第 3 个接口的完整请求响应原文
"""
import os
import re
import sys
import glob
import json
import collections

LOG_DIR = r'c:\Users\Administrator\AppData\Local\Raptor-Test\Logs'


def read_log(path):
    with open(path, 'rb') as fp:
        raw = fp.read()
    for enc in ('utf-8', 'utf-16', 'gbk'):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode('utf-8', errors='ignore')


def parse_blocks(text):
    """把日志切成 (请求块, 响应块) 列表。"""
    pairs = []
    # 按请求头切分：每个 "HTTP Request >>>" 到下一个 "HTTP Request >>>" 为一段
    chunks = text.split('[DETAIL] HTTP Request >>>')
    for ch in chunks[1:]:
        req_part, _, rest = ch.partition('[DETAIL] HTTP Response <<<')
        resp_part = rest.split('[DETAIL] HTTP Request >>>')[0] if rest else ''
        # 响应块到下一个非 DETAIL 行结束
        resp_part = re.split(r'\r?\n\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3} \[(?!DETAIL)',
                             resp_part)[0]
        pairs.append((req_part, resp_part))
    return pairs


def field(block, name, multi=False):
    """取 'Name: value' 的值；multi=True 时取整段（跨行）。"""
    if multi:
        m = re.search(r'%s:\s*\r?\n(.*?)(?=\r?\n  \S|\r?\n\d{4}-|\Z)' % re.escape(name),
                      block, re.S)
    else:
        m = re.search(r'^\s*%s:\s*(.*)$' % re.escape(name), block, re.M)
    return m.group(1).strip() if m else ''


def parse_one(req_part, resp_part):
    method = field(req_part, 'Method')
    url = field(req_part, 'URL')
    if not url:
        return None
    req_body = field(req_part, 'Request-Body')
    status = field(resp_part, 'Status')
    resp_body = field(resp_part, 'Response-Body')
    # 请求头（CID / User-Agent 等）
    req_hdr_part = re.search(r'Request-Headers:\s*\r?\n(.*?)(?=Content-Headers|Request-Body|\Z)',
                             req_part, re.S)
    headers = {}
    if req_hdr_part:
        for line in req_hdr_part.group(1).splitlines():
            line = line.strip()
            if ': ' in line:
                k, v = line.split(': ', 1)
                headers[k] = v
    return {
        'method': method, 'url': url, 'headers': headers,
        'req_body': req_body, 'status': status, 'resp_body': resp_body,
        'raw_req': req_part.strip(), 'raw_resp': resp_part.strip(),
    }


def load_all(limit=None):
    files = sorted(glob.glob(os.path.join(LOG_DIR, '*.log')))
    if limit:
        files = files[-limit:]
    records = []
    for f in files:
        text = read_log(f)
        ts = re.findall(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})', text, re.M)
        for req_part, resp_part in parse_blocks(text):
            rec = parse_one(req_part, resp_part)
            if rec:
                rec['file'] = os.path.basename(f)
                rec['ts'] = ts[0] if ts else ''
                records.append(rec)
    return files, records


def main():
    dump = None
    if '--dump' in sys.argv:
        dump = int(sys.argv[sys.argv.index('--dump') + 1])

    files, records = load_all()
    print('扫描日志 %d 个，抓到 HTTP 交互 %d 次' % (len(files), len(records)))
    if not records:
        print('没有抓到请求。日志可能不是 DETAIL 级别，或路径不对：')
        print('  ' + LOG_DIR)
        return

    # 按 URL 归类
    groups = collections.OrderedDict()
    for r in records:
        groups.setdefault(r['url'], []).append(r)

    print('不同接口地址 %d 个：\n' % len(groups))
    for i, (url, recs) in enumerate(groups.items(), 1):
        r0 = recs[0]
        hosts = sorted({x['method'] for x in recs})
        print('[%d] %s   %s   (出现 %d 次)' % (i, ' '.join(hosts), url, len(recs)))
        print('    首次: %s  @ %s' % (r0['file'], r0['ts']))
        if r0['headers']:
            print('    请求头: ' + ' | '.join('%s=%s' % kv for kv in
                                             list(r0['headers'].items())[:6]))
        print('    请求体: %s' % (r0['req_body'][:100] or '(空)'))
        print('    响应  : %s' % (r0['resp_body'][:100] or '(无)'))
        print()

    if dump:
        url = list(groups.keys())[dump - 1]
        rec = groups[url][0]
        print('=' * 70)
        print('完整原文：%s' % url)
        print('=' * 70)
        print('--- REQUEST ---')
        print(rec['raw_req'])
        print('--- RESPONSE ---')
        print(rec['raw_resp'])


if __name__ == '__main__':
    main()
