#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖注入容器
提供轻量级的依赖注入和服务管理功能
"""

import inspect
import logging
from typing import Any, Dict, Type, TypeVar, Callable, Optional, Union, get_type_hints
from functools import wraps
from abc import ABC, abstractmethod
from enum import Enum

T = TypeVar('T')

class ServiceLifetime(Enum):
    """服务生命周期"""
    SINGLETON = "singleton"  # 单例
    TRANSIENT = "transient"  # 每次创建新实例
    SCOPED = "scoped"       # 作用域内单例

class ServiceDescriptor:
    """服务描述符"""
    
    def __init__(self, 
                 service_type: Type,
                 implementation: Union[Type, Callable],
                 lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
                 factory: Optional[Callable] = None):
        self.service_type = service_type
        self.implementation = implementation
        self.lifetime = lifetime
        self.factory = factory
        self.instance = None  # 用于单例模式
    
    def __repr__(self):
        return f"ServiceDescriptor({self.service_type.__name__} -> {self.implementation.__name__}, {self.lifetime.value})"

class DIContainer:
    """依赖注入容器"""
    
    def __init__(self):
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._scoped_instances: Dict[Type, Any] = {}
        self._logger = logging.getLogger(__name__)
        self._building_stack = set()  # 防止循环依赖
    
    def register_singleton(self, service_type: Type[T], implementation: Union[Type[T], T, Callable[[], T]]) -> 'DIContainer':
        """注册单例服务"""
        return self._register(service_type, implementation, ServiceLifetime.SINGLETON)
    
    def register_transient(self, service_type: Type[T], implementation: Union[Type[T], Callable[[], T]]) -> 'DIContainer':
        """注册瞬态服务"""
        return self._register(service_type, implementation, ServiceLifetime.TRANSIENT)
    
    def register_scoped(self, service_type: Type[T], implementation: Union[Type[T], Callable[[], T]]) -> 'DIContainer':
        """注册作用域服务"""
        return self._register(service_type, implementation, ServiceLifetime.SCOPED)
    
    def register_factory(self, service_type: Type[T], factory: Callable[['DIContainer'], T], 
                        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT) -> 'DIContainer':
        """注册工厂方法"""
        descriptor = ServiceDescriptor(service_type, factory, lifetime, factory)
        self._services[service_type] = descriptor
        self._logger.debug(f"注册工厂服务: {descriptor}")
        return self
    
    def register_instance(self, service_type: Type[T], instance: T) -> 'DIContainer':
        """注册实例（单例）"""
        descriptor = ServiceDescriptor(service_type, type(instance), ServiceLifetime.SINGLETON)
        descriptor.instance = instance
        self._services[service_type] = descriptor
        self._logger.debug(f"注册实例服务: {descriptor}")
        return self
    
    def _register(self, service_type: Type[T], implementation: Union[Type[T], T, Callable], 
                 lifetime: ServiceLifetime) -> 'DIContainer':
        """内部注册方法"""
        # 如果传入的是实例，直接注册为单例
        if not inspect.isclass(implementation) and not callable(implementation):
            return self.register_instance(service_type, implementation)
        
        descriptor = ServiceDescriptor(service_type, implementation, lifetime)
        self._services[service_type] = descriptor
        self._logger.debug(f"注册服务: {descriptor}")
        return self
    
    def resolve(self, service_type: Type[T]) -> T:
        """解析服务"""
        if service_type in self._building_stack:
            raise ValueError(f"检测到循环依赖: {service_type.__name__}")
        
        if service_type not in self._services:
            # 尝试自动注册
            if inspect.isclass(service_type) and not inspect.isabstract(service_type):
                self.register_transient(service_type, service_type)
            else:
                raise ValueError(f"服务未注册: {service_type.__name__}")
        
        descriptor = self._services[service_type]
        
        # 单例模式
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            if descriptor.instance is None:
                descriptor.instance = self._create_instance(descriptor)
            return descriptor.instance
        
        # 作用域模式
        elif descriptor.lifetime == ServiceLifetime.SCOPED:
            if service_type not in self._scoped_instances:
                self._scoped_instances[service_type] = self._create_instance(descriptor)
            return self._scoped_instances[service_type]
        
        # 瞬态模式
        else:
            return self._create_instance(descriptor)
    
    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """创建服务实例"""
        self._building_stack.add(descriptor.service_type)
        
        try:
            # 使用工厂方法
            if descriptor.factory:
                return descriptor.factory(self)
            
            # 使用构造函数
            implementation = descriptor.implementation
            
            if callable(implementation) and not inspect.isclass(implementation):
                # 函数工厂
                return implementation()
            
            # 类构造
            return self._create_class_instance(implementation)
            
        finally:
            self._building_stack.discard(descriptor.service_type)
    
    def _create_class_instance(self, cls: Type) -> Any:
        """创建类实例（自动注入依赖）"""
        # 获取构造函数签名
        signature = inspect.signature(cls.__init__)
        type_hints = get_type_hints(cls.__init__)
        
        # 准备构造参数
        kwargs = {}
        for param_name, param in signature.parameters.items():
            if param_name == 'self':
                continue
            
            # 获取参数类型
            param_type = type_hints.get(param_name, param.annotation)
            
            if param_type == inspect.Parameter.empty:
                if param.default == inspect.Parameter.empty:
                    raise ValueError(f"无法解析参数 {param_name}，缺少类型注解")
                continue
            
            # 解析依赖
            if param.default == inspect.Parameter.empty:
                # 必需参数
                kwargs[param_name] = self.resolve(param_type)
            else:
                # 可选参数
                try:
                    kwargs[param_name] = self.resolve(param_type)
                except ValueError:
                    # 使用默认值
                    pass
        
        return cls(**kwargs)
    
    def clear_scoped(self):
        """清除作用域实例"""
        self._scoped_instances.clear()
        self._logger.debug("清除作用域实例")
    
    def is_registered(self, service_type: Type) -> bool:
        """检查服务是否已注册"""
        return service_type in self._services
    
    def get_services(self) -> Dict[Type, ServiceDescriptor]:
        """获取所有注册的服务"""
        return self._services.copy()
    
    def remove_service(self, service_type: Type) -> bool:
        """移除服务注册"""
        if service_type in self._services:
            del self._services[service_type]
            self._scoped_instances.pop(service_type, None)
            self._logger.debug(f"移除服务: {service_type.__name__}")
            return True
        return False

# 全局容器实例
default_container = DIContainer()

def injectable(lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT):
    """装饰器：标记类为可注入服务"""
    def decorator(cls):
        # 自动注册到默认容器
        if lifetime == ServiceLifetime.SINGLETON:
            default_container.register_singleton(cls, cls)
        elif lifetime == ServiceLifetime.SCOPED:
            default_container.register_scoped(cls, cls)
        else:
            default_container.register_transient(cls, cls)
        
        return cls
    return decorator

def inject(container: Optional[DIContainer] = None):
    """装饰器：自动注入依赖到函数参数"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 获取函数签名和类型提示
            signature = inspect.signature(func)
            type_hints = get_type_hints(func)
            
            # 使用指定容器或默认容器
            di_container = container or default_container
            
            # 注入依赖
            for param_name, param in signature.parameters.items():
                if param_name in kwargs:
                    continue  # 已提供参数
                
                param_type = type_hints.get(param_name, param.annotation)
                if param_type != inspect.Parameter.empty and di_container.is_registered(param_type):
                    kwargs[param_name] = di_container.resolve(param_type)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

class ServiceProvider(ABC):
    """服务提供者基类"""
    
    @abstractmethod
    def configure_services(self, container: DIContainer) -> None:
        """配置服务"""
        pass

class CozeServiceProvider(ServiceProvider):
    """Coze服务提供者"""
    
    def configure_services(self, container: DIContainer) -> None:
        """配置Coze相关服务"""
        from config_manager import CozeConfig, ConfigManager
        import requests
        
        # 注册配置管理
        container.register_singleton(ConfigManager, ConfigManager)
        
        # 注册配置（工厂方法）
        def config_factory(c: DIContainer) -> CozeConfig:
            config_manager = c.resolve(ConfigManager)
            return config_manager.get_config()
        
        container.register_factory(CozeConfig, config_factory, ServiceLifetime.SINGLETON)
        
        # 注册HTTP会话（单例）
        def session_factory(c: DIContainer) -> requests.Session:
            config = c.resolve(CozeConfig)
            session = requests.Session()
            session.timeout = config.timeout
            return session
        
        container.register_factory(requests.Session, session_factory, ServiceLifetime.SINGLETON)
        
        # 注册日志器
        def logger_factory(c: DIContainer) -> logging.Logger:
            config = c.resolve(CozeConfig)
            return config.setup_logging()
        
        container.register_factory(logging.Logger, logger_factory, ServiceLifetime.SINGLETON)

def configure_default_services():
    """配置默认服务"""
    provider = CozeServiceProvider()
    provider.configure_services(default_container)

# 示例服务类
if __name__ == "__main__":
    # 示例：定义服务接口和实现
    
    class IRepository(ABC):
        @abstractmethod
        def get_data(self) -> str:
            pass
    
    class DatabaseRepository(IRepository):
        def __init__(self, connection_string: str = "default_connection"):
            self.connection_string = connection_string
        
        def get_data(self) -> str:
            return f"Data from database: {self.connection_string}"
    
    @injectable(ServiceLifetime.SINGLETON)
    class CacheService:
        def __init__(self):
            self.cache = {}
        
        def get(self, key: str) -> Optional[str]:
            return self.cache.get(key)
        
        def set(self, key: str, value: str):
            self.cache[key] = value
    
    class BusinessService:
        def __init__(self, repository: IRepository, cache: CacheService):
            self.repository = repository
            self.cache = cache
        
        def get_cached_data(self, key: str) -> str:
            # 先检查缓存
            cached = self.cache.get(key)
            if cached:
                return f"Cached: {cached}"
            
            # 从仓库获取数据
            data = self.repository.get_data()
            self.cache.set(key, data)
            return data
    
    # 配置容器
    container = DIContainer()
    
    # 注册服务
    container.register_singleton(IRepository, DatabaseRepository)
    container.register_transient(BusinessService, BusinessService)
    
    # 解析和使用服务
    try:
        business_service = container.resolve(BusinessService)
        result = business_service.get_cached_data("test_key")
        print(f"结果: {result}")
        
        # 测试缓存
        result2 = business_service.get_cached_data("test_key")
        print(f"缓存结果: {result2}")
        
        # 测试单例
        cache1 = container.resolve(CacheService)
        cache2 = container.resolve(CacheService)
        print(f"缓存服务是单例: {cache1 is cache2}")
        
        # 显示注册的服务
        print("\n注册的服务:")
        for service_type, descriptor in container.get_services().items():
            print(f"- {descriptor}")
            
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()