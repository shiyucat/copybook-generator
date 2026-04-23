#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
字帖生成器
生成田字格格式的字帖，包含笔画步骤展示和描红功能
"""

import sys
import os
import json
from typing import List, Tuple, Optional
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color, black, gray
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


class CopybookGenerator:
    """字帖生成器类"""
    
    def __init__(self, 
                 paper_size: Tuple[float, float] = A4,
                 grid_cols: int = 5,
                 grid_rows: int = 10,
                 font_size: int = 48,
                 font_path: Optional[str] = None):
        """
        初始化字帖生成器
        
        Args:
            paper_size: 纸张大小，默认A4
            grid_cols: 每行田字格数量，默认5个
            grid_rows: 每页田字格行数，默认10行
            font_size: 字体大小，默认48点
            font_path: 字体文件路径，默认使用系统字体
        """
        self.paper_width, self.paper_height = paper_size
        self.grid_cols = grid_cols
        self.grid_rows = grid_rows
        self.font_size = font_size
        
        self.margin_left = 20 * mm
        self.margin_right = 20 * mm
        self.margin_top = 30 * mm
        self.margin_bottom = 20 * mm
        
        self.stroke_section_height = 40 * mm
        
        self._init_font(font_path)
        self._calculate_grid_dimensions()
        self._load_stroke_data()
    
    def _init_font(self, font_path: Optional[str]):
        """初始化字体"""
        self.font_name = "Helvetica"
        
        if font_path and os.path.exists(font_path):
            try:
                font_name = "CustomFont"
                pdfmetrics.registerFont(TTFont(font_name, font_path))
                self.font_name = font_name
                return
            except:
                pass
        
        chinese_fonts = [
            ("/System/Library/Fonts/STHeiti Light.ttc", "STHeitiLight"),
            ("/System/Library/Fonts/STHeiti Medium.ttc", "STHeitiMedium"),
            ("/System/Library/Fonts/Hiragino Sans GB.ttc", "HiraginoSansGB"),
            ("/System/Library/Fonts/ヒラギノ明朝 ProN.ttc", "HiraginoMincho"),
            ("/System/Library/Fonts/ヒラギノ丸ゴ ProN W4.ttc", "HiraginoMaruGothic"),
        ]
        
        for font_path, font_name in chinese_fonts:
            try:
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                    self.font_name = font_name
                    return
            except:
                continue
        
        self.font_name = "Helvetica"
    
    def _calculate_grid_dimensions(self):
        """计算田字格尺寸"""
        usable_width = self.paper_width - self.margin_left - self.margin_right
        usable_height = self.paper_height - self.margin_top - self.margin_bottom - self.stroke_section_height
        
        self.grid_size = min(
            usable_width / self.grid_cols,
            usable_height / self.grid_rows
        )
        
        self.grid_padding = (usable_width - self.grid_size * self.grid_cols) / 2
    
    def _load_stroke_data(self):
        """加载笔画数据"""
        self.stroke_data = {}
        stroke_data_path = Path(__file__).parent / "stroke_data" / "strokes.json"
        
        if stroke_data_path.exists():
            try:
                with open(stroke_data_path, 'r', encoding='utf-8') as f:
                    self.stroke_data = json.load(f)
            except Exception as e:
                print(f"加载笔画数据失败: {e}")
    
    def validate_input(self, character: str) -> Tuple[bool, str]:
        """
        验证输入是否有效
        
        Args:
            character: 输入的字符
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        if not character:
            return False, "输入不能为空"
        
        if len(character) != 1:
            return False, f"只能输入单个汉字，当前输入了{len(character)}个字符"
        
        if not ('\u4e00' <= character <= '\u9fff'):
            return False, "输入不是有效的汉字"
        
        return True, ""
    
    def _draw_grid(self, c: canvas.Canvas, x: float, y: float, 
                   is_highlight: bool = False, character: str = ""):
        """
        绘制单个田字格
        
        Args:
            c: PDF画布对象
            x: 田字格左下角x坐标
            y: 田字格左下角y坐标
            is_highlight: 是否为高亮模式（第一行）
            character: 要显示的汉字
        """
        grid_size = self.grid_size
        
        c.setStrokeColor(gray)
        c.setLineWidth(1)
        
        c.rect(x, y, grid_size, grid_size)
        
        c.setStrokeColor(Color(0.8, 0.8, 0.8))
        c.setLineWidth(0.5)
        
        c.line(x, y + grid_size/2, x + grid_size, y + grid_size/2)
        c.line(x + grid_size/2, y, x + grid_size/2, y + grid_size)
        c.line(x, y, x + grid_size, y + grid_size)
        c.line(x + grid_size, y, x, y + grid_size)
        
        c.setStrokeColor(gray)
        c.setLineWidth(1)
        
        if character and is_highlight:
            c.setFillColor(Color(0.95, 0.95, 0.95))
            c.rect(x, y, grid_size, grid_size, fill=1, stroke=0)
            
            c.setFillColor(Color(0.7, 0.7, 0.7))
            c.setFont(self.font_name, self.font_size)
            
            text_width = c.stringWidth(character, self.font_name, self.font_size)
            text_x = x + (grid_size - text_width) / 2
            text_y = y + (grid_size - self.font_size) / 2 + 5
            
            c.drawString(text_x, text_y, character)
            
            c.setStrokeColor(gray)
            c.setLineWidth(1)
            c.rect(x, y, grid_size, grid_size)
    
    def _draw_stroke_demonstration(self, c: canvas.Canvas, character: str, 
                                    x: float, y: float):
        """
        绘制笔画步骤展示
        
        Args:
            c: PDF画布对象
            character: 汉字
            x: 左下角x坐标
            y: 左下角y坐标
        """
        strokes = self.stroke_data.get(character, [])
        
        if not strokes:
            strokes = [f"第{i+1}笔" for i in range(8)]
        
        section_width = self.paper_width - self.margin_left - self.margin_right
        section_height = self.stroke_section_height
        
        c.setStrokeColor(gray)
        c.setLineWidth(1)
        c.rect(x, y, section_width, section_height)
        
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(black)
        title = f"汉字：{character}  笔画顺序"
        title_width = c.stringWidth(title, "Helvetica-Bold", 14)
        c.drawString(x + (section_width - title_width) / 2, 
                     y + section_height - 10 * mm, 
                     title)
        
        num_strokes = len(strokes)
        max_strokes_per_row = 8
        box_size = min(25 * mm, (section_width - 20 * mm) / max_strokes_per_row)
        
        for i, stroke in enumerate(strokes):
            row = i // max_strokes_per_row
            col = i % max_strokes_per_row
            
            box_x = x + 10 * mm + col * box_size
            box_y = y + section_height - 25 * mm - row * 30 * mm
            
            if box_y < y + 5 * mm:
                break
            
            c.setStrokeColor(gray)
            c.setLineWidth(1)
            c.rect(box_x, box_y, box_size, box_size)
            
            c.setFillColor(black)
            c.setFont("Helvetica", 10)
            order_text = f"{i+1}"
            order_width = c.stringWidth(order_text, "Helvetica", 10)
            c.drawString(box_x + (box_size - order_width) / 2, 
                         box_y + box_size - 8, 
                         order_text)
            
            c.setFont(self.font_name, 24)
            char_width = c.stringWidth(character, self.font_name, 24)
            c.drawString(box_x + (box_size - char_width) / 2, 
                         box_y + 8, 
                         character)
    
    def _draw_page(self, c: canvas.Canvas, character: str, page_num: int):
        """
        绘制单页字帖
        
        Args:
            c: PDF画布对象
            character: 汉字
            page_num: 页码
        """
        for row in range(self.grid_rows):
            for col in range(self.grid_cols):
                x = self.margin_left + self.grid_padding + col * self.grid_size
                y = self.paper_height - self.margin_top - (row + 1) * self.grid_size
                
                is_highlight = (row == 0)
                self._draw_grid(c, x, y, is_highlight=is_highlight, 
                               character=character if is_highlight else "")
        
        self._draw_stroke_demonstration(c, character, 
                                        self.margin_left, 
                                        self.margin_bottom)
        
        c.setFont("Helvetica", 10)
        c.setFillColor(gray)
        footer_text = f"第 {page_num} 页"
        c.drawString(self.margin_left, 10 * mm, footer_text)
    
    def generate(self, character: str, output_path: str, 
                 num_pages: int = 1) -> Tuple[bool, str]:
        """
        生成字帖
        
        Args:
            character: 要生成的汉字
            output_path: 输出PDF文件路径
            num_pages: 生成页数
            
        Returns:
            Tuple[bool, str]: (是否成功, 错误信息)
        """
        is_valid, error_msg = self.validate_input(character)
        if not is_valid:
            return False, error_msg
        
        try:
            c = canvas.Canvas(output_path, pagesize=A4)
            
            for page_num in range(1, num_pages + 1):
                self._draw_page(c, character, page_num)
                c.showPage()
            
            c.save()
            return True, f"字帖已成功生成：{output_path}"
            
        except Exception as e:
            return False, f"生成字帖时发生错误：{str(e)}"


def main():
    """主函数"""
    if len(sys.argv) < 3:
        print("用法: python copybook_generator.py <汉字> <输出文件路径> [页数]")
        print("示例: python copybook_generator.py 永 永字练习.pdf 2")
        sys.exit(1)
    
    character = sys.argv[1]
    output_path = sys.argv[2]
    num_pages = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    
    generator = CopybookGenerator()
    
    success, message = generator.generate(character, output_path, num_pages)
    
    if success:
        print(f"✓ {message}")
        sys.exit(0)
    else:
        print(f"✗ {message}")
        sys.exit(1)


if __name__ == "__main__":
    main()
