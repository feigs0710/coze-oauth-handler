#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coze.cn插件集成示例
展示如何在coze.cn插件中调用coze.com的工作流API

作者: AI Assistant
创建时间: 2025-07-20
"""

import json
import logging
from typing import Dict, Any, Optional, List
from coze_chatflow_client import CozeChatflowClient

class CozePluginIntegration:
    """
    Coze插件集成类
    用于在coze.cn插件中调用coze.com的工作流
    """
    
    def __init__(self, config_file: str = "chatflow_config.json"):
        """
        初始化插件集成
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.config = self._load_config()
        self.client = None
        self.logger = self._setup_logger()
        
        if self.config:
            self._initialize_client()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        加载配置文件
        
        Returns:
            配置字典
        """
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ 加载配置文件失败: {e}")
            return {}
    
    def _setup_logger(self) -> logging.Logger:
        """
        设置日志记录器
        
        Returns:
            日志记录器
        """
        logger = logging.getLogger("coze_plugin")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _initialize_client(self):
        """
        初始化chatflow客户端
        """
        try:
            access_token = self.config.get('access_token')
            base_url = self.config.get('base_url', 'https://api.coze.com')
            
            if not access_token:
                self.logger.error("未找到access_token配置")
                return
            
            self.client = CozeChatflowClient(
                access_token=access_token,
                base_url=base_url
            )
            
            self.logger.info("Chatflow客户端初始化成功")
            
        except Exception as e:
            self.logger.error(f"初始化客户端失败: {e}")
    
    def execute_workflow(self, 
                        user_input: str,
                        workflow_id: Optional[str] = None,
                        context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行工作流 - 插件主要调用接口
        
        Args:
            user_input: 用户输入内容
            workflow_id: 工作流ID（可选，默认使用配置文件中的）
            context: 上下文信息（可选）
            
        Returns:
            执行结果
        """
        if not self.client:
            return {
                'success': False,
                'message': 'Chatflow客户端未初始化',
                'error': 'Client not initialized'
            }
        
        try:
            # 获取工作流ID
            if not workflow_id:
                chatflow_config = self.config.get('chatflow_config', {})
                workflow_id = chatflow_config.get('workflow_id')
            
            if not workflow_id:
                return {
                    'success': False,
                    'message': '未指定工作流ID',
                    'error': 'No workflow_id specified'
                }
            
            # 准备参数
            chatflow_config = self.config.get('chatflow_config', {})
            
            # 构建额外消息
            additional_messages = [{
                'content': user_input,
                'content_type': 'text',
                'role': 'user',
                'type': 'question'
            }]
            
            # 添加上下文信息到meta_data
            if context:
                additional_messages[0]['meta_data'] = context
            
            # 执行工作流
            result = self.client.run_chatflow(
                workflow_id=workflow_id,
                additional_messages=additional_messages,
                app_id=chatflow_config.get('app_id') if not chatflow_config.get('app_id', '').startswith('请输入') else None,
                bot_id=chatflow_config.get('bot_id') if not chatflow_config.get('bot_id', '').startswith('请输入') else None,
                conversation_id=chatflow_config.get('conversation_id') if not chatflow_config.get('conversation_id', '').startswith('请输入') else None,
                parameters=chatflow_config.get('parameters', {}),
                ext=chatflow_config.get('ext', {})
            )
            
            # 记录日志
            if result['success']:
                self.logger.info(f"工作流执行成功: {workflow_id}")
            else:
                self.logger.error(f"工作流执行失败: {result['message']}")
            
            return result
            
        except Exception as e:
            error_msg = f"执行工作流时发生异常: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'message': error_msg,
                'error': str(e)
            }
    
    def process_user_message(self, message: str, session_id: Optional[str] = None) -> str:
        """
        处理用户消息 - 简化的插件接口
        
        Args:
            message: 用户消息
            session_id: 会话ID（可选）
            
        Returns:
            处理结果文本
        """
        context = {}
        if session_id:
            context['session_id'] = session_id
        
        result = self.execute_workflow(message, context=context)
        
        if result['success']:
            # 从响应中提取文本内容
            data = result.get('data', {})
            
            # 这里需要根据实际的API响应格式来提取内容
            # 以下是一个通用的提取逻辑
            if isinstance(data, dict):
                # 尝试提取常见的响应字段
                response_text = (
                    data.get('content') or 
                    data.get('message') or 
                    data.get('response') or 
                    data.get('output') or
                    str(data)
                )
                return response_text
            else:
                return str(data)
        else:
            return f"处理失败: {result['message']}"
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """
        获取工作流状态信息
        
        Returns:
            状态信息
        """
        if not self.client:
            return {
                'status': 'error',
                'message': '客户端未初始化'
            }
        
        # 测试连接
        test_result = self.client.test_connection()
        
        chatflow_config = self.config.get('chatflow_config', {})
        
        return {
            'status': 'ready' if test_result['success'] else 'error',
            'connection': test_result,
            'workflow_id': chatflow_config.get('workflow_id'),
            'api_endpoint': self.config.get('base_url'),
            'config_loaded': bool(self.config)
        }
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        验证配置有效性
        
        Returns:
            验证结果
        """
        issues = []
        warnings = []
        
        # 检查基础配置
        if not self.config:
            issues.append("配置文件加载失败")
            return {
                'valid': False,
                'issues': issues,
                'warnings': warnings
            }
        
        # 检查access_token
        access_token = self.config.get('access_token')
        if not access_token:
            issues.append("缺少access_token配置")
        elif access_token.startswith('请输入') or access_token == 'pat_ZJFRWrFB89O1vAZVXrNR90PvkN7UNMEecWANZ1gQghIAqX4xNGhwfElNf8NTdXAf':
            issues.append("access_token未正确配置")
        
        # 检查workflow_id
        chatflow_config = self.config.get('chatflow_config', {})
        workflow_id = chatflow_config.get('workflow_id')
        if not workflow_id:
            issues.append("缺少workflow_id配置")
        
        # 检查可选配置
        optional_fields = ['app_id', 'bot_id', 'conversation_id']
        for field in optional_fields:
            value = chatflow_config.get(field)
            if value and value.startswith('请输入'):
                warnings.append(f"{field}未配置，将使用默认值")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings
        }

# 插件入口函数示例
def plugin_main(user_input: str, **kwargs) -> str:
    """
    插件主入口函数
    这是在coze.cn插件中调用的主要函数
    
    Args:
        user_input: 用户输入
        **kwargs: 其他参数
        
    Returns:
        处理结果
    """
    try:
        # 初始化插件集成
        integration = CozePluginIntegration()
        
        # 验证配置
        validation = integration.validate_configuration()
        if not validation['valid']:
            return f"配置错误: {', '.join(validation['issues'])}"
        
        # 处理用户消息
        session_id = kwargs.get('session_id')
        result = integration.process_user_message(user_input, session_id)
        
        return result
        
    except Exception as e:
        return f"插件执行错误: {str(e)}"

# 高级插件入口函数示例
def plugin_advanced(user_input: str, workflow_id: str = None, **kwargs) -> Dict[str, Any]:
    """
    高级插件入口函数
    返回详细的执行结果
    
    Args:
        user_input: 用户输入
        workflow_id: 指定的工作流ID
        **kwargs: 其他参数
        
    Returns:
        详细执行结果
    """
    try:
        # 初始化插件集成
        integration = CozePluginIntegration()
        
        # 验证配置
        validation = integration.validate_configuration()
        if not validation['valid']:
            return {
                'success': False,
                'message': '配置验证失败',
                'issues': validation['issues']
            }
        
        # 准备上下文
        context = {
            'timestamp': kwargs.get('timestamp'),
            'user_id': kwargs.get('user_id'),
            'session_id': kwargs.get('session_id')
        }
        
        # 执行工作流
        result = integration.execute_workflow(
            user_input=user_input,
            workflow_id=workflow_id,
            context=context
        )
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'message': f'插件执行异常: {str(e)}',
            'error': str(e)
        }

def test_plugin_integration():
    """
    测试插件集成功能
    """
    print("🚀 测试Coze插件集成")
    print("=" * 40)
    
    # 初始化集成
    integration = CozePluginIntegration()
    
    # 验证配置
    print("\n🔍 验证配置...")
    validation = integration.validate_configuration()
    
    if validation['valid']:
        print("✅ 配置验证通过")
        if validation['warnings']:
            print("⚠️  警告:")
            for warning in validation['warnings']:
                print(f"   - {warning}")
    else:
        print("❌ 配置验证失败:")
        for issue in validation['issues']:
            print(f"   - {issue}")
        return
    
    # 获取状态
    print("\n📊 获取工作流状态...")
    status = integration.get_workflow_status()
    print(f"状态: {status['status']}")
    print(f"工作流ID: {status['workflow_id']}")
    print(f"API端点: {status['api_endpoint']}")
    
    # 测试消息处理
    print("\n💬 测试消息处理...")
    test_message = "你好，请介绍一下你的功能"
    result = integration.process_user_message(test_message, session_id="test_session_123")
    
    print(f"输入: {test_message}")
    print(f"输出: {result}")
    
    # 测试高级功能
    print("\n🔧 测试高级功能...")
    advanced_result = plugin_advanced(
        user_input="请帮我分析一下当前的市场趋势",
        user_id="test_user",
        session_id="test_session_456"
    )
    
    if advanced_result['success']:
        print("✅ 高级功能测试成功")
        print(f"响应数据类型: {type(advanced_result.get('data', {}))}")
    else:
        print(f"❌ 高级功能测试失败: {advanced_result['message']}")
    
    print("\n🎉 插件集成测试完成!")

if __name__ == "__main__":
    test_plugin_integration()