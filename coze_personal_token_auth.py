#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coze个人访问令牌认证模块
使用个人访问令牌(Personal Access Token)进行API认证

作者: AI Assistant
创建时间: 2025-07-20
"""

import requests
import json
from datetime import datetime
import logging
from typing import Dict, Any, Optional

class CozePersonalTokenAuth:
    """Coze个人访问令牌认证类"""
    
    def __init__(self, personal_token: str, base_url: str = "https://api.coze.com"):
        """
        初始化认证客户端
        
        Args:
            personal_token: 个人访问令牌
            base_url: API基础URL
        """
        self.personal_token = personal_token
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
        # 设置默认请求头
        self.session.headers.update({
            'Authorization': f'Bearer {self.personal_token}',
            'Content-Type': 'application/json',
            'User-Agent': 'Coze-Python-Client/1.0'
        })
        
        # 配置日志
        self.logger = logging.getLogger(__name__)
        
    def test_connection(self) -> Dict[str, Any]:
        """
        测试API连接和令牌有效性
        
        Returns:
            测试结果字典
        """
        try:
            # 尝试获取用户信息来验证令牌
            response = self.session.get(f"{self.base_url}/v1/user/profile")
            
            if response.status_code == 200:
                user_info = response.json()
                return {
                    'success': True,
                    'message': '连接成功，令牌有效',
                    'user_info': user_info,
                    'status_code': response.status_code
                }
            elif response.status_code == 401:
                return {
                    'success': False,
                    'message': '认证失败，请检查个人访问令牌',
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
    
    def list_bots(self) -> Dict[str, Any]:
        """
        获取用户的机器人列表
        
        Returns:
            机器人列表响应
        """
        try:
            response = self.session.get(f"{self.base_url}/v1/space/published_bots_list")
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json(),
                    'status_code': response.status_code
                }
            else:
                return {
                    'success': False,
                    'message': f'获取机器人列表失败，状态码: {response.status_code}',
                    'status_code': response.status_code,
                    'error': response.text
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'message': f'网络请求错误: {str(e)}',
                'error': str(e)
            }
    
    def chat_with_bot(self, bot_id: str, message: str, user_id: str = "user123", 
                     conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        与指定机器人进行对话
        
        Args:
            bot_id: 机器人ID
            message: 用户消息
            user_id: 用户ID
            conversation_id: 会话ID（可选）
            
        Returns:
            对话响应
        """
        try:
            payload = {
                "bot_id": bot_id,
                "user_id": user_id,
                "query": message,
                "stream": False
            }
            
            if conversation_id:
                payload["conversation_id"] = conversation_id
            
            response = self.session.post(
                f"{self.base_url}/v3/chat",
                json=payload
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json(),
                    'status_code': response.status_code
                }
            else:
                return {
                    'success': False,
                    'message': f'对话请求失败，状态码: {response.status_code}',
                    'status_code': response.status_code,
                    'error': response.text
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'message': f'网络请求错误: {str(e)}',
                'error': str(e)
            }
    
    def get_conversation_history(self, conversation_id: str) -> Dict[str, Any]:
        """
        获取会话历史记录
        
        Args:
            conversation_id: 会话ID
            
        Returns:
            会话历史响应
        """
        try:
            response = self.session.get(
                f"{self.base_url}/v1/conversation/message/list",
                params={'conversation_id': conversation_id}
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json(),
                    'status_code': response.status_code
                }
            else:
                return {
                    'success': False,
                    'message': f'获取会话历史失败，状态码: {response.status_code}',
                    'status_code': response.status_code,
                    'error': response.text
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'message': f'网络请求错误: {str(e)}',
                'error': str(e)
            }
    
    def create_workflow_run(self, workflow_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建工作流运行
        
        Args:
            workflow_id: 工作流ID
            parameters: 工作流参数
            
        Returns:
            工作流运行响应
        """
        try:
            payload = {
                "workflow_id": workflow_id,
                "parameters": parameters
            }
            
            response = self.session.post(
                f"{self.base_url}/v1/workflow/run",
                json=payload
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json(),
                    'status_code': response.status_code
                }
            else:
                return {
                    'success': False,
                    'message': f'工作流运行失败，状态码: {response.status_code}',
                    'status_code': response.status_code,
                    'error': response.text
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'message': f'网络请求错误: {str(e)}',
                'error': str(e)
            }

def load_personal_token() -> Optional[str]:
    """
    从配置文件加载个人访问令牌
    
    Returns:
        个人访问令牌或None
    """
    try:
        # 尝试从多个可能的配置文件加载
        config_files = [
            "personal_token.txt",
            "config.json",
            "coze_config.json"
        ]
        
        for config_file in config_files:
            try:
                if config_file.endswith('.txt'):
                    with open(config_file, 'r', encoding='utf-8') as f:
                        token = f.read().strip()
                        if token:
                            return token
                elif config_file.endswith('.json'):
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        if 'personal_token' in config:
                            return config['personal_token']
            except FileNotFoundError:
                continue
                
        return None
        
    except Exception as e:
        print(f"加载配置失败: {e}")
        return None

def create_sample_config():
    """
    创建示例配置文件
    """
    config = {
        "personal_token": "pat_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "base_url": "https://api.coze.com",
        "description": "请将personal_token替换为您的实际个人访问令牌"
    }
    
    with open("coze_config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print("✅ 示例配置文件已创建: coze_config.json")
    print("请编辑此文件，填入您的个人访问令牌")

def main():
    """
    主函数 - 演示个人访问令牌认证的使用
    """
    print("🚀 Coze个人访问令牌认证测试")
    print("=" * 50)
    
    # 尝试加载个人访问令牌
    personal_token = load_personal_token()
    
    if not personal_token:
        print("❌ 未找到个人访问令牌配置")
        print("\n创建示例配置文件...")
        create_sample_config()
        print("\n请按以下步骤操作:")
        print("1. 登录 Coze 控制台")
        print("2. 生成个人访问令牌")
        print("3. 编辑 coze_config.json 文件，填入令牌")
        print("4. 重新运行此脚本")
        return
    
    # 初始化认证客户端
    auth_client = CozePersonalTokenAuth(personal_token)
    
    # 测试连接
    print("\n🔍 测试API连接...")
    test_result = auth_client.test_connection()
    
    if test_result['success']:
        print("✅ 连接成功!")
        if 'user_info' in test_result:
            user_info = test_result['user_info']
            print(f"用户信息: {json.dumps(user_info, indent=2, ensure_ascii=False)}")
    else:
        print(f"❌ 连接失败: {test_result['message']}")
        return
    
    # 获取机器人列表
    print("\n🤖 获取机器人列表...")
    bots_result = auth_client.list_bots()
    
    if bots_result['success']:
        print("✅ 成功获取机器人列表")
        bots_data = bots_result['data']
        print(f"机器人数据: {json.dumps(bots_data, indent=2, ensure_ascii=False)}")
    else:
        print(f"❌ 获取机器人列表失败: {bots_result['message']}")
    
    print("\n🎉 个人访问令牌认证测试完成!")

if __name__ == "__main__":
    main()