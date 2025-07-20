#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coze.com连通性测试插件

专门用作Coze插件的简化版本，测试coze.com API的连通性。
包含错误处理、日志记录和结构化输出。
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Any, Optional


def _safe_log(logger, message: str, level: str = "info"):
    """统一的安全日志记录工具函数"""
    try:
        if logger and hasattr(logger, level):
            log_method = getattr(logger, level, None)
            if log_method and callable(log_method):
                log_method(message)
                return
        # 如果logger不存在或方法不可调用，使用print
        print(f"[{level.upper()}] {message}")
    except Exception:
        # 如果出现任何异常，回退到print
        print(f"[{level.upper()}] {message}")


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


class CozeConnectivityTester:
    """Coze.com连通性测试器"""
    
    def __init__(self, logger=None, timeout: int = 10):
        self.logger = logger
        self.timeout = timeout
        self.test_urls = [
            "https://api.coze.com/v1/chat",
            "https://api.coze.com/v1/workflows/chat",  # 更新为正确的workflow端点
            "https://api.coze.com/v1/workflows/run",
            "https://api.coze.com/open_api/v2/chat",
            "https://www.coze.com"
        ]
    
    def log(self, message: str, level: str = "info"):
        """统一的日志记录方法"""
        _safe_log(self.logger, message, level)
    
    def test_basic_connectivity(self) -> List[Dict[str, Any]]:
        """测试基本连通性"""
        self.log("开始测试coze.com API基本连通性")
        results = []
        
        for url in self.test_urls:
            self.log(f"测试URL: {url}")
            result = self._test_single_url(url)
            results.append(result)
            self.log(f"结果: {result['result']}")
        
        return results
    
    def _test_single_url(self, url: str) -> Dict[str, Any]:
        """测试单个URL的连通性"""
        try:
            response = requests.get(
                url, 
                timeout=self.timeout, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            
            status_code = response.status_code
            response_time = response.elapsed.total_seconds()
            
            # 分析响应状态
            result_map = {
                200: "✅ 连接成功",
                401: "🔑 需要认证（API正常，需要token）",
                403: "❌ 访问被禁止（可能被封禁）",
                404: "❓ 端点不存在"
            }
            
            if status_code >= 500:
                result = "⚠️ 服务器错误"
            else:
                result = result_map.get(status_code, f"❓ 未知状态: {status_code}")
            
            return {
                'url': url,
                'status_code': status_code,
                'response_time': response_time,
                'result': result,
                'success': status_code in [200, 401, 404]
            }
            
        except requests.exceptions.Timeout:
            return self._create_error_result(url, 'TIMEOUT', '❌ 请求超时（可能被封禁）')
        except requests.exceptions.ConnectionError:
            return self._create_error_result(url, 'CONNECTION_ERROR', '❌ 连接错误（可能被封禁）')
        except Exception as e:
            return self._create_error_result(url, 'ERROR', f'❌ 错误: {str(e)}')
    
    def _create_error_result(self, url: str, status: str, message: str) -> Dict[str, Any]:
        """创建错误结果"""
        return {
            'url': url,
            'status_code': status,
            'response_time': 'N/A',
            'result': message,
            'success': False
        }
    
    def test_workflow_api(self) -> Optional[bool]:
        """测试workflow API端点"""
        self.log("测试coze.com Workflow API")
        
        # 测试新的workflow/chat端点
        url = "https://api.coze.com/v1/workflows/chat"
        headers = {
            "Authorization": "Bearer pat_test_token_for_connectivity_check",
            "Content-Type": "application/json",
            "User-Agent": "CozePlugin/1.0"
        }
        
        # 根据API文档构造请求数据
        data = {
            "workflow_id": "7514923198020304901",  # 示例workflow ID
            "additional_messages": [{
                "content": "test message",
                "content_type": "text",
                "role": "user",
                "type": "question"
            }],
            "parameters": {},
            "app_id": "test_app_id",
            "conversation_id": "test_conversation_id"
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=self.timeout + 5)
            status_code = response.status_code
            
            if status_code == 401:
                self.log("✅ API服务器可达（401表示需要有效token）")
                return True
            elif status_code == 403:
                self.log("❌ 访问被禁止（可能被封禁）")
                return False
            elif status_code == 400:
                self.log("✅ API服务器可达（400表示请求格式问题，但服务正常）")
                return True
            else:
                self.log(f"❓ 其他响应: {status_code}")
                return None
                
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            self.log(f"❌ 网络错误: {type(e).__name__}")
            return False
        except Exception as e:
            self.log(f"❌ 其他错误: {str(e)}")
            return False
    
    def generate_summary(self, basic_results: List[Dict[str, Any]], api_result: Optional[bool]) -> tuple:
        """生成测试总结"""
        accessible_count = sum(1 for r in basic_results if r.get('success', False))
        total_count = len(basic_results)
        
        if accessible_count >= total_count * 0.5:
            summary = "✅ 总体评估：coze.com API可能没有被封禁"
            recommendation = "💡 建议：可以尝试使用OAuth 2.0进行长期授权"
        else:
            summary = "❌ 总体评估：可能存在网络限制或封禁"
            recommendation = "💡 建议：检查网络环境或考虑使用代理"
        
        return summary, recommendation


def handler(args: Args) -> Dict[str, Any]:
    """
    Coze插件的入口函数
    
    Parameters:
    args: 插件参数，包含input和logger
    
    Returns:
    Dict[str, Any]: 测试结果
    """
    try:
        # 首先检查args是否为None
        if args is None:
            return {
                "success": False,
                "error": "args参数为None",
                "message": "测试过程中发生错误: args参数为None",
                "summary": "❌ 测试失败",
                "recommendation": "💡 请检查插件调用参数",
                "basic_test_results": [],
                "api_test_result": None,
                "accessible_count": 0,
                "total_count": 0,
                "test_time": datetime.now().isoformat()
            }
        
        # 安全获取输入参数
        input_data = {}
        logger = None
        
        try:
            # 尝试获取input数据
            if hasattr(args, 'input'):
                input_data = getattr(args, 'input', {}) or {}
            elif hasattr(args, '__dict__') and 'input' in args.__dict__:
                input_data = args.__dict__.get('input', {})
        except Exception:
            input_data = {}
        
        try:
            # 尝试获取logger，但要确保它是可用的
            if hasattr(args, 'logger'):
                potential_logger = getattr(args, 'logger', None)
                # 验证logger是否可用
                if potential_logger and hasattr(potential_logger, 'info') and callable(getattr(potential_logger, 'info', None)):
                    logger = potential_logger
        except Exception:
            logger = None
        
        # 解析参数
        timeout = input_data.get('timeout', 10) if isinstance(input_data, dict) else 10
        test_type = input_data.get('test_type', 'all') if isinstance(input_data, dict) else 'all'
        verbose = input_data.get('verbose', True) if isinstance(input_data, dict) else True
        
        # 创建测试器
        tester = CozeConnectivityTester(logger=logger, timeout=timeout)
        
        if verbose:
            tester.log(f"开始测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            tester.log(f"测试类型: {test_type}, 超时时间: {timeout}秒")
        
        # 执行测试
        basic_results = []
        api_result = None
        
        if test_type in ['basic', 'all']:
            basic_results = tester.test_basic_connectivity()
        
        if test_type in ['api', 'all']:
            api_result = tester.test_workflow_api()
        
        # 生成总结
        summary, recommendation = tester.generate_summary(basic_results, api_result)
        
        if verbose:
            tester.log("\n" + "=" * 60)
            tester.log("测试总结")
            tester.log("=" * 60)
            tester.log(summary)
            tester.log(recommendation)
            tester.log(f"测试完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 返回结构化结果
        return {
            "success": True,
            "summary": summary,
            "recommendation": recommendation,
            "basic_test_results": basic_results,
            "api_test_result": api_result,
            "accessible_count": sum(1 for r in basic_results if r.get('success', False)),
            "total_count": len(basic_results),
            "test_time": datetime.now().isoformat()
        }
        
    except Exception as e:
        error_msg = f"测试过程中发生错误: {str(e)}"
        
        # 安全的错误日志记录
        try:
            # 尝试获取logger进行错误记录，但要更加谨慎
            safe_logger = None
            if args is not None and hasattr(args, 'logger'):
                try:
                    potential_logger = getattr(args, 'logger', None)
                    if potential_logger and hasattr(potential_logger, 'error'):
                        error_method = getattr(potential_logger, 'error', None)
                        if error_method and callable(error_method):
                            safe_logger = potential_logger
                except Exception:
                    # 如果获取logger过程中出现任何异常，忽略并使用None
                    safe_logger = None
            
            _safe_log(safe_logger, error_msg, 'error')
        except Exception:
            # 如果连错误日志都失败了，直接使用print
            print(f"[ERROR] {error_msg}")
        
        return {
            "success": False,
            "error": str(e),
            "message": error_msg,
            "summary": "❌ 测试失败",
            "recommendation": "💡 请检查网络连接和插件配置",
            "basic_test_results": [],
            "api_test_result": None,
            "accessible_count": 0,
            "total_count": 0,
            "test_time": datetime.now().isoformat()
        }


if __name__ == "__main__":
    # 本地测试
    class MockArgs:
        def __init__(self):
            self.input = {'test_type': 'all', 'timeout': 10, 'verbose': True}
            self.logger = None
    
    result = handler(MockArgs())
    print(json.dumps(result, indent=2, ensure_ascii=False))