#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vercel部署快速修复工具

此脚本帮助快速诊断和修复Vercel部署中的常见问题。

使用方法:
    python vercel_quick_fix.py

作者: AI Assistant
日期: 2024
"""

import os
import json
import subprocess
import sys
from pathlib import Path
import requests
from urllib.parse import urlparse

class VercelQuickFix:
    def __init__(self):
        self.project_dir = Path.cwd()
        self.issues = []
        self.fixes_applied = []
        
    def print_header(self):
        """打印工具标题"""
        print("\n" + "="*60)
        print("🔧 Vercel部署快速修复工具")
        print("="*60)
        print("此工具将帮助您诊断和修复Vercel部署问题\n")
    
    def check_file_structure(self):
        """检查文件结构"""
        print("📁 检查文件结构...")
        
        required_files = {
            'index.html': '主页面文件',
            'vercel.json': 'Vercel配置文件'
        }
        
        missing_files = []
        for file_name, description in required_files.items():
            file_path = self.project_dir / file_name
            if not file_path.exists():
                missing_files.append((file_name, description))
                print(f"  ❌ 缺失: {file_name} ({description})")
            else:
                print(f"  ✅ 存在: {file_name}")
        
        if missing_files:
            self.issues.append(('missing_files', missing_files))
        
        return len(missing_files) == 0
    
    def check_vercel_config(self):
        """检查vercel.json配置"""
        print("\n⚙️ 检查Vercel配置...")
        
        vercel_config_path = self.project_dir / 'vercel.json'
        if not vercel_config_path.exists():
            print("  ❌ vercel.json文件不存在")
            self.issues.append(('no_vercel_config', None))
            return False
        
        try:
            with open(vercel_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 检查重写规则
            if 'rewrites' not in config:
                print("  ❌ 缺少rewrites配置")
                self.issues.append(('no_rewrites', None))
            else:
                print("  ✅ 存在rewrites配置")
                
                # 检查OAuth回调路由
                oauth_route_found = False
                for rewrite in config['rewrites']:
                    if '/oauth/callback' in rewrite.get('source', ''):
                        oauth_route_found = True
                        break
                
                if not oauth_route_found:
                    print("  ❌ 缺少OAuth回调路由")
                    self.issues.append(('no_oauth_route', None))
                else:
                    print("  ✅ 存在OAuth回调路由")
            
            return True
            
        except json.JSONDecodeError as e:
            print(f"  ❌ vercel.json格式错误: {e}")
            self.issues.append(('invalid_json', str(e)))
            return False
        except Exception as e:
            print(f"  ❌ 读取vercel.json失败: {e}")
            return False
    
    def check_html_syntax(self):
        """检查HTML语法"""
        print("\n🌐 检查HTML文件...")
        
        html_path = self.project_dir / 'index.html'
        if not html_path.exists():
            print("  ❌ index.html文件不存在")
            return False
        
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 基本语法检查
            if '<!DOCTYPE html>' not in content:
                print("  ⚠️ 缺少DOCTYPE声明")
                self.issues.append(('no_doctype', None))
            
            if '<html' not in content:
                print("  ❌ 缺少html标签")
                self.issues.append(('no_html_tag', None))
            
            if '<head>' not in content:
                print("  ❌ 缺少head标签")
                self.issues.append(('no_head_tag', None))
            
            if '<body>' not in content:
                print("  ❌ 缺少body标签")
                self.issues.append(('no_body_tag', None))
            
            if 'getUrlParams' not in content:
                print("  ⚠️ 缺少OAuth参数处理函数")
                self.issues.append(('no_oauth_handler', None))
            
            print(f"  ✅ HTML文件大小: {len(content)} 字符")
            return True
            
        except Exception as e:
            print(f"  ❌ 读取HTML文件失败: {e}")
            return False
    
    def test_deployment_url(self, url):
        """测试部署URL"""
        print(f"\n🌍 测试部署URL: {url}")
        
        try:
            response = requests.get(url, timeout=10)
            print(f"  状态码: {response.status_code}")
            
            if response.status_code == 200:
                print("  ✅ 部署成功，页面可访问")
                return True
            elif response.status_code == 404:
                print("  ❌ 404错误 - 页面未找到")
                self.issues.append(('url_404', url))
            elif response.status_code == 401:
                print("  ❌ 401错误 - 认证失败")
                self.issues.append(('url_401', url))
            elif response.status_code == 500:
                print("  ❌ 500错误 - 服务器内部错误")
                self.issues.append(('url_500', url))
            else:
                print(f"  ❌ 未知错误: {response.status_code}")
                self.issues.append(('url_unknown', f"{url} - {response.status_code}"))
            
            return False
            
        except requests.exceptions.Timeout:
            print("  ❌ 请求超时")
            self.issues.append(('url_timeout', url))
        except requests.exceptions.ConnectionError:
            print("  ❌ 连接错误")
            self.issues.append(('url_connection', url))
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            self.issues.append(('url_error', f"{url} - {str(e)}"))
        
        return False
    
    def create_missing_files(self):
        """创建缺失的文件"""
        print("\n🔨 创建缺失的文件...")
        
        # 创建index.html
        if not (self.project_dir / 'index.html').exists():
            html_content = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OAuth授权处理</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }
        .success { color: #28a745; }
        .error { color: #dc3545; }
        .code {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            font-family: monospace;
            word-break: break-all;
            margin: 20px 0;
            border: 1px solid #dee2e6;
        }
        .copy-btn {
            background: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin-top: 10px;
        }
        .copy-btn:hover {
            background: #0056b3;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 OAuth授权处理</h1>
        <div id="status">正在处理授权...</div>
        <div id="result"></div>
        
        <div id="debug" style="margin-top: 30px; padding: 15px; background: #f8f9fa; border-radius: 5px; font-size: 12px; text-align: left;">
            <strong>调试信息：</strong><br>
            <span id="debug-info"></span>
        </div>
    </div>

    <script>
        function getUrlParams() {
            const params = new URLSearchParams(window.location.search);
            return {
                code: params.get('code'),
                state: params.get('state'),
                error: params.get('error'),
                error_description: params.get('error_description')
            };
        }

        function copyToClipboard(text) {
            if (navigator.clipboard) {
                navigator.clipboard.writeText(text).then(() => {
                    alert('授权码已复制到剪贴板！');
                }).catch(() => {
                    fallbackCopy(text);
                });
            } else {
                fallbackCopy(text);
            }
        }

        function fallbackCopy(text) {
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            try {
                document.execCommand('copy');
                alert('授权码已复制到剪贴板！');
            } catch (err) {
                alert('复制失败，请手动复制授权码');
            }
            document.body.removeChild(textArea);
        }

        function handleOAuthCallback() {
            const params = getUrlParams();
            const statusDiv = document.getElementById('status');
            const resultDiv = document.getElementById('result');
            const debugDiv = document.getElementById('debug-info');

            debugDiv.innerHTML = `
                URL: ${window.location.href}<br>
                Code: ${params.code || '无'}<br>
                State: ${params.state || '无'}<br>
                Error: ${params.error || '无'}<br>
                Error Description: ${params.error_description || '无'}<br>
                Timestamp: ${new Date().toLocaleString()}
            `;

            if (params.error) {
                statusDiv.innerHTML = '<div class="error">❌ 授权失败</div>';
                resultDiv.innerHTML = `
                    <p><strong>错误类型：</strong>${params.error}</p>
                    <p><strong>错误描述：</strong>${params.error_description || '未知错误'}</p>
                    <p>请返回应用重新尝试授权。</p>
                `;
            } else if (params.code) {
                statusDiv.innerHTML = '<div class="success">✅ 授权成功</div>';
                resultDiv.innerHTML = `
                    <p>授权码已获取，请复制以下代码：</p>
                    <div class="code" id="authCode">${params.code}</div>
                    <button class="copy-btn" onclick="copyToClipboard('${params.code}')">复制授权码</button>
                    <p style="margin-top: 20px; font-size: 14px; color: #666;">
                        请将此授权码粘贴到您的应用中完成OAuth流程。<br>
                        授权码有效期通常为10分钟，请尽快使用。
                    </p>
                `;
            } else {
                statusDiv.innerHTML = '<div class="success">✅ 页面加载成功</div>';
                resultDiv.innerHTML = `
                    <p>OAuth回调处理页面已就绪。</p>
                    <p>此页面用于处理来自coze.com的OAuth授权回调。</p>
                    <p style="font-size: 14px; color: #666; margin-top: 20px;">
                        如果您看到此页面，说明部署成功！<br>
                        回调URL: <code>${window.location.origin}/oauth/callback</code>
                    </p>
                `;
            }
        }

        document.addEventListener('DOMContentLoaded', handleOAuthCallback);
    </script>
</body>
</html>'''
            
            with open(self.project_dir / 'index.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            print("  ✅ 创建 index.html")
            self.fixes_applied.append('创建index.html文件')
        
        # 创建vercel.json
        if not (self.project_dir / 'vercel.json').exists():
            vercel_config = {
                "rewrites": [
                    {
                        "source": "/oauth/callback",
                        "destination": "/index.html"
                    },
                    {
                        "source": "/",
                        "destination": "/index.html"
                    }
                ],
                "headers": [
                    {
                        "source": "/(.*)",
                        "headers": [
                            {
                                "key": "X-Frame-Options",
                                "value": "DENY"
                            },
                            {
                                "key": "X-Content-Type-Options",
                                "value": "nosniff"
                            },
                            {
                                "key": "Cache-Control",
                                "value": "public, max-age=0, must-revalidate"
                            }
                        ]
                    }
                ]
            }
            
            with open(self.project_dir / 'vercel.json', 'w', encoding='utf-8') as f:
                json.dump(vercel_config, f, indent=2, ensure_ascii=False)
            print("  ✅ 创建 vercel.json")
            self.fixes_applied.append('创建vercel.json配置文件')
    
    def fix_vercel_config(self):
        """修复vercel.json配置"""
        print("\n🔧 修复Vercel配置...")
        
        vercel_config_path = self.project_dir / 'vercel.json'
        if not vercel_config_path.exists():
            self.create_missing_files()
            return
        
        try:
            with open(vercel_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except:
            # 如果配置文件损坏，重新创建
            os.remove(vercel_config_path)
            self.create_missing_files()
            return
        
        # 确保有rewrites配置
        if 'rewrites' not in config:
            config['rewrites'] = []
        
        # 检查并添加OAuth回调路由
        oauth_route_exists = False
        for rewrite in config['rewrites']:
            if '/oauth/callback' in rewrite.get('source', ''):
                oauth_route_exists = True
                break
        
        if not oauth_route_exists:
            config['rewrites'].insert(0, {
                "source": "/oauth/callback",
                "destination": "/index.html"
            })
            print("  ✅ 添加OAuth回调路由")
            self.fixes_applied.append('添加OAuth回调路由')
        
        # 确保有根路由
        root_route_exists = False
        for rewrite in config['rewrites']:
            if rewrite.get('source') == '/':
                root_route_exists = True
                break
        
        if not root_route_exists:
            config['rewrites'].append({
                "source": "/",
                "destination": "/index.html"
            })
            print("  ✅ 添加根路由")
            self.fixes_applied.append('添加根路由')
        
        # 保存修复后的配置
        with open(vercel_config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def suggest_git_commands(self):
        """建议Git命令"""
        print("\n📝 建议的Git命令:")
        print("  git add .")
        print("  git commit -m 'Fix Vercel deployment configuration'")
        print("  git push origin main")
        print("\n或者使用Vercel CLI重新部署:")
        print("  vercel --prod")
    
    def print_summary(self):
        """打印修复摘要"""
        print("\n" + "="*60)
        print("📋 修复摘要")
        print("="*60)
        
        if self.fixes_applied:
            print("✅ 已应用的修复:")
            for fix in self.fixes_applied:
                print(f"  • {fix}")
        else:
            print("ℹ️ 未发现需要修复的问题")
        
        if self.issues:
            print("\n⚠️ 剩余问题:")
            for issue_type, details in self.issues:
                if issue_type == 'url_404':
                    print(f"  • URL返回404错误: {details}")
                elif issue_type == 'url_401':
                    print(f"  • URL返回401错误: {details}")
                elif issue_type == 'url_500':
                    print(f"  • URL返回500错误: {details}")
                elif issue_type == 'url_timeout':
                    print(f"  • URL请求超时: {details}")
                elif issue_type == 'url_connection':
                    print(f"  • URL连接错误: {details}")
        
        print("\n🚀 下一步操作:")
        print("  1. 提交并推送代码到GitHub")
        print("  2. 等待Vercel自动重新部署")
        print("  3. 测试部署URL是否正常工作")
        print("  4. 在coze.com中配置正确的回调URL")
    
    def run_diagnosis(self, deployment_url=None):
        """运行完整诊断"""
        self.print_header()
        
        # 检查文件结构
        self.check_file_structure()
        
        # 检查配置
        self.check_vercel_config()
        
        # 检查HTML
        self.check_html_syntax()
        
        # 测试部署URL（如果提供）
        if deployment_url:
            self.test_deployment_url(deployment_url)
            # 测试回调URL
            callback_url = deployment_url.rstrip('/') + '/oauth/callback'
            self.test_deployment_url(callback_url)
        
        # 应用修复
        if any(issue[0] in ['missing_files', 'no_vercel_config', 'no_rewrites', 'no_oauth_route'] 
               for issue in self.issues):
            self.create_missing_files()
            self.fix_vercel_config()
        
        # 建议后续操作
        if self.fixes_applied:
            self.suggest_git_commands()
        
        # 打印摘要
        self.print_summary()

def main():
    """主函数"""
    fixer = VercelQuickFix()
    
    # 获取部署URL
    deployment_url = input("请输入您的Vercel部署URL（可选，按Enter跳过）: ").strip()
    if not deployment_url:
        deployment_url = None
    elif not deployment_url.startswith('http'):
        deployment_url = 'https://' + deployment_url
    
    # 运行诊断
    fixer.run_diagnosis(deployment_url)
    
    print("\n🎉 诊断完成！请按照建议进行操作。")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 用户取消操作")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        print("请检查您的环境配置或联系技术支持。")