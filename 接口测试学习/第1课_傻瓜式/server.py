# -*- coding: utf-8 -*-
"""
第1课：假的游戏服务端（本地跑，练接口测试用）

- 不联网、不用装任何库，Python 自带就能跑
- 提供 6 个接口：登录 / 查角色 / 领奖励 / GM改等级 / 重置 / 心跳
- 启动后会自动打开浏览器，你在网页上点按钮，这里就会打印收到了什么请求

【你要做的】双击 "启动.bat"，别的不用管。
"""
import json
import os
import socket
import threading
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

HOST = "127.0.0.1"
BASE_DIR = Path(__file__).resolve().parent
LOCK = threading.Lock()


# ==========================================================
# 假数据：相当于游戏里的数据表（用户表 / 领奖记录表）
# ==========================================================
def fresh_db():
    return {
        "user": {
            "username": "test01",
            "password": "123456",
            "token": "tk_abc123",       # 登录成功后发给客户端的"通行证"
            "name": "小涂的恐龙",
            "level": 5,
            "gold": 1000,
        },
        "claimed": [],                  # 已经领过的礼包 id，用来测"重复领取"
        "history": [],                  # 服务端自己记的请求流水
    }


DB = fresh_db()

# ==========================================================
# 礼包配置表：相当于策划填的数值表
# ==========================================================
REWARDS = {
    1: {"name": "新手礼包", "need_level": 0,  "gold": 100},
    2: {"name": "王者礼包", "need_level": 10, "gold": 1000},
}

# ==========================================================
# 业务错误码表（游戏服务端都长这样，HTTP 状态码永远是 200）
# ==========================================================
CODE_MSG = {
    0:     "ok",
    10001: "账号或密码错误",
    10002: "token 无效或已过期",
    20001: "必填参数缺失",
    20002: "rewardId 不存在",
    50002: "等级不足",
    50003: "该礼包已领取过",
    40400: "接口不存在",
}


def now_str():
    return datetime.now().strftime("%H:%M:%S")


class Handler(BaseHTTPRequestHandler):
    server_version = "FakeGameServer/1.0"
    protocol_version = "HTTP/1.1"

    # -------- 关掉自带的大量日志，改用我们自己的一行式打印 --------
    def log_message(self, fmt, *args):
        pass

    def _console(self, method, path, code):
        print(f"[{now_str()}] {method:4} {path:28} -> code={code}  {CODE_MSG.get(code, '')}")

    # -------- 统一的响应出口 --------
    def _send(self, obj, http_status=200):
        body = json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(http_status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def _ok(self, data=None, msg="ok"):
        self._send({"code": 0, "msg": msg, "data": data if data is not None else {}})

    def _err(self, code, msg=None, http_status=200):
        self._send({"code": code, "msg": msg or CODE_MSG.get(code, "error")}, http_status)

    # -------- 读请求体 --------
    def _read_json(self):
        """返回 dict；请求体不是合法 JSON 时返回 None"""
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n).decode("utf-8") if n else ""
        if not raw.strip():
            return {}
        try:
            return json.loads(raw)
        except Exception:
            return None

    # -------- 校验 token（每个需要登录的接口都要做） --------
    def _check_token(self, token):
        if not token:
            return 20001, "缺少 token"
        if token != DB["user"]["token"]:
            return 10002, None
        return 0, None

    # ======================================================
    # GET
    # ======================================================
    def do_GET(self):
        u = urlparse(self.path)
        path = u.path
        qs = parse_qs(u.query)

        if path in ("/", "/index.html"):
            return self._serve_console()

        if path == "/api/ping":
            return self._ok({"server": "ok", "time": now_str()})

        if path == "/api/state":
            return self._ok(self._state())

        if path == "/api/role/info":
            token = (qs.get("token") or [""])[0]
            code, msg = self._check_token(token)
            if code:
                self._console("GET", path, code)
                return self._err(code, msg)
            u_ = DB["user"]
            self._console("GET", path, 0)
            return self._ok({
                "name": u_["name"],
                "level": u_["level"],
                "gold": u_["gold"],
            })

        self._console("GET", path, 40400)
        return self._err(40400, f"没有这个接口: {path}", 404)

    # ======================================================
    # POST
    # ======================================================
    def do_POST(self):
        global DB
        path = urlparse(self.path).path
        body = self._read_json()

        # 协议层的错：请求体根本不是 JSON
        if body is None:
            self._console("POST", path, 20001)
            return self._err(20001, "请求体不是合法的 JSON 格式", 400)

        # ---------- 登录 ----------
        if path == "/api/login":
            username = str(body.get("username") or "").strip()
            password = str(body.get("password") or "")

            if not username or not password:
                self._console("POST", path, 20001)
                return self._err(20001, "username 和 password 都是必填的")

            u_ = DB["user"]
            if username != u_["username"] or password != u_["password"]:
                self._console("POST", path, 10001)
                return self._err(10001)

            self._console("POST", path, 0)
            return self._ok({
                "token": u_["token"],
                "name": u_["name"],
                "level": u_["level"],
                "gold": u_["gold"],
            })

        # ---------- 领奖励 ----------
        if path == "/api/reward/claim":
            token = str(body.get("token") or "")
            reward_id = body.get("rewardId")

            code, msg = self._check_token(token)
            if code:
                self._console("POST", path, code)
                return self._err(code, msg)

            if reward_id is None:
                self._console("POST", path, 20001)
                return self._err(20001, "rewardId 是必填的")
            try:
                reward_id = int(reward_id)
            except (TypeError, ValueError):
                self._console("POST", path, 20002)
                return self._err(20002, "rewardId 必须是数字")

            if reward_id not in REWARDS:
                self._console("POST", path, 20002)
                return self._err(20002)

            cfg = REWARDS[reward_id]
            u_ = DB["user"]

            # 规则1：等级门槛
            if u_["level"] <= cfg["need_level"]:
                self._console("POST", path, 50002)
                return self._err(50002, f"{cfg['name']}需要 {cfg['need_level']} 级，你当前 {u_['level']} 级")

            # 规则2：不能重复领
            if reward_id in DB["claimed"]:
                self._console("POST", path, 50003)
                return self._err(50003, f"{cfg['name']}已经领过了")

            # 通过校验，真发奖
            DB["claimed"].append(reward_id)
            u_["gold"] += cfg["gold"]
            self._console("POST", path, 0)
            return self._ok({
                "rewardName": cfg["name"],
                "rewardGold": cfg["gold"],
                "gold": u_["gold"],
            })

        # ---------- GM 工具：改等级 ----------
        if path == "/api/gm/set_level":
            try:
                lv = int(body.get("level"))
            except (TypeError, ValueError):
                self._console("POST", path, 20001)
                return self._err(20001, "level 必须是数字")
            DB["user"]["level"] = lv
            self._console("POST", path, 0)
            return self._ok({"level": lv})

        # ---------- GM 工具：重置全部数据 ----------
        if path == "/api/gm/reset":
            DB = fresh_db()
            self._console("POST", path, 0)
            return self._ok({"msg": "已重置"})

        self._console("POST", path, 40400)
        return self._err(40400, f"没有这个接口: {path}", 404)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Content-Length", "0")
        self.end_headers()

    # ======================================================
    # 辅助
    # ======================================================
    def _state(self):
        u_ = DB["user"]
        return {
            "token": u_["token"],
            "name": u_["name"],
            "level": u_["level"],
            "gold": u_["gold"],
            "claimed": DB["claimed"],
        }

    def _serve_console(self):
        f = BASE_DIR / "练习台.html"
        if not f.exists():
            return self._err(40400, "找不到 练习台.html，请确认它和 server.py 在同一个文件夹", 404)
        body = f.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def find_free_port(start=8899, tries=20):
    for p in range(start, start + tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((HOST, p))
                return p
            except OSError:
                continue
    return None


def main():
    port = int(os.environ.get("PORT") or 0) or find_free_port()
    if port is None:
        print("找不到可用端口，8899~8918 都被占用了。关掉一些程序再试。")
        return

    url = f"http://{HOST}:{port}/"
    print("=" * 58)
    print("  接口测试练习台 · 第1课")
    print("=" * 58)
    print(f"  练习台网址 : {url}")
    print(f"  接口根地址 : http://{HOST}:{port}")
    print()
    print("  下面每收到一个请求，都会打印一行。")
    print("  关掉这个窗口 = 关掉服务端。")
    print("=" * 58)
    print()

    if not os.environ.get("NO_BROWSER"):
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()

    srv = ThreadingHTTPServer((HOST, port), Handler)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")


if __name__ == "__main__":
    main()
