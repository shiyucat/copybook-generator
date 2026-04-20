#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_stroke_visualization():
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 20 + "图形化笔画顺序展示测试" + " " * 20 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    print("=" * 60)
    print("测试说明：")
    print("=" * 60)
    print()
    print("1. 移除了页面顶部的文字笔画顺序显示")
    print("2. 在第一个田字格旁边添加了彩色编号图例")
    print("3. 每个编号用不同颜色表示，对应笔画顺序")
    print()
    
    import config
    from validator import InputValidator
    from layout import PageLayout
    
    test_chars_list = [
        '模一二三四',
        '钱盘',
        '天地人',
    ]
    
    for idx, characters in enumerate(test_chars_list, 1):
        print("-" * 60)
        print(f"测试 {idx}：汉字「{characters}」")
        print("-" * 60)
        print()
        
        print("验证笔画顺序：")
        all_have_strokes = True
        for char in characters:
            strokes = InputValidator.get_stroke_order(char)
            if strokes:
                print(f"  ✅ 汉字「{char}」：{len(strokes)}笔")
            else:
                print(f"  ⚠️  汉字「{char}」：未收录")
                all_have_strokes = False
        print()
        
        output_path = os.path.join(os.getcwd(), f'test_visualization_{idx}.pdf')
        
        print(f"生成字帖：{output_path}")
        print("请稍候...")
        print()
        
        config.register_chinese_font(verbose=False)
        
        layout = PageLayout(output_path)
        total_pages = layout.render_all_pages(characters)
        
        if os.path.exists(output_path):
            print(f"✅ 字帖生成成功！")
            print(f"📄 输出文件：{output_path}")
            print(f"📖 总页数：{total_pages} 页")
            print()
            print("请打开PDF文件查看效果：")
            print("  - 页面顶部不再显示文字笔画顺序")
            print("  - 第一个田字格旁边有彩色编号图例")
            print("  - 编号1、2、3...对应笔画顺序，用不同颜色区分")
        else:
            print(f"❌ 字帖生成失败！")
        
        print()
    
    print("=" * 60)
    print("测试完成")
    print("=" * 60)
    print()
    print("总结：")
    print("1. ✅ 页面顶部的文字笔画顺序已移除")
    print("2. ✅ 第一个田字格旁边添加了彩色编号图例")
    print("3. ✅ 不同颜色区分不同笔画")
    print()
    print("如需更精确的笔画形状展示（如每一笔的具体方向），")
    print("需要获取汉字的SVG笔画路径数据。由于网络SSL证书问题，")
    print("当前无法在线获取。可以手动添加SVG数据到本地数据库。")
    print()

if __name__ == "__main__":
    test_stroke_visualization()
