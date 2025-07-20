#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coze配置管理模块
提供统一的配置管理、验证和加载功能
"""

import os
import json
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List
from pathlib import Path
import logging
from urllib.parse import urlparse

@dataclass
class CozeConfig:
    """
    Coze配置管理类
    
    Attributes:
        client_id: OAuth应用的客户端ID
        client_secret: OAuth应用的客户端密钥
        redirect_uri: OAuth重定向URI
        base_url: Coze API基础URL
        timeout: 请求超时时间（秒）
        max_retries: 最大重试次数
        log_level: 日志级别
        rate_limit: API调用频率限制（每分钟）
        cache_ttl: 缓存生存时间（秒）
        enable_metrics: 是否启用性能指标收集
    """
    
    # 必需配置
    client_id: str = ""
    client_secret: str = ""
    redirect_uri: str = "http://localhost:8080/oauth/callback"
    
    # API配置
    base_url: str = "https://api.coze.com"
    timeout: int = 30
    max_retries: int = 3
    
    # 日志配置
    log_level: str = "INFO"
    log_format: str = "structured"  # structured 或 simple
    
    # 性能配置
    rate_limit: int = 60  # 每分钟请求数
    cache_ttl: int = 300  # 5分钟
    enable_metrics: bool = True
    
    # 安全配置
    enable_encryption: bool = True
    token_storage_path: str = "~/.coze/tokens.enc"
    
    # 开发配置
    debug_mode: bool = False
    mock_responses: bool = False
    
    @classmethod
    def from_env(cls, prefix: str = "COZE_") -> 'CozeConfig':
        """
        从环境变量加载配置
        
        Args:
            prefix: 环境变量前缀
            
        Returns:
            配置实例
            
        Example:
            >>> config = CozeConfig.from_env()
            >>> print(config.client_id)
        """
        def get_env_bool(key: str, default: bool) -> bool:
            value = os.getenv(key, str(default)).lower()
            return value in ('true', '1', 'yes', 'on')
        
        def get_env_int(key: str, default: int) -> int:
            try:
                return int(os.getenv(key, str(default)))
            except ValueError:
                return default
        
        return cls(
            client_id=os.getenv(f'{prefix}CLIENT_ID', ''),
            client_secret=os.getenv(f'{prefix}CLIENT_SECRET', ''),
            redirect_uri=os.getenv(f'{prefix}REDIRECT_URI', 'http://localhost:8080/oauth/callback'),
            base_url=os.getenv(f'{prefix}BASE_URL', 'https://api.coze.com'),
            timeout=get_env_int(f'{prefix}TIMEOUT', 30),
            max_retries=get_env_int(f'{prefix}MAX_RETRIES', 3),
            log_level=os.getenv(f'{prefix}LOG_LEVEL', 'INFO'),
            log_format=os.getenv(f'{prefix}LOG_FORMAT', 'structured'),
            rate_limit=get_env_int(f'{prefix}RATE_LIMIT', 60),
            cache_ttl=get_env_int(f'{prefix}CACHE_TTL', 300),
            enable_metrics=get_env_bool(f'{prefix}ENABLE_METRICS', True),
            enable_encryption=get_env_bool(f'{prefix}ENABLE_ENCRYPTION', True),
            token_storage_path=os.getenv(f'{prefix}TOKEN_STORAGE_PATH', '~/.coze/tokens.enc'),
            debug_mode=get_env_bool(f'{prefix}DEBUG_MODE', False),
            mock_responses=get_env_bool(f'{prefix}MOCK_RESPONSES', False)
        )
    
    @classmethod
    def from_file(cls, config_path: Path) -> 'CozeConfig':
        """
        从配置文件加载配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置实例
            
        Raises:
            FileNotFoundError: 配置文件不存在
            json.JSONDecodeError: 配置文件格式错误
            
        Example:
            >>> config = CozeConfig.from_file(Path('config.json'))
        """
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 过滤掉不存在的字段
            valid_fields = {field.name for field in cls.__dataclass_fields__.values()}
            filtered_data = {k: v for k, v in data.items() if k in valid_fields}
            
            return cls(**filtered_data)
            
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"配置文件格式错误: {e}", e.doc, e.pos)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CozeConfig':
        """
        从字典创建配置
        
        Args:
            data: 配置字典
            
        Returns:
            配置实例
        """
        valid_fields = {field.name for field in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)
    
    def to_dict(self, exclude_secrets: bool = True) -> Dict[str, Any]:
        """
        转换为字典
        
        Args:
            exclude_secrets: 是否排除敏感信息
            
        Returns:
            配置字典
        """
        data = asdict(self)
        
        if exclude_secrets:
            # 隐藏敏感信息
            if data.get('client_secret'):
                data['client_secret'] = '***'
        
        return data
    
    def save_to_file(self, config_path: Path, exclude_secrets: bool = True) -> None:
        """
        保存配置到文件
        
        Args:
            config_path: 配置文件路径
            exclude_secrets: 是否排除敏感信息
        """
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(exclude_secrets), f, indent=2, ensure_ascii=False)
    
    def validate(self) -> List[str]:
        """
        验证配置有效性
        
        Returns:
            错误信息列表，空列表表示验证通过
        """
        errors = []
        
        # 检查必需字段
        if not self.client_id:
            errors.append("client_id 不能为空")
        
        if not self.client_secret:
            errors.append("client_secret 不能为空")
        
        if not self.redirect_uri:
            errors.append("redirect_uri 不能为空")
        
        # 验证URL格式
        if self.redirect_uri:
            try:
                parsed = urlparse(self.redirect_uri)
                if not parsed.scheme or not parsed.netloc:
                    errors.append("redirect_uri 格式无效")
            except Exception:
                errors.append("redirect_uri 格式无效")
        
        if self.base_url:
            try:
                parsed = urlparse(self.base_url)
                if not parsed.scheme or not parsed.netloc:
                    errors.append("base_url 格式无效")
            except Exception:
                errors.append("base_url 格式无效")
        
        # 验证数值范围
        if self.timeout <= 0:
            errors.append("timeout 必须大于0")
        
        if self.max_retries < 0:
            errors.append("max_retries 不能小于0")
        
        if self.rate_limit <= 0:
            errors.append("rate_limit 必须大于0")
        
        if self.cache_ttl < 0:
            errors.append("cache_ttl 不能小于0")
        
        # 验证日志级别
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.log_level.upper() not in valid_log_levels:
            errors.append(f"log_level 必须是以下之一: {', '.join(valid_log_levels)}")
        
        # 验证日志格式
        valid_log_formats = ['structured', 'simple']
        if self.log_format not in valid_log_formats:
            errors.append(f"log_format 必须是以下之一: {', '.join(valid_log_formats)}")
        
        return errors
    
    def is_valid(self) -> bool:
        """
        检查配置是否有效
        
        Returns:
            配置是否有效
        """
        return len(self.validate()) == 0
    
    def get_expanded_token_path(self) -> Path:
        """
        获取展开的令牌存储路径
        
        Returns:
            展开的路径
        """
        return Path(os.path.expanduser(self.token_storage_path))
    
    def setup_logging(self) -> logging.Logger:
        """
        根据配置设置日志
        
        Returns:
            配置好的日志器
        """
        logger = logging.getLogger('coze')
        logger.setLevel(getattr(logging, self.log_level.upper()))
        
        # 清除现有处理器
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # 创建新处理器
        handler = logging.StreamHandler()
        
        if self.log_format == 'structured':
            # 结构化日志格式
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        else:
            # 简单日志格式
            formatter = logging.Formatter('%(levelname)s: %(message)s')
        
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def __str__(self) -> str:
        """字符串表示（隐藏敏感信息）"""
        return f"CozeConfig(client_id={self.client_id[:8]}..., base_url={self.base_url})"
    
    def __repr__(self) -> str:
        """详细字符串表示（隐藏敏感信息）"""
        safe_dict = self.to_dict(exclude_secrets=True)
        return f"CozeConfig({safe_dict})"

class ConfigManager:
    """
    配置管理器
    
    提供配置的加载、验证、缓存和热重载功能
    """
    
    def __init__(self):
        self._config: Optional[CozeConfig] = None
        self._config_path: Optional[Path] = None
        self._logger = logging.getLogger(__name__)
    
    def load_config(self, 
                   config_path: Optional[Path] = None,
                   env_prefix: str = "COZE_",
                   fallback_to_env: bool = True) -> CozeConfig:
        """
        加载配置
        
        Args:
            config_path: 配置文件路径
            env_prefix: 环境变量前缀
            fallback_to_env: 文件不存在时是否回退到环境变量
            
        Returns:
            配置实例
            
        Raises:
            ValueError: 配置验证失败
        """
        config = None
        
        # 尝试从文件加载
        if config_path and config_path.exists():
            try:
                config = CozeConfig.from_file(config_path)
                self._config_path = config_path
                self._logger.info(f"从文件加载配置: {config_path}")
            except Exception as e:
                self._logger.warning(f"从文件加载配置失败: {e}")
                if not fallback_to_env:
                    raise
        
        # 回退到环境变量
        if config is None:
            config = CozeConfig.from_env(env_prefix)
            self._logger.info("从环境变量加载配置")
        
        # 验证配置
        errors = config.validate()
        if errors:
            error_msg = "配置验证失败:\n" + "\n".join(f"- {error}" for error in errors)
            raise ValueError(error_msg)
        
        self._config = config
        return config
    
    def get_config(self) -> CozeConfig:
        """
        获取当前配置
        
        Returns:
            当前配置实例
            
        Raises:
            RuntimeError: 配置未加载
        """
        if self._config is None:
            raise RuntimeError("配置未加载，请先调用 load_config()")
        return self._config
    
    def reload_config(self) -> CozeConfig:
        """
        重新加载配置
        
        Returns:
            重新加载的配置实例
        """
        if self._config_path:
            return self.load_config(self._config_path)
        else:
            return self.load_config()
    
    def create_sample_config(self, config_path: Path) -> None:
        """
        创建示例配置文件
        
        Args:
            config_path: 配置文件路径
        """
        sample_config = CozeConfig(
            client_id="your_client_id_here",
            client_secret="your_client_secret_here",
            redirect_uri="http://localhost:8080/oauth/callback",
            base_url="https://api.coze.com",
            timeout=30,
            max_retries=3,
            log_level="INFO",
            debug_mode=False
        )
        
        sample_config.save_to_file(config_path, exclude_secrets=False)
        self._logger.info(f"示例配置文件已创建: {config_path}")

# 全局配置管理器实例
config_manager = ConfigManager()

def get_config() -> CozeConfig:
    """
    获取全局配置实例
    
    Returns:
        配置实例
    """
    return config_manager.get_config()

def load_config(config_path: Optional[Path] = None, **kwargs) -> CozeConfig:
    """
    加载全局配置
    
    Args:
        config_path: 配置文件路径
        **kwargs: 其他参数传递给 ConfigManager.load_config
        
    Returns:
        配置实例
    """
    return config_manager.load_config(config_path, **kwargs)

if __name__ == "__main__":
    # 示例用法
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "create-sample":
        # 创建示例配置
        sample_path = Path("coze_config.json")
        config_manager.create_sample_config(sample_path)
        print(f"示例配置文件已创建: {sample_path}")
    else:
        # 测试配置加载
        try:
            config = load_config()
            print("配置加载成功:")
            print(config)
            
            # 验证配置
            errors = config.validate()
            if errors:
                print("\n配置验证错误:")
                for error in errors:
                    print(f"- {error}")
            else:
                print("\n配置验证通过")
                
        except Exception as e:
            print(f"配置加载失败: {e}")
            print("\n请设置环境变量或创建配置文件")
            print("创建示例配置: python config_manager.py create-sample")