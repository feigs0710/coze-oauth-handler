#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coze OAuth测试工具
用于测试OAuth应用配置和认证流程
"""

import sys
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import time
from coze_oauth_integration import CozeOAuthClient

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """
    OAuth回调处理器
    """
    
    def do_GET(self):
        """处理GET请求（OAuth回调）"""
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        
        # 获取授权码
        if 'code' in query_params:
            authorization_code = query_params['code'][0]
            state = query_params.get('state', [''])[0]
            
            # 保存授权码到服务器实例
            self.server.authorization_code = authorization_code
            self.server.state = state
            
            # 返回成功页面
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            success_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>OAuth授权成功</title>
                <meta charset="utf-8">
                <style>
                    body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                    .success { color: #28a745; font-size: 24px; }
                    .code { background: #f8f9fa; padding: 10px; margin: 20px; border-radius: 5px; }
                </style>
            </head>
            <body>
                <h1 class="success">✅ OAuth授权成功！</h1>
                <p>授权码已获取，您可以关闭此页面。</p>
                <div class="code">
                    <strong>授权码:</strong> {code}<br>
                    <strong>State:</strong> {state}
                </div>
                <p>测试工具将自动继续执行...</p>
            </body>
            </html>
            """.format(code=authorization_code, state=state)
            
            self.wfile.write(success_html.encode('utf-8'))
            
        elif 'error' in query_params:
            error = query_params['error'][0]
            error_description = query_params.get('error_description', [''])[0]
            
            # 保存错误信息
            self.server.error = error
            self.server.error_description = error_description
            
            # 返回错误页面
            self.send_response(400)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            error_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>OAuth授权失败</title>
                <meta charset="utf-8">
                <style>
                    body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                    .error { color: #dc3545; font-size: 24px; }
                    .details { background: #f8f9fa; padding: 10px; margin: 20px; border-radius: 5px; }
                </style>
            </head>
            <body>
                <h1 class="error">❌ OAuth授权失败</h1>
                <div class="details">
                    <strong>错误:</strong> {error}<br>
                    <strong>描述:</strong> {description}
                </div>
                <p>请检查OAuth应用配置并重试。</p>
            </body>
            </html>
            """.format(error=error, description=error_description)
            
            self.wfile.write(error_html.encode('utf-8'))
        
        else:
            # 未知请求
            self.send_response(400)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(b'Invalid OAuth callback')
    
    def log_message(self, format, *args):
        """禁用默认日志输出"""
        pass

class OAuthTestTool:
    """
    OAuth测试工具主类
    """
    
    def __init__(self):
        self.oauth_client = None
        self.server = None
        self.server_thread = None
    
    def setup_oauth_client(self):
        """设置OAuth客户端"""
        print("🔧 OAuth应用配置")
        print("=" * 50)
        
        # 获取OAuth配置
        client_id = input("请输入Client ID: ").strip()
        if not client_id:
            print("❌ Client ID不能为空")
            return False
        
        client_secret = input("请输入Client Secret: ").strip()
        if not client_secret:
            print("❌ Client Secret不能为空")
            return False
        
        # 使用固定的重定向URI
        redirect_uri = "http://localhost:8080/oauth/callback"
        
        print(f"\n📋 配置信息:")
        print(f"Client ID: {client_id}")
        print(f"Client Secret: {client_secret[:8]}...")
        print(f"Redirect URI: {redirect_uri}")
        
        # 创建OAuth客户端
        self.oauth_client = CozeOAuthClient(client_id, client_secret, redirect_uri)
        
        print("\n✅ OAuth客户端配置完成")
        return True
    
    def start_callback_server(self):
        """启动OAuth回调服务器"""
        try:
            self.server = HTTPServer(('localhost', 8080), OAuthCallbackHandler)
            self.server.authorization_code = None
            self.server.state = None
            self.server.error = None
            self.server.error_description = None
            
            # 在单独线程中运行服务器
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            print("🌐 OAuth回调服务器已启动 (http://localhost:8080)")
            return True
            
        except Exception as e:
            print(f"❌ 启动回调服务器失败: {e}")
            return False
    
    def stop_callback_server(self):
        """停止OAuth回调服务器"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            print("🛑 OAuth回调服务器已停止")
    
    def test_oauth_flow(self):
        """测试完整的OAuth流程"""
        print("\n🚀 开始OAuth认证流程测试")
        print("=" * 50)
        
        # 生成授权URL
        try:
            auth_url = self.oauth_client.get_authorization_url()
            print(f"\n🔗 授权URL已生成:")
            print(f"{auth_url}")
            
            # 自动打开浏览器
            print("\n🌐 正在打开浏览器进行授权...")
            webbrowser.open(auth_url)
            
            # 等待回调
            print("⏳ 等待OAuth回调...")
            print("   请在浏览器中完成授权，然后返回此处")
            
            # 轮询等待授权码
            timeout = 300  # 5分钟超时
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                if self.server.authorization_code:
                    print("\n✅ 收到授权码!")
                    return self.server.authorization_code
                elif self.server.error:
                    print(f"\n❌ OAuth授权失败: {self.server.error}")
                    if self.server.error_description:
                        print(f"   描述: {self.server.error_description}")
                    return None
                
                time.sleep(1)
            
            print("\n⏰ OAuth授权超时")
            return None
            
        except Exception as e:
            print(f"❌ OAuth流程测试失败: {e}")
            return None
    
    def test_token_exchange(self, authorization_code):
        """测试令牌交换"""
        print("\n🔄 测试令牌交换")
        print("=" * 50)
        
        try:
            token_data = self.oauth_client.exchange_code_for_token(authorization_code)
            
            print("✅ 令牌交换成功!")
            print(f"访问令牌: {token_data.get('access_token', '')[:20]}...")
            print(f"令牌类型: {token_data.get('token_type', 'N/A')}")
            print(f"过期时间: {token_data.get('expires_in', 'N/A')} 秒")
            
            if 'refresh_token' in token_data:
                print(f"刷新令牌: {token_data['refresh_token'][:20]}...")
            
            return True
            
        except Exception as e:
            print(f"❌ 令牌交换失败: {e}")
            return False
    
    def test_api_calls(self):
        """测试API调用"""
        print("\n🔌 测试API调用")
        print("=" * 50)
        
        # 测试获取工作流列表
        try:
            print("📋 测试获取工作流列表...")
            workflows = self.oauth_client.list_workflows()
            print(f"✅ 成功获取工作流列表 (共 {len(workflows.get('data', []))} 个工作流)")
            
            # 显示前几个工作流
            workflow_list = workflows.get('data', [])
            if workflow_list:
                print("\n📝 工作流列表:")
                for i, workflow in enumerate(workflow_list[:3]):
                    print(f"   {i+1}. {workflow.get('name', 'N/A')} (ID: {workflow.get('id', 'N/A')})")
                if len(workflow_list) > 3:
                    print(f"   ... 还有 {len(workflow_list) - 3} 个工作流")
            else:
                print("   (暂无工作流)")
            
            return True
            
        except Exception as e:
            print(f"❌ API调用失败: {e}")
            return False
    
    def run_full_test(self):
        """运行完整测试"""
        print("🧪 Coze OAuth集成测试工具")
        print("=" * 50)
        print("此工具将帮助您测试OAuth应用配置和API集成")
        print()
        
        # 步骤1: 配置OAuth客户端
        if not self.setup_oauth_client():
            return False
        
        # 步骤2: 启动回调服务器
        if not self.start_callback_server():
            return False
        
        try:
            # 步骤3: 测试OAuth流程
            authorization_code = self.test_oauth_flow()
            if not authorization_code:
                return False
            
            # 步骤4: 测试令牌交换
            if not self.test_token_exchange(authorization_code):
                return False
            
            # 步骤5: 测试API调用
            if not self.test_api_calls():
                return False
            
            # 测试完成
            print("\n🎉 所有测试通过!")
            print("=" * 50)
            print("✅ OAuth应用配置正确")
            print("✅ 认证流程工作正常")
            print("✅ API调用成功")
            print("\n💡 现在您可以在coze.cn插件中使用此OAuth配置")
            
            return True
            
        finally:
            # 清理资源
            self.stop_callback_server()
    
    def run_quick_test(self):
        """运行快速测试（仅测试配置）"""
        print("⚡ Coze OAuth快速配置测试")
        print("=" * 50)
        
        if not self.setup_oauth_client():
            return False
        
        # 生成授权URL
        try:
            auth_url = self.oauth_client.get_authorization_url()
            print(f"\n✅ OAuth配置有效")
            print(f"🔗 授权URL: {auth_url}")
            print("\n💡 请手动访问上述URL完成完整的OAuth测试")
            return True
            
        except Exception as e:
            print(f"❌ OAuth配置测试失败: {e}")
            return False

def main():
    """主函数"""
    tool = OAuthTestTool()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        # 快速测试模式
        success = tool.run_quick_test()
    else:
        # 完整测试模式
        success = tool.run_full_test()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()