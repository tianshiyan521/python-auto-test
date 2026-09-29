#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从维基文库获取红楼梦第26回原文（繁体转简体）"""

import re
import requests
from bs4 import BeautifulSoup
from zhconv import convert

URL = "https://zh.wikisource.org/wiki/紅樓夢/第026回"
OUTPUT = r"c:\Users\Administrator\WorkBuddy\Claw\每日红楼梦_第26回_蜂腰桥设言传心事_潇湘馆春困发幽情_wikisource.txt"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

resp = requests.get(URL, headers=headers, timeout=30)
resp.encoding = "utf-8"
soup = BeautifulSoup(resp.text, "html.parser")

container = soup.select_one(".mw-parser-output")
if not container:
    raise RuntimeError("未找到正文容器")

# 移除批注、编辑链接等
for tag in container.find_all(["script", "style", "sup", "a"]):
    tag.decompose()

# 获取文本
text = container.get_text("\n", strip=True)

# 转换为简体
text = convert(text, "zh-cn")

# 清理：移除空行，但保留段落结构
lines = [line.strip() for line in text.splitlines() if line.strip()]
text = "\n".join(lines)

# 保存
with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write(text)

print(f"已保存到 {OUTPUT}")
print(f"字数：{len(text)}")
