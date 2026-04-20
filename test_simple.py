#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 50)
print("开始测试：只测试获取'模'的笔画顺序")
print("=" * 50)
print()

print("--- 开始导入模块 ---")
from validator import InputValidator
print("--- 模块导入完成 ---")
print()

print("--- 开始获取笔画顺序 ---")
strokes = InputValidator.get_stroke_order('模')
print("--- 获取完成 ---")
print()

print("--- 输出结果 ---")
if strokes:
    print(f"汉字「模」的笔画顺序：{len(strokes)}笔")
    print(f"笔画：{', '.join(strokes)}")
else:
    print(f"汉字「模」：未找到笔画顺序")
print("--- 输出结束 ---")
print()

print("=" * 50)
print("测试结束")
print("=" * 50)
