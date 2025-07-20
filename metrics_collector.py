#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能监控和指标收集模块
提供API调用性能监控、错误统计和系统指标收集功能
"""

import time
import threading
import psutil
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from functools import wraps
from contextlib import contextmanager
from enum import Enum
import json
from pathlib import Path

class MetricType(Enum):
    """指标类型"""
    COUNTER = "counter"        # 计数器
    GAUGE = "gauge"           # 仪表盘
    HISTOGRAM = "histogram"   # 直方图
    TIMER = "timer"           # 计时器

@dataclass
class MetricPoint:
    """指标数据点"""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    metric_type: MetricType = MetricType.GAUGE
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'value': self.value,
            'timestamp': self.timestamp.isoformat(),
            'tags': self.tags,
            'type': self.metric_type.value
        }

@dataclass
class APICallMetric:
    """API调用指标"""
    endpoint: str
    method: str
    status_code: int
    duration_ms: float
    timestamp: datetime
    error: Optional[str] = None
    request_size: Optional[int] = None
    response_size: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'endpoint': self.endpoint,
            'method': self.method,
            'status_code': self.status_code,
            'duration_ms': self.duration_ms,
            'timestamp': self.timestamp.isoformat(),
            'error': self.error,
            'request_size': self.request_size,
            'response_size': self.response_size
        }

class MetricsCollector:
    """指标收集器"""
    
    def __init__(self, max_points: int = 10000, retention_hours: int = 24):
        self.max_points = max_points
        self.retention_hours = retention_hours
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_points))
        self._api_calls: deque = deque(maxlen=max_points)
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = defaultdict(float)
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
        
        # 启动清理线程
        self._cleanup_thread = threading.Thread(target=self._cleanup_old_metrics, daemon=True)
        self._cleanup_thread.start()
    
    def record_counter(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None):
        """记录计数器指标"""
        with self._lock:
            key = self._make_key(name, tags)
            self._counters[key] += value
            
            point = MetricPoint(
                name=name,
                value=self._counters[key],
                timestamp=datetime.now(),
                tags=tags or {},
                metric_type=MetricType.COUNTER
            )
            self._metrics[key].append(point)
    
    def record_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """记录仪表盘指标"""
        with self._lock:
            key = self._make_key(name, tags)
            self._gauges[key] = value
            
            point = MetricPoint(
                name=name,
                value=value,
                timestamp=datetime.now(),
                tags=tags or {},
                metric_type=MetricType.GAUGE
            )
            self._metrics[key].append(point)
    
    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """记录直方图指标"""
        with self._lock:
            key = self._make_key(name, tags)
            self._histograms[key].append(value)
            
            # 保持最近1000个值
            if len(self._histograms[key]) > 1000:
                self._histograms[key] = self._histograms[key][-1000:]
            
            point = MetricPoint(
                name=name,
                value=value,
                timestamp=datetime.now(),
                tags=tags or {},
                metric_type=MetricType.HISTOGRAM
            )
            self._metrics[key].append(point)
    
    def record_timer(self, name: str, duration_ms: float, tags: Optional[Dict[str, str]] = None):
        """记录计时器指标"""
        with self._lock:
            key = self._make_key(name, tags)
            
            point = MetricPoint(
                name=name,
                value=duration_ms,
                timestamp=datetime.now(),
                tags=tags or {},
                metric_type=MetricType.TIMER
            )
            self._metrics[key].append(point)
            
            # 同时记录到直方图用于统计分析
            self.record_histogram(f"{name}_histogram", duration_ms, tags)
    
    def record_api_call(self, metric: APICallMetric):
        """记录API调用指标"""
        with self._lock:
            self._api_calls.append(metric)
            
            # 记录相关指标
            tags = {
                'endpoint': metric.endpoint,
                'method': metric.method,
                'status_code': str(metric.status_code)
            }
            
            self.record_counter('api_calls_total', 1.0, tags)
            self.record_timer('api_call_duration', metric.duration_ms, tags)
            
            if metric.error:
                error_tags = tags.copy()
                error_tags['error_type'] = type(metric.error).__name__ if hasattr(metric.error, '__class__') else 'unknown'
                self.record_counter('api_errors_total', 1.0, error_tags)
            
            if metric.request_size:
                self.record_histogram('request_size_bytes', metric.request_size, tags)
            
            if metric.response_size:
                self.record_histogram('response_size_bytes', metric.response_size, tags)
    
    @contextmanager
    def timer_context(self, name: str, tags: Optional[Dict[str, str]] = None):
        """计时器上下文管理器"""
        start_time = time.time()
        try:
            yield
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self.record_timer(name, duration_ms, tags)
    
    def get_counter(self, name: str, tags: Optional[Dict[str, str]] = None) -> float:
        """获取计数器值"""
        key = self._make_key(name, tags)
        return self._counters.get(key, 0.0)
    
    def get_gauge(self, name: str, tags: Optional[Dict[str, str]] = None) -> Optional[float]:
        """获取仪表盘值"""
        key = self._make_key(name, tags)
        return self._gauges.get(key)
    
    def get_histogram_stats(self, name: str, tags: Optional[Dict[str, str]] = None) -> Dict[str, float]:
        """获取直方图统计信息"""
        key = self._make_key(name, tags)
        values = self._histograms.get(key, [])
        
        if not values:
            return {}
        
        sorted_values = sorted(values)
        count = len(sorted_values)
        
        return {
            'count': count,
            'min': min(sorted_values),
            'max': max(sorted_values),
            'mean': sum(sorted_values) / count,
            'p50': sorted_values[int(count * 0.5)],
            'p90': sorted_values[int(count * 0.9)],
            'p95': sorted_values[int(count * 0.95)],
            'p99': sorted_values[int(count * 0.99)] if count >= 100 else sorted_values[-1]
        }
    
    def get_api_call_stats(self, hours: int = 1) -> Dict[str, Any]:
        """获取API调用统计"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_calls = [call for call in self._api_calls if call.timestamp >= cutoff_time]
        
        if not recent_calls:
            return {}
        
        # 按端点分组统计
        endpoint_stats = defaultdict(lambda: {
            'count': 0,
            'total_duration': 0,
            'errors': 0,
            'status_codes': defaultdict(int)
        })
        
        for call in recent_calls:
            stats = endpoint_stats[call.endpoint]
            stats['count'] += 1
            stats['total_duration'] += call.duration_ms
            stats['status_codes'][call.status_code] += 1
            
            if call.error or call.status_code >= 400:
                stats['errors'] += 1
        
        # 计算平均值和错误率
        result = {}
        for endpoint, stats in endpoint_stats.items():
            result[endpoint] = {
                'total_calls': stats['count'],
                'avg_duration_ms': stats['total_duration'] / stats['count'],
                'error_rate': stats['errors'] / stats['count'],
                'status_codes': dict(stats['status_codes'])
            }
        
        return result
    
    def get_system_metrics(self) -> Dict[str, float]:
        """获取系统指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            
            # 磁盘使用情况
            disk = psutil.disk_usage('/')
            
            # 网络IO
            network = psutil.net_io_counters()
            
            metrics = {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_used_bytes': memory.used,
                'memory_available_bytes': memory.available,
                'disk_percent': (disk.used / disk.total) * 100,
                'disk_used_bytes': disk.used,
                'disk_free_bytes': disk.free,
                'network_bytes_sent': network.bytes_sent,
                'network_bytes_recv': network.bytes_recv
            }
            
            # 记录系统指标
            for name, value in metrics.items():
                self.record_gauge(f'system_{name}', value)
            
            return metrics
            
        except Exception as e:
            self._logger.warning(f"获取系统指标失败: {e}")
            return {}
    
    def export_metrics(self, format_type: str = 'json') -> str:
        """导出指标数据"""
        with self._lock:
            data = {
                'timestamp': datetime.now().isoformat(),
                'counters': dict(self._counters),
                'gauges': dict(self._gauges),
                'histograms': {k: self.get_histogram_stats(k.split('|')[0], 
                                                         self._parse_tags(k)) 
                              for k in self._histograms.keys()},
                'api_calls': self.get_api_call_stats(),
                'system_metrics': self.get_system_metrics()
            }
            
            if format_type == 'json':
                return json.dumps(data, indent=2, ensure_ascii=False)
            else:
                raise ValueError(f"不支持的格式: {format_type}")
    
    def save_metrics(self, file_path: Path, format_type: str = 'json'):
        """保存指标到文件"""
        content = self.export_metrics(format_type)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        self._logger.info(f"指标已保存到: {file_path}")
    
    def clear_metrics(self):
        """清除所有指标"""
        with self._lock:
            self._metrics.clear()
            self._api_calls.clear()
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
        self._logger.info("所有指标已清除")
    
    def _make_key(self, name: str, tags: Optional[Dict[str, str]]) -> str:
        """生成指标键"""
        if not tags:
            return name
        
        tag_str = '|'.join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}|{tag_str}"
    
    def _parse_tags(self, key: str) -> Optional[Dict[str, str]]:
        """解析标签"""
        if '|' not in key:
            return None
        
        _, tag_str = key.split('|', 1)
        tags = {}
        for tag in tag_str.split('|'):
            if '=' in tag:
                k, v = tag.split('=', 1)
                tags[k] = v
        return tags
    
    def _cleanup_old_metrics(self):
        """清理过期指标"""
        while True:
            try:
                time.sleep(3600)  # 每小时清理一次
                cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
                
                with self._lock:
                    # 清理API调用记录
                    while self._api_calls and self._api_calls[0].timestamp < cutoff_time:
                        self._api_calls.popleft()
                    
                    # 清理指标点
                    for key, points in self._metrics.items():
                        while points and points[0].timestamp < cutoff_time:
                            points.popleft()
                
                self._logger.debug("完成指标清理")
                
            except Exception as e:
                self._logger.error(f"指标清理失败: {e}")

# 全局指标收集器
default_metrics = MetricsCollector()

def monitor_api_call(endpoint: str, method: str = 'GET'):
    """装饰器：监控API调用"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            error = None
            status_code = 200
            
            try:
                result = func(*args, **kwargs)
                
                # 尝试从结果中提取状态码
                if hasattr(result, 'status_code'):
                    status_code = result.status_code
                elif isinstance(result, dict) and 'status_code' in result:
                    status_code = result['status_code']
                
                return result
                
            except Exception as e:
                error = str(e)
                status_code = 500
                raise
                
            finally:
                duration_ms = (time.time() - start_time) * 1000
                
                metric = APICallMetric(
                    endpoint=endpoint,
                    method=method,
                    status_code=status_code,
                    duration_ms=duration_ms,
                    timestamp=datetime.now(),
                    error=error
                )
                
                default_metrics.record_api_call(metric)
        
        return wrapper
    return decorator

def monitor_function(name: Optional[str] = None):
    """装饰器：监控函数执行时间"""
    def decorator(func: Callable) -> Callable:
        metric_name = name or f"function_{func.__name__}_duration"
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            with default_metrics.timer_context(metric_name):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator

class MetricsReporter:
    """指标报告器"""
    
    def __init__(self, collector: MetricsCollector = None):
        self.collector = collector or default_metrics
        self._logger = logging.getLogger(__name__)
    
    def generate_report(self, hours: int = 24) -> str:
        """生成指标报告"""
        report_lines = [
            "=== Coze API 性能报告 ===",
            f"报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"统计周期: 最近 {hours} 小时",
            ""
        ]
        
        # API调用统计
        api_stats = self.collector.get_api_call_stats(hours)
        if api_stats:
            report_lines.append("## API调用统计")
            for endpoint, stats in api_stats.items():
                report_lines.extend([
                    f"### {endpoint}",
                    f"- 总调用次数: {stats['total_calls']}",
                    f"- 平均响应时间: {stats['avg_duration_ms']:.2f}ms",
                    f"- 错误率: {stats['error_rate']:.2%}",
                    f"- 状态码分布: {stats['status_codes']}",
                    ""
                ])
        
        # 系统指标
        system_metrics = self.collector.get_system_metrics()
        if system_metrics:
            report_lines.append("## 系统指标")
            report_lines.extend([
                f"- CPU使用率: {system_metrics.get('cpu_percent', 0):.1f}%",
                f"- 内存使用率: {system_metrics.get('memory_percent', 0):.1f}%",
                f"- 磁盘使用率: {system_metrics.get('disk_percent', 0):.1f}%",
                ""
            ])
        
        # 性能统计
        duration_stats = self.collector.get_histogram_stats('api_call_duration_histogram')
        if duration_stats:
            report_lines.append("## 响应时间分布")
            report_lines.extend([
                f"- 平均值: {duration_stats.get('mean', 0):.2f}ms",
                f"- 50%分位: {duration_stats.get('p50', 0):.2f}ms",
                f"- 90%分位: {duration_stats.get('p90', 0):.2f}ms",
                f"- 95%分位: {duration_stats.get('p95', 0):.2f}ms",
                f"- 99%分位: {duration_stats.get('p99', 0):.2f}ms",
                ""
            ])
        
        return "\n".join(report_lines)
    
    def save_report(self, file_path: Path, hours: int = 24):
        """保存报告到文件"""
        report = self.generate_report(hours)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(report)
        self._logger.info(f"性能报告已保存到: {file_path}")

if __name__ == "__main__":
    # 示例用法
    import random
    
    # 模拟API调用
    @monitor_api_call('/api/chat', 'POST')
    def mock_api_call():
        time.sleep(random.uniform(0.1, 0.5))  # 模拟网络延迟
        if random.random() < 0.1:  # 10%错误率
            raise Exception("API调用失败")
        return {'status_code': 200, 'data': 'success'}
    
    @monitor_function('business_logic')
    def mock_business_logic():
        time.sleep(random.uniform(0.05, 0.2))
        return "处理完成"
    
    # 运行测试
    print("开始性能监控测试...")
    
    for i in range(50):
        try:
            mock_api_call()
            mock_business_logic()
        except Exception:
            pass  # 忽略模拟错误
    
    # 生成报告
    reporter = MetricsReporter()
    report = reporter.generate_report(hours=1)
    print(report)
    
    # 导出指标
    metrics_json = default_metrics.export_metrics()
    print("\n=== 详细指标数据 ===")
    print(metrics_json[:500] + "..." if len(metrics_json) > 500 else metrics_json)