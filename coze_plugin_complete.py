from runtime import Args
# 在 Coze 平台中，Input 和 Output 类型可能需要不同的导入方式
# 如果平台不支持 typings 模块，我们使用 Any 类型作为替代
try:
    from typings import Input, Output
except ImportError:
    # 如果无法导入 typings，使用 typing.Any 作为替代
    from typing import Any
    Input = Any
    Output = Any
import json
import urllib.request
import urllib.error
import urllib.parse
import time
from datetime import datetime


# 自定义异常类
class CozeAPIError(Exception):
    """Coze API 专用异常类"""
    def __init__(self, message, error_code=None, error_type=None):
        super().__init__(message)
        self.error_code = error_code
        self.error_type = error_type


class CozeAuthError(CozeAPIError):
    """认证错误"""
    pass


class CozeWorkflowError(CozeAPIError):
    """工作流错误"""
    pass


class CozeNetworkError(CozeAPIError):
    """网络连接错误"""
    pass

"""
Coze.cn 插件 - 调用 Coze.com 工作流

这是一个完整的插件代码，用于在 coze.cn 中调用 coze.com 的工作流。
插件支持个人访问令牌认证，提供安全、稳定的工作流调用功能。

主要功能:
- 个人访问令牌认证
- 工作流调用
- 完善的错误处理
- 详细的日志记录
- 灵活的参数配置

输入参数:
- user_input: 用户输入的消息 (必需)
- access_token: 个人访问令牌 (必需)
- workflow_id: 工作流ID (必需)
- base_url: API基础URL (可选，默认: https://api.coze.com)
- app_id: 应用ID (可选)
- bot_id: 机器人ID (可选)
- conversation_id: 会话ID (可选)
- parameters: 工作流参数 (可选)

输出:
- message: 工作流执行结果或错误信息
- success: 执行是否成功 (true/false)
- timestamp: 执行时间戳
"""


class CozeChatflowClient:
    """Coze Chatflow API 客户端"""
    
    def __init__(self, access_token, base_url="https://api.coze.com"):
        """
        初始化客户端
        
        Args:
            access_token: 个人访问令牌
            base_url: API基础URL
        """
        if not access_token:
            raise ValueError("access_token 不能为空")
        
        if not base_url:
            base_url = "https://api.coze.com"
        
        self.access_token = access_token.strip() if access_token else None
        self.base_url = base_url.rstrip('/') if base_url else "https://api.coze.com"
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'User-Agent': 'Coze-Plugin/1.0.0'
        }
        
        # 配置超时和重试参数
        self.timeouts = {
            'connection_test': 5,    # 连接测试超时
            'connection_test_fast': 2,  # 快速连接测试超时
            'workflow_run': 60,      # 工作流运行超时
            'default': 30            # 默认超时
        }
        self.retry_config = {
            'max_retries': 3,
            'backoff_factor': 1.5,
            'retry_on_network_error': True,
            'retry_on_server_error': True  # 5xx错误
        }
        
        # 移除连接测试配置以提升性能
    
    def _make_request(self, method, endpoint, data=None, timeout=30, request_type='default'):
        """
        发送HTTP请求（带重试机制）
        
        Args:
            method: HTTP方法
            endpoint: API端点
            data: 请求数据
            timeout: 超时时间
            request_type: 请求类型，用于选择合适的超时时间
            
        Returns:
            响应数据
        """
        url = f"{self.base_url}{endpoint}"
        
        # 根据请求类型选择超时时间
        if timeout == 30:  # 使用默认超时时
            timeout = self.timeouts.get(request_type, self.timeouts['default'])
        
        last_exception = None
        
        for attempt in range(self.retry_config['max_retries'] + 1):
            try:
                # 准备请求
                if data:
                    data_bytes = json.dumps(data).encode('utf-8')
                else:
                    data_bytes = None
                
                req = urllib.request.Request(url, data=data_bytes, headers=self.headers, method=method)
                
                # 发送请求
                with urllib.request.urlopen(req, timeout=timeout) as response:
                    response_data = response.read().decode('utf-8')
                    return json.loads(response_data)
                    
            except urllib.error.URLError as e:
                last_exception = e
                if attempt < self.retry_config['max_retries'] and self.retry_config['retry_on_network_error']:
                    wait_time = self.retry_config['backoff_factor'] ** attempt
                    time.sleep(wait_time)
                    continue
                break
                
            except urllib.error.HTTPError as e:
                last_exception = e
                # 对于5xx错误进行重试
                if (attempt < self.retry_config['max_retries'] and 
                    self.retry_config['retry_on_server_error'] and 
                    e.code >= 500):
                    wait_time = self.retry_config['backoff_factor'] ** attempt
                    time.sleep(wait_time)
                    continue
                break
                
            except Exception as e:
                last_exception = e
                break
        
        # 处理最终异常
        if isinstance(last_exception, urllib.error.HTTPError):
            try:
                error_data = json.loads(last_exception.read().decode('utf-8'))
                error_code = error_data.get('code', last_exception.code)
                error_msg = error_data.get('msg', error_data.get('error', last_exception.reason))
                
                # 根据错误码分类
                if last_exception.code == 401:
                    raise CozeAuthError(f"认证失败: {error_msg}", error_code)
                elif last_exception.code == 404:
                    raise CozeWorkflowError(f"资源不存在: {error_msg}", error_code)
                elif last_exception.code == 429:
                    raise CozeAPIError(f"请求频率限制: {error_msg}", error_code)
                elif last_exception.code >= 500:
                    raise CozeAPIError(f"服务器错误: {error_msg}", error_code)
                else:
                    raise CozeAPIError(f"API错误 {last_exception.code}: {error_msg}", error_code)
            except json.JSONDecodeError:
                if last_exception.code == 401:
                    raise CozeAuthError(f"认证失败: HTTP {last_exception.code} {last_exception.reason}")
                elif last_exception.code == 404:
                    raise CozeWorkflowError(f"资源不存在: HTTP {last_exception.code} {last_exception.reason}")
                else:
                    raise CozeAPIError(f"HTTP错误 {last_exception.code}: {last_exception.reason}")
        elif isinstance(last_exception, urllib.error.URLError):
            raise CozeNetworkError(f"网络连接错误: {last_exception.reason}")
        elif isinstance(last_exception, json.JSONDecodeError):
            raise CozeAPIError(f"响应解析错误: {last_exception}")
        else:
            if isinstance(last_exception, (CozeAPIError, CozeAuthError, CozeWorkflowError, CozeNetworkError)):
                raise  # 重新抛出我们的自定义异常
            raise CozeAPIError(f"请求失败: {last_exception}")
    
    # 移除 _make_request_fast 方法以简化代码
    
    def run_workflow(self, workflow_id, user_input, **kwargs):
        """
        运行工作流
        
        Args:
            workflow_id: 工作流ID
            user_input: 用户输入
            **kwargs: 其他参数
            
        Returns:
            工作流执行结果
        """
        # 构建请求数据 - 修复API参数格式和参数名称映射
        request_data = {
            "workflow_id": workflow_id,
            "parameters": {
                "USER_INPUT": user_input,  # 修复: user_input映射到USER_INPUT字段
                "CONVERSATION_NAME": kwargs.get('conversation_name', 'Default Conversation'),
                "apikey": kwargs.get('apikey', kwargs.get('access_token', '')),
                "prompt": user_input,  # 修复: user_input也映射到prompt字段
                "system_prompt": kwargs.get('system_prompt', '')  # 修复: system_prompt映射到system_prompt字段
            },
            "stream": False  # 添加stream参数，默认为false
        }
        
        # 添加bot_id (通常是必需的)
        # 如果没有提供bot_id，使用workflow_id作为默认值
        bot_id = kwargs.get('bot_id') or workflow_id
        if bot_id:
            request_data['bot_id'] = bot_id
        
        # 添加user_id (某些API可能需要)
        user_id = kwargs.get('user_id', 'plugin_user')
        if user_id:
            request_data['user_id'] = user_id
        
        # 添加conversation_id
        if 'conversation_id' in kwargs and kwargs['conversation_id']:
            request_data['conversation_id'] = kwargs['conversation_id']
        else:
            # 生成默认的conversation_id
            from datetime import datetime
            request_data['conversation_id'] = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 添加系统提示词
        if 'system_prompt' in kwargs and kwargs['system_prompt']:
            request_data['parameters']['system_prompt'] = kwargs['system_prompt']
        
        # 添加可选参数
        if 'app_id' in kwargs and kwargs['app_id']:
            request_data['app_id'] = kwargs['app_id']
            
        # 合并额外的parameters
        if 'parameters' in kwargs and kwargs['parameters']:
            request_data['parameters'].update(kwargs['parameters'])
        
        # 发送请求（使用工作流专用超时时间）
        response = self._make_request('POST', '/v1/workflow/run', request_data, request_type='workflow_run')
        
        return response
    
    # 移除连接测试方法以提升性能
    
    # 移除连接测试方法以提升性能


class CozePluginConfig:
    """插件配置管理"""
    
    @staticmethod
    def validate_config(config):
        """
        验证配置参数
        
        Args:
            config: 配置字典
            
        Returns:
            验证结果
        """
        errors = []
        
        # 检查必需参数
        required_fields = ['user_input', 'access_token', 'workflow_id']
        for field in required_fields:
            if not config.get(field):
                errors.append(f"{field} 未配置")
        
        # 验证访问令牌格式
        access_token = config.get('access_token', '')
        if access_token and not access_token.startswith('pat_'):
            errors.append("access_token 格式错误，应以 pat_ 开头")
        
        # 验证工作流ID格式
        workflow_id = config.get('workflow_id', '')
        if workflow_id and not workflow_id.isdigit():
            errors.append("workflow_id 应为数字格式")
        
        # 验证URL格式
        base_url = config.get('base_url', '')
        if base_url and not (base_url.startswith('http://') or base_url.startswith('https://')):
            errors.append("base_url 格式错误，应以 http:// 或 https:// 开头")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    @staticmethod
    def get_default_config():
        """
        获取默认配置
        
        Returns:
            默认配置字典
        """
        return {
            'base_url': 'https://api.coze.com',
            'app_id': None,
            'bot_id': None,
            'conversation_id': None,
            'parameters': {}
        }


def handler(args):
    # 类型注解: args: Args -> Dict[str, Any]
    """
    插件主入口函数
    
    处理用户输入，调用 Coze.com 工作流，返回结果
    
    Args:
        args: 插件参数，包含用户输入和配置信息
        
    Returns:
        插件输出结果
    """
    
    # 获取当前时间戳
    timestamp = datetime.now().isoformat() + 'Z'
    
    try:
        # 记录开始执行
        args.logger.info("开始执行 Coze 工作流调用插件")
        
        # 获取输入参数，确保字符串参数不为None
        config = {
            'user_input': getattr(args.input, 'user_input', '') or '',
            'access_token': getattr(args.input, 'access_token', '') or '',
            'workflow_id': getattr(args.input, 'workflow_id', '') or '',
            'base_url': getattr(args.input, 'base_url', 'https://api.coze.com') or 'https://api.coze.com',
            'app_id': getattr(args.input, 'app_id', None),
            'bot_id': getattr(args.input, 'bot_id', None),
            'conversation_id': getattr(args.input, 'conversation_id', None),
            'conversation_name': getattr(args.input, 'conversation_name', 'Default Conversation') or 'Default Conversation',
            'apikey': getattr(args.input, 'apikey', '') or '',
            'prompt': getattr(args.input, 'prompt', '') or '',
            'system_prompt': getattr(args.input, 'system_prompt', None),
            'parameters': getattr(args.input, 'parameters', {}) or {}
        }
        
        args.logger.info(f"接收到用户输入: {config['user_input'][:100]}...")
        
        # 验证配置
        validation = CozePluginConfig.validate_config(config)
        if not validation['valid']:
            error_msg = "❌ 配置错误: " + ", ".join(validation['errors'])
            args.logger.error(error_msg)
            return {
                "message": error_msg,
                "error": True,
                "timestamp": timestamp
            }
        
        args.logger.info("配置验证通过")
        
        # 初始化客户端
        try:
            client = CozeChatflowClient(
                access_token=config['access_token'],
                base_url=config['base_url']
            )
            args.logger.info("客户端初始化成功")
        except Exception as e:
            error_msg = f"❌ 客户端初始化失败: {e}"
            args.logger.error(error_msg)
            return {
                "message": error_msg,
                "error": True,
                "timestamp": timestamp
            }
        
        # 直接执行工作流，无需连接测试
        args.logger.info("直接执行工作流")
        
        # 调用工作流
        try:
            args.logger.info(f"开始调用工作流: {config['workflow_id']}")
            
            result = client.run_workflow(
                workflow_id=config['workflow_id'],
                user_input=config['user_input'],
                app_id=config['app_id'],
                bot_id=config['bot_id'],
                conversation_id=config['conversation_id'],
                conversation_name=config['conversation_name'],
                apikey=config['apikey'],
                prompt=config['prompt'],
                system_prompt=config['system_prompt'],
                access_token=config['access_token'],
                parameters=config['parameters']
            )
            
            args.logger.info("工作流调用成功")
            
            # 处理响应
            if 'data' in result:
                # 提取工作流输出
                output_data = result['data']
                if isinstance(output_data, dict) and 'output' in output_data:
                    message = output_data['output']
                elif isinstance(output_data, str):
                    message = output_data
                else:
                    message = json.dumps(output_data, ensure_ascii=False, indent=2)
            else:
                message = json.dumps(result, ensure_ascii=False, indent=2)
            
            args.logger.info(f"工作流执行完成，输出长度: {len(str(message))}")
            
            return {
                "message": message,
                "success": True,
                "timestamp": timestamp
            }
            
        except CozeAuthError as e:
            error_msg = f"❌ 认证失败: {e}"
            args.logger.error(error_msg)
            return {
                "message": error_msg,
                "error": True,
                "error_type": "authentication",
                "error_code": getattr(e, 'error_code', None),
                "timestamp": timestamp
            }
        except CozeWorkflowError as e:
            error_msg = f"❌ 工作流错误: {e}"
            args.logger.error(error_msg)
            return {
                "message": error_msg,
                "error": True,
                "error_type": "workflow",
                "error_code": getattr(e, 'error_code', None),
                "timestamp": timestamp
            }
        except CozeNetworkError as e:
            error_msg = f"❌ 网络连接错误: {e}"
            args.logger.error(error_msg)
            return {
                "message": error_msg,
                "error": True,
                "error_type": "network",
                "timestamp": timestamp
            }
        except CozeAPIError as e:
            error_msg = f"❌ API错误: {e}"
            args.logger.error(error_msg)
            return {
                "message": error_msg,
                "error": True,
                "error_type": "api",
                "error_code": getattr(e, 'error_code', None),
                "timestamp": timestamp
            }
        except Exception as e:
            error_msg = f"❌ 工作流执行失败: {e}"
            args.logger.error(error_msg)
            return {
                "message": error_msg,
                "error": True,
                "error_type": "unknown",
                "timestamp": timestamp
            }
    
    except Exception as e:
        # 捕获所有未处理的异常
        error_msg = f"❌ 插件执行失败: {e}"
        args.logger.error(error_msg)
        return {
            "message": error_msg,
            "error": True,
            "timestamp": timestamp
        }


# 插件信息
__version__ = "1.0.0"
__author__ = "Coze Plugin Team"
__description__ = "Coze.cn 插件 - 调用 Coze.com 工作流"


# 使用示例和配置说明
"""
=== 插件配置说明 ===

1. 获取个人访问令牌:
   - 登录 https://coze.com
   - 进入 个人设置 → API 密钥
   - 创建新令牌，设置权限: Workflow.run, User.profile
   - 复制令牌 (格式: pat_xxxxxx...)

2. 获取工作流ID:
   - 在 coze.com 中创建或选择工作流
   - 确保工作流已发布
   - 复制工作流ID (数字格式)

3. 在 coze.cn 中配置插件:
   - 输入参数:
     * user_input (string, 必需): 用户输入消息
     * access_token (string, 必需): 个人访问令牌
     * workflow_id (string, 必需): 工作流ID
     * base_url (string, 可选): API基础URL
     * app_id (string, 可选): 应用ID
     * bot_id (string, 可选): 机器人ID
     * conversation_id (string, 可选): 会话ID
     * parameters (object, 可选): 工作流参数
   
   - 输出参数:
     * message (string): 工作流结果或错误信息
     * success (boolean): 执行是否成功
     * timestamp (string): 执行时间戳

4. 使用示例:
   输入: {
     "user_input": "请帮我写一首诗",
     "access_token": "pat_ZJFRWrFB89O1vAZVXrNR90Pv...",
     "workflow_id": "7514923198020304901"
   }
   
   输出: {
     "message": "春风轻拂绿柳梢，\n花开满园香气飘...",
     "success": true,
     "timestamp": "2024-12-19T10:30:00Z"
   }

=== 故障排除 ===

1. 认证失败:
   - 检查 access_token 格式 (应以 pat_ 开头)
   - 确认令牌权限包含 Workflow.run
   - 重新生成访问令牌

2. 工作流不存在:
   - 确认 workflow_id 正确
   - 确保工作流已发布
   - 检查工作流权限

3. 网络错误:
   - 检查网络连接
   - 验证防火墙设置
   - 稍后重试

=== 安全注意事项 ===

- 不要在代码中硬编码访问令牌
- 使用插件配置参数传递敏感信息
- 定期轮换访问令牌
- 限制令牌权限范围

=== 版本信息 ===

版本: 1.0.0
更新时间: 2024年12月
状态: 稳定版本

功能特性:
✅ 完整的工作流调用功能
✅ 个人访问令牌认证
✅ 完善的错误处理
✅ 详细的日志记录
✅ 灵活的参数配置
✅ 安全的数据处理
"""