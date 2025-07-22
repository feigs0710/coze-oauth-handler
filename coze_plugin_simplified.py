from runtime import Args
import json
import urllib.request
import urllib.error
import time
from datetime import datetime

# 自定义异常类
class CozeAPIError(Exception):
    """Coze API 基础异常"""
    def __init__(self, message, error_code=None, response_data=None):
        super().__init__(message)
        self.error_code = error_code
        self.response_data = response_data

class CozeAuthError(CozeAPIError):
    """认证错误"""
    pass

class CozeNetworkError(CozeAPIError):
    """网络连接错误"""
    pass

class CozeWorkflowError(CozeAPIError):
    """工作流执行错误"""
    pass

class CozeRateLimitError(CozeAPIError):
    """请求频率限制错误"""
    pass

class CozeChatflowClient:
    """Coze.com 工作流客户端"""
    
    def __init__(self, access_token, base_url="https://api.coze.com"):
        self.access_token = access_token
        self.base_url = base_url.rstrip('/')
        self.timeout = 30
    
    def _make_request(self, method, endpoint, data=None, headers=None):
        """发送HTTP请求"""
        url = f"{self.base_url}{endpoint}"
        
        # 设置默认headers
        default_headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'User-Agent': 'Coze-Plugin/1.0.0'
        }
        
        if headers:
            default_headers.update(headers)
        
        # 准备请求数据
        if data:
            json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
        else:
            json_data = None
        
        # 创建请求
        req = urllib.request.Request(
            url=url,
            data=json_data,
            headers=default_headers,
            method=method
        )
        
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                response_data = response.read().decode('utf-8')
                
                if response.status == 200:
                    return json.loads(response_data)
                else:
                    raise CozeAPIError(
                        f"API请求失败: HTTP {response.status}",
                        error_code=response.status,
                        response_data=response_data
                    )
                    
        except urllib.error.HTTPError as e:
            error_data = e.read().decode('utf-8') if e.fp else None
            
            if e.code == 401:
                raise CozeAuthError("认证失败，请检查访问令牌", error_code=401, response_data=error_data)
            elif e.code == 403:
                raise CozeAuthError("权限不足，请检查令牌权限", error_code=403, response_data=error_data)
            elif e.code == 429:
                raise CozeRateLimitError("请求频率过高，请稍后重试", error_code=429, response_data=error_data)
            elif e.code >= 500:
                raise CozeAPIError(f"服务器错误: {e.code}", error_code=e.code, response_data=error_data)
            else:
                raise CozeAPIError(f"HTTP错误: {e.code}", error_code=e.code, response_data=error_data)
                
        except urllib.error.URLError as e:
            raise CozeNetworkError(f"网络连接失败: {e.reason}")
        except json.JSONDecodeError as e:
            raise CozeAPIError(f"响应解析失败: {e}")
        except Exception as e:
            raise CozeAPIError(f"请求失败: {e}")
    
    def run_workflow(self, workflow_id, user_input, **kwargs):
        """运行工作流"""
        endpoint = "/v1/workflow/run"
        
        # 构建请求数据
        payload = {
            "workflow_id": workflow_id,
            "parameters": {
                "user_input": user_input
            }
        }
        
        # 添加可选参数
        optional_params = [
            'app_id', 'bot_id', 'conversation_id', 'conversation_name',
            'apikey', 'prompt', 'system_prompt', 'access_token'
        ]
        
        for param in optional_params:
            if param in kwargs and kwargs[param] is not None:
                if param == 'parameters' and isinstance(kwargs[param], dict):
                    payload['parameters'].update(kwargs[param])
                else:
                    payload['parameters'][param] = kwargs[param]
        
        try:
            result = self._make_request('POST', endpoint, payload)
            return result
        except CozeAPIError:
            raise
        except Exception as e:
            raise CozeWorkflowError(f"工作流执行失败: {e}")

class CozePluginConfig:
    """插件配置管理"""
    
    @staticmethod
    def validate_config(config):
        """验证配置参数"""
        errors = []
        
        # 必需参数检查
        required_fields = {
            'access_token': '访问令牌',
            'workflow_id': '工作流ID',
            'user_input': '用户输入'
        }
        
        for field, name in required_fields.items():
            if not config.get(field):
                errors.append(f"{name}不能为空")
        
        # 访问令牌格式检查
        if config.get('access_token') and not config['access_token'].startswith('pat_'):
            errors.append("访问令牌格式错误，应以 'pat_' 开头")
        
        # 工作流ID格式检查
        workflow_id = config.get('workflow_id')
        if workflow_id:
            try:
                int(workflow_id)
            except (ValueError, TypeError):
                errors.append("工作流ID必须是数字")
        
        # URL格式检查
        base_url = config.get('base_url', '')
        if base_url and not (base_url.startswith('http://') or base_url.startswith('https://')):
            errors.append("基础URL格式错误，必须以 http:// 或 https:// 开头")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    @staticmethod
    def get_default_config():
        """获取默认配置"""
        return {
            'base_url': 'https://api.coze.com',
            'app_id': None,
            'bot_id': None,
            'conversation_id': None,
            'parameters': {}
        }

def handler(args):
    """插件主入口函数 - 简化版本，移除所有类型注解"""
    
    # 获取当前时间戳
    timestamp = datetime.now().isoformat() + 'Z'
    
    try:
        # 记录开始执行
        args.logger.info("开始执行 Coze 工作流调用插件 (简化版本)")
        
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
        
        # 直接执行工作流
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
__version__ = "1.0.1-simplified"
__author__ = "Coze Plugin Team"
__description__ = "Coze.cn 插件 - 调用 Coze.com 工作流 (简化版本，无类型注解)"