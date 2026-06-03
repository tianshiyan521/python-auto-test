# -*- coding: utf-8 -*-
"""
恐龙岛 - Unity Windows 自动化测试脚本
使用 Airtest + Poco(Unity) 进行游戏 UI 自动化测试

前提条件:
1. 恐龙岛游戏已启动并运行在 Windows 桌面
2. 已安装 airtest 1.4.3 + pocoui 1.0.94

使用方法:
1. 先启动恐龙岛游戏
2. 运行本脚本: python dino_island_test.py
"""

import sys, io, time, traceback
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from airtest.core.api import *

print("=" * 55)
print("  恐龙岛自动化测试 - Unity Windows 模式")
print("=" * 55)

# ============================================
# 配置区（根据实际情况修改）
# ============================================
GAME_WINDOW_TITLE = "恐龙岛"   # 游戏窗口标题, 用于定位游戏窗口

# ============================================
# Step 1: 连接 Windows 桌面
# ============================================
print("\n[Step 1] 连接 Windows 桌面...")
try:
    auto_setup(__file__, devices=["Windows:///"])
    print("  >> 连接成功!")
except Exception as e:
    print(f"  >> 连接失败: {e}")
    print("  请确保脚本以管理员权限运行")
    sys.exit(1)

# ============================================
# Step 2: 初始化 Poco (Unity 引擎)
# ============================================
print("\n[Step 2] 初始化 Poco (Unity引擎)...")
try:
    from poco.drivers.unityengine import UnityPoco
    poco = UnityPoco()
    # 验证 Poco 连接成功
    poco("Name").get_text()
    print("  >> Poco 连接成功! 可以读取游戏UI控件")
except Exception as e:
    print(f"  >> Poco 连接失败: {e}")
    print("  提示: 请确保游戏内已开启 Poco 服务")
    print("  需要在游戏工程中接入 Poco SDK:")
    print("  1. 将 PocoManager.prefab 拖入游戏场景")
    print("  2. 游戏启动后会自动监听 Poco 端口")
    print("\n  如果游戏未接入 Poco SDK, 将切换到纯图像识别模式...")
    poco = None

# ============================================
# 测试用例: 自动培养池功能
# ============================================
test_results = []

def run_test(name, func):
    """执行单个测试用例并记录结果"""
    print(f"\n--- 测试: {name} ---")
    try:
        func()
        test_results.append((name, "PASS", ""))
        print(f"  >> [PASS] {name}")
    except AssertionError as e:
        test_results.append((name, "FAIL", str(e)))
        print(f"  >> [FAIL] {name}: {e}")
        snapshot(f"fail_{name}.png")
    except Exception as e:
        test_results.append((name, "ERROR", str(e)))
        print(f"  >> [ERROR] {name}: {e}")
        snapshot(f"error_{name}.png")

def test_01_game_running():
    """测试1: 验证游戏正在运行"""
    if poco:
        # Poco 模式: 读取游戏内控件
        ui_tree = poco.renderHierarchy()
        assert len(ui_tree) > 0, "游戏UI树为空"
    else:
        # 图像模式: 验证游戏窗口存在
        # 需要提前截一张游戏主界面的图: game_main.png
        assert_exists(Template("game_main.png"), "游戏主界面")
    print("  游戏运行正常")

def test_02_enter_cultivate_pool():
    """测试2: 进入自动培养池"""
    if poco:
        poco("Btn_CultivatePool").click()
    else:
        touch(Template("btn_cultivate_pool.png"))
    sleep(2)
    print("  已点击培养池入口")

def test_03_select_dinosaur():
    """测试3: 选择一只恐龙"""
    if poco:
        # 找到恐龙列表中的第一个可培养恐龙
        dinosaurs = poco("DinosaurList").children()
        assert len(dinosaurs) > 0, "恐龙列表为空"
        dinosaurs[0].click()
        print(f"  已选择恐龙 (共 {len(dinosaurs)} 只)")
    else:
        touch(Template("first_dinosaur.png"))
        print("  已点击第一只恐龙")

def test_04_start_cultivate():
    """测试4: 开始培养"""
    if poco:
        btn = poco("Btn_StartCultivate")
        assert btn.exists(), "开始培养按钮不存在"
        btn.click()
        print("  已点击开始培养")
    else:
        touch(Template("btn_start_cultivate.png"))
    sleep(1)

def test_05_verify_cultivating():
    """测试5: 验证培养状态"""
    if poco:
        status_text = poco("Text_CultivateStatus").get_text()
        print(f"  培养状态文字: {status_text}")
        assert status_text, "未获取到培养状态"
        # 常见状态: "培养中", "已完成", "0/100" 等
    else:
        assert_exists(Template("cultivating_indicator.png"), "培养中标识")
    print("  培养功能正常")

def test_06_swipe_dinosaur_list():
    """测试6: 滑动恐龙列表"""
    # 获取屏幕分辨率, 计算滑动坐标
    w, h = device().get_current_resolution()
    start_pos = (w // 2, h * 3 // 4)
    end_pos = (w // 2, h // 4)
    swipe(start_pos, end_pos, duration=0.5)
    sleep(1)
    print(f"  已滑动恐龙列表 (屏幕: {w}x{h})")

def test_07_take_screenshot():
    """测试7: 截图保存测试证据"""
    filename = "cultivate_pool_test.png"
    snapshot(filename)
    print(f"  截图已保存: {filename}")

# ============================================
# 执行测试
# ============================================
print("\n" + "=" * 55)
print("  开始执行测试用例")
print("=" * 55)

tests = [
    ("游戏运行状态检查", test_01_game_running),
    ("进入自动培养池", test_02_enter_cultivate_pool),
    ("选择恐龙", test_03_select_dinosaur),
    ("开始培养", test_04_start_cultivate),
    ("验证培养状态", test_05_verify_cultivating),
    ("滑动恐龙列表", test_06_swipe_dinosaur_list),
    ("截图保存", test_07_take_screenshot),
]

for name, func in tests:
    run_test(name, func)
    sleep(1)

# ============================================
# 输出测试报告
# ============================================
print("\n" + "=" * 55)
print("  测试报告")
print("=" * 55)

pass_count = sum(1 for _, r, _ in test_results if r == "PASS")
fail_count = sum(1 for _, r, _ in test_results if r == "FAIL")
error_count = sum(1 for _, r, _ in test_results if r == "ERROR")
total = len(test_results)

print(f"\n  总计: {total}  通过: {pass_count}  失败: {fail_count}  错误: {error_count}\n")
for name, result, msg in test_results:
    status = "[PASS]" if result == "PASS" else f"[{result}]"
    print(f"  {status} {name}" + (f" - {msg}" if msg else ""))

print(f"\n  通过率: {pass_count/total*100:.1f}%")
print("=" * 55)
