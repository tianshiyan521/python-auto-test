from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

wb = Workbook()
ws = wb.active
ws.title = "测试用例"

# 样式定义
header_font = Font(name='Arial', bold=True, color='FFFFFF', size=11)
header_fill = PatternFill('solid', fgColor='2F5496')
module_font = Font(name='Arial', bold=True, color='1F3864', size=11)
module_fill = PatternFill('solid', fgColor='D6E4F0')
normal_font = Font(name='Arial', size=10)
wrap_align = Alignment(horizontal='left', vertical='top', wrap_text=True)
center_align = Alignment(horizontal='center', vertical='center')
thin_border = Border(
    left=Side(style='thin'), right=Side(style='thin'),
    top=Side(style='thin'), bottom=Side(style='thin')
)

# 表头
headers = ['用例编号', '所属模块', '用例标题', '前置条件', '操作步骤', '预期结果', '优先级']
for col, h in enumerate(headers, 1):
    cell = ws.cell(row=1, column=col, value=h)
    cell.font = header_font
    cell.fill = header_fill
    cell.alignment = center_align
    cell.border = thin_border

# 测试用例数据
cases = [
    # 创建角色大厅
    ['TC-1.1', '创建角色大厅', '首次创建角色时进入角色大厅',
     '账号在该服务器无任何角色',
     '1. 登录游戏，选择一个无角色的服务器\n2. 点击"进入服务器"',
     '成功进入角色大厅，显示角色创建界面', '高'],
    ['TC-1.2', '创建角色大厅', '已有角色时进入服务器不进入角色大厅',
     '账号在该服务器已创建过至少一个角色',
     '1. 登录游戏\n2. 选择已有角色的服务器\n3. 点击"进入服务器"',
     '直接进入游戏，不显示角色大厅界面', '高'],
    ['TC-1.3', '创建角色大厅', '不同服务器角色独立性验证',
     '服务器A有角色，服务器B无角色',
     '1. 进入服务器A → 观察是否直接进游戏\n2. 退出，进入服务器B → 观察是否进入大厅',
     '服务器A直接进游戏，服务器B进入角色大厅', '高'],
    ['TC-1.4', '创建角色大厅', '出生点选点调整为游戏内功能',
     '完成角色创建，首次进入游戏',
     '1. 在角色大厅完成创建角色\n2. 进入游戏后查看出生点选择功能',
     '出生点选点功能在游戏内提供，角色大厅中无出生点选择选项', '中'],

    # 角色死亡复活
    ['TC-2.1', '角色死亡复活', '角色死亡后复活流程',
     '角色已进入游戏，生命值正常',
     '1. 让角色死亡（掉血归零）\n2. 观察死亡后的复活界面\n3. 执行复活操作',
     '角色成功复活，复活后进入游戏场景', '高'],
    ['TC-2.2', '角色死亡复活', '死亡复活后不返回角色大厅',
     '角色已进入游戏',
     '1. 角色死亡\n2. 选择复活\n3. 观察复活后所在场景',
     '角色在指定复活点复活，不会跳转到角色大厅', '高'],

    # 传送点布点
    ['TC-3.1', '传送点布点', '传送点模型中心点与预制体中心点一致',
     '引擎中已布置传送点预制体',
     '1. 记录预制体中心坐标\n2. 进入游戏查看传送点模型\n3. 对比模型中心坐标与预制体中心坐标',
     '模型中心坐标与预制体中心坐标完全一致', '高'],
    ['TC-3.2', '传送点布点', '传送点模型旋转与预制体旋转一致',
     '预制体有非零旋转角度',
     '1. 在引擎中将预制体旋转任意角度（如45°）\n2. 进入游戏查看生成的传送点模型朝向',
     '模型旋转角度与预制体旋转角度完全一致', '高'],
    ['TC-3.3', '传送点布点', '同一地图多个传送点各自独立生成',
     '地图中布置了多个传送点预制体',
     '1. 进入地图\n2. 逐一检查每个传送点位置和旋转',
     '每个传送点独立生成，位置和旋转均与各自预制体一致', '中'],

    # 传送点激活
    ['TC-4.1', '传送点激活', '未激活的传送点无法传送',
     '传送点已生成但未被激活',
     '1. 走到未激活的传送点位置\n2. 尝试使用传送功能',
     '无法触发传送', '高'],
    ['TC-4.2', '传送点激活', '走到传送点附近按E激活',
     '玩家靠近未激活的传送点',
     '1. 走到传送点交互范围内\n2. 按下【E】键',
     '传送点成功激活，显示激活效果/提示', '高'],
    ['TC-4.3', '传送点激活', '交互范围边界测试（范围内）',
     '未激活的传送点',
     '1. 走到传送点交互范围的边界线上\n2. 按下【E】键',
     '成功激活传送点（边界属于有效范围）', '中'],
    ['TC-4.4', '传送点激活', '交互范围边界测试（超出范围）',
     '未激活的传送点',
     '1. 走到传送点交互范围外1步\n2. 按下【E】键',
     '无法激活传送点，无响应', '中'],
    ['TC-4.5', '传送点激活', '对已激活的传送点按E的行为',
     '传送点已被激活',
     '1. 走到已激活的传送点附近\n2. 按下【E】键',
     '触发传送功能或提示已激活，不重复激活', '中'],
    ['TC-4.6', '传送点激活', '激活后断线重连状态保持',
     '已激活某个传送点',
     '1. 激活传送点A\n2. 断开网络\n3. 重新连接进入游戏\n4. 检查传送点A状态',
     '传送点A仍然处于激活状态', '中'],

    # 传送功能 & 导表
    ['TC-5.1', '传送功能', '传送后角色不出现在内圈以内（<9m）',
     '已激活传送点，transpot_range={9, 12}',
     '1. 使用传送点传送\n2. 记录角色位置，计算与传送点中心距离\n3. 多次测试',
     '传送后角色距离中心均在9m~12m环形范围内，不会出现在<9m区域', '高'],
    ['TC-5.2', '传送功能', '传送后角色出现在环形范围内（9m~12m）',
     '已激活传送点，transpot_range={9, 12}',
     '1. 使用传送点传送\n2. 多次测试，记录每次传送后距离',
     '每次传送后角色与传送点中心距离均在9m~12m范围内', '高'],
    ['TC-5.3', '传送功能', '传送后角色不出现在外圈以外（>12m）',
     '已激活传送点，transpot_range={9, 12}',
     '1. 使用传送点传送\n2. 多次测试，记录每次距离',
     '传送后角色距离中心均≤12m，不会超出环形范围', '高'],
    ['TC-5.4', '传送功能', 'gamesystem表transpot_range字段正确读取',
     'gamesystem表已配置transpot_range={9, 12}',
     '1. 启动游戏\n2. 在传送点执行传送\n3. 检查实际传送范围与表配置是否一致',
     '实际传送范围为9m~12m，与导表配置一致', '高'],
    ['TC-5.5', '传送功能', 'transpot_range异常值（0或负数）容错',
     '修改gamesystem表transpot_range为{0,0}或{-1,5}',
     '1. 配置异常值\n2. 启动游戏使用传送点',
     '游戏不崩溃，传送功能有合理降级处理或报错提示', '中'],
    ['TC-5.6', '传送功能', 'transpot_range内圈≥外圈时（{12,9}）容错',
     '修改transpot_range为{12, 9}',
     '1. 配置异常值\n2. 启动游戏使用传送点',
     '游戏不崩溃，有合理容错处理', '低'],
]

for i, case in enumerate(cases, 2):
    for col, val in enumerate(case, 1):
        cell = ws.cell(row=i, column=col, value=val)
        cell.font = normal_font
        cell.alignment = wrap_align
        cell.border = thin_border

# 列宽
ws.column_dimensions['A'].width = 12
ws.column_dimensions['B'].width = 14
ws.column_dimensions['C'].width = 35
ws.column_dimensions['D'].width = 30
ws.column_dimensions['E'].width = 40
ws.column_dimensions['F'].width = 40
ws.column_dimensions['G'].width = 8

# 汇总表
ws2 = wb.create_sheet('用例统计')
stats = [
    ['模块', '用例数', '优先级'],
    ['创建角色大厅', 4, '高'],
    ['角色死亡复活', 2, '高'],
    ['传送点布点', 3, '高/中'],
    ['传送点激活', 6, '高/中'],
    ['传送功能 & 导表', 6, '高/中/低'],
    ['合计', '=SUM(B2:B6)', '—'],
]
for r, row_data in enumerate(stats, 1):
    for c, val in enumerate(row_data, 1):
        cell = ws2.cell(row=r, column=c, value=val)
        if r == 1:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center_align
        elif r == len(stats):
            cell.font = Font(name='Arial', bold=True, size=10)
        else:
            cell.font = normal_font
        cell.alignment = center_align if c != 1 else Alignment(horizontal='left', vertical='center')
        cell.border = thin_border

ws2.column_dimensions['A'].width = 22
ws2.column_dimensions['B'].width = 12
ws2.column_dimensions['C'].width = 15

output = r'c:\Users\Administrator\WorkBuddy\Claw\传送点功能_测试用例.xlsx'
wb.save(output)
print(f'OK: {output}')
