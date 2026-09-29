# 🐧 今日Linux命令 · Day 30/30

**【命令】**
`awk/sed` - 文本处理

**【基本语法】**
```bash
sed [选项] '命令' 文件           # 流编辑器，按行处理文本
awk [选项] '模式{动作}' 文件     # 文本分析+数据处理工具
```

**【常用示例】**（从简单到复杂）

1. 基础用法 - 用 sed 替换文件中的文本
```bash
sed 's/error/ERROR/g' app.log
```

2. 带选项用法 - 删除空行并直接修改原文件
```bash
sed -i '/^$/d' config.txt
```

3. awk 基础 - 打印文件第1列和第3列
```bash
awk '{print $1, $3}' access.log
```

4. 实际工作场景 - 从日志中提取 IP 并统计访问次数 Top 10
```bash
awk '{print $1}' access.log | sort | uniq -c | sort -rn | head -10
```

5. 实际工作场景 - 批量修改配置文件中的端口号
```bash
sed -i 's/8080/9090/g' *.conf
```

6. 高级用法 - 按条件过滤并计算某列平均值
```bash
awk '$3 > 100 {sum += $3; count++} END {print "avg:", sum/count}' data.txt
```

**【选项说明】**

| 选项 | 说明 | 示例 |
|------|------|------|
| `-i` | 直接修改原文件（sed） | `sed -i 's/old/new/g' file.txt` |
| `-n` | 只打印经过处理/p命令的行 | `sed -n '2,5p' file.txt` |
| `-F` | 指定 awk 分隔符 | `awk -F',' '{print $2}' data.csv` |
| `-e` | 执行多个 sed 命令 | `sed -e 's/a/A/g' -e 's/b/B/g' file.txt` |
| `-r` | 使用扩展正则表达式（sed） | `sed -r 's/([0-9]+)/\1/g' file.txt` |

**【注意事项】**
- ⚠️ `sed -i` 会直接修改原文件，建议先不加 `-i` 预览效果，或先备份原文件
- awk 中 `$0` 表示整行，`$1` `$2` 表示第1、2列；列数从1开始，不是0
- 正则表达式中特殊字符需要转义，复杂场景建议先用小文件测试
- 用 `sed` 处理大文件时效率较高，但做复杂统计和计算时 awk 更合适

**【一句话记住它】**
> "sed 是文本的'查找替换'能手，awk 是结构化数据的'表格处理'专家。"
