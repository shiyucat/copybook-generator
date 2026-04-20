#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from validator import InputValidator
from layout import PageLayout
import config

def main():
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 25 + "田字格字帖生成器" + " " * 25 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    validator = InputValidator()
    print(f"📚 本地笔画数据库已收录：{InputValidator.get_available_chars_count()} 个汉字")
    print()
    
    print("=" * 60)
    print("功能说明：")
    print("=" * 60)
    print("1. 字帖格式：A4纸张，田字格布局")
    print("2. 每行5个汉字，每页10行")
    print("3. 页面顶部显示第一个字的笔画顺序")
    print("4. 第一行田字格用浅色底展示汉字，便于临摹")
    print("5. 支持自动从网络获取新汉字的笔画顺序（可选）")
    print()
    
    if len(sys.argv) > 1:
        input_chars = ' '.join(sys.argv[1:])
    else:
        input_chars = input("请输入需要生成字帖的汉字（多个汉字连续输入）：")
    
    is_valid, result = validator.validate_characters(input_chars)
    
    if not is_valid:
        print()
        print("!" * 60)
        print("❌ 输入验证失败！")
        print(f"错误原因：{result}")
        print("!" * 60)
        print()
        print("正确输入示例：")
        print("  输入单个字：一")
        print("  输入多个字：一二三四五六七八九十")
        print("  输入常用字：天地人你我他")
        return 1
    
    characters = result
    
    print()
    print(f"✅ 验证通过！共 {len(characters)} 个汉字：{characters}")
    print()
    
    print("检查汉字笔画顺序状态...")
    found_strokes = []
    missing_strokes = []
    
    for char in characters:
        strokes = validator.get_stroke_order(char)
        if strokes:
            found_strokes.append(char)
        else:
            missing_strokes.append(char)
    
    print()
    if found_strokes:
        print(f"✅ 已找到笔画顺序：{len(found_strokes)} 个 - {''.join(found_strokes)}")
    if missing_strokes:
        print(f"⚠️  未找到笔画顺序：{len(missing_strokes)} 个 - {''.join(missing_strokes)}")
        print()
        print("💡 解决方案：")
        print("   1. 这些汉字的笔画顺序会在字帖中显示为「未收录」")
        print("   2. 您可以手动添加笔画顺序：")
        for char in missing_strokes:
            print(f"      InputValidator.add_to_database('{char}', ['笔画1', '笔画2', ...])")
        print("   3. 或编辑 stroke_data.py 中的 LOCAL_STROKE_DATABASE 字典")
    print()
    
    output_filename = input(f"请输入输出PDF文件名（默认：copybook.pdf）：") or "copybook.pdf"
    
    if not output_filename.lower().endswith('.pdf'):
        output_filename += '.pdf'
    
    output_path = os.path.join(os.getcwd(), output_filename)
    
    print()
    print(f"正在生成字帖：{output_path}")
    print("请稍候...")
    
    try:
        config.register_chinese_font()
        
        layout = PageLayout(output_path)
        total_pages = layout.render_all_pages(characters)
        
        print()
        print("=" * 60)
        print("🎉 字帖生成成功！")
        print("=" * 60)
        print(f"📄 输出文件：{output_path}")
        print(f"📖 总页数：{total_pages} 页")
        print(f"🔤 汉字数量：{len(characters)} 个")
        print(f"📐 每页格式：{config.GRID_PER_ROW}列 × {config.GRID_PER_COL}行 = {config.GRID_PER_ROW * config.GRID_PER_COL}格")
        print()
        
        first_char = characters[0]
        stroke_order = validator.get_stroke_order(first_char)
        
        if stroke_order:
            print(f"📝 首个汉字「{first_char}」的笔画顺序（已显示在字帖第一页顶部）：")
            for idx, stroke in enumerate(stroke_order, 1):
                print(f"   第{idx}笔：{stroke}")
        else:
            print(f"ℹ️  汉字「{first_char}」的笔画顺序未收录")
            print("   字帖第一页顶部会显示「未收录」提示及添加方法")
        print()
        
        return 0
        
    except Exception as e:
        print()
        print("!" * 60)
        print("❌ 字帖生成失败！")
        print(f"错误信息：{e}")
        print("!" * 60)
        print()
        print("可能的原因：")
        print("1. 中文字体未找到。请确保系统安装了中文字体。")
        print("2. 可以在 config.py 中设置 FONT_PATH 指定具体的字体文件路径。")
        print()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
