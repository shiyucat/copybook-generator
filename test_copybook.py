#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def find_chinese_fonts():
    font_paths = [
        '/System/Library/Fonts/PingFang.ttc',
        '/System/Library/Fonts/STHeiti Light.ttc',
        '/System/Library/Fonts/STHeiti Medium.ttc',
        '/System/Library/Fonts/Supplemental/Songti.ttc',
        '/System/Library/Fonts/Supplemental/Kaiti.ttc',
    ]
    
    available = []
    for path in font_paths:
        if os.path.exists(path):
            available.append(path)
    return available

def test_font_rendering():
    print("=" * 60)
    print("中文字体测试")
    print("=" * 60)
    print()
    
    fonts = find_chinese_fonts()
    
    if not fonts:
        print("警告：未找到系统中文字体！")
        print("请确保macOS系统安装了中文字体。")
        return None
    
    print(f"找到 {len(fonts)} 个可用字体：")
    for i, f in enumerate(fonts, 1):
        print(f"  {i}. {f}")
    
    selected_font = fonts[0]
    print(f"\n将使用：{selected_font}")
    
    font_name = 'TestChineseFont'
    pdfmetrics.registerFont(TTFont(font_name, selected_font))
    
    return font_name

def test_generate_copybook():
    print("\n" + "=" * 60)
    print("字帖生成测试")
    print("=" * 60)
    print()
    
    test_chars = "一二三四五六七八九十天地人你我他"
    
    font_name = test_font_rendering()
    if not font_name:
        font_name = 'Helvetica'
        print("\n警告：将使用英文字体测试，汉字可能显示为方块。")
    
    output_path = os.path.join(os.getcwd(), "test_copybook.pdf")
    
    c = canvas.Canvas(output_path, pagesize=A4)
    page_width, page_height = A4
    
    from reportlab.lib.units import mm, cm
    
    grid_size = 30 * mm
    margin_left = 1.5 * cm
    margin_top = 2 * cm
    
    chars_per_row = 5
    rows_per_page = 10
    
    usable_width = page_width - 2 * margin_left
    total_grid_width = chars_per_row * grid_size
    start_x = margin_left + (usable_width - total_grid_width) / 2
    
    usable_height = page_height - 2 * margin_top
    total_grid_height = rows_per_page * grid_size
    start_y = page_height - margin_top - total_grid_height
    
    c.setFillColorRGB(0, 0, 0.8)
    c.setFont('Helvetica-Bold', 12)
    title = f"测试字帖 - 汉字：{test_chars[:10]}..."
    c.drawString(margin_left, page_height - margin_top + 10, title)
    
    c.setFillColorRGB(0, 0, 0.6)
    c.setFont('Helvetica', 10)
    info = f"每行{chars_per_row}格 × 每页{rows_per_page}行 = {chars_per_page*rows_per_page}格"
    c.drawString(margin_left, page_height - margin_top - 5, info)
    
    for row in range(rows_per_page):
        for col in range(chars_per_row):
            x = start_x + col * grid_size
            y = start_y + (rows_per_page - 1 - row) * grid_size
            
            if row == 0:
                c.setFillColorRGB(0.95, 0.95, 0.95)
            else:
                c.setFillColorRGB(1.0, 1.0, 1.0)
            c.rect(x, y, grid_size, grid_size, fill=1, stroke=0)
            
            c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.setLineWidth(0.5)
            c.rect(x, y, grid_size, grid_size, fill=0, stroke=1)
            
            c.setStrokeColorRGB(0.5, 0.5, 0.5)
            c.setLineWidth(0.3)
            center_x = x + grid_size / 2
            center_y = y + grid_size / 2
            c.line(center_x, y, center_x, y + grid_size)
            c.line(x, center_y, x + grid_size, center_y)
            
            c.setLineWidth(0.3, dash=[2, 2])
            c.line(x, y, x + grid_size, y + grid_size)
            c.line(x, y + grid_size, x + grid_size, y)
            c.setDash([])
            
            char_idx = row * chars_per_row + col
            if char_idx < len(test_chars):
                char = test_chars[char_idx]
                
                if row == 0:
                    c.setFillColorRGB(0.3, 0.3, 0.3)
                else:
                    c.setFillColorRGB(0.0, 0.0, 0.0)
                
                font_size = grid_size * 0.8
                c.setFont(font_name, font_size)
                
                text_width = c.stringWidth(char, font_name, font_size)
                char_x = x + (grid_size - text_width) / 2
                char_y = y + (grid_size - font_size * 0.8) / 2
                
                c.drawString(char_x, char_y, char)
    
    c.save()
    
    print(f"\n测试字帖已生成：{output_path}")
    print(f"包含汉字：{test_chars}")
    print()
    
    return output_path

if __name__ == "__main__":
    test_generate_copybook()
