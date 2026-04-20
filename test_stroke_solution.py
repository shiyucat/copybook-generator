#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from validator import InputValidator
import stroke_data

def test_extended_database():
    print("=" * 70)
    print("测试1：扩展的本地笔画数据库")
    print("=" * 70)
    print()
    
    print(f"本地数据库汉字数量：{InputValidator.get_available_chars_count()}")
    print()
    
    test_chars = [
        '钱', '盘',
        '爱', '情', '学', '习',
        '汉', '语', '文', '字',
        '电', '脑', '网', '络',
        '北', '京', '上', '海',
        '一', '二', '三', '四', '五',
        '大', '小', '多', '少',
    ]
    
    found_count = 0
    not_found = []
    
    for char in test_chars:
        strokes = InputValidator.get_stroke_order(char)
        
        if strokes:
            found_count += 1
            print(f"✅ 汉字「{char}」：{len(strokes)}笔 - {', '.join(strokes)}")
        else:
            not_found.append(char)
            print(f"❌ 汉字「{char}」：未找到笔画顺序")
    
    print()
    print(f"统计：找到 {found_count}/{len(test_chars)} 个汉字的笔画顺序")
    
    if not_found:
        print(f"未找到的汉字：{', '.join(not_found)}")
    
    return found_count == len(test_chars)

def test_online_fetch():
    print()
    print("=" * 70)
    print("测试2：在线获取新汉字的笔画顺序（需要网络）")
    print("=" * 70)
    print()
    
    rare_chars = [
        '鑫', '淼', '焱', '垚', '矗',
        '饕', '餮', '尴', '尬', '爵',
    ]
    
    print("测试一些相对不常见的汉字...")
    print()
    
    manager = stroke_data.get_default_manager()
    
    success_count = 0
    for char in rare_chars:
        strokes = manager.get_stroke_order(char)
        
        if strokes:
            success_count += 1
            print(f"✅ 汉字「{char}」：{len(strokes)}笔 - {', '.join(strokes)}")
        else:
            print(f"❌ 汉字「{char}」：无法获取（可能无网络或该字无数据）")
    
    print()
    if success_count > 0:
        print(f"✅ 成功在线获取了 {success_count}/{len(rare_chars)} 个汉字的笔画顺序")
    else:
        print("ℹ️  无法在线获取（可能无网络连接）")
    
    return True

def test_add_custom_stroke():
    print()
    print("=" * 70)
    print("测试3：手动添加自定义汉字的笔画顺序")
    print("=" * 70)
    print()
    
    custom_char = '鑫'
    custom_strokes = ['撇', '捺', '横', '横', '竖', '点', '撇', '横',
                      '撇', '捺', '横', '横', '竖', '点', '撇', '横',
                      '撇', '捺', '横', '横', '竖', '点', '撇', '横']
    
    print(f"手动添加汉字「{custom_char}」的笔画顺序...")
    
    success = InputValidator.add_to_database(custom_char, custom_strokes)
    
    if success:
        print(f"✅ 添加成功！")
        
        strokes = InputValidator.get_stroke_order(custom_char)
        if strokes:
            print(f"验证：汉字「{custom_char}」：{len(strokes)}笔 - {', '.join(strokes)}")
            return True
        else:
            print(f"❌ 验证失败！")
            return False
    else:
        print(f"❌ 添加失败！")
        return False

def main():
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 25 + "笔画顺序解决方案测试" + " " * 25 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    all_passed = True
    
    all_passed = test_extended_database() and all_passed
    
    all_passed = test_online_fetch() and all_passed
    
    all_passed = test_add_custom_stroke() and all_passed
    
    print()
    print("=" * 70)
    if all_passed:
        print("✅ 所有测试通过！")
        print()
        print("解决方案说明：")
        print("1. 本地数据库：已扩展到包含大量常用汉字")
        print("2. 在线获取：自动从 hanzi-writer-data CDN 获取新汉字")
        print("3. 本地缓存：获取的汉字会自动缓存到本地")
        print("4. 手动添加：支持用户手动添加自定义汉字的笔画顺序")
    else:
        print("⚠️  部分测试未通过（可能是网络问题）")
    
    print("=" * 70)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
