from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

wb = Workbook()
ws = wb.active
ws.title = "测试用例"

header_font = Font(name='Arial', bold=True, color='FFFFFF', size=11)
header_fill = PatternFill('solid', fgColor='2F5496')
normal_font = Font(name='Arial', size=10)
wrap_align = Alignment(horizontal='left', vertical='top', wrap_text=True)
center_align = Alignment(horizontal='center', vertical='center')
thin_border = Border(
    left=Side(style='thin'), right=Side(style='thin'),
    top=Side(style='thin'), bottom=Side(style='thin')
)

headers = ['用例编号', '所属模块', '用例标题', '前置条件', '操作步骤', '预期结果', '优先级']
for col, h in enumerate(headers, 1):
    cell = ws.cell(row=1, column=col, value=h)
    cell.font = header_font
    cell.fill = header_fill
    cell.alignment = center_align
    cell.border = thin_border

cases = [
    # ========== 背包物品掉落（Goods表） ==========
    ['TC-G-01', '背包物品掉落', '背包物品drop=1死亡时掉入物品盒',
     '背包中有物品A，Goods表中物品A的drop=1',
     '1. 玩家携带物品A进入游戏\n2. 让玩家死亡\n3. 查看死亡后物品盒内容\n4. 查看玩家背包',
     '物品A从背包中消失，出现在死亡物品盒中', '高'],
    ['TC-G-02', '背包物品掉落', '背包物品drop=0死亡时不掉落',
     '背包中有物品B，Goods表中物品B的drop=0',
     '1. 玩家携带物品B进入游戏\n2. 让玩家死亡\n3. 查看死亡后物品盒和背包',
     '物品B仍在背包中，物品盒中无物品B', '高'],
    ['TC-G-03', '背包物品掉落', '背包物品drop=1掉落后不消耗耐久',
     '背包中有装备C（耐久80/100），Goods表中C的drop=1',
     '1. 记录装备C掉落前耐久\n2. 让玩家死亡\n3. 查看物品盒中装备C的耐久',
     '装备C出现在物品盒中，耐久仍为80/100（无损耗）', '高'],
    ['TC-G-04', '背包物品掉落', '背包中多种物品混合掉落',
     '背包中有物品A(drop=1)、物品B(drop=0)、装备C(drop=1)',
     '1. 让玩家死亡\n2. 检查物品盒和背包',
     '物品盒中：物品A + 装备C\n背包中：物品B（drop=0的保留）', '高'],
    ['TC-G-05', '背包物品掉落', '背包为空时死亡不触发物品掉落',
     '玩家背包为空',
     '1. 让玩家死亡\n2. 查看物品盒',
     '物品盒为空，无异常报错', '低'],
    ['TC-G-06', '背包物品掉落', '背包物品数量为多个时全部掉落',
     '背包中有物品A×5（drop=1）',
     '1. 让玩家死亡\n2. 检查物品盒中物品A的数量',
     '物品盒中物品A数量为5，背包中物品A为0', '中'],
    ['TC-G-07', '背包物品掉落', '死亡复活后物品盒可拾取',
     '玩家死亡，物品盒中有掉落物品',
     '1. 玩家复活\n2. 走到物品盒位置拾取\n3. 检查背包',
     '物品盒中的物品成功转移到背包', '中'],

    # ========== 装备栏装备掉落（Equipment表 - 概率掉落） ==========
    ['TC-E-01', '装备栏掉落-概率', '装备drop=100死亡时100%掉落',
     '玩家装备栏穿戴装备X，Equipment表中X的drop=100',
     '1. 记录装备X掉落前耐久\n2. 让玩家死亡\n3. 检查物品盒和装备栏',
     '装备X从装备栏消失，出现在物品盒中，耐久减少10%', '高'],
    ['TC-E-02', '装备栏掉落-概率', '装备drop=0死亡时100%不掉落（销毁）',
     '玩家装备栏穿戴装备Y，Equipment表中Y的drop=0',
     '1. 让玩家死亡\n2. 检查装备栏和物品盒',
     '装备Y从装备栏消失，物品盒中无装备Y（已被销毁）', '高'],
    ['TC-E-03', '装备栏掉落-概率', '装备drop=50死亡时按概率掉落或销毁',
     '玩家装备栏穿戴装备Z，Equipment表中Z的drop=50',
     '1. 让玩家死亡\n2. 记录结果（掉落/销毁）\n3. 重复测试20次以上统计概率',
     '装备Z约50%概率掉入物品盒（耐久减少），约50%概率被销毁', '高'],
    ['TC-E-04', '装备栏掉落-概率', '装备栏多个装备各自独立判定掉落',
     '装备栏穿戴装备A(drop=100)、装备B(drop=0)、装备C(drop=50)',
     '1. 让玩家死亡\n2. 检查每个装备的最终状态',
     '装备A掉入物品盒，装备B被销毁，装备C按50%概率掉落或销毁', '高'],
    ['TC-E-05', '装备栏掉落-概率', '死亡复活后装备栏为空（未掉落装备已销毁）',
     '装备栏穿戴装备(drop=0)',
     '1. 让玩家死亡\n2. 玩家复活\n3. 查看装备栏',
     '装备栏对应槽位为空', '中'],

    # ========== 装备掉落耐久计算 ==========
    ['TC-D-01', '掉落耐久', '装备掉落后耐久减少10%（有余数）',
     '装备栏穿戴耐久95/100的装备，drop=100',
     '1. 记录掉落前耐久：95\n2. 让玩家死亡\n3. 检查物品盒中装备耐久',
     '掉落后耐久 = Max{floor(95 - 100*10%), 1} = Max{floor(85), 1} = 85', '高'],
    ['TC-D-02', '掉落耐久', '装备掉落后耐久减少10%（耐久为10）',
     '装备栏穿戴耐久10/100的装备，drop=100',
     '1. 记录掉落前耐久：10\n2. 让玩家死亡\n3. 检查物品盒中装备耐久',
     '掉落后耐久 = Max{floor(10 - 100*10%), 1} = Max{floor(0), 1} = 1', '高'],
    ['TC-D-03', '掉落耐久', '装备掉落后耐久最低保底为1',
     '装备栏穿戴耐久1/100的装备，drop=100',
     '1. 记录掉落前耐久：1\n2. 让玩家死亡\n3. 检查物品盒中装备耐久',
     '掉落后耐久 = Max{floor(1 - 100*10%), 1} = Max{floor(-9), 1} = 1', '高'],
    ['TC-D-04', '掉落耐久', '装备满耐久掉落后耐久减少10%',
     '装备栏穿戴耐久100/100的装备，drop=100',
     '1. 记录掉落前耐久：100\n2. 让玩家死亡\n3. 检查物品盒中装备耐久',
     '掉落后耐久 = Max{floor(100 - 100*10%), 1} = Max{90, 1} = 90', '中'],
    ['TC-D-05', '掉落耐久', '装备耐久刚好扣到0时保底为1',
     '装备栏穿戴耐久9/100的装备，drop=100',
     '1. 记录掉落前耐久：9\n2. 让玩家死亡\n3. 检查物品盒中装备耐久',
     '掉落后耐久 = Max{floor(9 - 100*10%), 1} = Max{floor(-1), 1} = 1', '中'],
    ['TC-D-06', '掉落耐久', '耐久上限不为100时的计算验证',
     '装备栏穿戴耐久50/50的装备（耐久上限50），drop=100',
     '1. 记录掉落前耐久：50/50\n2. 让玩家死亡\n3. 检查物品盒中装备耐久',
     '掉落后耐久 = Max{floor(50 - 50*10%), 1} = Max{floor(45), 1} = 45', '中'],

    # ========== 边界与异常 ==========
    ['TC-B-01', '边界异常', 'drop字段为负数时的容错',
     'Equipment表中装备drop字段配置为-1',
     '1. 穿戴该装备\n2. 让玩家死亡\n3. 检查结果',
     '游戏不崩溃，装备不因负概率出现异常行为', '低'],
    ['TC-B-02', '边界异常', 'drop字段大于100时的容错',
     'Equipment表中装备drop字段配置为150',
     '1. 穿戴该装备\n2. 让玩家死亡\n3. 检查结果',
     '游戏不崩溃，装备按100%概率掉落（上限封顶）', '低'],
    ['TC-B-03', '边界异常', '装备耐久上限为1时的掉落耐久计算',
     '装备栏穿戴耐久1/1的装备，drop=100',
     '1. 让玩家死亡\n2. 检查物品盒中装备耐久',
     '掉落后耐久 = Max{floor(1 - 1*10%), 1} = Max{floor(0.9), 1} = Max{0, 1} = 1', '低'],
    ['TC-B-04', '边界异常', '多次死亡掉落物品盒物品是否叠加',
     '玩家在同一位置死亡两次，两次均有掉落',
     '1. 第一次死亡，物品盒有物品A\n2. 复活后不拾取\n3. 再次死亡\n4. 检查物品盒',
     '第二次死亡的掉落物品正确存入物品盒，与第一次不冲突', '中'],
]

for i, case in enumerate(cases, 2):
    for col, val in enumerate(case, 1):
        cell = ws.cell(row=i, column=col, value=val)
        cell.font = normal_font
        cell.alignment = wrap_align
        cell.border = thin_border

ws.column_dimensions['A'].width = 12
ws.column_dimensions['B'].width = 16
ws.column_dimensions['C'].width = 38
ws.column_dimensions['D'].width = 35
ws.column_dimensions['E'].width = 42
ws.column_dimensions['F'].width = 45
ws.column_dimensions['G'].width = 8

# 汇总表
ws2 = wb.create_sheet('用例统计')
stats = [
    ['模块', '用例数', '优先级分布'],
    ['背包物品掉落（Goods表 drop字段）', 7, '高3 / 中3 / 低1'],
    ['装备栏掉落-概率判定（Equipment表）', 5, '高4 / 中1'],
    ['掉落耐久计算', 6, '高3 / 中3'],
    ['边界与异常', 4, '中1 / 低3'],
    ['合计', 22, '高10 / 中8 / 低4'],
]
for r, row_data in enumerate(stats, 1):
    for c, val in enumerate(row_data, 1):
        cell = ws2.cell(row=r, column=c, value=val)
        if r == 1:
            cell.font = header_font
            cell.fill = header_fill
        elif r == len(stats):
            cell.font = Font(name='Arial', bold=True, size=10)
        else:
            cell.font = normal_font
        cell.alignment = center_align if c != 1 else Alignment(horizontal='left', vertical='center')
        cell.border = thin_border

ws2.column_dimensions['A'].width = 35
ws2.column_dimensions['B'].width = 12
ws2.column_dimensions['C'].width = 22

output = r'c:\Users\Administrator\WorkBuddy\Claw\物品掉落_测试用例.xlsx'
wb.save(output)
print(f'OK: {output}')
