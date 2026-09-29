"""
鼠标实时坐标工具 - 双击运行后，鼠标移动即可看到坐标
按 ESC 退出
"""
import ctypes
import time

# Windows API 获取鼠标位置
class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

def get_mouse_pos():
    pos = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pos))
    return pos.x, pos.y

print("=" * 40)
print("   鼠标坐标工具")
print("   移动鼠标查看坐标")
print("   按 ESC 退出")
print("=" * 40)

last_x, last_y = -1, -1
# ESC 的虚拟键码
VK_ESCAPE = 0x1B

try:
    while True:
        x, y = get_mouse_pos()
        # 只有坐标变了才打印，避免刷屏太快
        if x != last_x or y != last_y:
            print(f"\r   X: {x:>5d}   Y: {y:>5d}    ", end="", flush=True)
            last_x, last_y = x, y

        # 检测 ESC 键
        if ctypes.windll.user32.GetAsyncKeyState(VK_ESCAPE) & 0x8000:
            print(f"\n\n   最终坐标: ({x}, {y})")
            break

        time.sleep(0.05)
except KeyboardInterrupt:
    print("\n\n   已退出")
