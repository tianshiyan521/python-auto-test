#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""获取红楼梦第26回原文并保存"""

import re
import requests
from bs4 import BeautifulSoup

URL = "http://gushiwen.cn/guwen/bookv_100a98f7ca0d.aspx"
OUTPUT = r"c:\Users\Administrator\WorkBuddy\Claw\每日红楼梦_第26回_蜂腰桥设言传心事_潇湘馆春困发幽情.txt"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

resp = requests.get(URL, headers=headers, timeout=30)
resp.encoding = resp.apparent_encoding
soup = BeautifulSoup(resp.text, "html.parser")

# 古诗文网正文一般在 .contson 或 #sonsyuanwen 下
container = soup.select_one(".contson") or soup.select_one("#sonsyuanwen")
if not container:
    raise RuntimeError("未找到正文容器")

# 移除不需要的元素
for tag in container.find_all(["script", "style", "a", "img"]):
    tag.decompose()

# 获取文本并清理
text = container.get_text("\n", strip=True)

# 去除可能的赏析/注释部分（通常以特定关键词开始）
# 古诗文网红楼梦页面一般只有原文，这里先做简单过滤
lines = []
for line in text.splitlines():
    line = line.strip()
    if not line:
        continue
    lines.append(line)

text = "\n".join(lines)

# 确保包含回目标题
if "第二十六回" not in text:
    text = "第二十六回 蜂腰桥设言传心事 潇湘馆春困发幽情\n\n" + text

# 保存
with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write(text)

print(f"已保存到 {OUTPUT}")
print(f"字数：{len(text)}")
