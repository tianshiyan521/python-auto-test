#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信自动回复系统 v2.0
基于 itchat-uos（微信网页版API）
更稳定，无需窗口在前台
"""

import json
import time
import re
import threading
from datetime import datetime
from typing import Dict, List, Optional
import itchat
from itchat.content import *

class WeChatAutoReplyV2:
    """微信自动回复系统 v2.0"""
    
    def __init__(self, config_file: str = "wechat_config_v2.json"):
        """
        初始化自动回复系统
        
        Args:
            config_file: 配置文件路径
        """
        self.itchat = None
        self.config = self.load_config(config_file)
        self.running = False
        self.message_history = []
        self.max_history = 100
        self.reply_count = {}  # 记录每个对话的回复次数
        
        print("微信自动回复系统 v2.0 初始化...")
        print("基于 itchat-uos（微信网页版API）")
        print("无需微信窗口在前台，更稳定！")
    
    def load_config(self, config_file: str) -> Dict:
        """加载配置文件"""
        default_config = {
            "reply_rules": [
                {
                    "keywords": ["你好", "在吗", "hello", "hi", "哈喽", "嗨"],
                    "reply": "你好！我是自动回复助手，主人暂时不在，有事请留言~",
                    "enabled": True
                },
                {
                    "keywords": ["谢谢", "thank you", "thanks", "3Q", "谢啦"],
                    "reply": "不客气！主人回来后会看到你的消息的。",
                    "enabled": True
                },
                {
                    "keywords": ["什么时候回来", "几点回来", "多久回来", "在不在"],
                    "reply": "主人大概晚上6点后回来，我会转告他/她联系你。",
                    "enabled": True
                },
                {
                    "keywords": ["急事", "紧急", "urgent", "快点", "速回"],
                    "reply": "⚠️ 收到紧急消息！已经通过短信通知主人，请稍等。",
                    "enabled": True
                },
                {
                    "keywords": ["吃饭", "吃饭了吗", "吃了吗", "午饭", "晚饭"],
                    "reply": "主人正在忙，还没吃饭呢~ 你吃了吗？",
                    "enabled": True
                }
            ],
            "auto_reply_settings": {
                "enabled": True,
                "reply_to_friends": True,
                "reply_to_strangers": False,
                "reply_to_groups": False,
                "max_reply_per_conversation": 3,
                "working_hours": {
                    "start": "09:00",
                    "end": "22:00"
                }
            },
            "login_settings": {
                "hot_reload": True,  # 热重载，避免每次扫码
                "status_storage_dir": "itchat.pkl",
                "enable_cmd_qr": True  # 在命令行显示二维码
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
    
    def should_reply_to_message(self, msg_type: str, is_friend: bool, is_group: bool) -> bool:
        """判断是否应该回复此消息"""
        settings = self.config["auto_reply_settings"]
        
        # 检查消息类型
        if msg_type != "Text":
            return False
        
        # 检查是否回复好友
        if is_friend and not settings["reply_to_friends"]:
            return False
        
        # 检查是否回复陌生人
        if not is_friend and not settings["reply_to_strangers"]:
            return False
        
        # 检查是否回复群聊
        if is_group and not settings["reply_to_groups"]:
            return False
        
        # 检查工作时间
        if not self.is_within_working_hours():
            return False
        
        return True
    
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
        
        # 根据消息特征选择回复
        if len(content) > 50:
            return "收到长消息！主人回来后会仔细看的。"
        elif "?" in content or "？" in content:
            return "收到问题！主人回来后会回答你的。"
        elif "！" in content or "!" in content:
            return "收到重要消息！已记录。"
        else:
            import random
            return random.choice(default_replies)
    
    def get_reply_count_key(self, from_user_name: str, to_user_name: str) -> str:
        """生成回复计数器的键"""
        return f"{from_user_name}_{to_user_name}"
    
    def can_reply_to_conversation(self, from_user_name: str, to_user_name: str) -> bool:
        """检查是否可以回复此对话（限制回复次数）"""
        key = self.get_reply_count_key(from_user_name, to_user_name)
        max_replies = self.config["auto_reply_settings"]["max_reply_per_conversation"]
        
        current_count = self.reply_count.get(key, 0)
        if current_count >= max_replies:
            if self.config["debug_mode"]:
                print(f"已达到最大回复次数限制: {key} ({current_count}/{max_replies})")
            return False
        
        return True
    
    def record_reply(self, from_user_name: str, to_user_name: str):
        """记录回复次数"""
        key = self.get_reply_count_key(from_user_name, to_user_name)
        self.reply_count[key] = self.reply_count.get(key, 0) + 1
    
    @itchat.msg_register(TEXT)
    def handle_text_message(self, msg):
        """处理文本消息"""
        try:
            # 获取消息信息
            from_user_name = msg['FromUserName']
            to_user_name = msg['ToUserName']
            content = msg['Text']
            msg_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 获取发送者信息
            user_info = itchat.search_friends(userName=from_user_name)
            is_friend = user_info is not None
            is_group = from_user_name.startswith('@@')  # 群聊ID以@@开头
            
            # 获取发送者昵称
            if is_friend:
                sender_name = user_info.get('NickName', '好友')
            elif is_group:
                # 尝试获取群聊信息
                chatroom_info = itchat.search_chatrooms(userName=from_user_name)
                if chatroom_info:
                    sender_name = chatroom_info.get('NickName', '群聊')
                else:
                    sender_name = '群聊'
            else:
                sender_name = '陌生人'
            
            # 判断是否应该回复
            if not self.should_reply_to_message("Text", is_friend, is_group):
                if self.config["debug_mode"]:
                    print(f"[忽略] 来自 {sender_name}: {content[:30]}...")
                return
            
            # 检查回复次数限制
            if not self.can_reply_to_conversation(from_user_name, to_user_name):
                if self.config["debug_mode"]:
                    print(f"[限制] 来自 {sender_name}: 已达到最大回复次数")
                return
            
            # 记录消息
            print(f"[{msg_time}] 来自 {sender_name}: {content[:50]}...")
            
            # 查找匹配的回复
            reply = self.find_matching_reply(content)
            
            if reply:
                # 发送回复
                msg.user.send(reply)
                
                # 记录回复次数
                self.record_reply(from_user_name, to_user_name)
                
                # 保存到历史记录
                self.message_history.append({
                    "time": msg_time,
                    "sender": sender_name,
                    "content": content,
                    "reply": reply,
                    "type": "群聊" if is_group else "私聊",
                    "timestamp": datetime.now().isoformat()
                })
                
                # 限制历史记录大小
                if len(self.message_history) > self.max_history:
                    self.message_history = self.message_history[-self.max_history:]
                
                print(f"✓ 已回复 {sender_name}: {reply[:50]}...")
            
        except Exception as e:
            print(f"处理消息时出错: {e}")
    
    def login_and_run(self):
        """登录微信并运行"""
        print("="*50)
        print("微信自动回复系统 v2.0")
        print("="*50)
        print("请使用微信扫描二维码登录...")
        print("(二维码会在命令行中显示)")
        print("="*50)
        
        # 登录设置
        login_settings = self.config["login_settings"]
        
        try:
            # 登录微信 - 直接使用itchat模块，不是self.itchat
            itchat.auto_login(
                hotReload=login_settings["hot_reload"],
                statusStorageDir=login_settings["status_storage_dir"],
                enableCmdQR=login_settings["enable_cmd_qr"]
            )
            
            print("登录成功！")
            print("="*50)
            print("系统状态:")
            print(f"工作时段: {self.config['auto_reply_settings']['working_hours']['start']} - {self.config['auto_reply_settings']['working_hours']['end']}")
            print(f"当前时间: {datetime.now().strftime('%H:%M:%S')}")
            print(f"回复好友: {'是' if self.config['auto_reply_settings']['reply_to_friends'] else '否'}")
            print(f"回复陌生人: {'是' if self.config['auto_reply_settings']['reply_to_strangers'] else '否'}")
            print(f"回复群聊: {'是' if self.config['auto_reply_settings']['reply_to_groups'] else '否'}")
            print(f"每条对话最大回复: {self.config['auto_reply_settings']['max_reply_per_conversation']}次")
            print("="*50)
            print("自动回复已启用！按 Ctrl+C 停止程序")
            print("="*50)
            
            # 保持运行
            self.running = True
            itchat.run()
            
        except KeyboardInterrupt:
            print("\n收到停止信号，正在退出...")
        except Exception as e:
            print(f"登录或运行过程中出错: {e}")
        finally:
            self.running = False
            itchat.logout()
            print("程序已退出")
    
    def save_message_history(self, filename: str = "wechat_history_v2.json"):
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
        print("微信自动回复系统状态 v2.0")
        print("="*50)
        print(f"运行状态: {'运行中' if self.running else '已停止'}")
        print(f"微信登录: {'已登录' if self.itchat else '未登录'}")
        print(f"当前时间: {datetime.now().strftime('%H:%M:%S')}")
        print(f"在工作时段: {'是' if self.is_within_working_hours() else '否'}")
        print(f"消息历史记录: {len(self.message_history)} 条")
        print(f"回复规则数量: {len(self.config['reply_rules'])} 条")
        print("="*50)

def main():
    """主函数"""
    print("正在启动微信自动回复系统 v2.0...")
    
    # 创建自动回复实例
    auto_reply = WeChatAutoReplyV2()
    
    # 显示状态
    auto_reply.show_status()
    
    try:
        # 登录并运行
        auto_reply.login_and_run()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序运行出错: {e}")
    finally:
        # 保存消息历史
        auto_reply.save_message_history()
        print("感谢使用微信自动回复系统 v2.0！")

if __name__ == "__main__":
    main()