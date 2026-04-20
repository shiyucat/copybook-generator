#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from validator import InputValidator
from layout import PageLayout
import config

def test_stroke_orders():
    print("=" * 60)
    print("测试'钱'和'盘'的笔画顺序")
    print("=" * 60)
    print()
    
    validator = InputValidator()
    
    test_chars = ['钱', '盘']
    
    for char in test_chars:
        print(f"汉字：「{char}」")
        
        strokes = validator.get_stroke_order(char)
        
        if strokes:
            print(f"笔画数：{len(strokes)} 笔")
            print("笔画顺序：")
            for idx, stroke in enumerate(strokes, 1):
                print(f"  第{idx}笔：{stroke}")
        else:
            print(f"错误：未找到「{char}」的笔画顺序！")
            return False
        
        print()
    
    print("=" * 60)
    print("笔画顺序测试通过！")
    print("=" * 60)
    print()
    
    return True

def test_generate_copybook_with_qian_pan():
    print("=" * 60)
    print("生成包含'钱'和'盘'的字帖")
    print("=" * 60)
    print()
    
    test_chars = "钱盘一二三四五六七八九十"
    
    print(f"测试汉字：{test_chars}")
    print()
    
    validator = InputValidator()
    is_valid, result = validator.validate_characters(test_chars)
    
    if not is_valid:
        print(f"验证失败：{result}")
        return False
    
    output_path = os.path.join(os.path.dirname(__file__), "test_qian_pan_output.pdf")
    
    print(f"注册中文字体...")
    config.register_chinese_font()
    
    print(f"生成字帖：{output_path}")
    
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
        print("字帖生成测试通过！")
        print("=" * 60)
        return True
    else:
        print("错误：文件未生成！")
        return False

if __name__ == "__main__":
    success = test_stroke_orders()
    
    if success:
        success = test_generate_copybook_with_qian_pan()
    
    sys.exit(0 if success else 1)
