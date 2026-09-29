# -*- coding: utf-8 -*-
"""
第2课：把第1课手点的那些事，变成脚本一键跑完。

────────────────────────────────────────────────
所有自动化接口测试脚本，骨架都是下面这四块：

    ① 用例表  CASES      一条用例 = 一行数据。想加用例？加一行就行。
    ② 发请求  call()     封装 requests，统一处理超时和异常。
    ③ 断言    check()    判断"对不对"。
                         ⚠️ 注意：不是判断"通没通"，HTTP 200 什么都不代表。
    ④ 报告    report()   汇总结果，把失败的用例摊开说清楚。
────────────────────────────────────────────────

运行方式：双击同目录的 跑测试.bat
（它会自动帮你开关服务端，不用你操心）
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import requests
except ImportError:
    print("缺少 requests 库。先装一下：pip install requests")
    sys.exit(1)

HERE = Path(__file__).resolve().parent
SERVER_DIR = HERE.parent / "第1课_傻瓜式"
BASE = "http://127.0.0.1:8899"
TOKEN = "tk_abc123"

LINE = "=" * 66
THIN = "-" * 66


# ══════════════════════════════════════════════════════════════
#  ② 发请求：统一封装
# ══════════════════════════════════════════════════════════════
def call(method, path, params=None):
    """
    发一个请求，返回 (HTTP状态码, 响应体)。
    响应体不是 JSON 时返回 None —— 这种情况本身就算异常。
    """
    url = BASE + path
    try:
        if method == "GET":
            r = requests.get(url, params=params, timeout=5)
        else:
            r = requests.post(url, json=params, timeout=5)
    except requests.exceptions.RequestException as e:
        return -1, {"raw_error": str(e)}

    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, None


# ══════════════════════════════════════════════════════════════
#  前置动作：让每条用例从同一个起点出发
#  （用例之间互不影响，是设计用例的基本要求）
# ══════════════════════════════════════════════════════════════
def reset():
    call("POST", "/api/gm/reset", {})


def set_level(n):
    reset()
    call("POST", "/api/gm/set_level", {"level": n})


def already_claimed(rid):
    reset()
    call("POST", "/api/reward/claim", {"token": TOKEN, "rewardId": rid})


# ══════════════════════════════════════════════════════════════
#  ① 用例表
#  kind 一栏就是「测试点分类」，这批用例覆盖了 5 类
# ══════════════════════════════════════════════════════════════
CASES = [
    # ---------- 正常流程 ----------
    {
        "no": 1, "kind": "正常流程",
        "title": "账号密码正确 → 登录成功",
        "before": None,
        "req": ("POST", "/api/login", {"username": "test01", "password": "123456"}),
        "expect": {"code": 0, "data.token": TOKEN},
        "why": "最基本的正向路径。它要是挂了，后面的用例全都不用跑了。",
    },
    {
        "no": 4, "kind": "正常流程",
        "title": "带正确 token 查角色信息",
        "before": reset,
        "req": ("GET", "/api/role/info", {"token": TOKEN}),
        "expect": {"code": 0, "data.level": 5, "data.gold": 1000},
        "why": "光看 code=0 不够，还要核对返回的数值对不对（等级、金币）。",
    },
    {
        "no": 6, "kind": "正常流程",
        "title": "首次领新手礼包 → 金币到账",
        "before": reset,
        "req": ("POST", "/api/reward/claim", {"token": TOKEN, "rewardId": 1}),
        "expect": {"code": 0, "data.gold": 1100},
        "why": "1000 + 100 = 1100。必须核对加了多少，只看「成功」会被糊弄。",
    },
    {
        "no": 10, "kind": "正常流程",
        "title": "20 级领王者礼包 → 成功",
        "before": lambda: set_level(20),
        "req": ("POST", "/api/reward/claim", {"token": TOKEN, "rewardId": 2}),
        "expect": {"code": 0, "data.gold": 2000},
        "why": "超过门槛的正常发奖。1000 + 1000 = 2000。",
    },

    # ---------- 参数校验 ----------
    {
        "no": 2, "kind": "参数校验",
        "title": "密码错误 → 拒绝登录",
        "before": reset,
        "req": ("POST", "/api/login", {"username": "test01", "password": "wrong"}),
        "expect": {"code": 10001},
        "why": "错误密码必须被拦住，这是最基础的安全底线。",
    },
    {
        "no": 3, "kind": "参数校验",
        "title": "用户名为空 → 提示缺参",
        "before": reset,
        "req": ("POST", "/api/login", {"username": "", "password": "123456"}),
        "expect": {"code": 20001},
        "why": "空值校验，版本迭代时最容易被改漏。",
    },
    {
        "no": 11, "kind": "参数校验",
        "title": "rewardId 不存在（999）→ 拒绝",
        "before": reset,
        "req": ("POST", "/api/reward/claim", {"token": TOKEN, "rewardId": 999}),
        "expect": {"code": 20002},
        "why": "非法枚举值。客户端改包、策划改表都可能造出这种请求。",
    },

    # ---------- 鉴权 ----------
    {
        "no": 5, "kind": "鉴权",
        "title": "token 错误 → 拒绝访问",
        "before": reset,
        "req": ("GET", "/api/role/info", {"token": "wrong"}),
        "expect": {"code": 10002},
        "why": "通行证不对就必须拦住，这是权限测试的基础。",
    },

    # ---------- 幂等 / 重复提交 ----------
    {
        "no": 7, "kind": "幂等",
        "title": "重复领新手礼包 → 拦截",
        "before": lambda: already_claimed(1),
        "req": ("POST", "/api/reward/claim", {"token": TOKEN, "rewardId": 1}),
        "expect": {"code": 50003},
        "why": "重复提交是最常见的线上事故：点两下多拿一份奖励。",
    },

    # ---------- 边界值 ----------
    {
        "no": 8, "kind": "边界值",
        "title": "5 级领王者礼包 → 等级不足",
        "before": lambda: set_level(5),
        "req": ("POST", "/api/reward/claim", {"token": TOKEN, "rewardId": 2}),
        "expect": {"code": 50002},
        "why": "门槛是 10 级，差 5 级当然不能领。边界外侧。",
    },
    {
        "no": 9, "kind": "边界值",
        "title": "10 级领王者礼包 → 应该能领",
        "before": lambda: set_level(10),
        "req": ("POST", "/api/reward/claim", {"token": TOKEN, "rewardId": 2}),
        "expect": {"code": 0, "data.gold": 2000},
        "why": "★ 刚好等于门槛。手动测试最爱漏的就是「正好等于」这一个点。",
    },
]


# ══════════════════════════════════════════════════════════════
#  ③ 断言
# ══════════════════════════════════════════════════════════════
def dig(obj, path):
    """按 a.b.c 的路径，从嵌套字典里取值。取不到返回 (None, False)"""
    cur = obj
    for key in path.split("."):
        if isinstance(cur, dict) and key in cur:
            cur = cur[key]
        else:
            return None, False
    return cur, True


def check(body, expect):
    """逐项核对期望值，返回 (是否通过, 问题清单)"""
    if body is None:
        return False, ["响应体不是合法 JSON"]
    if "raw_error" in body:
        return False, ["请求根本没发出去：" + body["raw_error"]]

    problems = []
    for path, want in expect.items():
        got, found = dig(body, path)
        if not found:
            problems.append("%s  →  字段不存在" % path)
        elif got != want:
            problems.append("%s  →  期望 %r，实际 %r" % (path, want, got))
    return (len(problems) == 0), problems


# ══════════════════════════════════════════════════════════════
#  执行 + ④ 报告
# ══════════════════════════════════════════════════════════════
def run_all():
    results = []
    for c in CASES:
        if c["before"]:
            c["before"]()

        method, path, params = c["req"]
        http, body = call(method, path, params)
        ok, problems = check(body, c["expect"])

        results.append({
            "case": c, "http": http, "body": body,
            "ok": ok, "problems": problems,
            "sent": params,
        })
    return results


def pad(s, width):
    """按显示宽度左对齐补齐（中文算 2 格，否则表格会歪）"""
    w = sum(2 if ord(ch) > 127 else 1 for ch in str(s))
    return str(s) + " " * max(0, width - w)


def report(results):
    passed = [r for r in results if r["ok"]]
    failed = [r for r in results if not r["ok"]]

    print()
    print(LINE)
    print("  接口自动化测试报告")
    print("  被测对象：假游戏服务端  %s" % BASE)
    print(LINE)
    print("  " + pad("编号", 6) + pad("类型", 12) + pad("结果", 8) + "用例")
    print(THIN)
    for r in sorted(results, key=lambda x: x["case"]["no"]):
        mark = "✅" if r["ok"] else "❌"
        print("  " + pad(r["case"]["no"], 6) + pad(r["case"]["kind"], 12)
              + pad(mark, 8) + r["case"]["title"])
    print(THIN)
    print("  合计 %d 条   通过 %d   失败 %d" % (len(results), len(passed), len(failed)))
    print(LINE)

    # ---- 失败详情 ----
    if failed:
        print()
        print("  🐛 发现 %d 个疑似缺陷：" % len(failed))
        for r in failed:
            c = r["case"]
            print()
            print(THIN)
            print("  [%d] %s" % (c["no"], c["title"]))
            print(THIN)
            print("  打的是：%s %s" % (c["req"][0], c["req"][1]))
            print("  发出去：%s" % json.dumps(r["sent"], ensure_ascii=False))
            print("  HTTP  ：%s   ← 注意，这里通常也是 200" % r["http"])
            print("  实际回：%s" % json.dumps(r["body"], ensure_ascii=False))
            print()
            print("  问题：")
            for p in r["problems"]:
                print("    · %s" % p)
            print()
            print("  这条为什么值得测：")
            print("    %s" % c["why"])
        print()

    # ---- 覆盖说明 ----
    kinds = {}
    for r in results:
        kinds.setdefault(r["case"]["kind"], []).append(str(r["case"]["no"]))
    print(LINE)
    print("  这批用例覆盖了 %d 类测试点：" % len(kinds))
    for k, nos in kinds.items():
        print("    · " + pad(k, 10) + "用例 %s" % "、".join(nos))
    print(LINE)
    print()

    return 0 if not failed else 1


# ══════════════════════════════════════════════════════════════
#  服务端自动开关（不用你管）
# ══════════════════════════════════════════════════════════════
def server_is_up():
    try:
        r = requests.get(BASE + "/api/ping", timeout=1)
        return r.json().get("data", {}).get("server") == "ok"
    except Exception:
        return False


def start_server():
    env = dict(os.environ)
    env["NO_BROWSER"] = "1"
    env["PORT"] = "8899"
    script = SERVER_DIR / "server.py"
    if not script.exists():
        print("  找不到服务端文件：%s" % script)
        return None
    p = subprocess.Popen(
        [sys.executable, str(script)],
        cwd=str(SERVER_DIR), env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    for _ in range(40):
        if server_is_up():
            return p
        time.sleep(0.2)
    p.terminate()
    return None


def main():
    print()
    print("  第2课 · 接口自动化测试")
    print("  正在准备环境 ...")

    own = None
    if server_is_up():
        print("  检测到服务端已经开着，直接用它。")
    else:
        print("  服务端没开，正在自动启动 ...")
        own = start_server()
        if own is None:
            print("  ❌ 服务端启动失败。请确认 %s 存在。" % (SERVER_DIR / "server.py"))
            return 1
        print("  服务端就绪。")

    try:
        results = run_all()
        code = report(results)
    finally:
        if own:
            own.terminate()
            print("  服务端已自动关闭。")
            print()

    return code


if __name__ == "__main__":
    sys.exit(main())
