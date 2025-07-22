#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coze Chatflow客户端
专门用于在coze.cn插件中调用coze.com的工作流API

作者: AI Assistant
创建时间: 2025-07-20
"""

import requests
import json
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

class CozeChatflowClient:
    """Coze Chatflow API客户端"""
    
    def __init__(self, access_token: str, base_url: str = "https://api.coze.com"):
        """
        初始化Chatflow客户端
        
        Args:
            access_token: 访问令牌 (pat_开头的个人访问令牌)
            base_url: API基础URL
        """
        self.access_token = access_token
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
        # 设置请求头
        self.session.headers.update({
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'User-Agent': 'Coze-Chatflow-Client/1.0'
        })
        
        # 配置日志
        self.logger = logging.getLogger(__name__)
    
    def run_chatflow(self, 
                    workflow_id: str,
                    content: str = "你好",
                    app_id: Optional[str] = None,
                    bot_id: Optional[str] = None,
                    conversation_id: Optional[str] = None,
                    parameters: Optional[Dict[str, Any]] = None,
                    additional_messages: Optional[List[Dict[str, Any]]] = None,
                    ext: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        运行已发布的chatflow
        
        Args:
            workflow_id: 要执行的chatflow ID，必须是已发布的
            content: 消息内容，默认为"你好"
            app_id: Coze应用ID（可选）
            bot_id: 关联的智能体ID（可选）
            conversation_id: 关联的会话ID（可选）
            parameters: chatflow的输入参数（可选）
            additional_messages: 额外的聊天信息（可选）
            ext: 额外字段，Map[String][String]格式（可选）
            
        Returns:
            API响应结果
        """
        try:
            # 构建请求体
            payload = {
                "workflow_id": workflow_id
            }
            
            # 添加additional_messages
            if additional_messages is None:
                additional_messages = [{
                    "content": content,
                    "content_type": "text",
                    "role": "user",
                    "type": "question"
                }]
            
            payload["additional_messages"] = additional_messages
            
            # 添加可选参数
            if parameters is not None:
                payload["parameters"] = parameters
            else:
                payload["parameters"] = {}
            
            if app_id is not None:
                payload["app_id"] = app_id
            
            if bot_id is not None:
                payload["bot_id"] = bot_id
            
            if conversation_id is not None:
                payload["conversation_id"] = conversation_id
            
            if ext is not None:
                payload["ext"] = ext
            
            # 发送请求
            response = self.session.post(
                f"{self.base_url}/v1/workflows/chat",
                json=payload
            )
            
            # 处理响应
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json(),
                    'status_code': response.status_code,
                    'message': 'Chatflow执行成功'
                }
            else:
                error_data = {}
                try:
                    error_data = response.json()
                except:
                    pass
                
                return {
                    'success': False,
                    'message': f'Chatflow执行失败，状态码: {response.status_code}',
                    'status_code': response.status_code,
                    'error': error_data,
                    'error_text': response.text
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'message': f'网络请求错误: {str(e)}',
                'error': str(e)
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'未知错误: {str(e)}',
                'error': str(e)
            }
    
    def create_message(self, content: str, 
                      content_type: str = "text",
                      role: str = "user",
                      message_type: str = "question",
                      meta_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        创建消息对象
        
        Args:
            content: 消息内容
            content_type: 消息内容类型，默认为"text"
            role: 发送消息的实体，"user"或"assistant"
            message_type: 消息类型，"question"或"answer"或"function_call"或"tool_response"
            meta_data: 额外的消息数据
            
        Returns:
            消息对象
        """
        message = {
            "content": content,
            "content_type": content_type,
            "role": role,
            "type": message_type
        }
        
        if meta_data is not None:
            message["meta_data"] = meta_data
        
        return message
    
    def test_connection(self) -> Dict[str, Any]:
        """
        测试API连接和令牌有效性
        
        Returns:
            测试结果
        """
        try:
            # 尝试访问一个简单的API端点来测试连接
            response = self.session.get(f"{self.base_url}/v1/user/profile")
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'message': '连接成功，令牌有效',
                    'status_code': response.status_code
                }
            elif response.status_code == 401:
                return {
                    'success': False,
                    'message': '认证失败，请检查访问令牌',
                    'status_code': response.status_code,
                    'error': response.text
                }
            else:
                return {
                    'success': False,
                    'message': f'API请求失败，状态码: {response.status_code}',
                    'status_code': response.status_code,
                    'error': response.text
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'message': f'网络连接错误: {str(e)}',
                'error': str(e)
            }

def load_config() -> Dict[str, Any]:
    """
    从配置文件加载配置
    
    Returns:
        配置字典
    """
    try:
        with open("coze_config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
            return config
    except FileNotFoundError:
        print("❌ 配置文件 coze_config.json 不存在")
        return {}
    except json.JSONDecodeError as e:
        print(f"❌ 配置文件格式错误: {e}")
        return {}
    except Exception as e:
        print(f"❌ 加载配置文件失败: {e}")
        return {}

def create_chatflow_config_template():
    """
    创建chatflow配置模板
    """
    config = {
        "access_token": "pat_ZJFRWrFB89O1vAZVXrNR90PvkN7UNMEecWANZ1gQghIAqX4xNGhwfElNf8NTdXAf",
        "base_url": "https://api.coze.com",
        "chatflow_config": {
            "workflow_id": "7514923198020304901",
            "app_id": "请输入app_id",
            "bot_id": "请输入bot_id",
            "conversation_id": "请输入conversation_id",
            "default_content": "你好",
            "parameters": {},
            "ext": {
                "key_1": "输入值"
            }
        },
        "description": "Coze Chatflow API配置文件",
        "setup_instructions": {
            "step1": "将access_token替换为您的实际个人访问令牌",
            "step2": "配置workflow_id为您要调用的chatflow ID",
            "step3": "根据需要配置app_id、bot_id等参数",
            "step4": "运行测试脚本验证配置"
        }
    }
    
    with open("chatflow_config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print("✅ Chatflow配置模板已创建: chatflow_config.json")

def main():
    """
    主函数 - 演示chatflow调用
    """
    print("🚀 Coze Chatflow客户端测试")
    print("=" * 50)
    
    # 加载配置
    config = load_config()
    
    if not config or 'personal_token' not in config:
        print("❌ 未找到有效的配置")
        print("\n创建配置模板...")
        create_chatflow_config_template()
        print("\n请按以下步骤操作:")
        print("1. 编辑 chatflow_config.json 文件")
        print("2. 配置您的访问令牌和工作流ID")
        print("3. 重新运行此脚本")
        return
    
    # 初始化客户端
    access_token = config.get('personal_token')
    client = CozeChatflowClient(access_token)
    
    # 测试连接
    print("\n🔍 测试API连接...")
    test_result = client.test_connection()
    
    if test_result['success']:
        print("✅ 连接成功!")
    else:
        print(f"❌ 连接失败: {test_result['message']}")
        return
    
    # 示例：运行chatflow
    print("\n🔄 运行Chatflow示例...")
    
    # 使用示例配置
    workflow_id = "7514923198020304901"  # 示例工作流ID
    content = "你好，请介绍一下自己"
    
    result = client.run_chatflow(
        workflow_id=workflow_id,
        content=content
    )
    
    if result['success']:
        print("✅ Chatflow执行成功!")
        print(f"响应数据: {json.dumps(result['data'], indent=2, ensure_ascii=False)}")
    else:
        print(f"❌ Chatflow执行失败: {result['message']}")
        if 'error' in result:
            print(f"错误详情: {result['error']}")
    
    print("\n🎉 测试完成!")

if __name__ == "__main__":
    main()