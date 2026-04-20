#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from validator import InputValidator
from layout import PageLayout
import config

def test_full_workflow():
    print("=" * 60)
    print("完整流程测试")
    print("=" * 60)
    print()
    
    test_chars = "一二三四五六七八九十"
    
    print(f"测试汉字：{test_chars}")
    print()
    
    validator = InputValidator()
    is_valid, result = validator.validate_characters(test_chars)
    
    if not is_valid:
        print(f"验证失败：{result}")
        return False
    
    print(f"验证通过：{result}")
    
    output_path = os.path.join(os.path.dirname(__file__), "quick_test_output.pdf")
    
    print(f"\n注册中文字体...")
    config.register_chinese_font()
    
    print(f"\n生成字帖：{output_path}")
    
    layout = PageLayout(output_path)
    total_pages = layout.render_all_pages(result)
    
    print(f"\n生成完成！")
    print(f"总页数：{total_pages}")
    print(f"输出文件：{output_path}")
    
    if os.path.exists(output_path):
        file_size = os.path.getsize(output_path)
        print(f"文件大小：{file_size} 字节")
        print()
        print("=" * 60)
        print("测试成功！")
        print("=" * 60)
        return True
    else:
        print("错误：文件未生成！")
        return False

if __name__ == "__main__":
    success = test_full_workflow()
    sys.exit(0 if success else 1)
