#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试coze.cn是否封禁了coze.com的API调用

此脚本用于测试从coze.cn环境访问coze.com的API是否被封禁。
同时提供OAuth授权相关的信息和建议。

作为Coze插件使用时，需要导出handler函数。
"""

import requests
import json
import time
from datetime import datetime

# Coze插件所需的导入
try:
    from runtime import Args
    # 移除了dify相关的导入，因为已删除dify中转方案
except ImportError:
    # 如果不是在Coze环境中运行，定义简单的类型
    class Args:
        def __init__(self, input_data=None):
            self.input = input_data or {}
            self.logger = None
    
    class Input:
        pass
    
    class Output:
        pass

def test_coze_com_api_access():
    """
    测试coze.com API的基本连通性
    """
    print("=" * 60)
    print("测试coze.com API访问连通性")
    print("=" * 60)
    
    # coze.com的基本API端点
    test_urls = [
        "https://api.coze.com/v1/chat",
        "https://api.coze.com/v1/workflows/run",
        "https://api.coze.com/open_api/v2/chat",
        "https://www.coze.com"
    ]
    
    results = []
    
    for url in test_urls:
        print(f"\n测试URL: {url}")
        try:
            # 设置较短的超时时间
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            status_code = response.status_code
            response_time = response.elapsed.total_seconds()
            
            print(f"状态码: {status_code}")
            print(f"响应时间: {response_time:.2f}秒")
            
            # 分析响应
            if status_code == 200:
                result = "✅ 连接成功"
            elif status_code == 401:
                result = "🔑 需要认证（API正常，需要token）"
            elif status_code == 403:
                result = "❌ 访问被禁止（可能被封禁）"
            elif status_code == 404:
                result = "❓ 端点不存在"
            elif status_code >= 500:
                result = "⚠️ 服务器错误"
            else:
                result = f"❓ 未知状态: {status_code}"
            
            print(f"结果: {result}")
            
            results.append({
                'url': url,
                'status_code': status_code,
                'response_time': response_time,
                'result': result
            })
            
        except requests.exceptions.Timeout:
            print("❌ 请求超时")
            results.append({
                'url': url,
                'status_code': 'TIMEOUT',
                'response_time': 'N/A',
                'result': '❌ 请求超时（可能被封禁）'
            })
            
        except requests.exceptions.ConnectionError:
            print("❌ 连接错误")
            results.append({
                'url': url,
                'status_code': 'CONNECTION_ERROR',
                'response_time': 'N/A',
                'result': '❌ 连接错误（可能被封禁）'
            })
            
        except Exception as e:
            print(f"❌ 其他错误: {str(e)}")
            results.append({
                'url': url,
                'status_code': 'ERROR',
                'response_time': 'N/A',
                'result': f'❌ 错误: {str(e)}'
            })
    
    return results

def test_coze_com_workflow_api():
    """
    测试coze.com的workflow API（需要token）
    """
    print("\n" + "=" * 60)
    print("测试coze.com Workflow API")
    print("=" * 60)
    
    # 这里使用一个测试token（无效的），主要看是否能到达API服务器
    test_token = "pat_test_token_for_connectivity_check"
    
    url = "https://api.coze.com/v1/workflows/run"
    headers = {
        "Authorization": f"Bearer {test_token}",
        "Content-Type": "application/json",
        "User-Agent": "CozePlugin/1.0"
    }
    
    # 测试数据
    data = {
        "workflow_id": "test_workflow_id",
        "parameters": {
            "input": "test message"
        }
    }
    
    try:
        print(f"发送POST请求到: {url}")
        response = requests.post(url, headers=headers, json=data, timeout=15)
        
        print(f"状态码: {response.status_code}")
        print(f"响应时间: {response.elapsed.total_seconds():.2f}秒")
        
        if response.status_code == 401:
            print("✅ API服务器可达（401表示需要有效token）")
            return True
        elif response.status_code == 403:
            print("❌ 访问被禁止（可能被封禁）")
            return False
        else:
            print(f"❓ 其他响应: {response.status_code}")
            try:
                print(f"响应内容: {response.text[:200]}...")
            except:
                pass
            return None
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时（可能被封禁）")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ 连接错误（可能被封禁）")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {str(e)}")
        return False

def print_oauth_info():
    """
    打印OAuth授权相关信息
    """
    print("\n" + "=" * 60)
    print("OAuth授权 vs 个人令牌 对比分析")
    print("=" * 60)
    
    oauth_info = """
📋 授权方式对比：

🔑 个人令牌 (PAT):
   ✅ 优点：简单易用，立即生效
   ❌ 缺点：有效期仅30天，需要定期更新
   📝 适用场景：开发测试、短期项目

🔐 OAuth 2.0 授权:
   ✅ 优点：
      - 可以设置更长的有效期
      - 更安全的授权机制
      - 支持刷新令牌自动续期
      - 适合生产环境长期使用
   ❌ 缺点：配置相对复杂
   📝 适用场景：生产环境、长期运行的应用

💡 建议方案：
   1. 开发阶段：使用个人令牌快速测试
   2. 生产环境：使用OAuth 2.0确保长期稳定运行
   3. 实现令牌自动刷新机制，避免服务中断

🔄 OAuth令牌刷新策略：
   - 访问令牌通常有效期较短（如1小时）
   - 刷新令牌有效期较长（如30天或更长）
   - 在访问令牌过期前自动使用刷新令牌获取新的访问令牌
   - 这样可以实现长期无人值守运行
"""
    
    print(oauth_info)

def print_recommendations():
    """
    打印建议和解决方案
    """
    print("\n" + "=" * 60)
    print("建议和解决方案")
    print("=" * 60)
    
    recommendations = """
🎯 针对您的需求的建议：

1. 📊 测试结果分析：
   - 如果测试显示coze.com API可以正常访问，说明没有被封禁
   - 如果出现超时或连接错误，可能存在网络限制

2. 🔐 授权方案选择：
   - 短期使用：个人令牌（30天有效期）
   - 长期使用：OAuth 2.0（推荐）

3. 🛠️ 实施步骤：
   a) 在coze.com创建OAuth应用
   b) 配置适当的权限（Workflow运行权限）
   c) 实现OAuth授权流程
   d) 添加令牌自动刷新机制

4. 🔄 令牌管理策略：
   - 监控令牌过期时间
   - 实现自动刷新逻辑
   - 添加错误处理和重试机制
   - 记录授权状态日志

5. 🚨 风险控制：
   - 定期检查授权状态
   - 备用授权方案
   - 监控API调用成功率
"""
    
    print(recommendations)

def main():
    """
    主函数
    """
    print(f"开始测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试基本连通性
    basic_results = test_coze_com_api_access()
    
    # 测试API端点
    api_result = test_coze_com_workflow_api()
    
    # 打印OAuth信息
    print_oauth_info()
    
    # 打印建议
    print_recommendations()
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    accessible_count = sum(1 for r in basic_results if r['status_code'] in [200, 401, 404])
    total_count = len(basic_results)
    
    if accessible_count >= total_count * 0.5:
        print("✅ 总体评估：coze.com API可能没有被封禁")
        print("💡 建议：可以尝试使用OAuth 2.0进行长期授权")
    else:
        print("❌ 总体评估：可能存在网络限制或封禁")
        print("💡 建议：检查网络环境或考虑使用代理")
    
    print(f"\n测试完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def handler(args: Args) -> dict:
    """
    Coze插件的入口函数
    
    Parameters:
    args: 插件参数，包含input和logger
    
    Returns:
    dict: 测试结果
    """
    try:
        # 如果有logger，使用logger输出，否则使用print
        if hasattr(args, 'logger') and args.logger:
            logger = args.logger
            def log_print(msg):
                logger.info(msg)
        else:
            def log_print(msg):
                print(msg)
        
        # 重定向print函数以便在Coze环境中正确输出
        global print
        original_print = print
        print = log_print
        
        try:
            log_print(f"开始测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 测试基本连通性
            basic_results = test_coze_com_api_access()
            
            # 测试API端点
            api_result = test_coze_com_workflow_api()
            
            # 打印OAuth信息
            print_oauth_info()
            
            # 打印建议
            print_recommendations()
            
            # 总结
            log_print("\n" + "=" * 60)
            log_print("测试总结")
            log_print("=" * 60)
            
            accessible_count = sum(1 for r in basic_results if r['status_code'] in [200, 401, 404])
            total_count = len(basic_results)
            
            if accessible_count >= total_count * 0.5:
                summary = "✅ 总体评估：coze.com API可能没有被封禁"
                recommendation = "💡 建议：可以尝试使用OAuth 2.0进行长期授权"
            else:
                summary = "❌ 总体评估：可能存在网络限制或封禁"
                recommendation = "💡 建议：检查网络环境或考虑使用代理"
            
            log_print(summary)
            log_print(recommendation)
            
            log_print(f"\n测试完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 返回结构化结果
            return {
                "success": True,
                "summary": summary,
                "recommendation": recommendation,
                "basic_test_results": basic_results,
                "api_test_result": api_result,
                "accessible_count": accessible_count,
                "total_count": total_count,
                "test_time": datetime.now().isoformat()
            }
            
        finally:
            # 恢复原始的print函数
            print = original_print
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"测试过程中发生错误: {str(e)}"
        }

if __name__ == "__main__":
    main()