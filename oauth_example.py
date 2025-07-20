#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coze.com OAuth 2.0 授权示例

此脚本展示如何使用OAuth 2.0进行长期授权，避免30天令牌过期问题。
支持自动刷新令牌，实现长期无人值守运行。
"""

import requests
import json
import time
from datetime import datetime, timedelta
import base64
import hashlib
import secrets
import urllib.parse

class CozeOAuthManager:
    """
    Coze OAuth 2.0 授权管理器
    """
    
    def __init__(self, client_id, client_secret, redirect_uri="http://localhost:8080/callback"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.base_url = "https://www.coze.com"
        self.api_base_url = "https://api.coze.com"
        
        # 令牌存储
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        
    def generate_pkce_pair(self):
        """
        生成PKCE代码验证器和挑战
        """
        # 生成代码验证器
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        
        # 生成代码挑战
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')
        
        return code_verifier, code_challenge
    
    def get_authorization_url(self, scope="workflow:run", use_pkce=True):
        """
        获取授权URL
        
        Args:
            scope: 请求的权限范围
            use_pkce: 是否使用PKCE（推荐）
        
        Returns:
            tuple: (authorization_url, state, code_verifier)
        """
        # 生成状态参数
        state = secrets.token_urlsafe(32)
        
        # 基本参数
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": scope,
            "state": state
        }
        
        code_verifier = None
        if use_pkce:
            code_verifier, code_challenge = self.generate_pkce_pair()
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = "S256"
        
        # 构建授权URL
        auth_url = f"{self.base_url}/api/permission/oauth2/authorize?" + urllib.parse.urlencode(params)
        
        return auth_url, state, code_verifier
    
    def exchange_code_for_tokens(self, authorization_code, code_verifier=None):
        """
        使用授权码换取访问令牌
        
        Args:
            authorization_code: 授权码
            code_verifier: PKCE代码验证器
        
        Returns:
            bool: 是否成功获取令牌
        """
        token_url = f"{self.base_url}/api/permission/oauth2/token"
        
        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": authorization_code,
            "redirect_uri": self.redirect_uri
        }
        
        if code_verifier:
            data["code_verifier"] = code_verifier
        
        try:
            response = requests.post(token_url, data=data, timeout=30)
            
            if response.status_code == 200:
                token_data = response.json()
                
                self.access_token = token_data.get("access_token")
                self.refresh_token = token_data.get("refresh_token")
                
                # 计算过期时间
                expires_in = token_data.get("expires_in", 3600)  # 默认1小时
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                print(f"✅ 成功获取访问令牌")
                print(f"📅 令牌过期时间: {self.token_expires_at}")
                
                return True
            else:
                print(f"❌ 获取令牌失败: {response.status_code}")
                print(f"响应: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 请求异常: {str(e)}")
            return False
    
    def refresh_access_token(self):
        """
        刷新访问令牌
        
        Returns:
            bool: 是否成功刷新令牌
        """
        if not self.refresh_token:
            print("❌ 没有刷新令牌，无法刷新")
            return False
        
        token_url = f"{self.base_url}/api/permission/oauth2/token"
        
        data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token
        }
        
        try:
            response = requests.post(token_url, data=data, timeout=30)
            
            if response.status_code == 200:
                token_data = response.json()
                
                self.access_token = token_data.get("access_token")
                # 刷新令牌可能会更新
                if "refresh_token" in token_data:
                    self.refresh_token = token_data["refresh_token"]
                
                # 更新过期时间
                expires_in = token_data.get("expires_in", 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                print(f"✅ 成功刷新访问令牌")
                print(f"📅 新令牌过期时间: {self.token_expires_at}")
                
                return True
            else:
                print(f"❌ 刷新令牌失败: {response.status_code}")
                print(f"响应: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 刷新请求异常: {str(e)}")
            return False
    
    def ensure_valid_token(self):
        """
        确保令牌有效，如果即将过期则自动刷新
        
        Returns:
            bool: 令牌是否有效
        """
        if not self.access_token:
            print("❌ 没有访问令牌")
            return False
        
        # 检查是否即将过期（提前5分钟刷新）
        if self.token_expires_at and datetime.now() >= (self.token_expires_at - timedelta(minutes=5)):
            print("🔄 令牌即将过期，尝试刷新...")
            return self.refresh_access_token()
        
        return True
    
    def call_workflow_api(self, workflow_id, parameters):
        """
        调用工作流API
        
        Args:
            workflow_id: 工作流ID
            parameters: 工作流参数
        
        Returns:
            dict: API响应结果
        """
        if not self.ensure_valid_token():
            return {"error": "无效的访问令牌"}
        
        # 注意：根据测试结果，实际的API端点可能不同
        # 需要根据coze.com的实际API文档调整
        api_url = f"{self.api_base_url}/open_api/v2/chat"  # 使用测试中成功的端点
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # 构建请求数据（需要根据实际API调整）
        data = {
            "conversation_id": "",
            "bot_id": workflow_id,  # 可能需要调整
            "user": "oauth_user",
            "query": parameters.get("input", ""),
            "stream": False
        }
        
        try:
            response = requests.post(api_url, headers=headers, json=data, timeout=60)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "error": f"API调用失败: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            return {"error": f"请求异常: {str(e)}"}
    
    def save_tokens_to_file(self, filename="coze_tokens.json"):
        """
        保存令牌到文件
        """
        token_data = {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.token_expires_at.isoformat() if self.token_expires_at else None,
            "client_id": self.client_id
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(token_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 令牌已保存到 {filename}")
    
    def load_tokens_from_file(self, filename="coze_tokens.json"):
        """
        从文件加载令牌
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                token_data = json.load(f)
            
            self.access_token = token_data.get("access_token")
            self.refresh_token = token_data.get("refresh_token")
            
            expires_at_str = token_data.get("expires_at")
            if expires_at_str:
                self.token_expires_at = datetime.fromisoformat(expires_at_str)
            
            print(f"✅ 令牌已从 {filename} 加载")
            return True
            
        except FileNotFoundError:
            print(f"❌ 令牌文件 {filename} 不存在")
            return False
        except Exception as e:
            print(f"❌ 加载令牌失败: {str(e)}")
            return False

def demo_oauth_flow():
    """
    演示OAuth授权流程
    """
    print("=" * 60)
    print("Coze OAuth 2.0 授权流程演示")
    print("=" * 60)
    
    # 注意：这些是示例值，需要替换为实际的OAuth应用信息
    CLIENT_ID = "your_client_id_here"
    CLIENT_SECRET = "your_client_secret_here"
    
    if CLIENT_ID == "your_client_id_here":
        print("⚠️ 请先在coze.com创建OAuth应用并替换CLIENT_ID和CLIENT_SECRET")
        print("\n📋 创建OAuth应用步骤：")
        print("1. 登录 https://www.coze.com")
        print("2. 进入开发者设置 -> OAuth应用")
        print("3. 创建新应用，选择合适的应用类型")
        print("4. 配置回调URL: http://localhost:8080/callback")
        print("5. 获取Client ID和Client Secret")
        print("6. 设置权限：workflow:run")
        return
    
    # 创建OAuth管理器
    oauth_manager = CozeOAuthManager(CLIENT_ID, CLIENT_SECRET)
    
    # 尝试加载已保存的令牌
    if oauth_manager.load_tokens_from_file():
        if oauth_manager.ensure_valid_token():
            print("✅ 使用已保存的有效令牌")
        else:
            print("❌ 已保存的令牌无效，需要重新授权")
    else:
        print("📝 首次使用，需要进行OAuth授权")
        
        # 生成授权URL
        auth_url, state, code_verifier = oauth_manager.get_authorization_url()
        
        print(f"\n🔗 请访问以下URL进行授权：")
        print(auth_url)
        print(f"\n📋 授权后，从回调URL中提取authorization_code")
        print(f"💡 状态码（用于验证）: {state}")
        
        # 在实际应用中，这里应该启动一个本地服务器来接收回调
        # 或者让用户手动输入授权码
        authorization_code = input("\n请输入授权码: ").strip()
        
        if authorization_code:
            if oauth_manager.exchange_code_for_tokens(authorization_code, code_verifier):
                oauth_manager.save_tokens_to_file()
            else:
                print("❌ 授权失败")
                return
    
    # 测试API调用
    print("\n🧪 测试工作流API调用...")
    result = oauth_manager.call_workflow_api(
        workflow_id="your_workflow_id",
        parameters={"input": "Hello, this is a test message"}
    )
    
    print(f"📋 API调用结果: {json.dumps(result, indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    demo_oauth_flow()