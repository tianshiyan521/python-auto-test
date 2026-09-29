# -*- coding: utf-8 -*-
"""生成《启动器登录链路 · 接口测试用例表》Excel。"""
import os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

OUT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    '用例表.xlsx')

HEAD = ['用例编号', '模块', '测试点类型', '用例标题', '输入/步骤',
        '预期结果', '优先级', '状态']

# (编号, 模块, 类型, 标题, 输入, 预期, 优先级)
CASES = [
    # ---------- A 登录 ----------
    ('A01', '登录CID1396', '正常流程', '正确账号密码登录',
     '账号 your_account / your_password',
     'HTTP 200；code=0；Account=<测试账号>', 'P0'),
    ('A02', '登录CID1396', '正常流程', '登录返回昵称与Token',
     '同 A01',
     'Name 字段非空；Token 为 44 位字符串', 'P0'),
    ('A03', '登录CID1396', '异常流程', '密码错误',
     'your_account / wrongpwd123',
     'HTTP 200；code=14（密码错误）', 'P0'),
    ('A04', '登录CID1396', '异常流程', '密码为空',
     'your_account / 空密码',
     'HTTP 200；code=10（密码为空）', 'P0'),
    ('A05', '登录CID1396', '异常流程', '账号为空',
     '空账号 / your_password',
     'HTTP 200；code=39（账号为空）', 'P0'),
    ('A06', '登录CID1396', '异常流程', '账号不存在',
     'nosuchuser99 / nosuchpwd',
     'HTTP 200；code=13（账号不存在）', 'P0'),
    ('A07', '登录CID1396', '边界值', '账号超长（65位）',
     'a×65 / x',
     'HTTP 200；code=13，服务端拒绝且不崩溃', 'P1'),
    ('A08', '登录CID1396', '边界值', '账号仅1位',
     'a / x',
     'HTTP 200；code=13', 'P2'),
    ('A09', '登录CID1396', '异常流程', '账号含特殊字符',
     'wuyan@233 / your_password',
     'HTTP 200；code=13（格式校验生效）', 'P1'),
    ('A10', '登录CID1396', '边界值', '账号大小写敏感',
     'WUYAN233 / your_password',
     'HTTP 200；code=13（大写不被识别）', 'P1'),
    ('A11', '登录CID1396', '边界值', '账号前后含空格',
     '"your_account" / your_password',
     'HTTP 200；code=13（未做trim）', 'P1'),
    ('A12', '登录CID1396', '异常流程', '请求体缺少密码字段',
     '仅发字段1=账号',
     'HTTP 200；code=10', 'P1'),
    ('A13', '登录CID1396', '异常流程', '请求体为空',
     'body = 0 字节',
     'HTTP 200；code=39', 'P1'),
    ('A14', '登录CID1396', '协议校验', '缺失字段1标签(0x0A)',
     '按日志原文构造body（无0x0A）',
     'HTTP 200；code=38（参数错误）★本项目最易踩的坑', 'P0'),
    ('A15', '登录CID1396', '健壮性', '版本号为空',
     'version=""',
     'HTTP 200；code=0（版本非必填校验项）', 'P2'),
    ('A16', '登录CID1396', '健壮性', '版本号为异常值',
     'version="9.9.9"',
     'HTTP 200；code=0（服务端不校验）', 'P2'),
    ('A17', '登录CID1396', '健壮性', '昵称与账号不一致',
     'nickname="测试昵称"',
     'HTTP 200；code=0，返回昵称以账号数据为准', 'P2'),
    ('A18', '登录CID1396', '幂等性', '重复登录',
     '同参数连续登录 2 次',
     '两次均 code=0，服务端不报"重复登录"', 'P1'),
    ('A19', '登录CID1396', '结果校验', 'HTTP状态码恒为200',
     '上述所有错误输入',
     'HTTP 状态码全部为 200，成败只体现在响应体 code ★', 'P0'),

    # ---------- B 会话 ----------
    ('B01', '鉴权CID1401', '正常流程', '用登录Token换access token',
     '登录返回的 Token',
     'HTTP 200；code=0；返回字段2为新的 access token', 'P0'),
    ('B02', '鉴权CID1401', '异常流程', '使用伪造Token（字段可解析、值无效）',
     '"A"×44（带正确的 0x0A 字段标签）',
     'HTTP 499；code=35 ★网关在协议层直接拦截，间隔1.5s连打8次结果稳定，非限流', 'P0'),
    ('B03', '鉴权CID1401', '协议校验', '缺字段1标签(0x0A)',
     '只发 长度+Token（解析不出字段1）',
     'HTTP 200；code=1 ★与B02对照：字段能否解析决定走协议层还是业务层', 'P1'),
    ('B04', '鉴权CID1401', '异常流程', 'Token 为空',
     '字段1 = 空串（带 0x0A）',
     'HTTP 499；code=35（字段可解析但值为空，协议层拦截）', 'P1'),
    ('B05', '鉴权CID1401', '异常流程', '请求体为空',
     'body = 0 字节（完全无字段）',
     'HTTP 200；code=1', 'P2'),
    ('B06', '鉴权CID1401', '会话机制', '单会话互踢：新登录顶掉旧Token',
     '登录取T1 → 跨秒后再登录 → 用T1换access token',
     '旧T1 被拒：HTTP 499；code=35 ★说明启动器拉起游戏前必须重换token', 'P0'),
    ('B07', '鉴权CID1401', '会话机制', '重新登录后Token立即恢复可用',
     '用最新一次登录的Token换access token',
     'HTTP 200；code=0；返回新 access token', 'P0'),

    # ---------- C 更新链路 ----------
    ('C01', '更新CDN', '正常流程', '拉取启动器远程配置',
     'GET /Preferences/Bot/Default/Launcher/0.1.json',
     'HTTP 200；返回 JSON 含 Game/Version 与 Game/Cgi/Url', 'P0'),
    ('C02', '更新CDN', '正常流程', '拉取游戏清单',
     'GET /Builds/Game/Bot/0.1/Default/Raptor-Default-Test/Manifest.json',
     'HTTP 200；返回 JSON 清单', 'P0'),
    ('C03', '更新CDN', '数据校验', '清单MD5完整性校验',
     '下载 Manifest.json 并计算 MD5，与同名 .md5 比对',
     '实际 MD5 == 声明 MD5', 'P0'),
    ('C04', '更新CDN', '版本比对', '本地版本与远程版本一致',
     '本地 game=0.1 / 远程 Game/Version=0.1',
     '判定"无需更新"', 'P1'),
    ('C05', '更新CDN', '异常流程', '拉取不存在的清单',
     'GET .../NoSuchGame/Manifest.json',
     'HTTP 404（对象不存在）', 'P1'),
    ('C06', '更新CDN', '异常流程', '拉取不存在的版本配置',
     'GET .../Launcher/9.9.9.json',
     'HTTP 404', 'P2'),

    # ---------- D 网关健壮性 ----------
    ('D01', '网关健壮性', '异常流程', '缺少 CID 路由头',
     'POST 网关，不带头 CID',
     'HTTP 500；响应体 "no route for cid -1"', 'P1'),
    ('D02', '网关健壮性', '异常流程', '使用不存在的 CID',
     'CID = 9999',
     'HTTP 500；响应体 "no route for cid 9999"', 'P1'),
    ('D03', '网关健壮性', '异常流程', '使用 GET 方法',
     'GET 网关',
     'HTTP 501；响应体 "invalid method GET"', 'P2'),

    # ---------- E 拉起游戏 ----------
    ('E01', '拉起游戏', '正常流程', '用 access token 启动游戏进程',
     '以 --access-token 参数启动 Raptor-Default-Test.exe',
     '游戏进程成功创建（默认关闭，见 config.json）', 'P1'),
]

# ---------------------------------------------------------------- 写表
wb = Workbook()
ws = wb.active
ws.title = '登录链路用例'

thin = Side(style='thin', color='BFBFBF')
border = Border(left=thin, right=thin, top=thin, bottom=thin)

title_font = Font(name='微软雅黑', size=14, bold=True, color='FFFFFF')
head_font = Font(name='微软雅黑', size=10, bold=True, color='FFFFFF')
body_font = Font(name='微软雅黑', size=10)

ws.merge_cells('A1:H1')
c = ws['A1']
c.value = '《龙岛异兽：起源》启动器 · 登录链路接口测试用例表'
c.font = title_font
c.fill = PatternFill('solid', fgColor='1F4E79')
c.alignment = Alignment(horizontal='center', vertical='center')
ws.row_dimensions[1].height = 30

ws.merge_cells('A2:H2')
c = ws['A2']
c.value = ('被测网关 <网关地址>  |  资源CDN <CDN地址>  |  '
           '测试账号 your_account  |  共 %d 条' % len(CASES))
c.font = Font(name='微软雅黑', size=9, color='404040')
c.alignment = Alignment(horizontal='center', vertical='center')
ws.row_dimensions[2].height = 20

for j, h in enumerate(HEAD, 1):
    c = ws.cell(row=3, column=j, value=h)
    c.font = head_font
    c.fill = PatternFill('solid', fgColor='2E75B6')
    c.alignment = Alignment(horizontal='center', vertical='center')
    c.border = border
ws.row_dimensions[3].height = 22

type_color = {'正常流程': 'E2EFDA', '异常流程': 'FCE4E4', '边界值': 'FFF2CC',
              '协议校验': 'FBD5D5', '健壮性': 'EDEDED', '幂等性': 'DEEAF6',
              '结果校验': 'FBD5D5', '数据校验': 'DEEAF6', '版本比对': 'DEEAF6',
              '异常流程 ': 'FCE4E4'}

for i, (no, mod, kind, title, inp, exp, pri) in enumerate(CASES):
    r = 4 + i
    vals = [no, mod, kind, title, inp, exp, pri, '']
    for j, v in enumerate(vals, 1):
        c = ws.cell(row=r, column=j, value=v)
        c.font = body_font
        c.border = border
        c.alignment = Alignment(
            horizontal='center' if j in (1, 2, 3, 7, 8) else 'left',
            vertical='center', wrap_text=(j in (5, 6)))
    ws.cell(row=r, column=3).fill = PatternFill(
        'solid', fgColor=type_color.get(kind, 'FFFFFF'))
    if pri == 'P0':
        ws.cell(row=r, column=7).font = Font(
            name='微软雅黑', size=10, bold=True, color='C00000')
    ws.row_dimensions[r].height = 30

widths = [9, 15, 11, 26, 30, 40, 8, 8]
for j, w in enumerate(widths, 1):
    ws.column_dimensions[get_column_letter(j)].width = w

ws.freeze_panes = 'A4'
ws.auto_filter.ref = 'A3:H%d' % (3 + len(CASES))

# 第二个 sheet：错误码字典
ws2 = wb.create_sheet('错误码字典')
ws2.append(['响应体 code', '含义', '触发条件（实测）'])
for j in range(1, 4):
    cc = ws2.cell(row=1, column=j)
    cc.font = head_font
    cc.fill = PatternFill('solid', fgColor='2E75B6')
    cc.alignment = Alignment(horizontal='center', vertical='center')
CODES = [
    (0, '成功', '账号密码正确'),
    (1, 'Token 无效 / 协议错误', '伪造 token；或 1401 请求缺 0x0A 前缀（★此时 HTTP 仍为 200）'),
    (10, '密码为空', '密码传空串，或请求体缺字段2'),
    (13, '账号不存在或格式非法', '账号不存在 / 超长 / 含特殊字符 / 大小写不符 / 带空格'),
    (14, '密码错误', '账号存在但密码不对'),
    (35, 'Token 已失效', '旧 token 被新登录顶掉；或 token 字段可解析但值无效（这两种都返回 HTTP 499）'),
    (38, '协议/参数错误', '★ body 开头缺 0x0A（照抄日志就会踩到）'),
    (39, '账号为空', '账号传空串，或请求体为空'),
]
for code, mean, cond in CODES:
    ws2.append([code, mean, cond])
for j, w in zip((1, 2, 3), (12, 26, 60)):
    ws2.column_dimensions[get_column_letter(j)].width = w
for r in range(2, 2 + len(CODES)):
    for j in range(1, 4):
        ws2.cell(row=r, column=j).font = body_font
        ws2.cell(row=r, column=j).border = border
    ws2.row_dimensions[r].height = 22

wb.save(OUT)
print('已生成: %s' % OUT)
print('用例 %d 条（P0 %d 条）' % (
    len(CASES), sum(1 for x in CASES if x[6] == 'P0')))
