#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
极简微信自动回复测试脚本
"""

import itchat
from itchat.content import *
import time
from datetime import datetime

print("="*50)
print("极简微信自动回复测试")
print("="*50)

# 回复规则
REPLY_RULES = {
    "你好": "你好！我是自动回复助手~",
    "在吗": "在的，主人暂时不在，有事请留言",
    "谢谢": "不客气！",
    "吃饭": "主人还没吃饭呢，你吃了吗？",
    "工作": "主人正在忙，稍后回复",
    "晚上": "晚上好！主人可能休息了",
}

@itchat.msg_register(TEXT)
def simple_reply(msg):
    """简单回复函数"""
    content = msg['Text']
    sender = msg['User']['NickName'] if msg['User'] else '未知'
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 收到 {sender}: {content}")
    
    # 查找匹配的回复
    for keyword, reply in REPLY_RULES.items():
        if keyword in content:
            print(f"  -> 回复: {reply}")
            return reply
    
    # 默认回复
    default_reply = "收到消息！主人稍后回复你。"
    print(f"  -> 回复: {default_reply}")
    return default_reply

def main():
    """主函数"""
    print("请使用微信扫描二维码登录...")
    print("按 Ctrl+C 停止程序")
    print("="*50)
    
    try:
        # 登录微信（启用热重载，避免重复扫码）
        itchat.auto_login(
            hotReload=True,
            statusStorageDir='itchat_simple.pkl',
            enableCmdQR=2  # 在命令行显示二维码
        )
        
        print("登录成功！")
        print("开始监控消息...")
        print("测试关键词：你好、在吗、谢谢、吃饭、工作、晚上")
        print("="*50)
        
        # 保持运行
        itchat.run()
        
    except KeyboardInterrupt:
        print("\n收到停止信号，正在退出...")
    except Exception as e:
        print(f"程序运行出错: {e}")
    finally:
        itchat.logout()
        print("程序已退出")

if __name__ == "__main__":
    main()