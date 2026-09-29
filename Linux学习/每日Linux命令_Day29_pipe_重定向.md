# 🐧 今日Linux命令 · Day 29/30

**【命令】**
`pipe |` 和重定向 `> >>` - 管道与重定向

**【基本语法】**
```bash
命令1 | 命令2            # 管道：将命令1的输出作为命令2的输入
命令 > 文件              # 输出重定向：覆盖写入文件
命令 >> 文件             # 输出重定向：追加写入文件
命令 < 文件              # 输入重定向：从文件读取输入
命令 2> 文件             # 错误重定向：将错误信息写入文件
命令 &> 文件             # 同时重定向标准输出和错误
```

**【常用示例】**（从简单到复杂）

1. 基础用法 - 查看日志文件的最后20行
```bash
tail -20 /var/log/syslog
```

2. 管道用法 - 查找包含"error"的日志行并统计数量
```bash
grep "error" /var/log/syslog | wc -l
```

3. 实际工作场景 - 多重管道：查找日志中错误，去重，排序后输出到文件
```bash
grep "ERROR" app.log | awk '{print $5}' | sort | uniq -c | sort -rn > error_summary.txt
```

4. 重定向实战 - 运行脚本，正常输出和错误分别保存
```bash
python test_script.py > output.log 2> error.log
```

5. 追加写入 - 记录多次测试的执行时间
```bash
echo "=== Test started at $(date) ===" >> test_results.log
```

**【选项说明】**

| 符号 | 说明 | 示例 |
|------|------|------|
| `\|` | 管道符，将前一个命令的输出传给下一个命令 | `cat file \| grep keyword` |
| `>` | 覆盖重定向，将输出写入文件（原内容被清空） | `echo "hello" > file.txt` |
| `>>` | 追加重定向，将输出追加到文件末尾 | `echo "world" >> file.txt` |
| `<` | 输入重定向，从文件读取内容 | `wc -l < file.txt` |
| `2>` | 错误重定向，只捕获 stderr | `cmd 2> errors.log` |
| `2>&1` | 将 stderr 合并到 stdout | `cmd > all.log 2>&1` |
| `&>` | 同时重定向 stdout 和 stderr（bash 4+） | `cmd &> all.log` |

**【注意事项】**
- ⚠️ `>` 会覆盖文件原有内容，如果文件有重要数据，建议先用 `>>` 或确认文件路径正确
- `2>&1` 的写法顺序有讲究：`> file 2>&1` 正确，`2>&1 > file` 则错误信息不会被重定向到 file（只会到屏幕）
- 管道中前一个命令失败，后一个命令可能 still 运行，可以用 `set -o pipefail` 让管道整体返回失败状态码

**【一句话记住它】**
> "管道是命令之间的接力赛，重定向是命令输出的搬家服务。"
