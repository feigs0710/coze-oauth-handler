#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终健壮性测试 - 专注于边界情况和错误处理
"""

import sys
sys.path.append('.')

from coze_connectivity_test_plugin import handler, _safe_log, CozeConnectivityTester
from datetime import datetime

class BrokenLogger:
    """故意损坏的Logger对象"""
    
    def __init__(self, break_type="none"):
        self.break_type = break_type
    
    def info(self, message):
        if self.break_type == "info_exception":
            raise Exception("Logger info方法故意抛出异常")
        else:
            print(f"[BROKEN_LOGGER_INFO] {message}")
    
    def error(self, message):
        if self.break_type == "error_exception":
            raise Exception("Logger error方法故意抛出异常")
        else:
            print(f"[BROKEN_LOGGER_ERROR] {message}")

class MockArgs:
    """模拟Args对象"""
    pass

def test_none_args():
    """测试args为None的情况"""
    try:
        result = handler(None)
        return result['success'] == False and 'error' in result
    except Exception:
        return False

def test_args_without_input():
    """测试args没有input属性的情况"""
    args = MockArgs()
    args.logger = None
    result = handler(args)
    return result['success'] == True

def test_args_without_logger():
    """测试args没有logger属性的情况"""
    args = MockArgs()
    args.input = {'test_type': 'basic', 'timeout': 1, 'verbose': False}
    result = handler(args)
    return result['success'] == True

def test_broken_logger_info():
    """测试损坏的logger.info方法"""
    args = MockArgs()
    args.input = {'test_type': 'basic', 'timeout': 1, 'verbose': False}
    args.logger = BrokenLogger("info_exception")
    result = handler(args)
    return result['success'] == True

def test_broken_logger_error():
    """测试损坏的logger.error方法"""
    try:
        broken_logger = BrokenLogger("error_exception")
        _safe_log(broken_logger, "测试错误消息", "error")
        return True
    except Exception:
        return False

def test_none_logger():
    """测试logger为None的情况"""
    args = MockArgs()
    args.input = {'test_type': 'basic', 'timeout': 1, 'verbose': False}
    args.logger = None
    result = handler(args)
    return result['success'] == True

def test_non_callable_logger_methods():
    """测试logger方法不可调用的情况"""
    args = MockArgs()
    args.input = {'test_type': 'basic', 'timeout': 1, 'verbose': False}
    
    class BadLogger:
        info = "not_callable"
        error = 123
    
    args.logger = BadLogger()
    result = handler(args)
    return result['success'] == True

def test_safe_log_functions():
    """测试_safe_log函数的各种情况"""
    try:
        # 测试None logger
        _safe_log(None, "测试消息1", "info")
        
        # 测试损坏的logger
        broken_logger = BrokenLogger("info_exception")
        _safe_log(broken_logger, "测试消息2", "info")
        
        # 测试损坏的error方法
        broken_error_logger = BrokenLogger("error_exception")
        _safe_log(broken_error_logger, "测试消息3", "error")
        
        return True
    except Exception:
        return False

def test_input_data_edge_cases():
    """测试input数据的边界情况"""
    test_cases = [
        None,
        "not_a_dict",
        [],
        123,
        {},
    ]
    
    for input_data in test_cases:
        try:
            args = MockArgs()
            args.input = input_data
            args.logger = None
            
            result = handler(args)
            if not isinstance(result, dict) or 'success' not in result:
                return False
        except Exception:
            return False
    
    return True

def test_extreme_timeout_values():
    """测试极端的timeout值"""
    extreme_values = [-1, 0, 0.1, "not_a_number", None]
    
    for timeout_val in extreme_values:
        try:
            args = MockArgs()
            args.input = {'timeout': timeout_val, 'test_type': 'basic', 'verbose': False}
            args.logger = None
            
            result = handler(args)
            if not isinstance(result, dict) or 'success' not in result:
                return False
        except Exception:
            return False
    
    return True

def main():
    """主测试函数"""
    print("🚀 最终健壮性测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    tests = [
        ("args为None测试", test_none_args),
        ("缺少input属性测试", test_args_without_input),
        ("缺少logger属性测试", test_args_without_logger),
        ("损坏的logger.info测试", test_broken_logger_info),
        ("损坏的logger.error测试", test_broken_logger_error),
        ("logger为None测试", test_none_logger),
        ("不可调用的logger方法测试", test_non_callable_logger_methods),
        ("_safe_log函数测试", test_safe_log_functions),
        ("input数据边界情况测试", test_input_data_edge_cases),
        ("极端timeout值测试", test_extreme_timeout_values),
    ]
    
    passed = 0
    total = len(tests)
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            status = "✅ 通过" if success else "❌ 失败"
            results.append((test_name, success, None))
            if success:
                passed += 1
        except Exception as e:
            results.append((test_name, False, str(e)))
            status = f"💥 异常: {e}"
        
        print(f"{status} {test_name}")
    
    print("\n" + "=" * 60)
    print("🎯 测试总结")
    print("=" * 60)
    print(f"总测试数: {total}")
    print(f"通过测试: {passed}")
    print(f"失败测试: {total - passed}")
    print(f"成功率: {(passed / total * 100):.1f}%")
    
    if passed == total:
        print("\n🎉 所有测试通过！代码具有良好的健壮性。")
        return True
    else:
        print("\n⚠️ 部分测试失败，需要进一步改进。")
        for test_name, success, error in results:
            if not success:
                print(f"   ❌ {test_name}: {error or '测试函数返回False'}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)