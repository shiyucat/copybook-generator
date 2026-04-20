#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from validator import InputValidator

def test_validator():
    print("=" * 60)
    print("输入验证功能测试")
    print("=" * 60)
    print()
    
    test_cases = [
        ("", "空输入"),
        ("   ", "只有空格"),
        ("abc", "英文字符"),
        ("123", "数字"),
        ("一", "单个汉字"),
        ("一二三四", "多个汉字"),
        ("天地人你我他", "常用汉字"),
        ("一b二", "混合字符"),
        ("  一二三  ", "带前后空格"),
    ]
    
    validator = InputValidator()
    
    for input_str, description in test_cases:
        print(f"测试用例: {description}")
        print(f"输入内容: '{input_str}'")
        
        is_valid, result = validator.validate_characters(input_str)
        
        if is_valid:
            print(f"状态: 验证通过")
            print(f"处理后: '{result}'")
        else:
            print(f"状态: 验证失败")
            print(f"错误信息: {result}")
        
        print("-" * 60)
        print()
    
    print("=" * 60)
    print("笔画顺序测试")
    print("=" * 60)
    print()
    
    stroke_test_chars = ['一', '二', '三', '十', '大', '小', '人', '口', '日', '月', '水', '火', '木', '金']
    
    for char in stroke_test_chars:
        strokes = validator.get_stroke_order(char)
        if strokes:
            print(f"汉字「{char}」的笔画顺序：")
            for idx, stroke in enumerate(strokes, 1):
                print(f"  第{idx}笔：{stroke}")
        else:
            print(f"汉字「{char}」：未收录笔画顺序")
        print()

if __name__ == "__main__":
    test_validator()
