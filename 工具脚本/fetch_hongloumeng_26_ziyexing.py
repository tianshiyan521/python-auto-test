#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 ziyexing.com 获取红楼梦第26回原文（去批注）"""

import re
import requests
from bs4 import BeautifulSoup

URL = "http://www.ziyexing.com/book/hongloumeng_p/hongloumeng_p_26.htm"
OUTPUT = r"c:\Users\Administrator\WorkBuddy\Claw\每日红楼梦_第26回_蜂腰桥设言传心事_潇湘馆春困发幽情_ziyexing.txt"

headers = {"User-Agent": "Mozilla/5.0"}
resp = requests.get(URL, headers=headers, timeout=30)
resp.encoding = resp.apparent_encoding
soup = BeautifulSoup(resp.text, "html.parser")

# 子夜星的正文在 body 内多个 table 中，取文本后清理
text = soup.get_text("\n", strip=True)

# 移除批注：〔...〕以及单行批注标记
lines = []
for line in text.splitlines():
    line = line.strip()
    if not line:
        continue
    # 跳过导航、标题等
    if line.startswith("《红楼梦》") or line.startswith("子夜星") or line.startswith("---"):
        continue
    if "返回首页" in line or "下一回" in line or "上一回" in line:
        continue
    # 去除批注〔...〕
    line = re.sub(r"〔[^〕]*〕", "", line)
    line = line.strip()
    if line:
        lines.append(line)

text = "\n".join(lines)

# 确保回目标题
if "第二十六回" not in text[:100]:
    text = "第二十六回 蜂腰桥设言传心事 潇湘馆春困发幽情\n\n" + text

# 清理多余空白
text = re.sub(r"\n{3,}", "\n\n", text)

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write(text)

print(f"已保存到 {OUTPUT}")
print(f"字数：{len(text)}")
