#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
健壮性测试脚本

专门测试coze_connectivity_test_plugin.py在各种边界情况下的表现
确保不会出现'NoneType' object is not callable等错误
"""

import sys
import traceback
from datetime import datetime

# 导入被测试的模块
try:
    from coze_connectivity_test_plugin import handler, _safe_log, CozeConnectivityTester
except ImportError as e:
    print(f"导入错误: {e}")
    sys.exit(1)


class TestScenarios:
    """测试场景集合"""
    
    def __init__(self):
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
    
    def run_test(self, test_name: str, test_func):
        """运行单个测试"""
        self.total_tests += 1
        print(f"\n🧪 测试: {test_name}")
        print("-" * 50)
        
        try:
            result = test_func()
            if result:
                print("✅ 测试通过")
                self.passed_tests += 1
                self.test_results.append((test_name, "PASS", None))
            else:
                print("❌ 测试失败")
                self.test_results.append((test_name, "FAIL", "测试函数返回False"))
        except Exception as e:
            print(f"💥 测试异常: {str(e)}")
            print(f"异常详情: {traceback.format_exc()}")
            self.test_results.append((test_name, "ERROR", str(e)))
    
    def print_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 60)
        print("🎯 测试总结")
        print("=" * 60)
        print(f"总测试数: {self.total_tests}")
        print(f"通过测试: {self.passed_tests}")
        print(f"失败测试: {self.total_tests - self.passed_tests}")
        print(f"成功率: {(self.passed_tests / self.total_tests * 100):.1f}%")
        
        print("\n📋 详细结果:")
        for test_name, status, error in self.test_results:
            status_icon = {"PASS": "✅", "FAIL": "❌", "ERROR": "💥"}[status]
            print(f"{status_icon} {test_name}: {status}")
            if error:
                print(f"   错误: {error}")


class MockArgs:
    """模拟Args对象的各种情况"""
    pass


class BrokenLogger:
    """故意损坏的Logger对象"""
    
    def __init__(self, break_type="none"):
        self.break_type = break_type
    
    def info(self, message):
        if self.break_type == "info_none":
            return None
        elif self.break_type == "info_exception":
            raise Exception("Logger info方法故意抛出异常")
        else:
            print(f"[BROKEN_LOGGER_INFO] {message}")
    
    def error(self, message):
        if self.break_type == "error_none":
            return None
        elif self.break_type == "error_exception":
            raise Exception("Logger error方法故意抛出异常")
        else:
            print(f"[BROKEN_LOGGER_ERROR] {message}")


def test_normal_case():
    """测试正常情况"""
    args = MockArgs()
    args.input = {'test_type': 'basic', 'timeout': 2, 'verbose': False}
    args.logger = None
    
    result = handler(args)
    return result['success'] == True


def test_none_args():
    """测试args为None的情况"""
    try:
        result = handler(None)
        return result['success'] == False  # 应该失败但不崩溃
    except Exception:
        return False  # 不应该抛出异常


def test_args_without_input():
    """测试args没有input属性的情况"""
    args = MockArgs()
    # 故意不设置input属性
    args.logger = None
    
    result = handler(args)
    return result['success'] == True  # 应该使用默认值


def test_args_without_logger():
    """测试args没有logger属性的情况"""
    args = MockArgs()
    args.input = {'test_type': 'basic', 'timeout': 5, 'verbose': False}
    # 故意不设置logger属性
    
    result = handler(args)
    return result['success'] == True


def test_broken_logger_info():
    """测试损坏的logger.info方法"""
    args = MockArgs()
    args.input = {'test_type': 'basic', 'timeout': 5, 'verbose': False}
    args.logger = BrokenLogger("info_exception")
    
    result = handler(args)
    return result['success'] == True  # 应该能处理logger异常


def test_broken_logger_error():
    """测试损坏的logger.error方法"""
    # 直接测试_safe_log函数处理损坏的error方法
    try:
        broken_logger = BrokenLogger("error_exception")
        _safe_log(broken_logger, "测试错误消息", "error")
        return True  # 应该能正确处理损坏的logger.error方法
    except Exception:
        return False  # 不应该抛出异常


def test_none_logger():
    """测试logger为None的情况"""
    args = MockArgs()
    args.input = {'test_type': 'basic', 'timeout': 5, 'verbose': False}
    args.logger = None
    
    result = handler(args)
    return result['success'] == True


def test_non_callable_logger_methods():
    """测试logger方法不可调用的情况"""
    args = MockArgs()
    args.input = {'test_type': 'basic', 'timeout': 5, 'verbose': False}
    
    # 创建一个logger，但其方法不可调用
    class BadLogger:
        info = "not_callable"  # 不是函数
        error = 123  # 不是函数
    
    args.logger = BadLogger()
    
    result = handler(args)
    return result['success'] == True  # 应该回退到print


def test_safe_log_with_none():
    """测试_safe_log函数处理None logger"""
    try:
        _safe_log(None, "测试消息", "info")
        return True
    except Exception:
        return False


def test_safe_log_with_broken_logger():
    """测试_safe_log函数处理损坏的logger"""
    try:
        broken_logger = BrokenLogger("info_exception")
        _safe_log(broken_logger, "测试消息", "info")
        return True
    except Exception:
        return False


def test_connectivity_tester_with_none_logger():
    """测试CozeConnectivityTester处理None logger"""
    try:
        tester = CozeConnectivityTester(logger=None, timeout=5)
        tester.log("测试消息")
        return True
    except Exception:
        return False


def test_connectivity_tester_with_broken_logger():
    """测试CozeConnectivityTester处理损坏的logger"""
    try:
        broken_logger = BrokenLogger("info_exception")
        tester = CozeConnectivityTester(logger=broken_logger, timeout=5)
        tester.log("测试消息")
        return True
    except Exception:
        return False


def test_input_data_edge_cases():
    """测试input数据的边界情况"""
    test_cases = [
        None,  # input为None
        "not_a_dict",  # input不是字典
        [],  # input是列表
        123,  # input是数字
        {},  # input是空字典
    ]
    
    for i, input_data in enumerate(test_cases):
        try:
            args = MockArgs()
            args.input = input_data
            args.logger = None
            
            result = handler(args)
            if not isinstance(result, dict) or 'success' not in result:
                print(f"测试用例 {i} 失败: 返回结果格式错误")
                return False
        except Exception as e:
            print(f"测试用例 {i} 异常: {e}")
            return False
    
    return True


def test_extreme_timeout_values():
    """测试极端的timeout值"""
    extreme_values = [-1, 0, 0.1, 1000, "not_a_number", None]
    
    for timeout_val in extreme_values:
        try:
            args = MockArgs()
            args.input = {'timeout': timeout_val, 'test_type': 'basic', 'verbose': False}
            args.logger = None
            
            result = handler(args)
            if not result.get('success', False):
                # 对于无效timeout，应该使用默认值并成功
                if timeout_val in ["not_a_number", None]:
                    continue  # 这些情况下失败是可以接受的
                else:
                    print(f"Timeout {timeout_val} 测试失败")
                    return False
        except Exception as e:
            print(f"Timeout {timeout_val} 异常: {e}")
            return False
    
    return True


def main():
    """主测试函数"""
    print("🚀 开始健壮性测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    scenarios = TestScenarios()
    
    # 运行所有测试
    scenarios.run_test("正常情况测试", test_normal_case)
    scenarios.run_test("args为None测试", test_none_args)
    scenarios.run_test("缺少input属性测试", test_args_without_input)
    scenarios.run_test("缺少logger属性测试", test_args_without_logger)
    scenarios.run_test("损坏的logger.info测试", test_broken_logger_info)
    scenarios.run_test("损坏的logger.error测试", test_broken_logger_error)
    scenarios.run_test("logger为None测试", test_none_logger)
    scenarios.run_test("不可调用的logger方法测试", test_non_callable_logger_methods)
    scenarios.run_test("_safe_log处理None logger测试", test_safe_log_with_none)
    scenarios.run_test("_safe_log处理损坏logger测试", test_safe_log_with_broken_logger)
    scenarios.run_test("CozeConnectivityTester处理None logger测试", test_connectivity_tester_with_none_logger)
    scenarios.run_test("CozeConnectivityTester处理损坏logger测试", test_connectivity_tester_with_broken_logger)
    scenarios.run_test("input数据边界情况测试", test_input_data_edge_cases)
    scenarios.run_test("极端timeout值测试", test_extreme_timeout_values)
    
    # 打印总结
    scenarios.print_summary()
    
    # 返回是否所有测试都通过
    return scenarios.passed_tests == scenarios.total_tests


if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 所有测试通过！代码具有良好的健壮性。")
        sys.exit(0)
    else:
        print("\n⚠️ 部分测试失败，需要进一步改进。")
        sys.exit(1)