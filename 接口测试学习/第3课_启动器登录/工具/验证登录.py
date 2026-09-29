# -*- coding: utf-8 -*-
"""
验证：不通过启动器，直接用 Python 打登录接口。

协议（从日志逆推）：
  POST http://<网关地址>:9511/
  Header: CID: 1396  |  User-Agent: RaptorLauncher/0.1
  Content-Type: application/octet-stream
  Body: [账号长度][账号] + protobuf 字段
"""
import sys
import requests

GW = 'http://<网关地址>:9511/'
CID_LOGIN = '1396'

ACCOUNT = 'test_account'
PASSWORD = 'test_account'
NICKNAME = 'test_account'

GUID = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
MAC = '001122334455'
GPU = 'OrayIddDriver Device (128G)'
CPU = '12th Gen Intel(R) Core(TM) i7-12700KF (12\u6838 @ 3600MHz)'
RAM = '32G'
OS = 'Microsoft Windows 10 \u4e13\u4e1a\u7248 10.0.19045'
BOARD = 'System Product Name'


def s_field(tag, value):
    """protobuf LEN 字段：[tag][len][data]"""
    data = value.encode('utf-8')
    return bytes([tag]) + bytes([len(data)]) + data


def build_body(account, password, nickname, with_tag1=False):
    b = bytearray()
    acc = account.encode('utf-8')
    # 已知结论：账号长度是首字节（日志里 CS1063 -> 0x06, test_account -> 0x08）
    b += bytes([len(acc)]) + acc
    b += s_field(0x12, password)          # 字段2 密码
    b += s_field(0x1a, nickname)          # 字段3 昵称
    b += b'\x22\x00'                      # 字段4 空
    b += b'\x28\x00'                      # 字段5 = 0
    b += s_field(0x3a, GUID)              # 字段7 设备
    b += s_field(0x42, MAC)               # 字段8 MAC
    b += b'\x52\x00'                      # 字段10 空
    b += s_field(0x62, GPU)               # 字段12 显卡
    b += s_field(0x6a, CPU)               # 字段13 CPU
    b += s_field(0x72, RAM)               # 字段14 内存
    b += s_field(0x7a, OS)                # 字段15 系统
    b += s_field(0x82, BOARD)             # 字段16 主板
    b += b'\x8a\x01\x01\x01'              # 字段17 (1 字节，值未知)
    b += b'\x92\x01\x00'                  # 字段18 空

    if with_tag1:
        return b'\x0a' + bytes(b)         # 补上可能的字段1标签
    return bytes(b)


def send(body, label):
    print('--- %s（%d 字节）---' % (label, len(body)))
    try:
        r = requests.post(
            GW, data=body,
            headers={
                'CID': CID_LOGIN,
                'User-Agent': 'RaptorLauncher/0.1',
                'Content-Type': 'application/octet-stream',
            },
            timeout=8,
        )
    except Exception as e:
        print('  请求异常: %s' % e)
        return None
    print('  HTTP %s  响应 %d 字节' % (r.status_code, len(r.content)))
    print('  HEX: %s' % ' '.join('%02x' % x for x in r.content[:80]))
    print('  TXT: %s' % ''.join(
        chr(x) if 32 <= x < 127 else '.' for x in r.content[:80]))
    return r.content


def main():
    print('账号=%s 密码=%s' % (ACCOUNT, PASSWORD))
    print('目标=%s  CID=%s\n' % (GW, CID_LOGIN))

    a = send(build_body(ACCOUNT, PASSWORD, NICKNAME, with_tag1=False), 'A 首字节=账号长度')
    if a and ACCOUNT.encode() in a:
        print('\n>>> A 变体：响应里出现了账号，很可能登录成功')
        return
    b = send(build_body(ACCOUNT, PASSWORD, NICKNAME, with_tag1=True), 'B 补 0x0A 标签')


if __name__ == '__main__':
    main()
