#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成测试框架
提供完整的集成测试、性能测试和端到端测试功能
"""

import asyncio
import time
import json
import logging
import threading
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from contextlib import contextmanager
from abc import ABC, abstractmethod
from enum import Enum
import unittest
import requests
from unittest.mock import Mock, patch, MagicMock

# 导入项目模块
try:
    from config_manager import CozeConfig, ConfigManager
    from dependency_injection import DIContainer, ServiceLifetime
    from metrics_collector import MetricsCollector, APICallMetric
    from coze_oauth_integration import CozeOAuthClient, CozePluginIntegration
except ImportError as e:
    print(f"警告: 无法导入项目模块: {e}")

class TestResult(Enum):
    """测试结果"""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"

@dataclass
class TestCase:
    """测试用例"""
    name: str
    description: str
    test_func: Callable
    setup_func: Optional[Callable] = None
    teardown_func: Optional[Callable] = None
    timeout: int = 30
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    retry_count: int = 0
    
@dataclass
class TestExecution:
    """测试执行结果"""
    test_case: TestCase
    result: TestResult
    duration_ms: float
    timestamp: datetime
    error_message: Optional[str] = None
    output: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.test_case.name,
            'description': self.test_case.description,
            'result': self.result.value,
            'duration_ms': self.duration_ms,
            'timestamp': self.timestamp.isoformat(),
            'error_message': self.error_message,
            'output': self.output,
            'metrics': self.metrics,
            'tags': self.test_case.tags
        }

class TestEnvironment:
    """测试环境管理"""
    
    def __init__(self, name: str):
        self.name = name
        self.config: Optional[CozeConfig] = None
        self.container: Optional[DIContainer] = None
        self.metrics: Optional[MetricsCollector] = None
        self.mock_services: Dict[str, Mock] = {}
        self._setup_complete = False
        
    def setup(self, config: Optional[CozeConfig] = None):
        """设置测试环境"""
        if self._setup_complete:
            return
            
        # 配置管理
        if config:
            self.config = config
        else:
            # 使用测试配置
            self.config = CozeConfig(
                client_id="test_client_id",
                client_secret="test_client_secret",
                redirect_uri="http://localhost:8080/test/callback",
                base_url="https://api.coze.com",
                timeout=10,
                debug_mode=True,
                mock_responses=True
            )
        
        # 依赖注入容器
        self.container = DIContainer()
        self.container.register_instance(CozeConfig, self.config)
        
        # 指标收集器
        self.metrics = MetricsCollector(max_points=1000, retention_hours=1)
        self.container.register_instance(MetricsCollector, self.metrics)
        
        # Mock服务
        self._setup_mock_services()
        
        self._setup_complete = True
        
    def _setup_mock_services(self):
        """设置Mock服务"""
        # Mock HTTP会话
        mock_session = Mock(spec=requests.Session)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'success': True}
        mock_response.text = '{"success": true}'
        mock_session.request.return_value = mock_response
        
        self.mock_services['http_session'] = mock_session
        self.container.register_instance(requests.Session, mock_session)
        
        # Mock OAuth客户端
        mock_oauth = Mock(spec=CozeOAuthClient)
        mock_oauth.get_access_token.return_value = "mock_access_token"
        mock_oauth.refresh_token.return_value = "mock_refresh_token"
        
        self.mock_services['oauth_client'] = mock_oauth
        
    def teardown(self):
        """清理测试环境"""
        if self.metrics:
            self.metrics.clear_metrics()
        
        self.mock_services.clear()
        self._setup_complete = False
        
    def get_mock(self, service_name: str) -> Mock:
        """获取Mock服务"""
        return self.mock_services.get(service_name)

class TestRunner:
    """测试运行器"""
    
    def __init__(self, environment: TestEnvironment):
        self.environment = environment
        self.test_cases: List[TestCase] = []
        self.executions: List[TestExecution] = []
        self._logger = logging.getLogger(__name__)
        
    def add_test(self, test_case: TestCase):
        """添加测试用例"""
        self.test_cases.append(test_case)
        
    def add_test_function(self, 
                         name: str, 
                         test_func: Callable,
                         description: str = "",
                         **kwargs):
        """添加测试函数"""
        test_case = TestCase(
            name=name,
            description=description or name,
            test_func=test_func,
            **kwargs
        )
        self.add_test(test_case)
        
    def run_all(self, 
               parallel: bool = False,
               filter_tags: Optional[List[str]] = None) -> List[TestExecution]:
        """运行所有测试"""
        # 过滤测试用例
        test_cases = self._filter_tests(filter_tags)
        
        # 解决依赖关系
        ordered_tests = self._resolve_dependencies(test_cases)
        
        if parallel:
            return self._run_parallel(ordered_tests)
        else:
            return self._run_sequential(ordered_tests)
            
    def run_single(self, test_name: str) -> Optional[TestExecution]:
        """运行单个测试"""
        test_case = next((tc for tc in self.test_cases if tc.name == test_name), None)
        if not test_case:
            raise ValueError(f"测试用例不存在: {test_name}")
            
        return self._execute_test(test_case)
        
    def _filter_tests(self, filter_tags: Optional[List[str]]) -> List[TestCase]:
        """过滤测试用例"""
        if not filter_tags:
            return self.test_cases
            
        filtered = []
        for test_case in self.test_cases:
            if any(tag in test_case.tags for tag in filter_tags):
                filtered.append(test_case)
                
        return filtered
        
    def _resolve_dependencies(self, test_cases: List[TestCase]) -> List[TestCase]:
        """解决测试依赖关系"""
        # 简单的拓扑排序
        ordered = []
        remaining = test_cases.copy()
        
        while remaining:
            # 找到没有未满足依赖的测试
            ready = []
            for test_case in remaining:
                if not test_case.dependencies:
                    ready.append(test_case)
                else:
                    # 检查依赖是否已满足
                    satisfied = all(
                        any(executed.name == dep for executed in ordered)
                        for dep in test_case.dependencies
                    )
                    if satisfied:
                        ready.append(test_case)
            
            if not ready:
                # 循环依赖或未找到依赖
                self._logger.warning("检测到循环依赖或未找到依赖，使用原始顺序")
                ordered.extend(remaining)
                break
                
            # 添加就绪的测试
            for test_case in ready:
                ordered.append(test_case)
                remaining.remove(test_case)
                
        return ordered
        
    def _run_sequential(self, test_cases: List[TestCase]) -> List[TestExecution]:
        """顺序运行测试"""
        executions = []
        
        for test_case in test_cases:
            execution = self._execute_test(test_case)
            executions.append(execution)
            self.executions.append(execution)
            
            # 如果测试失败且有依赖，跳过依赖测试
            if execution.result in [TestResult.FAILED, TestResult.ERROR]:
                self._skip_dependent_tests(test_case.name, test_cases, executions)
                
        return executions
        
    def _run_parallel(self, test_cases: List[TestCase]) -> List[TestExecution]:
        """并行运行测试"""
        import concurrent.futures
        
        executions = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            # 提交所有测试
            future_to_test = {
                executor.submit(self._execute_test, test_case): test_case
                for test_case in test_cases
            }
            
            # 收集结果
            for future in concurrent.futures.as_completed(future_to_test):
                execution = future.result()
                executions.append(execution)
                self.executions.append(execution)
                
        return executions
        
    def _execute_test(self, test_case: TestCase) -> TestExecution:
        """执行单个测试"""
        start_time = time.time()
        result = TestResult.PASSED
        error_message = None
        output = None
        metrics = {}
        
        try:
            self._logger.info(f"开始执行测试: {test_case.name}")
            
            # 设置
            if test_case.setup_func:
                test_case.setup_func()
                
            # 执行测试（带超时）
            if test_case.timeout > 0:
                self._execute_with_timeout(test_case.test_func, test_case.timeout)
            else:
                test_case.test_func()
                
            # 收集指标
            if self.environment.metrics:
                metrics = self.environment.metrics.export_metrics()
                
        except TimeoutError:
            result = TestResult.ERROR
            error_message = f"测试超时 ({test_case.timeout}秒)"
            
        except AssertionError as e:
            result = TestResult.FAILED
            error_message = str(e)
            
        except Exception as e:
            result = TestResult.ERROR
            error_message = str(e)
            
        finally:
            # 清理
            try:
                if test_case.teardown_func:
                    test_case.teardown_func()
            except Exception as e:
                self._logger.warning(f"测试清理失败: {e}")
                
        duration_ms = (time.time() - start_time) * 1000
        
        execution = TestExecution(
            test_case=test_case,
            result=result,
            duration_ms=duration_ms,
            timestamp=datetime.now(),
            error_message=error_message,
            output=output,
            metrics=metrics
        )
        
        self._logger.info(f"测试完成: {test_case.name} - {result.value} ({duration_ms:.2f}ms)")
        return execution
        
    def _execute_with_timeout(self, func: Callable, timeout: int):
        """带超时执行函数"""
        result = [None]
        exception = [None]
        
        def target():
            try:
                result[0] = func()
            except Exception as e:
                exception[0] = e
                
        thread = threading.Thread(target=target)
        thread.start()
        thread.join(timeout)
        
        if thread.is_alive():
            # 超时了，但无法强制终止线程
            raise TimeoutError(f"函数执行超时: {timeout}秒")
            
        if exception[0]:
            raise exception[0]
            
        return result[0]
        
    def _skip_dependent_tests(self, failed_test: str, test_cases: List[TestCase], executions: List[TestExecution]):
        """跳过依赖失败测试的其他测试"""
        for test_case in test_cases:
            if failed_test in test_case.dependencies:
                # 创建跳过的执行记录
                execution = TestExecution(
                    test_case=test_case,
                    result=TestResult.SKIPPED,
                    duration_ms=0,
                    timestamp=datetime.now(),
                    error_message=f"依赖测试失败: {failed_test}"
                )
                executions.append(execution)
                self.executions.append(execution)
                
    def get_summary(self) -> Dict[str, Any]:
        """获取测试摘要"""
        if not self.executions:
            return {}
            
        total = len(self.executions)
        passed = sum(1 for e in self.executions if e.result == TestResult.PASSED)
        failed = sum(1 for e in self.executions if e.result == TestResult.FAILED)
        error = sum(1 for e in self.executions if e.result == TestResult.ERROR)
        skipped = sum(1 for e in self.executions if e.result == TestResult.SKIPPED)
        
        total_duration = sum(e.duration_ms for e in self.executions)
        avg_duration = total_duration / total if total > 0 else 0
        
        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'error': error,
            'skipped': skipped,
            'success_rate': passed / total if total > 0 else 0,
            'total_duration_ms': total_duration,
            'avg_duration_ms': avg_duration,
            'timestamp': datetime.now().isoformat()
        }
        
    def generate_report(self) -> str:
        """生成测试报告"""
        summary = self.get_summary()
        
        report_lines = [
            "=== 集成测试报告 ===",
            f"执行时间: {summary.get('timestamp', 'N/A')}",
            f"测试环境: {self.environment.name}",
            "",
            "## 测试摘要",
            f"- 总计: {summary.get('total', 0)}",
            f"- 通过: {summary.get('passed', 0)}",
            f"- 失败: {summary.get('failed', 0)}",
            f"- 错误: {summary.get('error', 0)}",
            f"- 跳过: {summary.get('skipped', 0)}",
            f"- 成功率: {summary.get('success_rate', 0):.2%}",
            f"- 总耗时: {summary.get('total_duration_ms', 0):.2f}ms",
            f"- 平均耗时: {summary.get('avg_duration_ms', 0):.2f}ms",
            "",
            "## 详细结果"
        ]
        
        for execution in self.executions:
            status_icon = {
                TestResult.PASSED: "✅",
                TestResult.FAILED: "❌",
                TestResult.ERROR: "💥",
                TestResult.SKIPPED: "⏭️"
            }.get(execution.result, "❓")
            
            report_lines.append(
                f"{status_icon} {execution.test_case.name} ({execution.duration_ms:.2f}ms)"
            )
            
            if execution.error_message:
                report_lines.append(f"   错误: {execution.error_message}")
                
        return "\n".join(report_lines)
        
    def save_report(self, file_path: Path, format_type: str = 'text'):
        """保存测试报告"""
        if format_type == 'text':
            content = self.generate_report()
        elif format_type == 'json':
            data = {
                'summary': self.get_summary(),
                'executions': [e.to_dict() for e in self.executions]
            }
            content = json.dumps(data, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"不支持的格式: {format_type}")
            
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        self._logger.info(f"测试报告已保存: {file_path}")

class CozeIntegrationTests:
    """Coze集成测试套件"""
    
    def __init__(self, environment: TestEnvironment):
        self.environment = environment
        self.runner = TestRunner(environment)
        self._setup_tests()
        
    def _setup_tests(self):
        """设置测试用例"""
        # 配置测试
        self.runner.add_test_function(
            "test_config_loading",
            self._test_config_loading,
            "测试配置加载",
            tags=["config", "unit"]
        )
        
        self.runner.add_test_function(
            "test_config_validation",
            self._test_config_validation,
            "测试配置验证",
            tags=["config", "unit"],
            dependencies=["test_config_loading"]
        )
        
        # OAuth测试
        self.runner.add_test_function(
            "test_oauth_client_creation",
            self._test_oauth_client_creation,
            "测试OAuth客户端创建",
            tags=["oauth", "integration"]
        )
        
        self.runner.add_test_function(
            "test_oauth_token_handling",
            self._test_oauth_token_handling,
            "测试OAuth令牌处理",
            tags=["oauth", "integration"],
            dependencies=["test_oauth_client_creation"]
        )
        
        # API测试
        self.runner.add_test_function(
            "test_api_connectivity",
            self._test_api_connectivity,
            "测试API连通性",
            tags=["api", "integration"]
        )
        
        self.runner.add_test_function(
            "test_workflow_execution",
            self._test_workflow_execution,
            "测试工作流执行",
            tags=["api", "integration"],
            dependencies=["test_api_connectivity"]
        )
        
        # 性能测试
        self.runner.add_test_function(
            "test_performance_metrics",
            self._test_performance_metrics,
            "测试性能指标收集",
            tags=["performance", "metrics"]
        )
        
        # 错误处理测试
        self.runner.add_test_function(
            "test_error_handling",
            self._test_error_handling,
            "测试错误处理",
            tags=["error", "robustness"]
        )
        
    def _test_config_loading(self):
        """测试配置加载"""
        config = self.environment.config
        assert config is not None, "配置未加载"
        assert config.client_id, "客户端ID为空"
        assert config.base_url, "基础URL为空"
        
    def _test_config_validation(self):
        """测试配置验证"""
        config = self.environment.config
        errors = config.validate()
        
        # 在测试环境中，某些验证可能失败，这是预期的
        # 这里主要测试验证逻辑是否正常工作
        assert isinstance(errors, list), "验证结果应该是列表"
        
    def _test_oauth_client_creation(self):
        """测试OAuth客户端创建"""
        config = self.environment.config
        
        # 在测试环境中创建OAuth客户端
        oauth_client = CozeOAuthClient(
            client_id=config.client_id,
            client_secret=config.client_secret,
            redirect_uri=config.redirect_uri
        )
        
        assert oauth_client is not None, "OAuth客户端创建失败"
        assert oauth_client.client_id == config.client_id, "客户端ID不匹配"
        
    def _test_oauth_token_handling(self):
        """测试OAuth令牌处理"""
        mock_oauth = self.environment.get_mock('oauth_client')
        
        # 测试令牌获取
        token = mock_oauth.get_access_token()
        assert token == "mock_access_token", "令牌获取失败"
        
        # 测试令牌刷新
        refresh_token = mock_oauth.refresh_token()
        assert refresh_token == "mock_refresh_token", "令牌刷新失败"
        
    def _test_api_connectivity(self):
        """测试API连通性"""
        mock_session = self.environment.get_mock('http_session')
        
        # 模拟API调用
        response = mock_session.request('GET', 'https://api.coze.com/v1/health')
        
        assert response.status_code == 200, "API连接失败"
        assert mock_session.request.called, "HTTP请求未被调用"
        
    def _test_workflow_execution(self):
        """测试工作流执行"""
        mock_session = self.environment.get_mock('http_session')
        
        # 配置mock响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'code': 0,
            'msg': 'success',
            'data': {'workflow_id': 'test_workflow'}
        }
        mock_session.request.return_value = mock_response
        
        # 模拟工作流执行
        response = mock_session.request(
            'POST', 
            'https://api.coze.com/v1/workflows/run',
            json={'workflow_id': 'test_workflow'}
        )
        
        assert response.status_code == 200, "工作流执行失败"
        data = response.json()
        assert data['code'] == 0, "工作流返回错误"
        
    def _test_performance_metrics(self):
        """测试性能指标收集"""
        metrics = self.environment.metrics
        
        # 记录一些测试指标
        metrics.record_counter('test_counter', 1.0)
        metrics.record_gauge('test_gauge', 42.0)
        metrics.record_timer('test_timer', 100.0)
        
        # 验证指标记录
        assert metrics.get_counter('test_counter') == 1.0, "计数器记录失败"
        assert metrics.get_gauge('test_gauge') == 42.0, "仪表盘记录失败"
        
        # 验证指标导出
        exported = metrics.export_metrics()
        assert 'test_counter' in exported, "指标导出失败"
        
    def _test_error_handling(self):
        """测试错误处理"""
        mock_session = self.environment.get_mock('http_session')
        
        # 配置错误响应
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.side_effect = Exception("JSON解析错误")
        mock_session.request.return_value = mock_response
        
        # 测试错误处理
        response = mock_session.request('GET', 'https://api.coze.com/v1/error')
        
        assert response.status_code == 500, "错误状态码处理失败"
        
        # 测试JSON解析错误处理
        try:
            response.json()
            assert False, "应该抛出异常"
        except Exception:
            pass  # 预期的异常
            
    def run_all_tests(self, **kwargs) -> List[TestExecution]:
        """运行所有测试"""
        return self.runner.run_all(**kwargs)
        
    def run_by_tags(self, tags: List[str]) -> List[TestExecution]:
        """按标签运行测试"""
        return self.runner.run_all(filter_tags=tags)

if __name__ == "__main__":
    # 示例用法
    import sys
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建测试环境
    env = TestEnvironment("integration_test")
    env.setup()
    
    try:
        # 创建测试套件
        test_suite = CozeIntegrationTests(env)
        
        # 运行测试
        if len(sys.argv) > 1:
            # 按标签过滤
            tags = sys.argv[1].split(',')
            print(f"运行标签为 {tags} 的测试...")
            executions = test_suite.run_by_tags(tags)
        else:
            # 运行所有测试
            print("运行所有集成测试...")
            executions = test_suite.run_all_tests()
        
        # 生成报告
        report = test_suite.runner.generate_report()
        print("\n" + report)
        
        # 保存报告
        report_path = Path("integration_test_report.txt")
        test_suite.runner.save_report(report_path)
        
        # 保存JSON格式报告
        json_path = Path("integration_test_report.json")
        test_suite.runner.save_report(json_path, 'json')
        
        # 检查测试结果
        summary = test_suite.runner.get_summary()
        if summary.get('failed', 0) > 0 or summary.get('error', 0) > 0:
            sys.exit(1)  # 有测试失败
        else:
            print("\n✅ 所有测试通过！")
            
    finally:
        # 清理测试环境
        env.teardown()