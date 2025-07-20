#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试脚本 - 验证关键修复
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
    print("🧪 测试: args为None")
    try:
        result = handler(None)
        success = result['success'] == False and 'error' in result
        print(f"   结果: {'✅ 通过' if success else '❌ 失败'}")
        return success
    except Exception as e:
        print(f"   结果: ❌ 异常 - {e}")
        return False

def test_broken_logger_error():
    """测试损坏的logger.error方法"""
    print("🧪 测试: 损坏的logger.error")
    
    # 直接测试_safe_log函数处理损坏的error方法
    try:
        broken_logger = BrokenLogger("error_exception")
        _safe_log(broken_logger, "测试错误消息", "error")
        print("   结果: ✅ 通过 - _safe_log正确处理了损坏的logger.error")
        return True
    except Exception as e:
        print(f"   结果: ❌ 异常 - {e}")
        return False

def test_safe_log():
    """测试_safe_log函数"""
    print("🧪 测试: _safe_log函数")
    try:
        # 测试None logger
        _safe_log(None, "测试消息1", "info")
        
        # 测试损坏的logger
        broken_logger = BrokenLogger("info_exception")
        _safe_log(broken_logger, "测试消息2", "info")
        
        print("   结果: ✅ 通过")
        return True
    except Exception as e:
        print(f"   结果: ❌ 异常 - {e}")
        return False

def main():
    print("🚀 快速健壮性测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    tests = [
        test_none_args,
        test_broken_logger_error,
        test_safe_log
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        if test_func():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有关键测试通过！")
        return True
    else:
        print("⚠️ 部分测试失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)