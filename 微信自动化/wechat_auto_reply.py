#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信自动回复脚本
基于wxauto v4实现
"""

import json
import time
import sys
import re
from datetime import datetime
from typing import Dict, List, Optional
import threading

try:
    from wxauto import WeChat
    WXAUTO_AVAILABLE = True
except ImportError:
    WXAUTO_AVAILABLE = False
    print("警告: wxauto未安装，将无法实际控制微信")
    print("请运行: pip install wxauto==4.0.0")

class WeChatAutoReply:
    """微信自动回复核心类"""
    
    def __init__(self, config_file: str = "wechat_config.json"):
        """
        初始化自动回复系统
        
        Args:
            config_file: 配置文件路径
        """
        self.wechat = None
        self.config = self.load_config(config_file)
        self.running = False
        self.last_message_id = None
        self.message_history = []
        self.max_history = 100
        
        # 初始化微信客户端
        if WXAUTO_AVAILABLE:
            try:
                self.wechat = WeChat()
                print("微信客户端初始化成功")
            except Exception as e:
                print(f"微信客户端初始化失败: {e}")
        else:
            print("wxauto未安装，运行在模拟模式")
    
    def load_config(self, config_file: str) -> Dict:
        """加载配置文件"""
        default_config = {
            "reply_rules": [
                {
                    "keywords": ["你好", "在吗", "hello", "hi"],
                    "reply": "你好！我是自动回复助手，主人暂时不在，有事请留言~",
                    "enabled": True
                },
                {
                    "keywords": ["谢谢", "thank you", "thanks"],
                    "reply": "不客气！主人回来后会看到你的消息的。",
                    "enabled": True
                },
                {
                    "keywords": ["什么时候回来", "几点回来"],
                    "reply": "主人大概晚上6点后回来，我会转告他/她联系你。",
                    "enabled": True
                },
                {
                    "keywords": ["急事", "紧急", "urgent"],
                    "reply": "收到紧急消息！已经通过短信通知主人，请稍等。",
                    "enabled": True
                }
            ],
            "auto_reply_settings": {
                "enabled": True,
                "check_interval": 2.0,  # 检查间隔（秒）
                "working_hours": {
                    "start": "09:00",
                    "end": "22:00"
                },
                "ignore_groups": True,  # 是否忽略群聊
                "max_reply_per_conversation": 3  # 每个对话最大回复次数
            },
            "greeting_message": "🤖 自动回复已启用\n时间: {time}\n状态: {status}",
            "debug_mode": False
        }
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                # 合并配置
                default_config.update(user_config)
                print(f"配置文件加载成功: {config_file}")
        except FileNotFoundError:
            print(f"配置文件不存在，使用默认配置: {config_file}")
            # 保存默认配置
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"配置文件加载失败: {e}")
        
        return default_config
    
    def is_within_working_hours(self) -> bool:
        """检查是否在工作时间内"""
        settings = self.config["auto_reply_settings"]
        if not settings["enabled"]:
            return False
        
        try:
            now = datetime.now()
            current_time = now.strftime("%H:%M")
            
            start_time = settings["working_hours"]["start"]
            end_time = settings["working_hours"]["end"]
            
            return start_time <= current_time <= end_time
        except:
            return True  # 如果时间解析失败，默认允许回复
    
    def should_ignore_message(self, sender: str, content: str) -> bool:
        """判断是否应该忽略此消息"""
        # 忽略空消息
        if not content or content.strip() == "":
            return True
        
        # 忽略系统消息
        if sender == "微信团队" or "系统消息" in sender:
            return True
        
        # 如果配置忽略群聊，检查是否为群聊
        if self.config["auto_reply_settings"]["ignore_groups"]:
            if "群聊" in sender or "(" in sender and ")" in sender:
                return True
        
        # 忽略自己发送的消息
        if "我" in sender or "自己" in sender:
            return True
        
        return False
    
    def find_matching_reply(self, content: str) -> Optional[str]:
        """根据消息内容找到匹配的回复规则"""
        content_lower = content.lower()
        
        for rule in self.config["reply_rules"]:
            if not rule.get("enabled", True):
                continue
            
            for keyword in rule["keywords"]:
                if keyword.lower() in content_lower:
                    return rule["reply"]
        
        # 如果没有匹配的规则，使用默认回复
        default_replies = [
            "收到消息！主人暂时不在，我会转告他/她。",
            "消息已收到，主人稍后会回复你。",
            "好的，已经记录下来了。",
            "明白，我会转告主人。"
        ]
        
        # 根据消息长度选择不同的回复
        if len(content) > 50:
            return "收到长消息！主人回来后会仔细看的。"
        elif "?" in content or "？" in content:
            return "收到问题！主人回来后会回答你的。"
        else:
            import random
            return random.choice(default_replies)
    
    def generate_message_id(self, sender: str, content: str, timestamp: str) -> str:
        """生成消息唯一ID"""
        # 简单的哈希生成
        import hashlib
        message_str = f"{sender}:{content}:{timestamp}"
        return hashlib.md5(message_str.encode('utf-8')).hexdigest()[:16]
    
    def send_reply(self, sender: str, reply_content: str) -> bool:
        """发送回复消息"""
        if not self.wechat or not WXAUTO_AVAILABLE:
            if self.config["debug_mode"]:
                print(f"[模拟] 回复给 {sender}: {reply_content}")
            return True
        
        try:
            # 切换到对应的聊天窗口
            self.wechat.ChatWith(sender)
            time.sleep(0.5)  # 等待窗口切换
            
            # 发送回复
            self.wechat.SendMsg(reply_content)
            
            print(f"✓ 已回复 {sender}: {reply_content[:50]}...")
            return True
        except Exception as e:
            print(f"✗ 回复失败 {sender}: {e}")
            return False
    
    def monitor_messages(self):
        """监控微信消息"""
        if not self.wechat and WXAUTO_AVAILABLE:
            print("微信客户端未初始化，无法监控消息")
            return
        
        print("开始监控微信消息...")
        print(f"检查间隔: {self.config['auto_reply_settings']['check_interval']}秒")
        print(f"工作时段: {self.config['auto_reply_settings']['working_hours']['start']} - {self.config['auto_reply_settings']['working_hours']['end']}")
        
        self.running = True
        check_count = 0
        
        while self.running:
            try:
                check_count += 1
                
                # 检查是否在工作时间
                if not self.is_within_working_hours():
                    if check_count % 30 == 0:  # 每30次检查打印一次状态
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] 非工作时间，暂停自动回复")
                    time.sleep(self.config["auto_reply_settings"]["check_interval"])
                    continue
                
                if self.wechat and WXAUTO_AVAILABLE:
                    # 获取最新消息
                    messages = self.wechat.GetAllMessage()
                    
                    if messages and len(messages) > 0:
                        latest_message = messages[-1]
                        
                        sender = latest_message.get('sender', '')
                        content = latest_message.get('content', '')
                        msg_time = latest_message.get('time', '')
                        
                        # 生成消息ID
                        message_id = self.generate_message_id(sender, content, msg_time)
                        
                        # 检查是否是新消息
                        if message_id != self.last_message_id:
                            self.last_message_id = message_id
                            
                            # 处理新消息
                            if not self.should_ignore_message(sender, content):
                                print(f"[{msg_time}] 新消息来自 {sender}: {content[:50]}...")
                                
                                # 查找匹配的回复
                                reply = self.find_matching_reply(content)
                                
                                if reply:
                                    # 发送回复
                                    success = self.send_reply(sender, reply)
                                    
                                    if success:
                                        # 记录消息历史
                                        self.message_history.append({
                                            "time": msg_time,
                                            "sender": sender,
                                            "content": content,
                                            "reply": reply,
                                            "timestamp": datetime.now().isoformat()
                                        })
                                        
                                        # 限制历史记录大小
                                        if len(self.message_history) > self.max_history:
                                            self.message_history = self.message_history[-self.max_history:]
                else:
                    # 模拟模式，每10次检查打印一次状态
                    if check_count % 10 == 0:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] 模拟模式运行中...")
                
                # 等待下次检查
                time.sleep(self.config["auto_reply_settings"]["check_interval"])
                
            except KeyboardInterrupt:
                print("\n收到停止信号，正在退出...")
                self.running = False
                break
            except Exception as e:
                print(f"监控过程中出现错误: {e}")
                time.sleep(5)  # 出错后等待5秒再重试
    
    def save_message_history(self, filename: str = "wechat_history.json"):
        """保存消息历史"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.message_history, f, ensure_ascii=False, indent=2)
            print(f"消息历史已保存到: {filename}")
        except Exception as e:
            print(f"保存消息历史失败: {e}")
    
    def show_status(self):
        """显示当前状态"""
        print("\n" + "="*50)
        print("微信自动回复系统状态")
        print("="*50)
        print(f"运行状态: {'运行中' if self.running else '已停止'}")
        print(f"微信客户端: {'已连接' if self.wechat else '未连接'}")
        print(f"工作时段: {self.config['auto_reply_settings']['working_hours']['start']} - {self.config['auto_reply_settings']['working_hours']['end']}")
        print(f"当前时间: {datetime.now().strftime('%H:%M:%S')}")
        print(f"在工作时段: {'是' if self.is_within_working_hours() else '否'}")
        print(f"消息历史记录: {len(self.message_history)} 条")
        print(f"回复规则数量: {len(self.config['reply_rules'])} 条")
        print("="*50)

def main():
    """主函数"""
    print("微信自动回复系统 v1.0")
    print("="*50)
    
    # 创建自动回复实例
    auto_reply = WeChatAutoReply()
    
    # 显示状态
    auto_reply.show_status()
    
    # 检查依赖
    if not WXAUTO_AVAILABLE:
        print("\n⚠️  重要提醒:")
        print("1. 请先安装 wxauto: pip install wxauto==4.0.0")
        print("2. 确保微信客户端已登录并处于前台")
        print("3. 当前运行在模拟模式，不会实际控制微信")
        print("\n是否继续? (y/n): ", end="")
        choice = input().strip().lower()
        if choice != 'y':
            print("退出程序")
            return
    
    print("\n自动回复系统已启动!")
    print("按 Ctrl+C 停止程序")
    
    try:
        # 启动监控
        auto_reply.monitor_messages()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序运行出错: {e}")
    finally:
        # 保存消息历史
        auto_reply.save_message_history()
        print("程序已退出")

if __name__ == "__main__":
    main()