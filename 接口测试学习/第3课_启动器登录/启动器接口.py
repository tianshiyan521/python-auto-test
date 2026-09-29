# -*- coding: utf-8 -*-
"""
《龙岛异兽：起源》启动器 · 登录链路接口客户端（纯 Python 复现）

背景
----
启动器登录界面是 WebView2 加载的 H5，但 H5 只负责收集输入，
真正的 HTTP 请求由 C# 宿主（Raptor-Test.exe）发出。
所以接口地址不在前端代码里 —— 而是被启动器**明文写进了日志**：
    <安装目录>\Logs\launcher-*.log  中的 [DETAIL] HTTP Request/Response 段。

协议（从日志逆推 + 实测验证）
----------------------------
网关   POST http://<网关>/            （地址见 config.json，形如 http://<host>:9511/）
路由   靠 HTTP 头 CID 区分消息类型；无此头返回 500 "no route for cid -1"
编码   Content-Type: application/octet-stream，body 为 protobuf

  CID=1396  登录
      Body   1=账号 2=密码 3=昵称 4='' 5=0
             7=设备GUID 8=MAC 10=启动器版本
             12=显卡 13=CPU 14=内存 15=系统 16=主板 17/18=标志位
      Resp   1=Result 2=Account 3=Name 5=DisplayId 9=Token …

  CID=1401  用登录 Token 换 access token
      Body   1=Token
      Resp   1=Result 2=AccessToken

  CID=1527  拉公告 / CID=1409  心跳
      Body   1=0
      Resp   正常数据

★ 最大的坑
---------
日志会把 body 当字符串打印，**开头的 0x0A（protobuf 字段1的标签）是换行符，
被日志吃掉了**。照抄日志的 body 会得到 code=38（参数错误）。
必须在 body 最前面补回一个 0x0A。
"""
import hashlib
import requests

# ---------------------------------------------------------------- 配置
#
# 网关地址、CDN 地址、测试账号等敏感信息不写死在代码里，
# 统一从 config.json 读取（该文件已加入 .gitignore，不会上传）。
# 首次使用：复制 config.example.json 为 config.json，填入自己的环境。
import json as _json
import os as _os

_HERE = _os.path.dirname(_os.path.abspath(__file__))
_CFG_PATH = _os.path.join(_HERE, 'config.json')
_CFG_EXAMPLE = _os.path.join(_HERE, 'config.example.json')

_cfg = {}
for _p in (_CFG_PATH, _CFG_EXAMPLE):
    if _os.path.exists(_p):
        try:
            with open(_p, encoding='utf-8') as _f:
                _cfg = _json.load(_f)
            break
        except Exception:
            pass

GATEWAY = _cfg.get('网关', 'http://127.0.0.1:9511/')       # 登录/鉴权网关
CDN = _cfg.get('CDN', 'http://127.0.0.1:9000/raptor-client-test')  # 资源 CDN
CID_LOGIN = '1396'
CID_TOKEN = '1401'
CID_NEWS = '1527'
UA = 'RaptorLauncher/0.1'

# 设备指纹（取自启动器日志，测试机固定值，非敏感）
GUID = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
MAC = '001122334455'
GPU = 'OrayIddDriver Device (128G)'
CPU = '12th Gen Intel(R) Core(TM) i7-12700KF (12\u6838 @ 3600MHz)'
RAM = '32G'
OS = 'Microsoft Windows 10 \u4e13\u4e1a\u7248 10.0.19045'
BOARD = 'System Product Name'
VERSION = '0.1'

# 错误码对照（实测）
CODES = {
    0:  '成功',
    1:  'Token 无效/已失效（伪造 token，或 1401 缺 0x0A 前缀）',
    10: '密码为空',
    13: '账号不存在或格式非法',
    14: '密码错误',
    35: 'Token 已失效（旧 token 被新登录顶掉，HTTP 499；或 token 为空串）',
    38: '协议/参数错误（字段1标签 0x0A 缺失时会踩到）',
    39: '账号为空',
}

# ★ 会话机制（实测）
#   1) 登录返回的 token 按"秒"派生，同一秒内重复登录得到相同 token；
#   2) 一旦发生一次产生新 token 的登录，先前 token 立即失效
#      → 再拿去换 access token 会得到 HTTP 499 / code=35。
#   所以启动器在拉起游戏前一定会重新登录并刷新一次 token，
#   自动化脚本也必须遵循"用之前先刷"的顺序。


# ---------------------------------------------------------------- 编解码
def _varint(n):
    out = b''
    while True:
        b = n & 0x7f
        n >>= 7
        out += bytes([b | (0x80 if n else 0)])
        if not n:
            return out


def f_len(field, value):
    """写一个 LEN（字符串/字节）字段。"""
    if isinstance(value, str):
        value = value.encode('utf-8')
    return _varint((field << 3) | 2) + _varint(len(value)) + value


def f_int(field, value):
    """写一个 varint 字段。"""
    return _varint(field << 3) + _varint(value)


def parse_proto(raw):
    """宽容解析 protobuf，返回 {字段号: 值}。"""
    out = {}
    i, n = 0, len(raw)
    while i < n:
        tag, shift = 0, 0
        while True:
            if i >= n:
                return out
            b = raw[i]; i += 1
            tag |= (b & 0x7f) << shift
            shift += 7
            if not b & 0x80:
                break
        field, wt = tag >> 3, tag & 7
        if wt == 2:
            ln, shift = 0, 0
            while True:
                if i >= n:
                    return out
                b = raw[i]; i += 1
                ln |= (b & 0x7f) << shift
                shift += 7
                if not b & 0x80:
                    break
            val = raw[i:i + ln]; i += ln
            try:
                out[field] = val.decode('utf-8')
            except UnicodeDecodeError:
                out[field] = val
        elif wt == 0:
            v, shift = 0, 0
            while True:
                if i >= n:
                    return out
                b = raw[i]; i += 1
                v |= (b & 0x7f) << shift
                shift += 7
                if not b & 0x80:
                    break
            out[field] = v
        else:
            break
    return out


# ---------------------------------------------------------------- 请求
def build_login_body(account, password, nickname=None, version=VERSION):
    """第 1 个字段必须带 0x0A 标签（日志里看不到，是本项目最大的坑）。"""
    if nickname is None:
        nickname = account
    return (f_len(1, account) + f_len(2, password) + f_len(3, nickname) +
            f_len(4, '') + f_int(5, 0) +
            f_len(7, GUID) + f_len(8, MAC) + f_len(10, version) +
            f_len(12, GPU) + f_len(13, CPU) + f_len(14, RAM) +
            f_len(15, OS) + f_len(16, BOARD) +
            f_len(17, b'\x01') + f_len(18, b''))


def _post(cid, body, gateway=GATEWAY, timeout=8):
    return requests.post(
        gateway, data=body, timeout=timeout,
        headers={'CID': cid, 'User-Agent': UA,
                 'Content-Type': 'application/octet-stream'})


def login(account, password, nickname=None, gateway=GATEWAY, timeout=8):
    """登录。返回 dict：http / raw / proto / code / token / account / name"""
    r = _post(CID_LOGIN, build_login_body(account, password, nickname),
              gateway, timeout)
    d = parse_proto(r.content)
    return {
        'http': r.status_code,
        'raw': r.content,
        'proto': d,
        'code': d.get(1),
        'account': d.get(2),
        'name': d.get(3),
        'token': d.get(9) if isinstance(d.get(9), str) else None,
    }


def exchange_access_token(token, gateway=GATEWAY, timeout=8):
    """用登录 token 换 access token（游戏启动参数里用的那个）。"""
    r = _post(CID_TOKEN, f_len(1, token), gateway, timeout)
    d = parse_proto(r.content)
    return {'http': r.status_code, 'raw': r.content, 'proto': d,
            'code': d.get(1), 'access_token': d.get(2)}


# ---------------------------------------------------------------- 更新链路
def fetch_remote_config(channel='Bot', version=VERSION, cdn=CDN, timeout=10):
    """拉启动器远程配置（版本号、网关地址等）。"""
    import json
    url = '%s/Preferences/%s/Default/Launcher/%s.json' % (cdn, channel, version)
    r = requests.get(url, timeout=timeout)
    try:
        data = json.loads(r.content.decode('utf-8'))
    except Exception:
        data = None
    return {'http': r.status_code, 'url': url, 'json': data,
            'game_version': (data or {}).get('Game/Version'),
            'cgi_url': (data or {}).get('Game/Cgi/Url')}


def fetch_manifest(stage='Game', channel='Bot', version=VERSION,
                   build='Raptor-Default-Test', cdn=CDN, timeout=15):
    """拉游戏/补丁清单，并和同名 .md5 文件比对完整性。"""
    base = '%s/Builds/%s/%s/%s/Default/%s' % (cdn, stage, channel, version, build)
    r = requests.get(base + '/Manifest.json', timeout=timeout)
    m = requests.get(base + '/Manifest.json.md5', timeout=timeout)
    real = hashlib.md5(r.content).hexdigest()
    declared = m.content.decode('utf-8', 'ignore').strip()
    return {
        'http': r.status_code, 'http_md5': m.status_code,
        'size': len(r.content),
        'real_md5': real, 'declared_md5': declared,
        'md5_ok': (real == declared),
        'url': base + '/Manifest.json',
    }


# ---------------------------------------------------------------- 自检
if __name__ == '__main__':
    print('=' * 70)
    print('  启动器登录链路 · 接口自检')
    print('=' * 70)

    _acc = _cfg.get('账号', 'test_account')
    _pwd = _cfg.get('密码', 'test_password')
    print('\n[1] 登录  账号 %s' % _acc)
    r = login(_acc, _pwd)
    print('    HTTP %s   code=%s (%s)' % (
        r['http'], r['code'], CODES.get(r['code'], '未知')))
    print('    账号=%s  昵称=%s' % (r['account'], r['name']))
    print('    token=%s' % r['token'])

    if r['code'] == 0:
        print('\n[2] 换 access token')
        t = exchange_access_token(r['token'])
        print('    HTTP %s   code=%s' % (t['http'], t['code']))
        print('    access token=%s' % t['access_token'])

    print('\n[3] 更新链路')
    c = fetch_remote_config()
    print('    远程配置 HTTP %s  游戏版本=%s  网关=%s' % (
        c['http'], c['game_version'], c['cgi_url']))
    mf = fetch_manifest()
    print('    清单 HTTP %s  %d 字节' % (mf['http'], mf['size']))
    print('    声明MD5=%s' % mf['declared_md5'])
    print('    实际MD5=%s' % mf['real_md5'])
    print('    完整性: %s' % ('✅ 一致' if mf['md5_ok'] else '❌ 不一致'))
