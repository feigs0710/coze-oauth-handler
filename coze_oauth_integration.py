#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coze.com OAuth集成模块
用于在coze.cn插件中通过OAuth认证调用coze.com工作流API
"""

import requests
import json
import time
import urllib.parse
from typing import Dict, Any, Optional
import logging

class CozeOAuthClient:
    """
    Coze.com OAuth客户端
    处理OAuth认证流程和API调用
    """
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        """
        初始化OAuth客户端
        
        Args:
            client_id: OAuth应用的Client ID
            client_secret: OAuth应用的Client Secret
            redirect_uri: 重定向URI
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        
        # API端点配置
        self.base_url = "https://api.coze.com"
        self.auth_base_url = "https://www.coze.com/api/permission/oauth2"
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
    
    def get_authorization_url(self, state: Optional[str] = None, scopes: Optional[list] = None) -> str:
        """
        构建OAuth授权URL
        
        Args:
            state: 防CSRF攻击的随机字符串
            scopes: 权限范围列表
            
        Returns:
            授权URL字符串
        """
        if scopes is None:
            scopes = ["workflows:read", "workflows:execute", "chat:read", "chat:write"]
        
        if state is None:
            state = f"state_{int(time.time())}"
        
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(scopes),
            "state": state
        }
        
        query_string = urllib.parse.urlencode(params)
        auth_url = f"{self.auth_base_url}/authorize?{query_string}"
        
        self.logger.info(f"生成授权URL: {auth_url}")
        return auth_url
    
    def exchange_code_for_token(self, authorization_code: str) -> Dict[str, Any]:
        """
        使用授权码换取访问令牌
        
        Args:
            authorization_code: OAuth授权码
            
        Returns:
            包含访问令牌信息的字典
        """
        token_url = f"{self.auth_base_url}/token"
        
        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": authorization_code,
            "redirect_uri": self.redirect_uri
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        
        try:
            response = requests.post(token_url, data=data, headers=headers, timeout=30)
            response.raise_for_status()
            
            token_data = response.json()
            
            # 保存令牌信息
            self.access_token = token_data.get("access_token")
            self.refresh_token = token_data.get("refresh_token")
            
            # 计算过期时间
            expires_in = token_data.get("expires_in", 3600)
            self.token_expires_at = time.time() + expires_in
            
            self.logger.info("成功获取访问令牌")
            return token_data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"获取访问令牌失败: {e}")
            raise Exception(f"OAuth令牌交换失败: {e}")
    
    def refresh_access_token(self) -> Dict[str, Any]:
        """
        刷新访问令牌
        
        Returns:
            新的令牌信息
        """
        if not self.refresh_token:
            raise Exception("没有可用的刷新令牌")
        
        token_url = f"{self.auth_base_url}/token"
        
        data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        
        try:
            response = requests.post(token_url, data=data, headers=headers, timeout=30)
            response.raise_for_status()
            
            token_data = response.json()
            
            # 更新令牌信息
            self.access_token = token_data.get("access_token")
            if "refresh_token" in token_data:
                self.refresh_token = token_data.get("refresh_token")
            
            # 更新过期时间
            expires_in = token_data.get("expires_in", 3600)
            self.token_expires_at = time.time() + expires_in
            
            self.logger.info("成功刷新访问令牌")
            return token_data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"刷新访问令牌失败: {e}")
            raise Exception(f"令牌刷新失败: {e}")
    
    def ensure_valid_token(self):
        """
        确保访问令牌有效，如果即将过期则自动刷新
        """
        if not self.access_token:
            raise Exception("没有可用的访问令牌，请先进行OAuth认证")
        
        # 如果令牌在5分钟内过期，则刷新
        if self.token_expires_at and (self.token_expires_at - time.time()) < 300:
            self.logger.info("访问令牌即将过期，正在刷新...")
            self.refresh_access_token()
    
    def make_api_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                        params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        发起API请求
        
        Args:
            method: HTTP方法 (GET, POST, PUT, DELETE)
            endpoint: API端点路径
            data: 请求体数据
            params: URL参数
            
        Returns:
            API响应数据
        """
        self.ensure_valid_token()
        
        url = f"{self.base_url}{endpoint}"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, params=params, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data, params=params, timeout=30)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, params=params, timeout=30)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            response.raise_for_status()
            
            # 尝试解析JSON响应
            try:
                return response.json()
            except json.JSONDecodeError:
                return {"raw_response": response.text}
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API请求失败: {e}")
            raise Exception(f"API请求失败: {e}")
    
    def list_workflows(self) -> Dict[str, Any]:
        """
        获取工作流列表
        
        Returns:
            工作流列表数据
        """
        return self.make_api_request("GET", "/v1/workflows")
    
    def get_workflow_info(self, workflow_id: str) -> Dict[str, Any]:
        """
        获取特定工作流信息
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            工作流详细信息
        """
        return self.make_api_request("GET", f"/v1/workflows/{workflow_id}")
    
    def execute_workflow(self, workflow_id: str, parameters: Optional[Dict] = None, 
                        stream: bool = False) -> Dict[str, Any]:
        """
        执行工作流
        
        Args:
            workflow_id: 工作流ID
            parameters: 工作流参数
            stream: 是否使用流式响应
            
        Returns:
            工作流执行结果
        """
        endpoint = f"/v1/workflows/{workflow_id}/run"
        
        payload = {
            "parameters": parameters or {},
            "stream": stream
        }
        
        return self.make_api_request("POST", endpoint, data=payload)
    
    def get_workflow_run_status(self, workflow_id: str, run_id: str) -> Dict[str, Any]:
        """
        获取工作流运行状态
        
        Args:
            workflow_id: 工作流ID
            run_id: 运行ID
            
        Returns:
            运行状态信息
        """
        endpoint = f"/v1/workflows/{workflow_id}/runs/{run_id}"
        return self.make_api_request("GET", endpoint)
    
    def send_chat_message(self, conversation_id: str, message: str, 
                         user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        发送聊天消息
        
        Args:
            conversation_id: 对话ID
            message: 消息内容
            user_id: 用户ID
            
        Returns:
            聊天响应
        """
        endpoint = "/v1/chat"
        
        payload = {
            "conversation_id": conversation_id,
            "query": message,
            "user": user_id or "default_user"
        }
        
        return self.make_api_request("POST", endpoint, data=payload)


class CozePluginIntegration:
    """
    Coze插件集成类
    专门用于在coze.cn插件环境中使用
    """
    
    def __init__(self, oauth_client: CozeOAuthClient):
        """
        初始化插件集成
        
        Args:
            oauth_client: OAuth客户端实例
        """
        self.oauth_client = oauth_client
        self.logger = logging.getLogger(__name__)
    
    def plugin_handler(self, args):
        """
        插件主处理函数
        适配coze.cn插件调用格式
        
        Args:
            args: 插件参数对象
            
        Returns:
            插件执行结果
        """
        try:
            # 安全获取输入参数
            input_data = getattr(args, 'input', {}) or {}
            
            # 获取操作类型
            action = input_data.get('action', 'execute_workflow')
            
            if action == 'execute_workflow':
                return self._handle_workflow_execution(input_data)
            elif action == 'list_workflows':
                return self._handle_list_workflows()
            elif action == 'get_workflow_info':
                return self._handle_get_workflow_info(input_data)
            elif action == 'send_chat':
                return self._handle_send_chat(input_data)
            else:
                return {
                    'success': False,
                    'error': f'不支持的操作类型: {action}',
                    'supported_actions': ['execute_workflow', 'list_workflows', 'get_workflow_info', 'send_chat']
                }
                
        except Exception as e:
            self.logger.error(f"插件处理失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def _handle_workflow_execution(self, input_data: Dict) -> Dict[str, Any]:
        """
        处理工作流执行请求
        """
        workflow_id = input_data.get('workflow_id')
        if not workflow_id:
            return {
                'success': False,
                'error': '缺少必需参数: workflow_id'
            }
        
        parameters = input_data.get('parameters', {})
        stream = input_data.get('stream', False)
        
        try:
            result = self.oauth_client.execute_workflow(workflow_id, parameters, stream)
            return {
                'success': True,
                'data': result,
                'workflow_id': workflow_id
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'工作流执行失败: {e}',
                'workflow_id': workflow_id
            }
    
    def _handle_list_workflows(self) -> Dict[str, Any]:
        """
        处理获取工作流列表请求
        """
        try:
            result = self.oauth_client.list_workflows()
            return {
                'success': True,
                'data': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'获取工作流列表失败: {e}'
            }
    
    def _handle_get_workflow_info(self, input_data: Dict) -> Dict[str, Any]:
        """
        处理获取工作流信息请求
        """
        workflow_id = input_data.get('workflow_id')
        if not workflow_id:
            return {
                'success': False,
                'error': '缺少必需参数: workflow_id'
            }
        
        try:
            result = self.oauth_client.get_workflow_info(workflow_id)
            return {
                'success': True,
                'data': result,
                'workflow_id': workflow_id
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'获取工作流信息失败: {e}',
                'workflow_id': workflow_id
            }
    
    def _handle_send_chat(self, input_data: Dict) -> Dict[str, Any]:
        """
        处理发送聊天消息请求
        """
        conversation_id = input_data.get('conversation_id')
        message = input_data.get('message')
        
        if not conversation_id or not message:
            return {
                'success': False,
                'error': '缺少必需参数: conversation_id 和 message'
            }
        
        user_id = input_data.get('user_id')
        
        try:
            result = self.oauth_client.send_chat_message(conversation_id, message, user_id)
            return {
                'success': True,
                'data': result,
                'conversation_id': conversation_id
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'发送聊天消息失败: {e}',
                'conversation_id': conversation_id
            }


# 使用示例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # OAuth配置（请替换为实际值）
    CLIENT_ID = "your_client_id_here"
    CLIENT_SECRET = "your_client_secret_here"
    REDIRECT_URI = "http://localhost:8080/oauth/callback"
    
    # 创建OAuth客户端
    oauth_client = CozeOAuthClient(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)
    
    # 创建插件集成
    plugin_integration = CozePluginIntegration(oauth_client)
    
    # 示例：获取授权URL
    auth_url = oauth_client.get_authorization_url()
    print(f"请访问以下URL进行授权:\n{auth_url}")
    
    # 注意：在实际使用中，您需要：
    # 1. 设置Web服务器处理OAuth回调
    # 2. 从回调中提取授权码
    # 3. 使用授权码换取访问令牌
    # 4. 然后就可以调用API了
    
    print("\n集成完成！现在可以在coze.cn插件中使用此模块。")