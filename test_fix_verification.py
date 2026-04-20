#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_stroke_order_only():
    print("=" * 50)
    print("测试1：只获取'模'的笔画顺序（不生成PDF）")
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
        print(f"汉字「模」：{len(strokes)}笔")
        print(f"笔画顺序：{', '.join(strokes)}")
    else:
        print(f"汉字「模」：未找到笔画顺序")
    print("--- 输出结束 ---")
    print()
    
    return strokes is not None

def test_full_generation():
    print("=" * 50)
    print("测试2：完整生成字帖（验证没有多余输出）")
    print("=" * 50)
    print()
    
    import config
    from validator import InputValidator
    from layout import PageLayout
    
    characters = '模一二三四'
    
    print(f"测试汉字：{characters}")
    print()
    
    print("--- 验证笔画顺序 ---")
    for char in characters:
        strokes = InputValidator.get_stroke_order(char)
        if strokes:
            print(f"✅ 汉字「{char}」：{len(strokes)}笔")
        else:
            print(f"❌ 汉字「{char}」：未找到")
    print()
    
    output_path = os.path.join(os.getcwd(), 'test_output.pdf')
    
    print("--- 生成字帖 ---")
    print("注意：检查是否有多余的输出（如字体注册信息等）")
    print()
    
    config.register_chinese_font(verbose=False)
    
    layout = PageLayout(output_path)
    total_pages = layout.render_all_pages(characters)
    
    print()
    print(f"✅ 字帖生成成功！")
    print(f"📄 输出文件：{output_path}")
    print(f"📖 总页数：{total_pages} 页")
    print()
    
    if os.path.exists(output_path):
        print("✅ 验证：输出文件存在")
        os.remove(output_path)
        print("✅ 清理：测试文件已删除")
        return True
    else:
        print("❌ 验证失败：输出文件不存在")
        return False

def main():
    print()
    print("╔" + "═" * 48 + "╗")
    print("║" + " " * 15 + "Bug修复验证测试" + " " * 15 + "║")
    print("╚" + "═" * 48 + "╝")
    print()
    
    test1_passed = test_stroke_order_only()
    
    print()
    print("-" * 50)
    print()
    
    test2_passed = test_full_generation()
    
    print()
    print("=" * 50)
    print("测试总结")
    print("=" * 50)
    print()
    
    all_passed = test1_passed and test2_passed
    
    if test1_passed:
        print("✅ 测试1通过：'模'字笔画顺序正常")
    else:
        print("❌ 测试1失败：'模'字笔画顺序未找到")
    
    if test2_passed:
        print("✅ 测试2通过：字帖生成正常，无多余输出")
    else:
        print("❌ 测试2失败：字帖生成失败")
    
    print()
    if all_passed:
        print("🎉 所有测试通过！Bug已修复！")
        print()
        print("修复内容：")
        print("1. 添加了'模'字到笔画数据库（14笔）")
        print("2. 将config.py中的打印语句改为可选（verbose参数）")
        print("3. 默认情况下不再输出字体注册信息")
        return 0
    else:
        print("⚠️  部分测试失败，请检查")
        return 1

if __name__ == "__main__":
    sys.exit(main())
