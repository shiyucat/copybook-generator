#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
字帖生成器
生成田字格格式的字帖，包含笔画步骤展示和描红功能
"""

import sys
import os
import json
import re
import math
import urllib.parse
from typing import List, Tuple, Optional, Dict, Any
from pathlib import Path
import urllib.request
import urllib.error

try:
    from pypinyin import pinyin, Style
    PINYIN_AVAILABLE = True
except ImportError:
    PINYIN_AVAILABLE = False

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color, black, gray, red, blue

light_red = Color(1.0, 0.4, 0.4, alpha=0.8)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

PAGE_SIZES = {
    "A4": A4,
    "SIZE_16K": (185 * mm, 260 * mm),
    "A5": (148 * mm, 210 * mm),
    "B5": (176 * mm, 250 * mm),
}

DEFAULT_PAGE_SIZE = "A4"

DEFAULT_GRID_SIZE_CM = 2.0
DEFAULT_LINES_PER_CHAR = 1
DEFAULT_SHOW_PINYIN = False
DEFAULT_SHOW_CHARACTER_PINYIN = True
BORDER_RATIO = 0.1
DEFAULT_FONT_COLOR = (0.0, 0.0, 0.0)
DEFAULT_PINYIN_COLOR = (0.0, 0.0, 0.0)
DEFAULT_CHARACTER_COLOR = (0.0, 0.0, 0.0)
DEFAULT_RIGHT_GRID_COLOR = (0.0, 0.0, 0.0)
DEFAULT_RIGHT_GRID_TYPE = "米字格"
DEFAULT_STROKE_ORDER_COLOR = (0.0, 0.0, 0.0)

CHARACTER_SCENE_CONFIG = {
    "CHARACTER_BOX_SIZE_MM": 50,
    "RIGHT_GRID_SIZE_MM": 20,
    "GAP_SIZE_MM": 2,
    "RIGHT_GRID_ROWS": 2,
    "STROKE_ORDER_ROW_HEIGHT_MM": 10,
}

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class GridType:
    """格子类型"""
    TIANZI = "田字格"
    MIZI = "米字格"
    HUIGONG = "回宫格"
    FANGGE = "方格"


class CopybookPreview:
    """字帖预览绘制器 - 核心业务逻辑"""
    
    def __init__(self):
        self.grid_size = 60
        self.grid_padding = 5
        self.font_size = 40
        self._init_font()
        
    def _init_font(self):
        """初始化字体"""
        self.font = None
        self.font_name = "Default"
        self.font_path = None
        
        font_dirs = [
            Path(__file__).parent / "fonts",
            Path.home() / "Library" / "Fonts",
            Path("/System/Library/Fonts"),
            Path("/System/Library/Fonts/Supplemental"),
            Path("/Library/Fonts"),
        ]
        
        font_patterns = [
            "STXINGKA.ttf", "Kai.ttc", "STKaiti.ttc", "KaiTi.ttc", 
            "simkai.ttf", "Kai.ttf", "STKaiti.ttf", "KaiTi.ttf",
            "Songti.ttc", "STHeiti Light.ttc", "STHeiti Medium.ttc",
            "Hiragino Sans GB.ttc",
        ]
        
        for font_dir in font_dirs:
            if not font_dir.exists():
                continue
            for pattern in font_patterns:
                font_file = font_dir / pattern
                if font_file.exists():
                    try:
                        self.font = ImageFont.truetype(str(font_file), self.font_size)
                        self.font_name = pattern
                        self.font_path = str(font_file)
                        return
                    except Exception:
                        continue
        
        try:
            self.font = ImageFont.load_default()
        except:
            pass
    
    def draw_grid(self, draw: ImageDraw.Draw, x: int, y: int, grid_type: str, 
                  character: str = "", is_template: bool = False):
        """
        绘制单个格子
        
        Args:
            draw: ImageDraw对象
            x: 格子左上角x坐标
            y: 格子左上角y坐标
            grid_type: 格子类型
            character: 要显示的字符
            is_template: 是否为模板字（第一个字）
        """
        size = self.grid_size
        
        if is_template and character:
            draw.rectangle([x, y, x + size, y + size], fill=(245, 245, 245))
        
        draw.rectangle([x, y, x + size, y + size], outline=(128, 128, 128), width=1)
        
        if grid_type == GridType.TIANZI or grid_type == GridType.MIZI:
            draw.line([x, y + size//2, x + size, y + size//2], fill=(200, 200, 200), width=1)
            draw.line([x + size//2, y, x + size//2, y + size], fill=(200, 200, 200), width=1)
        
        if grid_type == GridType.MIZI:
            draw.line([x, y, x + size, y + size], fill=(200, 200, 200), width=1)
            draw.line([x + size, y, x, y + size], fill=(200, 200, 200), width=1)
        
        if grid_type == GridType.HUIGONG:
            inner_margin = size // 5
            draw.rectangle([x + inner_margin, y + inner_margin, 
                           x + size - inner_margin, y + size - inner_margin], 
                          outline=(200, 200, 200), width=1)
        
        if character and self.font:
            try:
                bbox = draw.textbbox((0, 0), character, font=self.font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                text_x = x + (size - text_width) // 2 - bbox[0]
                text_y = y + (size - text_height) // 2 - bbox[1]
                
                if is_template:
                    draw.text((text_x, text_y), character, font=self.font, fill=(180, 180, 180))
                else:
                    draw.text((text_x, text_y), character, font=self.font, fill=(100, 100, 100))
            except Exception:
                pass
    
    def _calculate_layout(self, page_width: int, page_height: int):
        """计算排版参数"""
        cols = max(1, (page_width - self.grid_padding * 2) // (self.grid_size + self.grid_padding))
        max_rows_per_page = max(1, (page_height - self.grid_padding * 2) // (self.grid_size + self.grid_padding))
        return cols, max_rows_per_page
    
    def _generate_page_image(self, characters: List[str], start_char_index: int,
                            grid_type: str, page_width: int, page_height: int) -> Tuple[Image.Image, int]:
        """
        生成单页图像
        
        Args:
            characters: 字符列表
            start_char_index: 起始字符索引
            grid_type: 格子类型
            page_width: 页面宽度
            page_height: 页面高度
            
        Returns:
            (图像对象, 下一页起始字符索引)
        """
        cols, max_rows_per_page = self._calculate_layout(page_width, page_height)
        
        img = Image.new('RGB', (page_width, page_height), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        total_chars = len(characters)
        char_index = start_char_index
        
        for row_in_page in range(max_rows_per_page):
            if char_index >= total_chars:
                for col in range(cols):
                    x = self.grid_padding + col * (self.grid_size + self.grid_padding)
                    y = self.grid_padding + row_in_page * (self.grid_size + self.grid_padding)
                    if x + self.grid_size <= page_width and y + self.grid_size <= page_height:
                        self.draw_grid(draw, x, y, grid_type, "", False)
                continue
            
            current_char = characters[char_index]
            
            for col in range(cols):
                x = self.grid_padding + col * (self.grid_size + self.grid_padding)
                y = self.grid_padding + row_in_page * (self.grid_size + self.grid_padding)
                
                if x + self.grid_size > page_width or y + self.grid_size > page_height:
                    continue
                
                is_template = (col == 0)
                if is_template:
                    self.draw_grid(draw, x, y, grid_type, current_char, is_template)
                else:
                    self.draw_grid(draw, x, y, grid_type, "", False)
            
            char_index += 1
        
        return img, char_index
    
    def generate_preview_page(self, characters: List[str], page_number: int,
                              grid_type: str, page_width: int, page_height: int) -> Optional[Image.Image]:
        """
        生成指定页码的预览图像
        
        Args:
            characters: 字符列表
            page_number: 页码（从1开始）
            grid_type: 格子类型
            page_width: 页面宽度
            page_height: 页面高度
            
        Returns:
            PIL Image对象，如果页码超出范围则返回None
        """
        if page_number < 1:
            return None
        
        cols, max_rows_per_page = self._calculate_layout(page_width, page_height)
        chars_per_page = max_rows_per_page
        
        total_pages = self.calculate_total_pages(characters, page_width, page_height)
        
        if page_number > total_pages:
            return None
        
        start_char_index = (page_number - 1) * chars_per_page
        
        img, _ = self._generate_page_image(characters, start_char_index, grid_type, page_width, page_height)
        return img
    
    def calculate_total_pages(self, characters: List[str], page_width: int, page_height: int) -> int:
        """
        计算总页数
        
        Args:
            characters: 字符列表
            page_width: 页面宽度
            page_height: 页面高度
            
        Returns:
            总页数
        """
        if not characters:
            return 1
        
        _, max_rows_per_page = self._calculate_layout(page_width, page_height)
        chars_per_page = max_rows_per_page
        
        return max(1, (len(characters) + chars_per_page - 1) // chars_per_page)
    
    def generate_all_pages(self, characters: List[str], grid_type: str,
                           page_width: int, page_height: int) -> List[Image.Image]:
        """
        生成所有页面的图像（用于PDF导出）
        
        Args:
            characters: 字符列表
            grid_type: 格子类型
            page_width: 页面宽度
            page_height: 页面高度
            
        Returns:
            PIL Image对象列表，每个元素是一页
        """
        pages = []
        total_chars = len(characters)
        char_index = 0
        
        while total_chars == 0 or char_index < total_chars:
            img, next_char_index = self._generate_page_image(characters, char_index, grid_type, page_width, page_height)
            pages.append(img)
            
            if total_chars == 0:
                break
            
            if next_char_index >= total_chars:
                break
            char_index = next_char_index
        
        return pages
    
    @staticmethod
    def filter_valid_characters(text: str) -> List[str]:
        """
        过滤有效字符（用于预览生成）
        
        Args:
            text: 输入的原始文本
            
        Returns:
            有效字符列表（只包含中文、英文、数字）
        """
        valid_chars = []
        
        for char in text:
            if re.match(r'^[\u4e00-\u9fff\u3400-\u4dbf]$', char):
                valid_chars.append(char)
            elif re.match(r'^[a-zA-Z0-9]$', char):
                valid_chars.append(char)
        
        return valid_chars
    
    @staticmethod
    def is_allowed_character(char: str) -> bool:
        """
        检查字符是否允许输入
        
        允许的字符：
        - 中文：\u4e00-\u9fff, \u3400-\u4dbf
        - 英文：a-z, A-Z
        - 数字：0-9
        - 空格和换行（不占格但允许输入）
        
        Args:
            char: 要检查的字符
            
        Returns:
            是否允许输入
        """
        if re.match(r'^[\u4e00-\u9fff\u3400-\u4dbf]$', char):
            return True
        
        if re.match(r'^[a-zA-Z0-9\s\n]$', char):
            return True
        
        return False
    
    @staticmethod
    def clean_input_text(text: str) -> str:
        """
        清理输入文本，移除不允许的字符
        
        Args:
            text: 原始输入文本
            
        Returns:
            清理后的文本
        """
        cleaned = []
        for char in text:
            if CopybookPreview.is_allowed_character(char):
                cleaned.append(char)
        return ''.join(cleaned)


class StrokeType:
    """笔画类型"""
    HENG = "横"
    SHU = "竖"
    PIE = "撇"
    NA = "捺"
    DIAN = "点"
    HENG_ZHE = "横折"
    SHU_GOU = "竖钩"
    HENG_GOU = "横钩"
    PIE_DIAN = "撇点"
    HENG_PIE = "横撇"
    SHU_ZHE = "竖折"
    SHU_WAN = "竖弯"
    SHU_WAN_GOU = "竖弯钩"
    WO_GOU = "卧钩"
    XIE_GOU = "斜钩"
    HENG_ZHE_GOU = "横折钩"
    HENG_ZHE_WAN_GOU = "横折弯钩"
    HENG_XIE_GOU = "横斜钩"
    SHU_ZHE_ZHE_GOU = "竖折折钩"
    HENG_ZHE_ZHE = "横折折"
    HENG_ZHE_ZHE_PIE = "横折折撇"
    HENG_ZHE_PIE = "横折撇"
    PIE_ZHE = "撇折"
    TI = "提"
    WAN_GOU = "弯钩"


class StrokeDirection:
    """笔画方向"""
    LEFT_TO_RIGHT = "left_to_right"
    TOP_TO_BOTTOM = "top_to_bottom"
    TOP_LEFT_TO_BOTTOM_RIGHT = "top_left_to_bottom_right"
    TOP_RIGHT_TO_BOTTOM_LEFT = "top_right_to_bottom_left"
    TOP_TO_BOTTOM_RIGHT = "top_to_bottom_right"
    TOP_TO_BOTTOM_LEFT = "top_to_bottom_left"
    CURVED = "curved"


class StrokeType:
    """笔画类型"""
    LINEAR = "linear"
    CURVED = "curved"
    
    HENG = "heng"
    SHU = "shu"
    PIE = "pie"
    NA = "na"
    DIAN = "dian"
    HENG_ZHE = "heng_zhe"
    HENG_GOU = "heng_gou"
    HENG_PIE = "heng_pie"
    HENG_ZHE_GOU = "heng_zhe_gou"
    HENG_ZHE_WAN_GOU = "heng_zhe_wan_gou"
    SHU_GOU = "shu_gou"
    SHU_ZHE = "shu_zhe"
    SHU_WAN = "shu_wan"
    SHU_ZHE_GOU = "shu_zhe_gou"
    SHU_ZHE_ZHE_GOU = "shu_zhe_zhe_gou"
    WAN_GOU = "wan_gou"
    WO_GOU = "wo_gou"
    XIE_GOU = "xie_gou"
    PIE_DIAN = "pie_dian"
    PIE_ZHE = "pie_zhe"
    SHU_TI = "shu_ti"
    HENG_TI = "heng_ti"
    TI = "ti"


class StrokeDirection:
    """笔画方向"""
    LEFT_TO_RIGHT = "left_to_right"
    TOP_TO_BOTTOM = "top_to_bottom"
    TOP_LEFT_TO_BOTTOM_RIGHT = "top_left_to_bottom_right"
    TOP_RIGHT_TO_BOTTOM_LEFT = "top_right_to_bottom_left"
    TOP_TO_BOTTOM_RIGHT = "top_to_bottom_right"
    TOP_TO_BOTTOM_LEFT = "top_to_bottom_left"
    CURVED = "curved"


STROKE_NAME_TO_CHAR = {
    "横": "一",
    "竖": "丨",
    "撇": "丿",
    "捺": "㇏",
    "点": "丶",
    "横折": "𠃍",
    "竖钩": "亅",
    "横钩": "乛",
    "撇点": "𡿨",
    "横撇": "㇇",
    "竖折": "𠃊",
    "竖弯": "㇄",
    "竖弯钩": "乚",
    "卧钩": "㇃",
    "斜钩": "㇂",
    "横折钩": "𠃌",
    "横折弯钩": "㇈",
    "横斜钩": "⺄",
    "竖折折钩": "㇉",
    "横折折": "㇅",
    "横折折撇": "㇋",
    "横折撇": "㇇",
    "撇折": "𠃋",
    "提": "㇀",
    "弯钩": "㇁",
    "横折提": "𠊌",
    "横折弯钩": "㇈",
    "横撇弯钩": "㇌",
    "横折折折钩": "㇎",
    "竖折撇": "ㄥ",
}


class StrokeData:
    """笔画数据类"""
    
    def __init__(self, character: str):
        self.character = character
        self.strokes = []
        self.medians = []
        self.rad_strokes = []
        
    def load_from_json(self, data: Dict[str, Any]):
        """从JSON数据加载笔画信息"""
        self.strokes = data.get('strokes', [])
        self.medians = data.get('medians', [])
        self.rad_strokes = data.get('radStrokes', [])


class SVGPathParser:
    """SVG路径解析器"""
    
    @staticmethod
    def parse_commands(path_str: str) -> List[Tuple[str, List[float]]]:
        """
        解析SVG路径字符串为命令列表
        
        Args:
            path_str: SVG路径字符串，如 "M 10 10 L 20 20 Q 30 30 40 40"
            
        Returns:
            命令列表，每个命令为 (命令字符, [坐标列表])
        """
        commands = []
        tokens = re.findall(r'([A-Za-z])|(-?\d+\.?\d*)', path_str)
        tokens = [t[0] or t[1] for t in tokens if t[0] or t[1]]
        
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token.isalpha():
                cmd = token
                i += 1
            else:
                cmd = commands[-1][0].lower() if commands else 'M'
            
            coords = []
            while i < len(tokens) and not tokens[i].isalpha():
                coords.append(float(tokens[i]))
                i += 1
            
            commands.append((cmd, coords))
        
        return commands
    
    @staticmethod
    def get_path_points(commands: List[Tuple[str, List[float]]]) -> List[Tuple[float, float]]:
        """
        从路径命令获取所有关键点
        
        Args:
            commands: 路径命令列表
            
        Returns:
            点坐标列表
        """
        points = []
        current_pos = (0.0, 0.0)
        
        for cmd, coords in commands:
            if cmd == 'M':
                current_pos = (coords[0], coords[1])
                points.append(current_pos)
            elif cmd == 'L':
                for i in range(0, len(coords), 2):
                    current_pos = (coords[i], coords[i+1])
                    points.append(current_pos)
            elif cmd == 'Q':
                for i in range(0, len(coords), 4):
                    ctrl = (coords[i], coords[i+1])
                    end = (coords[i+2], coords[i+3])
                    points.append(ctrl)
                    points.append(end)
                    current_pos = end
            elif cmd == 'C':
                for i in range(0, len(coords), 6):
                    ctrl1 = (coords[i], coords[i+1])
                    ctrl2 = (coords[i+2], coords[i+3])
                    end = (coords[i+4], coords[i+5])
                    points.append(ctrl1)
                    points.append(ctrl2)
                    points.append(end)
                    current_pos = end
            elif cmd == 'Z':
                pass
        
        return points


class StrokeAnalyzer:
    """笔画分析器"""
    
    @staticmethod
    def analyze_stroke_type(median: List[List[float]]) -> str:
        """
        分析笔画类型：直线型还是弧形
        
        Args:
            median: 笔画中心线的点列表，每个点为 [x, y]
            
        Returns:
            StrokeType.LINEAR 或 StrokeType.CURVED
        """
        if len(median) < 3:
            return StrokeType.LINEAR
        
        start = median[0]
        end = median[-1]
        
        max_deviation = 0.0
        line_length = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
        
        if line_length < 1.0:
            return StrokeType.LINEAR
        
        for point in median[1:-1]:
            deviation = StrokeAnalyzer._point_to_line_distance(
                point, start, end
            )
            max_deviation = max(max_deviation, deviation)
        
        relative_deviation = max_deviation / line_length
        
        if relative_deviation > 0.15:
            return StrokeType.CURVED
        else:
            return StrokeType.LINEAR
    
    @staticmethod
    def _point_to_line_distance(point: List[float], 
                                 line_start: List[float], 
                                 line_end: List[float]) -> float:
        """
        计算点到直线的距离
        
        Args:
            point: 点坐标 [x, y]
            line_start: 直线起点 [x, y]
            line_end: 直线终点 [x, y]
            
        Returns:
            距离值
        """
        x0, y0 = point
        x1, y1 = line_start
        x2, y2 = line_end
        
        numerator = abs((y2 - y1) * x0 - (x2 - x1) * y0 + x2 * y1 - y2 * x1)
        denominator = math.sqrt((y2 - y1)**2 + (x2 - x1)**2)
        
        if denominator < 1e-10:
            return math.sqrt((x0 - x1)**2 + (y0 - y1)**2)
        
        return numerator / denominator
    
    @staticmethod
    def get_stroke_direction(median: List[List[float]]) -> Tuple[float, float]:
        """
        获取笔画的主方向（从起点到终点的方向向量）
        
        Args:
            median: 笔画中心线的点列表
            
        Returns:
            方向向量 (dx, dy)
        """
        if len(median) < 2:
            return (0.0, 0.0)
        
        start = median[0]
        end = median[-1]
        
        return (end[0] - start[0], end[1] - start[1])
    
    @staticmethod
    def get_stroke_endpoints(median: List[List[float]]) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """
        获取笔画的起点和终点
        
        Args:
            median: 笔画中心线的点列表
            
        Returns:
            (起点, 终点) 元组
        """
        if len(median) < 2:
            return ((0.0, 0.0), (0.0, 0.0))
        
        return (
            (median[0][0], median[0][1]),
            (median[-1][0], median[-1][1])
        )


class ArrowDrawer:
    """箭头绘制器"""
    
    @staticmethod
    def draw_linear_arrow(c: canvas.Canvas, 
                          start: Tuple[float, float], 
                          end: Tuple[float, float],
                          color: Color = red,
                          line_width: float = 2.0):
        """
        绘制直线箭头
        
        Args:
            c: PDF画布对象
            start: 起点坐标 (x, y)
            end: 终点坐标 (x, y)
            color: 箭头颜色
            line_width: 线宽
        """
        c.setStrokeColor(color)
        c.setFillColor(color)
        c.setLineWidth(line_width)
        
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.sqrt(dx * dx + dy * dy)
        
        if length < 1.0:
            return
        
        c.line(start[0], start[1], end[0], end[1])
        
        arrow_length = 10.0
        arrow_angle = math.pi / 6
        
        angle = math.atan2(dy, dx)
        
        arrow_point1 = (
            end[0] - arrow_length * math.cos(angle - arrow_angle),
            end[1] - arrow_length * math.sin(angle - arrow_angle)
        )
        arrow_point2 = (
            end[0] - arrow_length * math.cos(angle + arrow_angle),
            end[1] - arrow_length * math.sin(angle + arrow_angle)
        )
        
        c.line(end[0], end[1], arrow_point1[0], arrow_point1[1])
        c.line(end[0], end[1], arrow_point2[0], arrow_point2[1])
    
    @staticmethod
    def draw_curved_arrow(c: canvas.Canvas,
                          median: List[List[float]],
                          color: Color = red,
                          line_width: float = 2.0):
        """
        绘制弧形箭头
        
        Args:
            c: PDF画布对象
            median: 笔画中心线的点列表
            color: 箭头颜色
            line_width: 线宽
        """
        if len(median) < 2:
            return
        
        c.setStrokeColor(color)
        c.setFillColor(color)
        c.setLineWidth(line_width)
        
        points = [(float(p[0]), float(p[1])) for p in median]
        
        if len(points) == 2:
            ArrowDrawer.draw_linear_arrow(c, points[0], points[1], color, line_width)
            return
        
        c.setLineWidth(line_width)
        path = c.beginPath()
        path.moveTo(points[0][0], points[0][1])
        
        for i in range(1, len(points) - 1, 2):
            if i + 1 < len(points):
                path.curveTo(
                    points[i][0], points[i][1],
                    points[i][0], points[i][1],
                    points[i + 1][0], points[i + 1][1]
                )
            elif i < len(points):
                path.lineTo(points[i][0], points[i][1])
        
        c.drawPath(path, stroke=1, fill=0)
        
        if len(points) >= 3:
            last_segment_start = points[-3] if len(points) >= 3 else points[-2]
            last_segment_end = points[-1]
            ArrowDrawer._draw_arrowhead(c, last_segment_start, last_segment_end, color)
        elif len(points) == 2:
            ArrowDrawer._draw_arrowhead(c, points[0], points[1], color)
    
    @staticmethod
    def _draw_arrowhead(c: canvas.Canvas,
                       start: Tuple[float, float],
                       end: Tuple[float, float],
                       color: Color):
        """
        绘制箭头头部
        
        Args:
            c: PDF画布对象
            start: 线段起点
            end: 线段终点
            color: 颜色
        """
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.sqrt(dx * dx + dy * dy)
        
        if length < 1.0:
            return
        
        arrow_length = 10.0
        arrow_angle = math.pi / 6
        
        angle = math.atan2(dy, dx)
        
        arrow_point1 = (
            end[0] - arrow_length * math.cos(angle - arrow_angle),
            end[1] - arrow_length * math.sin(angle - arrow_angle)
        )
        arrow_point2 = (
            end[0] - arrow_length * math.cos(angle + arrow_angle),
            end[1] - arrow_length * math.sin(angle + arrow_angle)
        )
        
        c.line(end[0], end[1], arrow_point1[0], arrow_point1[1])
        c.line(end[0], end[1], arrow_point2[0], arrow_point2[1])


class StrokeSegment:
    """笔画线段"""
    
    def __init__(self, 
                 start: Tuple[float, float], 
                 end: Tuple[float, float],
                 segment_type: str = "linear",
                 control_points: List[Tuple[float, float]] = None):
        """
        初始化笔画线段
        
        Args:
            start: 起点坐标
            end: 终点坐标
            segment_type: 线段类型（linear 或 curved）
            control_points: 控制点（用于曲线）
        """
        self.start = start
        self.end = end
        self.segment_type = segment_type
        self.control_points = control_points or []
        
    def get_length(self) -> float:
        """获取线段长度"""
        return math.sqrt(
            (self.end[0] - self.start[0])**2 + 
            (self.end[1] - self.start[1])**2
        )
    
    def get_direction(self) -> Tuple[float, float]:
        """获取线段方向向量"""
        length = self.get_length()
        if length < 1e-10:
            return (0.0, 0.0)
        return (
            (self.end[0] - self.start[0]) / length,
            (self.end[1] - self.start[1]) / length
        )
    
    def get_midpoint(self) -> Tuple[float, float]:
        """获取线段中点"""
        return (
            (self.start[0] + self.end[0]) / 2,
            (self.start[1] + self.end[1]) / 2
        )


class ImprovedStrokeAnalyzer:
    """改进版笔画分析器"""
    
    @staticmethod
    def get_stroke_primary_direction(median: List[List[float]]) -> str:
        """
        获取笔画的主方向
        
        Args:
            median: 笔画中位数点列表
            
        Returns:
            主方向："horizontal"（横）、"vertical"（竖）、"diagonal"（斜）、"curved"（曲）
        """
        if len(median) < 2:
            return "horizontal"
        
        start = median[0]
        end = median[-1]
        
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        
        angle = math.atan2(abs(dy), abs(dx))
        
        horizontal_threshold = math.pi / 6
        vertical_threshold = math.pi / 3
        
        if angle < horizontal_threshold:
            return "horizontal"
        elif angle > vertical_threshold:
            return "vertical"
        else:
            stroke_type = StrokeAnalyzer.analyze_stroke_type(median)
            if stroke_type == StrokeType.CURVED:
                return "curved"
            return "diagonal"
    
    @staticmethod
    def split_stroke_into_segments(median: List[List[float]], 
                                    angle_threshold: float = math.pi / 4) -> List[StrokeSegment]:
        """
        将笔画拆分为多个线段，检测转折点
        
        Args:
            median: 笔画中位数点列表
            angle_threshold: 角度阈值，超过此角度认为是转折点
            
        Returns:
            笔画线段列表
        """
        if len(median) < 2:
            return []
        
        segments = []
        
        if len(median) == 2:
            segments.append(StrokeSegment(
                (median[0][0], median[0][1]),
                (median[1][0], median[1][1]),
                "linear"
            ))
            return segments
        
        segment_start = median[0]
        prev_direction = None
        
        for i in range(1, len(median)):
            current_point = median[i]
            
            if i >= 2:
                prev_point = median[i - 1]
                prev_prev_point = median[i - 2]
                
                dx1 = prev_point[0] - prev_prev_point[0]
                dy1 = prev_point[1] - prev_prev_point[1]
                dx2 = current_point[0] - prev_point[0]
                dy2 = current_point[1] - prev_point[1]
                
                angle1 = math.atan2(dy1, dx1)
                angle2 = math.atan2(dy2, dx2)
                
                angle_diff = abs(angle2 - angle1)
                if angle_diff > math.pi:
                    angle_diff = 2 * math.pi - angle_diff
                
                if angle_diff > angle_threshold:
                    segments.append(StrokeSegment(
                        (segment_start[0], segment_start[1]),
                        (prev_point[0], prev_point[1]),
                        "linear"
                    ))
                    segment_start = prev_point
        
        if segment_start != median[-1]:
            segments.append(StrokeSegment(
                (segment_start[0], segment_start[1]),
                (median[-1][0], median[-1][1]),
                "linear"
            ))
        
        return segments
    
    @staticmethod
    def get_perpendicular_direction(direction: Tuple[float, float]) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """
        获取笔画方向的两个垂直方向（法线方向）
        
        Args:
            direction: 笔画方向向量 (dx, dy)
            
        Returns:
            两个垂直方向向量 (left_normal, right_normal)
        """
        dx, dy = direction
        length = math.sqrt(dx * dx + dy * dy)
        
        if length < 1e-10:
            return ((0.0, 1.0), (0.0, -1.0))
        
        normalized_dx = dx / length
        normalized_dy = dy / length
        
        left_normal = (-normalized_dy, normalized_dx)
        right_normal = (normalized_dy, -normalized_dx)
        
        return left_normal, right_normal
    
    @staticmethod
    def get_best_offset_direction(median: List[List[float]],
                                   grid_x: float,
                                   grid_y: float,
                                   grid_size: float,
                                   stroke_index: int,
                                   total_strokes: int) -> Tuple[float, float]:
        """
        智能选择最佳的箭头偏移方向
        
        Args:
            median: 笔画中位数点列表
            grid_x: 田字格左下角x坐标
            grid_y: 田字格左下角y坐标
            grid_size: 田字格大小
            stroke_index: 当前笔画索引
            total_strokes: 总笔画数
            
        Returns:
            最佳偏移方向向量 (dx, dy)
        """
        if len(median) < 2:
            return (0.7, 0.7)
        
        start_point = median[0]
        end_point = median[-1]
        
        dx = end_point[0] - start_point[0]
        dy = end_point[1] - start_point[1]
        
        angle = math.atan2(abs(dy), abs(dx))
        
        horizontal_threshold = math.pi / 6
        vertical_threshold = math.pi / 3
        
        grid_center_x = grid_x + grid_size / 2
        grid_center_y = grid_y + grid_size / 2
        
        stroke_mid_x = (start_point[0] + end_point[0]) / 2
        stroke_mid_y = (start_point[1] + end_point[1]) / 2
        
        if angle < horizontal_threshold:
            if stroke_mid_y > grid_center_y:
                return (0.0, 1.0)
            else:
                return (0.0, -1.0)
        
        elif angle > vertical_threshold:
            if stroke_mid_x > grid_center_x:
                return (1.0, 0.0)
            else:
                return (-1.0, 0.0)
        
        else:
            if dx > 0 and dy > 0:
                if stroke_mid_x + stroke_mid_y > grid_center_x + grid_center_y:
                    return (0.7, 0.7)
                else:
                    return (-0.7, -0.7)
            elif dx > 0 and dy < 0:
                if stroke_mid_x - stroke_mid_y > grid_center_x - grid_center_y:
                    return (0.7, -0.7)
                else:
                    return (-0.7, 0.7)
            elif dx < 0 and dy > 0:
                if stroke_mid_x - stroke_mid_y > grid_center_x - grid_center_y:
                    return (-0.7, 0.7)
                else:
                    return (0.7, -0.7)
            else:
                if stroke_mid_x + stroke_mid_y > grid_center_x + grid_center_y:
                    return (-0.7, -0.7)
                else:
                    return (0.7, 0.7)
    
    @staticmethod
    def get_point_along_median(median: List[List[float]], 
                                ratio: float) -> Tuple[float, float]:
        """
        获取笔画中线上指定比例位置的点
        
        Args:
            median: 笔画中位数点列表
            ratio: 比例（0.0 到 1.0）
            
        Returns:
            点坐标 (x, y)
        """
        if len(median) < 2:
            return (0.0, 0.0)
        
        if ratio <= 0.0:
            return (median[0][0], median[0][1])
        if ratio >= 1.0:
            return (median[-1][0], median[-1][1])
        
        total_length = 0.0
        segment_lengths = []
        
        for i in range(len(median) - 1):
            length = math.sqrt(
                (median[i + 1][0] - median[i][0])**2 + 
                (median[i + 1][1] - median[i][1])**2
            )
            segment_lengths.append(length)
            total_length += length
        
        if total_length < 1e-10:
            return (median[0][0], median[0][1])
        
        target_length = total_length * ratio
        accumulated_length = 0.0
        
        for i in range(len(median) - 1):
            if accumulated_length + segment_lengths[i] >= target_length:
                segment_ratio = (target_length - accumulated_length) / segment_lengths[i]
                return (
                    median[i][0] + (median[i + 1][0] - median[i][0]) * segment_ratio,
                    median[i][1] + (median[i + 1][1] - median[i][1]) * segment_ratio
                )
            accumulated_length += segment_lengths[i]
        
        return (median[-1][0], median[-1][1])


class ImprovedArrowDrawer:
    """改进版箭头绘制器"""
    
    ARROW_LENGTH_RATIO = 0.25
    ARROW_WIDTH_RATIO = 0.2
    STROKE_WIDTH_RATIO = 0.05
    
    @staticmethod
    def calculate_arrow_dimensions(grid_size: float, 
                                    stroke_length: float) -> Tuple[float, float, float]:
        """
        计算箭头的尺寸
        
        Args:
            grid_size: 田字格大小
            stroke_length: 笔画长度
            
        Returns:
            (箭头长度, 箭头宽度, 笔画基准宽度)
        """
        base_stroke_width = grid_size * ImprovedArrowDrawer.STROKE_WIDTH_RATIO
        
        arrow_length = stroke_length * ImprovedArrowDrawer.ARROW_LENGTH_RATIO
        arrow_length = max(arrow_length, grid_size * 0.08)
        arrow_length = min(arrow_length, grid_size * 0.3)
        
        arrow_width = base_stroke_width * ImprovedArrowDrawer.ARROW_WIDTH_RATIO
        
        return arrow_length, arrow_width, base_stroke_width
    
    @staticmethod
    def draw_short_arrow(c: canvas.Canvas,
                        start: Tuple[float, float],
                        direction: Tuple[float, float],
                        arrow_length: float,
                        arrow_width: float,
                        offset_direction: Tuple[float, float],
                        offset_distance: float,
                        color: Color = light_red):
        """
        绘制短箭头（笔画长度的1/4）
        
        Args:
            c: PDF画布对象
            start: 箭头起点（在笔画开始位置）
            direction: 箭头方向向量
            arrow_length: 箭头长度
            arrow_width: 箭头线宽
            offset_direction: 偏移方向向量（表示箭头相对于笔画中心线的偏移方向）
            offset_distance: 偏移距离
            color: 箭头颜色
        """
        dir_length = math.sqrt(direction[0]**2 + direction[1]**2)
        if dir_length < 1e-10:
            return
        
        normalized_dir = (direction[0] / dir_length, direction[1] / dir_length)
        
        offset_length = math.sqrt(offset_direction[0]**2 + offset_direction[1]**2)
        if offset_length > 1e-10:
            normalized_offset = (
                offset_direction[0] / offset_length,
                offset_direction[1] / offset_length
            )
        else:
            normalized_offset = (0.0, 0.0)
        
        arrow_start = (
            start[0] + normalized_offset[0] * offset_distance,
            start[1] + normalized_offset[1] * offset_distance
        )
        
        arrow_end = (
            arrow_start[0] + normalized_dir[0] * arrow_length,
            arrow_start[1] + normalized_dir[1] * arrow_length
        )
        
        c.setStrokeColor(color)
        c.setFillColor(color)
        c.setLineWidth(arrow_width)
        
        c.line(arrow_start[0], arrow_start[1], arrow_end[0], arrow_end[1])
        
        arrowhead_length = arrow_width * 3
        arrowhead_angle = math.pi / 6
        
        angle = math.atan2(normalized_dir[1], normalized_dir[0])
        
        arrow_point1 = (
            arrow_end[0] - arrowhead_length * math.cos(angle - arrowhead_angle),
            arrow_end[1] - arrowhead_length * math.sin(angle - arrowhead_angle)
        )
        arrow_point2 = (
            arrow_end[0] - arrowhead_length * math.cos(angle + arrowhead_angle),
            arrow_end[1] - arrowhead_length * math.sin(angle + arrowhead_angle)
        )
        
        c.line(arrow_end[0], arrow_end[1], arrow_point1[0], arrow_point1[1])
        c.line(arrow_end[0], arrow_end[1], arrow_point2[0], arrow_point2[1])
        
        return arrow_start
    
    @staticmethod
    def draw_stroke_number(c: canvas.Canvas,
                           stroke_order: int,
                           position: Tuple[float, float],
                           arrow_width: float,
                           color: Color = blue):
        """
        在箭头开始位置绘制笔顺数字编号
        
        Args:
            c: PDF画布对象
            stroke_order: 笔顺数字序号
            position: 数字位置（箭头开始位置）
            arrow_width: 箭头宽度（用于确定数字大小）
            color: 数字颜色
        """
        font_size = max(arrow_width * 5, 8)
        font_size = min(font_size, 14)
        
        c.setFillColor(color)
        c.setFont("Helvetica-Bold", font_size)
        
        order_text = str(stroke_order)
        order_width = c.stringWidth(order_text, "Helvetica-Bold", font_size)
        
        label_x = position[0] - order_width - 3
        label_y = position[1] - font_size / 4
        
        c.drawString(label_x, label_y, order_text)
    
    @staticmethod
    def draw_curved_short_arrow(c: canvas.Canvas,
                                 median: List[List[float]],
                                 arrow_length_ratio: float,
                                 arrow_width: float,
                                 offset_direction: Tuple[float, float],
                                 offset_distance: float,
                                 color: Color = light_red):
        """
        绘制弧形短箭头
        
        Args:
            c: PDF画布对象
            median: 笔画中位数点列表
            arrow_length_ratio: 箭头长度比例
            arrow_width: 箭头线宽
            offset_direction: 偏移方向向量
            offset_distance: 偏移距离
            color: 箭头颜色
        """
        if len(median) < 2:
            return None
        
        offset_length = math.sqrt(offset_direction[0]**2 + offset_direction[1]**2)
        if offset_length > 1e-10:
            normalized_offset = (
                offset_direction[0] / offset_length,
                offset_direction[1] / offset_length
            )
        else:
            normalized_offset = (0.0, 0.0)
        
        start_point = (
            median[0][0] + normalized_offset[0] * offset_distance,
            median[0][1] + normalized_offset[1] * offset_distance
        )
        
        end_ratio = min(arrow_length_ratio, 0.5)
        end_point = ImprovedStrokeAnalyzer.get_point_along_median(median, end_ratio)
        end_point = (
            end_point[0] + normalized_offset[0] * offset_distance,
            end_point[1] + normalized_offset[1] * offset_distance
        )
        
        mid_ratio = end_ratio / 2
        mid_point = ImprovedStrokeAnalyzer.get_point_along_median(median, mid_ratio)
        mid_point = (
            mid_point[0] + normalized_offset[0] * offset_distance,
            mid_point[1] + normalized_offset[1] * offset_distance
        )
        
        c.setStrokeColor(color)
        c.setFillColor(color)
        c.setLineWidth(arrow_width)
        
        path = c.beginPath()
        path.moveTo(start_point[0], start_point[1])
        path.curveTo(
            mid_point[0], mid_point[1],
            mid_point[0], mid_point[1],
            end_point[0], end_point[1]
        )
        c.drawPath(path, stroke=1, fill=0)
        
        if len(median) >= 2:
            last_segment_start = mid_point
            last_segment_end = end_point
            
            dx = last_segment_end[0] - last_segment_start[0]
            dy = last_segment_end[1] - last_segment_start[1]
            angle = math.atan2(dy, dx)
            
            arrowhead_length = arrow_width * 3
            arrowhead_angle = math.pi / 6
            
            arrow_point1 = (
                end_point[0] - arrowhead_length * math.cos(angle - arrowhead_angle),
                end_point[1] - arrowhead_length * math.sin(angle - arrowhead_angle)
            )
            arrow_point2 = (
                end_point[0] - arrowhead_length * math.cos(angle + arrowhead_angle),
                end_point[1] - arrowhead_length * math.sin(angle + arrowhead_angle)
            )
            
            c.line(end_point[0], end_point[1], arrow_point1[0], arrow_point1[1])
            c.line(end_point[0], end_point[1], arrow_point2[0], arrow_point2[1])
        
        return start_point


class HanziDataLoader:
    """汉字数据加载器"""
    
    HANZI_WRITER_DATA_URL = "https://cdn.jsdelivr.net/npm/hanzi-writer-data@latest/{char}.json"
    
    @classmethod
    def load_character_data(cls, character: str) -> Optional[Dict[str, Any]]:
        """
        从CDN加载汉字笔画数据
        
        Args:
            character: 汉字字符
            
        Returns:
            汉字数据字典，包含 strokes, medians, radStrokes 字段
        """
        encoded_char = urllib.parse.quote(character)
        url = cls.HANZI_WRITER_DATA_URL.format(char=encoded_char)
        
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                return data
        except (urllib.error.URLError, json.JSONDecodeError) as e:
            print(f"加载汉字数据失败: {e}")
            return None
    
    @classmethod
    def load_character_data_from_file(cls, character: str, 
                                       data_dir: str = None) -> Optional[Dict[str, Any]]:
        """
        从本地文件加载汉字笔画数据
        
        Args:
            character: 汉字字符
            data_dir: 数据目录，默认为 stroke_data 目录
            
        Returns:
            汉字数据字典
        """
        if data_dir is None:
            data_dir = Path(__file__).parent / "stroke_data"
        else:
            data_dir = Path(data_dir)
        
        file_path = data_dir / f"{character}.json"
        
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"读取本地汉字数据失败: {e}")
        
        return None


class CopybookGenerator:
    """字帖生成器类"""
    
    def __init__(self, 
                 paper_size: Tuple[float, float] = A4,
                 grid_cols: int = 5,
                 grid_rows: int = 10,
                 font_size: int = 48,
                 font_path: Optional[str] = None,
                 grid_type: str = "mizi",
                 font_style: str = "zhenkai",
                 grid_color: Tuple[float, float, float] = (0.5, 0.5, 0.5),
                 font_color: Tuple[float, float, float] = DEFAULT_FONT_COLOR,
                 pinyin_color: Tuple[float, float, float] = DEFAULT_PINYIN_COLOR,
                 character_color: Tuple[float, float, float] = DEFAULT_CHARACTER_COLOR,
                 right_grid_color: Tuple[float, float, float] = DEFAULT_RIGHT_GRID_COLOR,
                 right_grid_type: str = DEFAULT_RIGHT_GRID_TYPE,
                 stroke_order_color: Tuple[float, float, float] = DEFAULT_STROKE_ORDER_COLOR,
                 grid_size_cm: float = DEFAULT_GRID_SIZE_CM,
                 lines_per_char: int = DEFAULT_LINES_PER_CHAR,
                 show_pinyin: bool = DEFAULT_SHOW_PINYIN,
                 show_character_pinyin: bool = DEFAULT_SHOW_CHARACTER_PINYIN,
                 student_name: str = "",
                 student_id: str = "",
                 class_name: str = ""):
        """
        初始化字帖生成器
        
        Args:
            paper_size: 纸张大小，默认A4
            grid_cols: 每行田字格数量，默认5个
            grid_rows: 每页田字格行数，默认10行
            font_size: 字体大小，默认48点
            font_path: 字体文件路径，默认使用系统字体
            grid_type: 格子类型，"mizi" 表示米字格（默认），"tianzi" 表示田字格
            font_style: 字体样式，"zhenkai" 表示正楷（默认），"xingkai" 表示行楷
            grid_color: 格子颜色（RGB元组，值为0.0-1.0），默认灰色
            font_color: 字体颜色（RGB元组，值为0.0-1.0），默认黑色
            pinyin_color: 拼音颜色（RGB元组，值为0.0-1.0），默认黑色
            character_color: 生字颜色（RGB元组，值为0.0-1.0），默认黑色
            right_grid_color: 右侧格子颜色（RGB元组，值为0.0-1.0），默认黑色
            right_grid_type: 右侧格子类型，"田字格"、"米字格"、"回宫格"、"方格"，默认米字格
            stroke_order_color: 笔顺颜色（RGB元组，值为0.0-1.0），默认黑色
            grid_size_cm: 格子大小（厘米），默认2.0cm
            lines_per_char: 每个字的行数，默认1行
            show_pinyin: 是否显示拼音（普通场景），默认False
            show_character_pinyin: 是否显示拼音（生字场景），默认True
            student_name: 学生姓名
            student_id: 学号
            class_name: 班级
        """
        self.paper_width, self.paper_height = paper_size
        self.grid_cols = grid_cols
        self.grid_rows = grid_rows
        self.font_size = font_size
        
        self.grid_type = grid_type
        self.font_style = font_style
        self.grid_color = grid_color
        self.font_color = font_color
        self.pinyin_color = pinyin_color
        self.character_color = character_color
        self.right_grid_color = right_grid_color
        self.right_grid_type = right_grid_type
        self.stroke_order_color = stroke_order_color
        self.grid_size_cm = grid_size_cm
        self.lines_per_char = max(1, min(50, lines_per_char))
        self.show_pinyin = show_pinyin
        self.show_character_pinyin = show_character_pinyin
        
        self.student_name = student_name or ""
        self.student_id = student_id or ""
        self.class_name = class_name or ""
        
        self.margin_left = 20 * mm
        self.margin_right = 20 * mm
        self.margin_top = 30 * mm
        self.margin_bottom = 20 * mm
        
        self._init_font(font_path)
        self._calculate_grid_dimensions()
        self._load_stroke_data()
    
    def _init_font(self, font_path: Optional[str]):
        """初始化字体"""
        self.font_name = "Helvetica"
        self.font_used_name = "Helvetica (默认英文字体)"
        self.font_used_path = None
        self.font_warning = None
        
        if font_path and os.path.exists(font_path):
            try:
                font_name = "CustomFont"
                pdfmetrics.registerFont(TTFont(font_name, font_path))
                self.font_name = font_name
                self.font_used_name = "自定义字体"
                self.font_used_path = font_path
                return
            except:
                pass
        
        project_font_dir = Path(__file__).parent / "fonts"
        user_font_dir = Path.home() / "Library" / "Fonts"
        system_font_dir = Path("/System/Library/Fonts")
        system_font_supplemental_dir = Path("/System/Library/Fonts/Supplemental")
        library_font_dir = Path("/Library/Fonts")
        
        font_dirs = [project_font_dir, user_font_dir, library_font_dir, system_font_dir, system_font_supplemental_dir]
        
        zhenkai_font_patterns = [
            "Kai.ttc", "STKaiti.ttc", "KaiTi.ttc", "楷体.ttc", "simkai.ttf", "KaiTi_GB2312.ttf",
            "Kai.ttf", "STKaiti.ttf", "KaiTi.ttf", "楷体.ttf",
        ]
        
        xingkai_font_patterns = [
            "STXingkai.ttc", "Xingkai.ttc", "行楷.ttc", "STXingkai.ttf", "simxingkai.ttf",
            "Xingkai.ttf", "行楷.ttf", "华文行楷.ttf", "华文行楷.ttc",
        ]
        
        fallback_fonts = [
            ("/System/Library/Fonts/Supplemental/Songti.ttc", "Songti", "宋体"),
            ("/System/Library/Fonts/STHeiti Light.ttc", "STHeitiLight", "黑体-细"),
            ("/System/Library/Fonts/STHeiti Medium.ttc", "STHeitiMedium", "黑体-中"),
            ("/System/Library/Fonts/Hiragino Sans GB.ttc", "HiraginoSansGB", "冬青黑体"),
            ("/System/Library/Fonts/ヒラギノ明朝 ProN.ttc", "HiraginoMincho", "冬青明朝"),
            ("/System/Library/Fonts/ヒラギノ丸ゴ ProN W4.ttc", "HiraginoMaruGothic", "冬青圆体"),
        ]
        
        def find_font_in_dirs(patterns):
            for font_dir in font_dirs:
                if not font_dir.exists():
                    continue
                for pattern in patterns:
                    font_file = font_dir / pattern
                    if font_file.exists():
                        return str(font_file)
                    for file in font_dir.glob("*"):
                        if file.is_file():
                            filename_lower = file.name.lower()
                            pattern_lower = pattern.lower()
                            if pattern_lower in filename_lower or filename_lower in pattern_lower:
                                return str(file)
            return None
        
        def register_font(font_path, font_name, display_name):
            try:
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                    self.font_name = font_name
                    self.font_used_name = display_name
                    self.font_used_path = font_path
                    return True
            except:
                pass
            return False
        
        requested_style = "行楷" if self.font_style == "xingkai" else "正楷"
        found_requested = False
        
        if self.font_style == "xingkai":
            xingkai_path = find_font_in_dirs(xingkai_font_patterns)
            if xingkai_path:
                if register_font(xingkai_path, "Xingkai", "行楷"):
                    found_requested = True
                    return
            
            zhenkai_path = find_font_in_dirs(zhenkai_font_patterns)
            if zhenkai_path:
                if register_font(zhenkai_path, "KaiTi", "楷体"):
                    return
        else:
            zhenkai_path = find_font_in_dirs(zhenkai_font_patterns)
            if zhenkai_path:
                if register_font(zhenkai_path, "KaiTi", "楷体"):
                    found_requested = True
                    return
            
            xingkai_path = find_font_in_dirs(xingkai_font_patterns)
            if xingkai_path:
                if register_font(xingkai_path, "Xingkai", "行楷"):
                    return
        
        for font_path, font_name, display_name in fallback_fonts:
            if register_font(font_path, font_name, display_name):
                if not found_requested:
                    self.font_warning = (
                        f"⚠️  未找到请求的{requested_style}字体，已自动回退到【{display_name}】。\n"
                        f"   如需使用{requested_style}字体，请按以下步骤操作：\n"
                        f"   1. 下载{requested_style}字体文件（.ttf 或 .ttc 格式）\n"
                        f"   2. 将字体文件放置到项目目录的 fonts/ 文件夹中\n"
                        f"   3. 或放置到 ~/Library/Fonts/ 系统字体目录\n"
                        f"   字体搜索目录（按优先级）：\n"
                        f"   - 项目目录: {project_font_dir}\n"
                        f"   - 用户字体: {user_font_dir}\n"
                        f"   - 系统字体: {system_font_dir}\n"
                    )
                return
        
        self.font_name = "Helvetica"
        self.font_used_name = "Helvetica (默认英文字体)"
        self.font_used_path = None
        self.font_warning = (
            f"⚠️  未找到任何中文字体，使用默认英文字体。\n"
            f"   请下载中文字体并放置到 fonts/ 目录或系统字体目录。"
        )
    
    def _calculate_grid_dimensions(self):
        """计算田字格尺寸"""
        usable_width = self.paper_width - self.margin_left - self.margin_right
        usable_height = self.paper_height - self.margin_top - self.margin_bottom
        
        self.grid_size = self.grid_size_cm * 10 * mm
        
        border_width = usable_width * BORDER_RATIO
        actual_usable_width = usable_width - 2 * border_width
        
        self.grid_cols = max(1, int(actual_usable_width / self.grid_size))
        self.grid_rows = max(1, int(usable_height / self.grid_size))
        
        actual_used_width = self.grid_size * self.grid_cols
        self.grid_padding = (actual_usable_width - actual_used_width) / 2 + border_width
    
    def _load_stroke_data(self):
        """加载笔画数据"""
        self.stroke_data = {}
        self.detailed_stroke_data = self._get_default_stroke_data()
        self.hanzi_writer_cache = {}
        
        stroke_data_path = Path(__file__).parent / "stroke_data" / "strokes.json"
        
        if stroke_data_path.exists():
            try:
                with open(stroke_data_path, 'r', encoding='utf-8') as f:
                    self.stroke_data = json.load(f)
            except Exception as e:
                print(f"加载笔画数据失败: {e}")
    
    def _get_hanzi_writer_data(self, character: str) -> Optional[Dict[str, Any]]:
        """
        获取汉字的详细笔画数据（从缓存或CDN加载）
        
        Args:
            character: 汉字字符
            
        Returns:
            汉字数据字典，包含 strokes, medians, radStrokes 字段
        """
        if character in self.hanzi_writer_cache:
            return self.hanzi_writer_cache[character]
        
        data = HanziDataLoader.load_character_data_from_file(character)
        if data is None:
            data = HanziDataLoader.load_character_data(character)
        
        if data is not None:
            self.hanzi_writer_cache[character] = data
        
        return data
    
    def _transform_medians_to_grid(self, 
                                    medians: List[List[float]], 
                                    grid_x: float, 
                                    grid_y: float, 
                                    grid_size: float) -> List[List[float]]:
        """
        将 hanzi-writer 的坐标系统转换到田字格坐标系统
        
        hanzi-writer 的坐标系统是：
        - 原点在左上角
        - y轴向下为正
        - 典型范围是 0-1024
        
        田字格坐标系统是：
        - 原点在左下角
        - y轴向上为正
        - 范围是 grid_x 到 grid_x + grid_size (x轴)
        - 范围是 grid_y 到 grid_y + grid_size (y轴)
        
        Args:
            medians: hanzi-writer 格式的中位数点列表
            grid_x: 田字格左下角x坐标
            grid_y: 田字格左下角y坐标
            grid_size: 田字格大小
            
        Returns:
            转换后的中位数点列表
        """
        HANZI_WRITER_MAX = 1024.0
        
        transformed = []
        for point in medians:
            x = point[0]
            y = point[1]
            
            normalized_x = x / HANZI_WRITER_MAX
            normalized_y = y / HANZI_WRITER_MAX
            
            grid_normalized_x = normalized_x
            grid_normalized_y = 1.0 - normalized_y
            
            transformed_x = grid_x + grid_normalized_x * grid_size
            transformed_y = grid_y + grid_normalized_y * grid_size
            
            transformed.append([transformed_x, transformed_y])
        
        return transformed
    
    def _draw_stroke_order_standard(self, 
                                    c: canvas.Canvas, 
                                    character: str, 
                                    grid_x: float, 
                                    grid_y: float, 
                                    grid_size: float):
        """
        绘制笔顺标准功能（改进版）：
        1. 每个字符按照国家标准标准书写笔顺，拆分出依次书写的独立笔画
        2. 每一笔分配唯一的笔顺数字序号，数字从1开始依次递增
        3. 每一笔都需要标注：笔顺数字序号 + 跟随笔画走向的书写方向引导箭头
        4. 直线笔画（竖、横、撇、捺等直线型笔画）：
           - 箭头为直线箭头，完全贴合笔画走向
           - 箭头方向=笔画实际书写运笔方向
           - 数字序号标注在直线笔画外侧相邻空白处
           - 横：箭头在笔画上方，从左到右
           - 竖：箭头在笔画右侧，从上到下
        5. 弧形笔画（圆弧、半圆、曲线型笔画）：
           - 箭头为同弧度弯曲弧形箭头，完全贴合圆弧笔画走向
           - 箭头弧度与笔画弧度完全一致
           - 箭头方向=圆弧笔画实际环绕运笔方向
           - 数字序号标注在弧形笔画外侧相邻空白处
        6. 箭头粗细：笔画粗细的1/5
        7. 箭头长度：笔画长度的1/4
        8. 转折笔画（如横折）：
           - 在笔顺开始的地方、转折的地方都存在上述标识
           - 表示是第几笔的数字只在开始的位置即可
        9. 严格按照书写先后顺序标注数字，第一笔标数字1、第二笔标数字2，以此类推
        10. 箭头完整指示每一笔：起笔位置→运笔路径→收笔位置的完整书写方向
        
        Args:
            c: PDF画布对象
            character: 汉字字符
            grid_x: 田字格左下角x坐标
            grid_y: 田字格左下角y坐标
            grid_size: 田字格大小
        """
        hanzi_data = self._get_hanzi_writer_data(character)
        
        if hanzi_data is None:
            self._draw_improved_default_stroke_order(c, character, grid_x, grid_y, grid_size)
            return
        
        medians = hanzi_data.get('medians', [])
        
        if not medians:
            self._draw_improved_default_stroke_order(c, character, grid_x, grid_y, grid_size)
            return
        
        for stroke_index, median in enumerate(medians):
            stroke_order = stroke_index + 1
            
            transformed_median = self._transform_medians_to_grid(
                median, grid_x, grid_y, grid_size
            )
            
            if len(transformed_median) < 2:
                continue
            
            self._draw_improved_stroke_with_arrow(
                c, transformed_median, stroke_order,
                grid_x, grid_y, grid_size
            )
    
    def _draw_stroke_number(self, 
                           c: canvas.Canvas, 
                           stroke_order: int, 
                           median: List[List[float]], 
                           stroke_type: str,
                           grid_x: float, 
                           grid_y: float, 
                           grid_size: float):
        """
        在笔画外侧相邻空白处标注笔顺数字序号
        
        Args:
            c: PDF画布对象
            stroke_order: 笔顺数字序号
            median: 笔画中位数点列表
            stroke_type: 笔画类型（直线型或弧形）
            grid_x: 田字格左下角x坐标
            grid_y: 田字格左下角y坐标
            grid_size: 田字格大小
        """
        if len(median) < 2:
            return
        
        start_point = median[0]
        end_point = median[-1]
        
        label_offset = 12
        font_size = 10
        
        c.setFillColor(blue)
        c.setFont("Helvetica-Bold", font_size)
        
        order_text = str(stroke_order)
        order_width = c.stringWidth(order_text, "Helvetica-Bold", font_size)
        order_height = font_size
        
        mid_index = len(median) // 2
        mid_point = median[mid_index]
        
        direction = StrokeAnalyzer.get_stroke_direction(median)
        dx, dy = direction
        
        direction_length = math.sqrt(dx * dx + dy * dy)
        if direction_length < 1e-10:
            direction_length = 1.0
        
        normalized_dx = dx / direction_length
        normalized_dy = dy / direction_length
        
        perpendicular_dx = -normalized_dy
        perpendicular_dy = normalized_dx
        
        test_offset = 5
        
        test_point1 = (
            mid_point[0] + perpendicular_dx * test_offset,
            mid_point[1] + perpendicular_dy * test_offset
        )
        test_point2 = (
            mid_point[0] - perpendicular_dx * test_offset,
            mid_point[1] - perpendicular_dy * test_offset
        )
        
        dist1 = self._get_min_distance_to_other_strokes(test_point1, median)
        dist2 = self._get_min_distance_to_other_strokes(test_point2, median)
        
        if dist1 > dist2:
            label_dx = perpendicular_dx
            label_dy = perpendicular_dy
        else:
            label_dx = -perpendicular_dx
            label_dy = -perpendicular_dy
        
        label_x = mid_point[0] + label_dx * label_offset
        label_y = mid_point[1] + label_dy * label_offset
        
        label_x = max(grid_x + 2, min(grid_x + grid_size - order_width - 2, label_x))
        label_y = max(grid_y + 2, min(grid_y + grid_size - order_height - 2, label_y))
        
        c.drawString(label_x, label_y, order_text)
    
    def _get_min_distance_to_other_strokes(self, 
                                            point: Tuple[float, float], 
                                            current_stroke_median: List[List[float]]) -> float:
        """
        计算点到其他笔画的最小距离（简化版，只考虑与当前笔画的距离）
        
        Args:
            point: 测试点坐标
            current_stroke_median: 当前笔画的中位数点列表
            
        Returns:
            最小距离
        """
        min_dist = float('inf')
        
        for stroke_point in current_stroke_median:
            dist = math.sqrt(
                (point[0] - stroke_point[0])**2 + 
                (point[1] - stroke_point[1])**2
            )
            min_dist = min(min_dist, dist)
        
        return min_dist
    
    def _draw_default_stroke_order(self, 
                                   c: canvas.Canvas, 
                                   character: str, 
                                   grid_x: float, 
                                   grid_y: float, 
                                   grid_size: float):
        """
        当无法获取 hanzi-writer 数据时，使用默认的笔画顺序绘制
        
        Args:
            c: PDF画布对象
            character: 汉字字符
            grid_x: 田字格左下角x坐标
            grid_y: 田字格左下角y坐标
            grid_size: 田字格大小
        """
        strokes = self.detailed_stroke_data.get(character, [])
        
        if not strokes:
            default_strokes = self.stroke_data.get(character, [])
            if default_strokes:
                for i, stroke_name in enumerate(default_strokes):
                    stroke_order = i + 1
                    
                    angle_step = 2 * math.pi / len(default_strokes)
                    angle = i * angle_step
                    
                    center_x = grid_x + grid_size / 2
                    center_y = grid_y + grid_size / 2
                    radius = grid_size * 0.3
                    
                    start_x = center_x
                    start_y = center_y
                    end_x = center_x + radius * math.cos(angle)
                    end_y = center_y + radius * math.sin(angle)
                    
                    ArrowDrawer.draw_linear_arrow(
                        c, (start_x, start_y), (end_x, end_y),
                        color=red, line_width=1.0
                    )
                    
                    c.setFillColor(blue)
                    c.setFont("Helvetica-Bold", 10)
                    order_text = str(stroke_order)
                    order_width = c.stringWidth(order_text, "Helvetica-Bold", 10)
                    
                    label_x = end_x + 5
                    label_y = end_y + 5
                    
                    label_x = max(grid_x + 2, min(grid_x + grid_size - order_width - 2, label_x))
                    label_y = max(grid_y + 2, min(grid_y + grid_size - 12, label_y))
                    
                    c.drawString(label_x, label_y, order_text)
            return
        
        for stroke in strokes:
            start_x = grid_x + stroke["start_x"] * grid_size
            start_y = grid_y + stroke["start_y"] * grid_size
            end_x = grid_x + stroke["end_x"] * grid_size
            end_y = grid_y + stroke["end_y"] * grid_size
            
            if stroke["direction"] == StrokeDirection.CURVED:
                mid_x = (start_x + end_x) / 2
                mid_y = (start_y + end_y) / 2 + grid_size * 0.1
                
                ArrowDrawer.draw_curved_arrow(
                    c, [[start_x, start_y], [mid_x, mid_y], [end_x, end_y]],
                    color=red, line_width=1.0
                )
            else:
                ArrowDrawer.draw_linear_arrow(
                    c, (start_x, start_y), (end_x, end_y),
                    color=red, line_width=1.0
                )
            
            c.setFillColor(blue)
            c.setFont("Helvetica-Bold", 10)
            order_text = str(stroke["order"])
            order_width = c.stringWidth(order_text, "Helvetica-Bold", 10)
            
            mid_x = (start_x + end_x) / 2
            mid_y = (start_y + end_y) / 2
            
            label_offset = 12
            if stroke["direction"] == StrokeDirection.LEFT_TO_RIGHT:
                label_x = end_x + label_offset / 2
                label_y = mid_y - 3
            elif stroke["direction"] == StrokeDirection.TOP_TO_BOTTOM:
                label_x = mid_x - order_width / 2
                label_y = end_y - label_offset
            elif stroke["direction"] == StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT:
                label_x = end_x + label_offset / 2
                label_y = end_y - label_offset / 2
            elif stroke["direction"] == StrokeDirection.TOP_RIGHT_TO_BOTTOM_LEFT:
                label_x = end_x - label_offset - order_width
                label_y = end_y - label_offset / 2
            else:
                label_x = mid_x - order_width / 2
                label_y = mid_y
            
            label_x = max(grid_x + 2, min(grid_x + grid_size - order_width - 2, label_x))
            label_y = max(grid_y + 2, min(grid_y + grid_size - 12, label_y))
            
            c.drawString(label_x, label_y, order_text)
    
    def _draw_improved_stroke_with_arrow(self,
                                         c: canvas.Canvas,
                                         median: List[List[float]],
                                         stroke_order: int,
                                         grid_x: float,
                                         grid_y: float,
                                         grid_size: float):
        """
        绘制改进版的带箭头笔画
        
        每个笔画的标识沿着该笔画的走势，避免集中在一起。
        横笔画：根据在田字格中的位置，选择向上或向下偏移
        竖笔画：根据在田字格中的位置，选择向左或向右偏移
        斜笔画：根据在田字格中的位置，选择合适的对角线方向偏移
        
        Args:
            c: PDF画布对象
            median: 笔画中位数点列表
            stroke_order: 笔顺数字序号
            grid_x: 田字格左下角x坐标
            grid_y: 田字格左下角y坐标
            grid_size: 田字格大小
        """
        if len(median) < 2:
            return
        
        primary_direction = ImprovedStrokeAnalyzer.get_stroke_primary_direction(median)
        
        stroke_type = StrokeAnalyzer.analyze_stroke_type(median)
        
        start_point, end_point = StrokeAnalyzer.get_stroke_endpoints(median)
        
        total_length = 0.0
        for i in range(len(median) - 1):
            segment_length = math.sqrt(
                (median[i + 1][0] - median[i][0])**2 + 
                (median[i + 1][1] - median[i][1])**2
            )
            total_length += segment_length
        
        if total_length < 1e-10:
            return
        
        arrow_length, arrow_width, base_stroke_width = ImprovedArrowDrawer.calculate_arrow_dimensions(
            grid_size, total_length
        )
        
        offset_direction = ImprovedStrokeAnalyzer.get_best_offset_direction(
            median, grid_x, grid_y, grid_size, stroke_order - 1, 10
        )
        
        offset_distance = base_stroke_width * 5
        
        segments = ImprovedStrokeAnalyzer.split_stroke_into_segments(median)
        
        number_drawn = False
        
        for segment_index, segment in enumerate(segments):
            segment_length = segment.get_length()
            if segment_length < 1e-10:
                continue
            
            segment_direction = segment.get_direction()
            
            if stroke_type == StrokeType.LINEAR:
                arrow_start = segment.start
                
                actual_arrow_length = min(arrow_length, segment_length * 0.5)
                
                arrow_start_pos = (
                    arrow_start[0] + offset_direction[0] * offset_distance,
                    arrow_start[1] + offset_direction[1] * offset_distance
                )
                
                drawn_arrow_start = ImprovedArrowDrawer.draw_short_arrow(
                    c,
                    arrow_start,
                    segment_direction,
                    actual_arrow_length,
                    arrow_width,
                    offset_direction,
                    offset_distance,
                    color=light_red
                )
                
                if not number_drawn and drawn_arrow_start is not None:
                    ImprovedArrowDrawer.draw_stroke_number(
                        c,
                        stroke_order,
                        drawn_arrow_start,
                        arrow_width,
                        color=blue
                    )
                    number_drawn = True
            else:
                arrow_start_pos = ImprovedArrowDrawer.draw_curved_short_arrow(
                    c,
                    median,
                    ImprovedArrowDrawer.ARROW_LENGTH_RATIO,
                    arrow_width,
                    offset_direction,
                    offset_distance,
                    color=light_red
                )
                
                if not number_drawn and arrow_start_pos is not None:
                    ImprovedArrowDrawer.draw_stroke_number(
                        c,
                        stroke_order,
                        arrow_start_pos,
                        arrow_width,
                        color=blue
                    )
                    number_drawn = True
    
    def _draw_improved_default_stroke_order(self,
                                            c: canvas.Canvas,
                                            character: str,
                                            grid_x: float,
                                            grid_y: float,
                                            grid_size: float):
        """
        改进版的默认笔画顺序绘制（当无法获取 hanzi-writer 数据时使用）
        
        Args:
            c: PDF画布对象
            character: 汉字字符
            grid_x: 田字格左下角x坐标
            grid_y: 田字格左下角y坐标
            grid_size: 田字格大小
        """
        strokes = self.detailed_stroke_data.get(character, [])
        
        if not strokes:
            default_strokes = self.stroke_data.get(character, [])
            if default_strokes:
                for i, stroke_name in enumerate(default_strokes):
                    stroke_order = i + 1
                    
                    angle_step = 2 * math.pi / len(default_strokes)
                    angle = i * angle_step
                    
                    center_x = grid_x + grid_size / 2
                    center_y = grid_y + grid_size / 2
                    radius = grid_size * 0.3
                    
                    start_x = center_x
                    start_y = center_y
                    end_x = center_x + radius * math.cos(angle)
                    end_y = center_y + radius * math.sin(angle)
                    
                    total_length = radius
                    arrow_length, arrow_width, base_stroke_width = ImprovedArrowDrawer.calculate_arrow_dimensions(
                        grid_size, total_length
                    )
                    
                    direction = (end_x - start_x, end_y - start_y)
                    offset_direction = (0.7, 0.7)
                    offset_distance = base_stroke_width * 3
                    
                    actual_arrow_length = min(arrow_length, total_length * 0.5)
                    
                    drawn_arrow_start = ImprovedArrowDrawer.draw_short_arrow(
                        c,
                        (start_x, start_y),
                        direction,
                        actual_arrow_length,
                        arrow_width,
                        offset_direction,
                        offset_distance,
                        color=light_red
                    )
                    
                    if drawn_arrow_start is not None:
                        ImprovedArrowDrawer.draw_stroke_number(
                            c,
                            stroke_order,
                            drawn_arrow_start,
                            arrow_width,
                            color=blue
                        )
            return
        
        for stroke in strokes:
            stroke_order = stroke["order"]
            
            start_x = grid_x + stroke["start_x"] * grid_size
            start_y = grid_y + stroke["start_y"] * grid_size
            end_x = grid_x + stroke["end_x"] * grid_size
            end_y = grid_y + stroke["end_y"] * grid_size
            
            total_length = math.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
            arrow_length, arrow_width, base_stroke_width = ImprovedArrowDrawer.calculate_arrow_dimensions(
                grid_size, total_length
            )
            
            direction = (end_x - start_x, end_y - start_y)
            
            if stroke["direction"] == StrokeDirection.LEFT_TO_RIGHT:
                offset_direction = (0.0, 1.0)
            elif stroke["direction"] == StrokeDirection.TOP_TO_BOTTOM:
                offset_direction = (1.0, 0.0)
            else:
                offset_direction = (0.7, 0.7)
            
            offset_distance = base_stroke_width * 3
            
            if stroke["direction"] == StrokeDirection.CURVED:
                median = [
                    [start_x, start_y],
                    [(start_x + end_x) / 2, (start_y + end_y) / 2 + grid_size * 0.1],
                    [end_x, end_y]
                ]
                
                arrow_start_pos = ImprovedArrowDrawer.draw_curved_short_arrow(
                    c,
                    median,
                    ImprovedArrowDrawer.ARROW_LENGTH_RATIO,
                    arrow_width,
                    offset_direction,
                    offset_distance,
                    color=light_red
                )
                
                if arrow_start_pos is not None:
                    ImprovedArrowDrawer.draw_stroke_number(
                        c,
                        stroke_order,
                        arrow_start_pos,
                        arrow_width,
                        color=blue
                    )
            else:
                actual_arrow_length = min(arrow_length, total_length * 0.5)
                
                drawn_arrow_start = ImprovedArrowDrawer.draw_short_arrow(
                    c,
                    (start_x, start_y),
                    direction,
                    actual_arrow_length,
                    arrow_width,
                    offset_direction,
                    offset_distance,
                    color=light_red
                )
                
                if drawn_arrow_start is not None:
                    ImprovedArrowDrawer.draw_stroke_number(
                        c,
                        stroke_order,
                        drawn_arrow_start,
                        arrow_width,
                        color=blue
                    )
    
    def _get_default_stroke_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        获取默认的详细笔画数据
        
        Returns:
            Dict[str, List[Dict]]: 汉字到详细笔画列表的映射
        """
        return {
            "一": [
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.2, "start_y": 0.5, "end_x": 0.8, "end_y": 0.5, "order": 1}
            ],
            "二": [
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.25, "start_y": 0.65, "end_x": 0.75, "end_y": 0.65, "order": 1},
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.15, "start_y": 0.35, "end_x": 0.85, "end_y": 0.35, "order": 2}
            ],
            "三": [
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.25, "start_y": 0.7, "end_x": 0.75, "end_y": 0.7, "order": 1},
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.3, "start_y": 0.5, "end_x": 0.7, "end_y": 0.5, "order": 2},
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.15, "start_y": 0.3, "end_x": 0.85, "end_y": 0.3, "order": 3}
            ],
            "十": [
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.15, "start_y": 0.5, "end_x": 0.85, "end_y": 0.5, "order": 1},
                {"type": StrokeType.SHU, "direction": StrokeDirection.TOP_TO_BOTTOM, 
                 "start_x": 0.5, "start_y": 0.85, "end_x": 0.5, "end_y": 0.15, "order": 2}
            ],
            "人": [
                {"type": StrokeType.PIE, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.5, "start_y": 0.85, "end_x": 0.15, "end_y": 0.15, "order": 1},
                {"type": StrokeType.NA, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.5, "start_y": 0.85, "end_x": 0.85, "end_y": 0.15, "order": 2}
            ],
            "大": [
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.2, "start_y": 0.65, "end_x": 0.8, "end_y": 0.65, "order": 1},
                {"type": StrokeType.PIE, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.5, "start_y": 0.85, "end_x": 0.2, "end_y": 0.2, "order": 2},
                {"type": StrokeType.NA, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.5, "start_y": 0.85, "end_x": 0.8, "end_y": 0.15, "order": 3}
            ],
            "天": [
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.25, "start_y": 0.75, "end_x": 0.75, "end_y": 0.75, "order": 1},
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.2, "start_y": 0.55, "end_x": 0.8, "end_y": 0.55, "order": 2},
                {"type": StrokeType.PIE, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.5, "start_y": 0.75, "end_x": 0.2, "end_y": 0.15, "order": 3},
                {"type": StrokeType.NA, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.5, "start_y": 0.75, "end_x": 0.8, "end_y": 0.15, "order": 4}
            ],
            "永": [
                {"type": StrokeType.DIAN, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.5, "start_y": 0.9, "end_x": 0.45, "end_y": 0.8, "order": 1},
                {"type": StrokeType.HENG_ZHE_GOU, "direction": StrokeDirection.CURVED, 
                 "start_x": 0.3, "start_y": 0.75, "end_x": 0.7, "end_y": 0.75, "order": 2},
                {"type": StrokeType.HENG_PIE, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.35, "start_y": 0.55, "end_x": 0.25, "end_y": 0.35, "order": 3},
                {"type": StrokeType.PIE, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.5, "start_y": 0.55, "end_x": 0.35, "end_y": 0.2, "order": 4},
                {"type": StrokeType.NA, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.5, "start_y": 0.55, "end_x": 0.75, "end_y": 0.15, "order": 5}
            ],
            "木": [
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.2, "start_y": 0.65, "end_x": 0.8, "end_y": 0.65, "order": 1},
                {"type": StrokeType.SHU, "direction": StrokeDirection.TOP_TO_BOTTOM, 
                 "start_x": 0.5, "start_y": 0.85, "end_x": 0.5, "end_y": 0.15, "order": 2},
                {"type": StrokeType.PIE, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.5, "start_y": 0.5, "end_x": 0.2, "end_y": 0.2, "order": 3},
                {"type": StrokeType.NA, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.5, "start_y": 0.5, "end_x": 0.8, "end_y": 0.15, "order": 4}
            ],
            "日": [
                {"type": StrokeType.SHU, "direction": StrokeDirection.TOP_TO_BOTTOM, 
                 "start_x": 0.25, "start_y": 0.85, "end_x": 0.25, "end_y": 0.15, "order": 1},
                {"type": StrokeType.HENG_ZHE, "direction": StrokeDirection.CURVED, 
                 "start_x": 0.25, "start_y": 0.85, "end_x": 0.75, "end_y": 0.15, "order": 2},
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.25, "start_y": 0.5, "end_x": 0.75, "end_y": 0.5, "order": 3},
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.25, "start_y": 0.15, "end_x": 0.75, "end_y": 0.15, "order": 4}
            ],
            "月": [
                {"type": StrokeType.PIE, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.35, "start_y": 0.85, "end_x": 0.15, "end_y": 0.15, "order": 1},
                {"type": StrokeType.HENG_ZHE_GOU, "direction": StrokeDirection.CURVED, 
                 "start_x": 0.35, "start_y": 0.85, "end_x": 0.85, "end_y": 0.15, "order": 2},
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.35, "start_y": 0.55, "end_x": 0.75, "end_y": 0.55, "order": 3},
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.35, "start_y": 0.35, "end_x": 0.75, "end_y": 0.35, "order": 4}
            ],
            "水": [
                {"type": StrokeType.SHU_GOU, "direction": StrokeDirection.TOP_TO_BOTTOM, 
                 "start_x": 0.5, "start_y": 0.85, "end_x": 0.5, "end_y": 0.15, "order": 1},
                {"type": StrokeType.HENG_PIE, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.35, "start_y": 0.6, "end_x": 0.2, "end_y": 0.4, "order": 2},
                {"type": StrokeType.PIE, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.5, "start_y": 0.5, "end_x": 0.3, "end_y": 0.25, "order": 3},
                {"type": StrokeType.NA, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.5, "start_y": 0.5, "end_x": 0.75, "end_y": 0.15, "order": 4}
            ],
            "火": [
                {"type": StrokeType.DIAN, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.35, "start_y": 0.8, "end_x": 0.3, "end_y": 0.7, "order": 1},
                {"type": StrokeType.PIE, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.5, "start_y": 0.85, "end_x": 0.25, "end_y": 0.35, "order": 2},
                {"type": StrokeType.PIE, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.6, "start_y": 0.65, "end_x": 0.45, "end_y": 0.25, "order": 3},
                {"type": StrokeType.NA, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.5, "start_y": 0.65, "end_x": 0.8, "end_y": 0.15, "order": 4}
            ],
            "山": [
                {"type": StrokeType.SHU, "direction": StrokeDirection.TOP_TO_BOTTOM, 
                 "start_x": 0.5, "start_y": 0.85, "end_x": 0.5, "end_y": 0.2, "order": 1},
                {"type": StrokeType.SHU_ZHE, "direction": StrokeDirection.CURVED, 
                 "start_x": 0.5, "start_y": 0.65, "end_x": 0.15, "end_y": 0.2, "order": 2},
                {"type": StrokeType.SHU, "direction": StrokeDirection.TOP_TO_BOTTOM, 
                 "start_x": 0.85, "start_y": 0.65, "end_x": 0.85, "end_y": 0.2, "order": 3}
            ],
            "田": [
                {"type": StrokeType.SHU, "direction": StrokeDirection.TOP_TO_BOTTOM, 
                 "start_x": 0.2, "start_y": 0.85, "end_x": 0.2, "end_y": 0.15, "order": 1},
                {"type": StrokeType.HENG_ZHE, "direction": StrokeDirection.CURVED, 
                 "start_x": 0.2, "start_y": 0.85, "end_x": 0.8, "end_y": 0.15, "order": 2},
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.2, "start_y": 0.5, "end_x": 0.8, "end_y": 0.5, "order": 3},
                {"type": StrokeType.SHU, "direction": StrokeDirection.TOP_TO_BOTTOM, 
                 "start_x": 0.5, "start_y": 0.85, "end_x": 0.5, "end_y": 0.15, "order": 4},
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.2, "start_y": 0.15, "end_x": 0.8, "end_y": 0.15, "order": 5}
            ],
            "王": [
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.25, "start_y": 0.8, "end_x": 0.75, "end_y": 0.8, "order": 1},
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.3, "start_y": 0.55, "end_x": 0.7, "end_y": 0.55, "order": 2},
                {"type": StrokeType.SHU, "direction": StrokeDirection.TOP_TO_BOTTOM, 
                 "start_x": 0.5, "start_y": 0.8, "end_x": 0.5, "end_y": 0.2, "order": 3},
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.2, "start_y": 0.2, "end_x": 0.8, "end_y": 0.2, "order": 4}
            ],
            "土": [
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.25, "start_y": 0.7, "end_x": 0.75, "end_y": 0.7, "order": 1},
                {"type": StrokeType.SHU, "direction": StrokeDirection.TOP_TO_BOTTOM, 
                 "start_x": 0.5, "start_y": 0.7, "end_x": 0.5, "end_y": 0.35, "order": 2},
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.2, "start_y": 0.2, "end_x": 0.8, "end_y": 0.2, "order": 3}
            ],
            "女": [
                {"type": StrokeType.PIE_DIAN, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.5, "start_y": 0.7, "end_x": 0.25, "end_y": 0.35, "order": 1},
                {"type": StrokeType.PIE, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.5, "start_y": 0.7, "end_x": 0.7, "end_y": 0.35, "order": 2},
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.2, "start_y": 0.35, "end_x": 0.8, "end_y": 0.35, "order": 3}
            ],
            "子": [
                {"type": StrokeType.HENG_PIE, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.3, "start_y": 0.75, "end_x": 0.2, "end_y": 0.55, "order": 1},
                {"type": StrokeType.WAN_GOU, "direction": StrokeDirection.CURVED, 
                 "start_x": 0.5, "start_y": 0.75, "end_x": 0.5, "end_y": 0.2, "order": 2},
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.2, "start_y": 0.3, "end_x": 0.8, "end_y": 0.3, "order": 3}
            ],
            "马": [
                {"type": StrokeType.HENG_ZHE, "direction": StrokeDirection.CURVED, 
                 "start_x": 0.25, "start_y": 0.8, "end_x": 0.75, "end_y": 0.55, "order": 1},
                {"type": StrokeType.SHU_ZHE_ZHE_GOU, "direction": StrokeDirection.CURVED, 
                 "start_x": 0.5, "start_y": 0.8, "end_x": 0.5, "end_y": 0.2, "order": 2},
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.25, "start_y": 0.2, "end_x": 0.75, "end_y": 0.2, "order": 3}
            ],
            "牛": [
                {"type": StrokeType.PIE, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.5, "start_y": 0.85, "end_x": 0.25, "end_y": 0.55, "order": 1},
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.2, "start_y": 0.65, "end_x": 0.8, "end_y": 0.65, "order": 2},
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.25, "start_y": 0.45, "end_x": 0.75, "end_y": 0.45, "order": 3},
                {"type": StrokeType.SHU, "direction": StrokeDirection.TOP_TO_BOTTOM, 
                 "start_x": 0.5, "start_y": 0.85, "end_x": 0.5, "end_y": 0.15, "order": 4}
            ],
            "羊": [
                {"type": StrokeType.DIAN, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.35, "start_y": 0.9, "end_x": 0.3, "end_y": 0.8, "order": 1},
                {"type": StrokeType.PIE, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.5, "start_y": 0.9, "end_x": 0.3, "end_y": 0.6, "order": 2},
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.25, "start_y": 0.7, "end_x": 0.75, "end_y": 0.7, "order": 3},
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.3, "start_y": 0.5, "end_x": 0.7, "end_y": 0.5, "order": 4},
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.2, "start_y": 0.3, "end_x": 0.8, "end_y": 0.3, "order": 5},
                {"type": StrokeType.SHU, "direction": StrokeDirection.TOP_TO_BOTTOM, 
                 "start_x": 0.5, "start_y": 0.9, "end_x": 0.5, "end_y": 0.15, "order": 6}
            ],
            "鸟": [
                {"type": StrokeType.PIE, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.5, "start_y": 0.9, "end_x": 0.3, "end_y": 0.65, "order": 1},
                {"type": StrokeType.HENG_ZHE_GOU, "direction": StrokeDirection.CURVED, 
                 "start_x": 0.35, "start_y": 0.9, "end_x": 0.8, "end_y": 0.5, "order": 2},
                {"type": StrokeType.DIAN, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.6, "start_y": 0.7, "end_x": 0.55, "end_y": 0.6, "order": 3},
                {"type": StrokeType.SHU_ZHE_ZHE_GOU, "direction": StrokeDirection.CURVED, 
                 "start_x": 0.5, "start_y": 0.5, "end_x": 0.5, "end_y": 0.15, "order": 4},
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.35, "start_y": 0.35, "end_x": 0.65, "end_y": 0.35, "order": 5}
            ],
            "心": [
                {"type": StrokeType.DIAN, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.25, "start_y": 0.6, "end_x": 0.2, "end_y": 0.5, "order": 1},
                {"type": StrokeType.WO_GOU, "direction": StrokeDirection.CURVED, 
                 "start_x": 0.3, "start_y": 0.5, "end_x": 0.7, "end_y": 0.25, "order": 2},
                {"type": StrokeType.DIAN, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.6, "start_y": 0.5, "end_x": 0.55, "end_y": 0.4, "order": 3},
                {"type": StrokeType.DIAN, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.75, "start_y": 0.6, "end_x": 0.7, "end_y": 0.5, "order": 4}
            ],
            "手": [
                {"type": StrokeType.PIE, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.5, "start_y": 0.9, "end_x": 0.3, "end_y": 0.65, "order": 1},
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.2, "start_y": 0.7, "end_x": 0.8, "end_y": 0.7, "order": 2},
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.25, "start_y": 0.45, "end_x": 0.75, "end_y": 0.45, "order": 3},
                {"type": StrokeType.SHU_GOU, "direction": StrokeDirection.TOP_TO_BOTTOM, 
                 "start_x": 0.5, "start_y": 0.9, "end_x": 0.5, "end_y": 0.2, "order": 4}
            ],
            "耳": [
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.25, "start_y": 0.85, "end_x": 0.75, "end_y": 0.85, "order": 1},
                {"type": StrokeType.SHU, "direction": StrokeDirection.TOP_TO_BOTTOM, 
                 "start_x": 0.25, "start_y": 0.85, "end_x": 0.25, "end_y": 0.15, "order": 2},
                {"type": StrokeType.SHU, "direction": StrokeDirection.TOP_TO_BOTTOM, 
                 "start_x": 0.75, "start_y": 0.85, "end_x": 0.75, "end_y": 0.15, "order": 3},
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.25, "start_y": 0.65, "end_x": 0.75, "end_y": 0.65, "order": 4},
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.25, "start_y": 0.4, "end_x": 0.75, "end_y": 0.4, "order": 5},
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.25, "start_y": 0.15, "end_x": 0.75, "end_y": 0.15, "order": 6}
            ],
            "目": [
                {"type": StrokeType.SHU, "direction": StrokeDirection.TOP_TO_BOTTOM, 
                 "start_x": 0.2, "start_y": 0.85, "end_x": 0.2, "end_y": 0.15, "order": 1},
                {"type": StrokeType.HENG_ZHE, "direction": StrokeDirection.CURVED, 
                 "start_x": 0.2, "start_y": 0.85, "end_x": 0.8, "end_y": 0.15, "order": 2},
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.2, "start_y": 0.65, "end_x": 0.8, "end_y": 0.65, "order": 3},
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.2, "start_y": 0.45, "end_x": 0.8, "end_y": 0.45, "order": 4},
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.2, "start_y": 0.15, "end_x": 0.8, "end_y": 0.15, "order": 5}
            ],
            "小": [
                {"type": StrokeType.SHU_GOU, "direction": StrokeDirection.TOP_TO_BOTTOM, 
                 "start_x": 0.5, "start_y": 0.85, "end_x": 0.5, "end_y": 0.2, "order": 1},
                {"type": StrokeType.PIE, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.5, "start_y": 0.5, "end_x": 0.25, "end_y": 0.25, "order": 2},
                {"type": StrokeType.DIAN, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.5, "start_y": 0.5, "end_x": 0.75, "end_y": 0.25, "order": 3}
            ],
            "多": [
                {"type": StrokeType.PIE, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.5, "start_y": 0.9, "end_x": 0.25, "end_y": 0.65, "order": 1},
                {"type": StrokeType.HENG_PIE, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.35, "start_y": 0.75, "end_x": 0.25, "end_y": 0.5, "order": 2},
                {"type": StrokeType.DIAN, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.5, "start_y": 0.65, "end_x": 0.55, "end_y": 0.55, "order": 3},
                {"type": StrokeType.PIE, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.5, "start_y": 0.5, "end_x": 0.25, "end_y": 0.2, "order": 4},
                {"type": StrokeType.HENG_PIE, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.35, "start_y": 0.35, "end_x": 0.25, "end_y": 0.15, "order": 5},
                {"type": StrokeType.DIAN, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.5, "start_y": 0.25, "end_x": 0.55, "end_y": 0.15, "order": 6}
            ],
            "少": [
                {"type": StrokeType.SHU, "direction": StrokeDirection.TOP_TO_BOTTOM, 
                 "start_x": 0.5, "start_y": 0.85, "end_x": 0.5, "end_y": 0.4, "order": 1},
                {"type": StrokeType.PIE, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.5, "start_y": 0.6, "end_x": 0.3, "end_y": 0.35, "order": 2},
                {"type": StrokeType.DIAN, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.5, "start_y": 0.4, "end_x": 0.65, "end_y": 0.25, "order": 3},
                {"type": StrokeType.PIE, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.7, "start_y": 0.7, "end_x": 0.55, "end_y": 0.45, "order": 4}
            ],
            "上": [
                {"type": StrokeType.SHU, "direction": StrokeDirection.TOP_TO_BOTTOM, 
                 "start_x": 0.5, "start_y": 0.85, "end_x": 0.5, "end_y": 0.4, "order": 1},
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.25, "start_y": 0.65, "end_x": 0.75, "end_y": 0.65, "order": 2},
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.2, "start_y": 0.2, "end_x": 0.8, "end_y": 0.2, "order": 3}
            ],
            "下": [
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.2, "start_y": 0.8, "end_x": 0.8, "end_y": 0.8, "order": 1},
                {"type": StrokeType.SHU, "direction": StrokeDirection.TOP_TO_BOTTOM, 
                 "start_x": 0.5, "start_y": 0.8, "end_x": 0.5, "end_y": 0.3, "order": 2},
                {"type": StrokeType.DIAN, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.5, "start_y": 0.5, "end_x": 0.65, "end_y": 0.35, "order": 3}
            ],
            "左": [
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.25, "start_y": 0.8, "end_x": 0.75, "end_y": 0.8, "order": 1},
                {"type": StrokeType.PIE, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.5, "start_y": 0.8, "end_x": 0.2, "end_y": 0.3, "order": 2},
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.3, "start_y": 0.5, "end_x": 0.7, "end_y": 0.5, "order": 3},
                {"type": StrokeType.SHU, "direction": StrokeDirection.TOP_TO_BOTTOM, 
                 "start_x": 0.5, "start_y": 0.5, "end_x": 0.5, "end_y": 0.2, "order": 4},
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.3, "start_y": 0.2, "end_x": 0.7, "end_y": 0.2, "order": 5}
            ],
            "右": [
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.25, "start_y": 0.8, "end_x": 0.75, "end_y": 0.8, "order": 1},
                {"type": StrokeType.PIE, "direction": StrokeDirection.TOP_LEFT_TO_BOTTOM_RIGHT, 
                 "start_x": 0.5, "start_y": 0.8, "end_x": 0.25, "end_y": 0.4, "order": 2},
                {"type": StrokeType.SHU, "direction": StrokeDirection.TOP_TO_BOTTOM, 
                 "start_x": 0.5, "start_y": 0.6, "end_x": 0.5, "end_y": 0.2, "order": 3},
                {"type": StrokeType.HENG_ZHE, "direction": StrokeDirection.CURVED, 
                 "start_x": 0.5, "start_y": 0.6, "end_x": 0.8, "end_y": 0.2, "order": 4},
                {"type": StrokeType.HENG, "direction": StrokeDirection.LEFT_TO_RIGHT, 
                 "start_x": 0.5, "start_y": 0.2, "end_x": 0.8, "end_y": 0.2, "order": 5}
            ]
        }
    
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
    
    def _draw_arrow(self, c: canvas.Canvas, 
                    start_x: float, start_y: float, 
                    end_x: float, end_y: float, 
                    color: Color = red, 
                    line_width: float = 0.5,
                    arrow_size: float = 6):
        """
        绘制带箭头的细线，表示笔画走势
        
        Args:
            c: PDF画布对象
            start_x: 起点x坐标
            start_y: 起点y坐标
            end_x: 终点x坐标
            end_y: 终点y坐标
            color: 箭头颜色
            line_width: 线宽（很细）
            arrow_size: 箭头大小
        """
        c.setStrokeColor(color)
        c.setLineWidth(line_width)
        
        c.line(start_x, start_y, end_x, end_y)
        
        c.setFillColor(color)
        p = c.beginPath()
        p.moveTo(end_x, end_y)
        
        angle = math.atan2(end_y - start_y, end_x - start_x)
        arrow_angle = math.pi / 6
        
        arrow_x1 = end_x - arrow_size * math.cos(angle - arrow_angle)
        arrow_y1 = end_y - arrow_size * math.sin(angle - arrow_angle)
        
        arrow_x2 = end_x - arrow_size * math.cos(angle + arrow_angle)
        arrow_y2 = end_y - arrow_size * math.sin(angle + arrow_angle)
        
        p.lineTo(arrow_x1, arrow_y1)
        p.lineTo(arrow_x2, arrow_y2)
        p.close()
        c.drawPath(p, fill=1, stroke=0)
    
    def _draw_start_marker(self, c: canvas.Canvas, 
                           x: float, y: float, 
                           color: Color = red, 
                           radius: float = 3):
        """
        绘制起点标记（小圆圈）
        
        Args:
            c: PDF画布对象
            x: 中心x坐标
            y: 中心y坐标
            color: 颜色
            radius: 半径
        """
        c.setStrokeColor(color)
        c.setFillColor(color)
        c.setLineWidth(1)
        
        p = c.beginPath()
        p.circle(x, y, radius)
        c.drawPath(p, fill=1, stroke=0)
    
    def _draw_dashed_line(self, c: canvas.Canvas, x1: float, y1: float, x2: float, y2: float, dash_length: float = 2):
        """
        绘制虚线
        
        Args:
            c: PDF画布对象
            x1, y1: 起点坐标
            x2, y2: 终点坐标
            dash_length: 虚线每段长度
        """
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx * dx + dy * dy)
        dash_count = int(length / (dash_length * 2))
        if dash_count < 1:
            dash_count = 1
        
        actual_dash_length = length / (dash_count * 2)
        
        for i in range(dash_count):
            start_ratio = (i * 2) / (dash_count * 2)
            end_ratio = (i * 2 + 1) / (dash_count * 2)
            start_x = x1 + dx * start_ratio
            start_y = y1 + dy * start_ratio
            end_x = x1 + dx * end_ratio
            end_y = y1 + dy * end_ratio
            c.line(start_x, start_y, end_x, end_y)
    
    def _draw_grid(self, c: canvas.Canvas, x: float, y: float, 
                   is_stroke_demo: bool = False, 
                   is_highlight: bool = False, 
                   character: str = "",
                   pinyin_text: str = ""):
        """
        绘制单个田字格
        
        Args:
            c: PDF画布对象
            x: 田字格左下角x坐标
            y: 田字格左下角y坐标
            is_stroke_demo: 是否为笔画展示模式（第一个格子）
            is_highlight: 是否为高亮模式（描红）
            character: 要显示的汉字
            pinyin_text: 拼音文本
        """
        grid_size = self.grid_size
        
        if character and (is_stroke_demo or is_highlight):
            c.setFillColor(Color(0.95, 0.95, 0.95))
            c.rect(x, y, grid_size, grid_size, fill=1, stroke=0)
        
        c.setStrokeColor(gray)
        c.setLineWidth(1)
        
        if self.show_pinyin:
            pinyin_grid_height = grid_size / 3
            char_grid_height = grid_size - pinyin_grid_height
            char_grid_y = y
            
            pinyin_grid_top = y + grid_size
            pinyin_grid_bottom = y + char_grid_height
            
            c.rect(x, y, grid_size, grid_size)
            
            c.setStrokeColor(gray)
            c.setLineWidth(1)
            c.line(x, pinyin_grid_bottom, x + grid_size, pinyin_grid_bottom)
            
            line_1_y = pinyin_grid_top
            line_2_y = pinyin_grid_top - pinyin_grid_height * 0.25
            line_3_y = pinyin_grid_top - pinyin_grid_height * 0.75
            line_4_y = pinyin_grid_bottom
            
            if pinyin_text:
                pinyin_font_size = int(pinyin_grid_height * 0.5)
                c.setFillColor(Color(self.pinyin_color[0], self.pinyin_color[1], self.pinyin_color[2]))
                c.setFont(self.font_name, pinyin_font_size)
                
                pinyin_width = c.stringWidth(pinyin_text, self.font_name, pinyin_font_size)
                pinyin_x = x + (grid_size - pinyin_width) / 2
                pinyin_y = line_2_y - (line_2_y - line_3_y) / 2 - pinyin_font_size / 2
                
                c.drawString(pinyin_x, pinyin_y, pinyin_text)
            
            c.setStrokeColor(Color(0.5, 0.5, 0.5))
            c.setLineWidth(0.5)
            self._draw_dashed_line(c, x, line_2_y, x + grid_size, line_2_y, 2)
            self._draw_dashed_line(c, x, line_3_y, x + grid_size, line_3_y, 2)
            
            char_font_size = int(char_grid_height * 0.7)
            
            if character and (is_stroke_demo or is_highlight):
                c.setFillColor(Color(self.font_color[0], self.font_color[1], self.font_color[2]))
                c.setFont(self.font_name, char_font_size)
                
                text_width = c.stringWidth(character, self.font_name, char_font_size)
                text_x = x + (grid_size - text_width) / 2
                text_y = char_grid_y + (char_grid_height - char_font_size) / 2 + (char_font_size * 0.15)
                
                c.drawString(text_x, text_y, character)
            
            if self.grid_type == "tianzi":
                c.setStrokeColor(Color(0.8, 0.8, 0.8))
                c.setLineWidth(0.5)
                c.line(x, char_grid_y + char_grid_height / 2, x + grid_size, char_grid_y + char_grid_height / 2)
                c.line(x + grid_size / 2, char_grid_y, x + grid_size / 2, char_grid_y + char_grid_height)
            
            elif self.grid_type == "mizi":
                c.setStrokeColor(Color(0.8, 0.8, 0.8))
                c.setLineWidth(0.5)
                c.line(x, char_grid_y + char_grid_height / 2, x + grid_size, char_grid_y + char_grid_height / 2)
                c.line(x + grid_size / 2, char_grid_y, x + grid_size / 2, char_grid_y + char_grid_height)
                c.line(x, char_grid_y, x + grid_size, char_grid_y + char_grid_height)
                c.line(x + grid_size, char_grid_y, x, char_grid_y + char_grid_height)
            
            elif self.grid_type == "huigong":
                inner_margin = char_grid_height / 5
                c.setStrokeColor(Color(0.8, 0.8, 0.8))
                c.setLineWidth(0.5)
                c.rect(x + inner_margin, char_grid_y + inner_margin, 
                       grid_size - inner_margin * 2, char_grid_height - inner_margin * 2)
            
            elif self.grid_type == "fangge":
                pass
        else:
            c.rect(x, y, grid_size, grid_size)
            
            char_font_size = int(grid_size * 0.7)
            
            if character and (is_stroke_demo or is_highlight):
                c.setFillColor(Color(self.font_color[0], self.font_color[1], self.font_color[2]))
                c.setFont(self.font_name, char_font_size)
                
                text_width = c.stringWidth(character, self.font_name, char_font_size)
                text_x = x + (grid_size - text_width) / 2
                text_y = y + (grid_size - char_font_size) / 2 + (char_font_size * 0.15)
                
                c.drawString(text_x, text_y, character)
            
            if self.grid_type == "tianzi":
                c.setStrokeColor(Color(0.8, 0.8, 0.8))
                c.setLineWidth(0.5)
                c.line(x, y + grid_size / 2, x + grid_size, y + grid_size / 2)
                c.line(x + grid_size / 2, y, x + grid_size / 2, y + grid_size)
            
            elif self.grid_type == "mizi":
                c.setStrokeColor(Color(0.8, 0.8, 0.8))
                c.setLineWidth(0.5)
                c.line(x, y + grid_size / 2, x + grid_size, y + grid_size / 2)
                c.line(x + grid_size / 2, y, x + grid_size / 2, y + grid_size)
                c.line(x, y, x + grid_size, y + grid_size)
                c.line(x + grid_size, y, x, y + grid_size)
            
            elif self.grid_type == "huigong":
                inner_margin = grid_size / 5
                c.setStrokeColor(Color(0.8, 0.8, 0.8))
                c.setLineWidth(0.5)
                c.rect(x + inner_margin, y + inner_margin, 
                       grid_size - inner_margin * 2, grid_size - inner_margin * 2)
            
            elif self.grid_type == "fangge":
                pass
    
    def _draw_header(self, c: canvas.Canvas):
        """
        绘制页眉（学生信息）
        
        Args:
            c: PDF画布对象
        """
        info_parts = []
        if self.student_name:
            info_parts.append(f"姓名：{self.student_name}")
        else:
            info_parts.append("姓名：______")
        
        if self.student_id:
            info_parts.append(f"学号：{self.student_id}")
        else:
            info_parts.append("学号：______")
        
        if self.class_name:
            info_parts.append(f"班级：{self.class_name}")
        else:
            info_parts.append("班级：______")
        
        info_text = "  ".join(info_parts)
        
        c.setFillColor(black)
        
        if self.font_name != "Helvetica":
            c.setFont(self.font_name, 10)
        else:
            c.setFont("Helvetica", 10)
        
        text_width = c.stringWidth(info_text, self.font_name if self.font_name != "Helvetica" else "Helvetica", 10)
        
        header_x = self.paper_width - self.margin_right - text_width
        header_y = self.paper_height - 15 * mm
        
        c.drawString(header_x, header_y, info_text)
    
    def _draw_page_from_chars(self, c: canvas.Canvas, characters: List[str], 
                               start_char_index: int, lines_rendered_for_char: int,
                               page_num: int) -> Tuple[int, int]:
        """
        从字符列表绘制单页字帖（支持单字跨多页）
        
        Args:
            c: PDF画布对象
            characters: 字符列表
            start_char_index: 起始字符索引
            lines_rendered_for_char: 当前字符已渲染的行数
            page_num: 页码
            
        Returns:
            (下一页起始字符索引, 下一页当前字符已渲染的行数)
        """
        self._draw_header(c)
        
        pinyin_cache = {}
        if self.show_pinyin and PINYIN_AVAILABLE:
            for char in characters:
                if char and char not in pinyin_cache:
                    try:
                        pinyin_result = pinyin(char, style=Style.TONE)
                        if pinyin_result and pinyin_result[0]:
                            pinyin_cache[char] = pinyin_result[0][0]
                        else:
                            pinyin_cache[char] = char
                    except Exception:
                        pinyin_cache[char] = char
        
        row_index = 0
        char_index = start_char_index
        current_lines_rendered = lines_rendered_for_char
        total_chars = len(characters)
        
        while char_index < total_chars and row_index < self.grid_rows:
            current_char = characters[char_index]
            char_pinyin = pinyin_cache.get(current_char, "")
            
            lines_remaining_for_char = self.lines_per_char - current_lines_rendered
            lines_to_render_this_page = min(lines_remaining_for_char, self.grid_rows - row_index)
            
            for line_repeat in range(lines_to_render_this_page):
                if row_index >= self.grid_rows:
                    break
                
                for col in range(self.grid_cols):
                    x = self.margin_left + self.grid_padding + col * self.grid_size
                    y = self.paper_height - self.margin_top - (row_index + 1) * self.grid_size
                    
                    is_template = (col == 0)
                    
                    self._draw_grid(c, x, y,
                                   is_stroke_demo=is_template,
                                   is_highlight=is_template,
                                   character=current_char if is_template else "",
                                   pinyin_text=char_pinyin if is_template else "")
                
                row_index += 1
                current_lines_rendered += 1
            
            if current_lines_rendered >= self.lines_per_char:
                char_index += 1
                current_lines_rendered = 0
        
        while row_index < self.grid_rows:
            for col in range(self.grid_cols):
                x = self.margin_left + self.grid_padding + col * self.grid_size
                y = self.paper_height - self.margin_top - (row_index + 1) * self.grid_size
                self._draw_grid(c, x, y)
            row_index += 1
        
        c.setFont("Helvetica", 10)
        c.setFillColor(gray)
        footer_text = f"第 {page_num} 页"
        c.drawString(self.margin_left, 10 * mm, footer_text)
        
        return char_index, current_lines_rendered
    
    def generate_from_chars(self, characters: List[str], output_path: str) -> Tuple[bool, str]:
        """
        从字符列表生成字帖（支持单字跨多页）
        
        Args:
            characters: 要生成的字符列表
            output_path: 输出PDF文件路径
            
        Returns:
            Tuple[bool, str]: (是否成功, 错误信息)
        """
        if not characters:
            return False, "字符列表不能为空"
        
        try:
            c = canvas.Canvas(output_path, pagesize=(self.paper_width, self.paper_height))
            
            char_index = 0
            lines_rendered_for_char = 0
            page_num = 1
            total_chars = len(characters)
            
            while char_index < total_chars:
                char_index, lines_rendered_for_char = self._draw_page_from_chars(
                    c, characters, char_index, lines_rendered_for_char, page_num
                )
                c.showPage()
                page_num += 1
            
            c.save()
            return True, f"字帖已成功生成：{output_path}"
            
        except Exception as e:
            return False, f"生成字帖时发生错误：{str(e)}"
    
    def _draw_page(self, c: canvas.Canvas, character: str, page_num: int):
        """
        绘制单页字帖（单个字符版本，向后兼容）
        
        Args:
            c: PDF画布对象
            character: 汉字
            page_num: 页码
        """
        for row in range(self.grid_rows):
            for col in range(self.grid_cols):
                x = self.margin_left + self.grid_padding + col * self.grid_size
                y = self.paper_height - self.margin_top - (row + 1) * self.grid_size
                
                is_first_cell = (row == 0 and col == 0)
                
                self._draw_grid(c, x, y, 
                               is_stroke_demo=is_first_cell,
                               is_highlight=is_first_cell,
                               character=character if is_first_cell else "")
        
        c.setFont("Helvetica", 10)
        c.setFillColor(gray)
        footer_text = f"第 {page_num} 页"
        c.drawString(self.margin_left, 10 * mm, footer_text)
    
    def _calculate_character_scene_layout(self):
        """
        计算生字模式的布局参数
        
        Returns:
            Dict: 包含布局参数的字典
        """
        usable_width = self.paper_width - self.margin_left - self.margin_right
        usable_height = self.paper_height - self.margin_top - self.margin_bottom
        
        char_box_size = CHARACTER_SCENE_CONFIG["CHARACTER_BOX_SIZE_MM"] * mm
        right_grid_size = CHARACTER_SCENE_CONFIG["RIGHT_GRID_SIZE_MM"] * mm
        gap = CHARACTER_SCENE_CONFIG["GAP_SIZE_MM"] * mm
        right_rows = CHARACTER_SCENE_CONFIG["RIGHT_GRID_ROWS"]
        stroke_order_row_height = CHARACTER_SCENE_CONFIG["STROKE_ORDER_ROW_HEIGHT_MM"] * mm
        
        right_area_width = usable_width - char_box_size - gap
        
        right_cols = max(1, int(right_area_width / right_grid_size))
        
        right_area_height = right_grid_size * right_rows + stroke_order_row_height
        row_height = max(char_box_size, right_area_height) + gap
        max_rows_per_page = max(1, int(usable_height / row_height))
        
        return {
            "char_box_size": char_box_size,
            "right_grid_size": right_grid_size,
            "gap": gap,
            "right_rows": right_rows,
            "right_cols": right_cols,
            "row_height": row_height,
            "max_rows_per_page": max_rows_per_page,
            "usable_width": usable_width,
            "usable_height": usable_height,
            "stroke_order_row_height": stroke_order_row_height,
        }
    
    def _get_stroke_names(self, character: str) -> List[str]:
        """
        获取汉字的笔画名称列表
        
        Args:
            character: 汉字字符
            
        Returns:
            List[str]: 笔画名称列表，如果没有数据则返回空列表
        """
        if character in self.stroke_data:
            return self.stroke_data[character]
        return []
    
    def _get_stroke_chars(self, character: str) -> List[str]:
        """
        获取汉字的笔画字符列表（将笔画名称转换为笔画字符）
        
        Args:
            character: 汉字字符
            
        Returns:
            List[str]: 笔画字符列表
        """
        stroke_names = self._get_stroke_names(character)
        stroke_chars = []
        
        for name in stroke_names:
            if name in STROKE_NAME_TO_CHAR:
                stroke_chars.append(STROKE_NAME_TO_CHAR[name])
            else:
                stroke_chars.append("□")
        
        return stroke_chars
    
    def _get_stroke_order_text(self, character: str) -> str:
        """
        获取笔顺展示文本
        
        格式："笔顺：xxxx"
        例如"三"字："笔顺：一 二 三"（逐步书写，每次多写一笔）
        例如"人"字："笔顺：丿 人"（逐步书写，每次多写一笔）
        
        Args:
            character: 汉字字符
            
        Returns:
            str: 笔顺展示文本
        """
        stroke_chars = self._get_stroke_chars(character)
        
        if not stroke_chars:
            return f"笔顺：{character}"
        
        stroke_count = len(stroke_chars)
        
        if stroke_count == 1:
            return f"笔顺：{character}"
        
        progressive_texts = []
        
        for i in range(1, stroke_count + 1):
            partial_strokes = stroke_chars[:i]
            partial_str = ''.join(partial_strokes)
            
            if i == stroke_count:
                progressive_texts.append(character)
            else:
                progressive_texts.append(partial_str)
        
        progressive_str = ' '.join(progressive_texts)
        
        return f"笔顺：{progressive_str}"
    
    def _get_progressive_stroke_texts(self, character: str) -> List[str]:
        """
        获取逐步书写的文本列表（从第一笔每次多写一笔，直到完整）
        
        例如"人"字：
        - 第一笔："丿"
        - 第二笔："人"（完整）
        
        例如"三"字：
        - 第一笔："一"
        - 第二笔："二"
        - 第三笔："三"（完整）
        
        Args:
            character: 汉字字符
            
        Returns:
            List[str]: 逐步书写的文本列表
        """
        stroke_names = self._get_stroke_names(character)
        stroke_count = len(stroke_names)
        
        if stroke_count == 0:
            return [character]
        
        texts = []
        
        for i in range(1, stroke_count + 1):
            partial = character[:i] if len(character) >= i else character
            texts.append(partial)
        
        return texts
    
    def _draw_stroke_order_row(self, c: canvas.Canvas, x: float, y: float, 
                                width: float, character: str = ""):
        """
        绘制笔顺行（右侧格子上方1cm高的行）
        
        Args:
            c: PDF画布对象
            x: 左下角x坐标
            y: 左下角y坐标
            width: 行宽度
            character: 汉字字符
        """
        layout = self._calculate_character_scene_layout()
        row_height = layout["stroke_order_row_height"]
        
        c.setStrokeColor(Color(self.stroke_order_color[0], self.stroke_order_color[1], self.stroke_order_color[2]))
        c.setLineWidth(0.5)
        c.rect(x, y, width, row_height)
        
        if character:
            stroke_order_text = self._get_stroke_order_text(character)
            
            font_size = max(10, int(row_height * 0.6))
            c.setFillColor(Color(self.stroke_order_color[0], self.stroke_order_color[1], self.stroke_order_color[2]))
            c.setFont(self.font_name, font_size)
            
            text_width = c.stringWidth(stroke_order_text, self.font_name, font_size)
            text_x = x + (width - text_width) / 2
            text_y = y + (row_height - font_size) / 2 + (font_size * 0.2)
            
            c.drawString(text_x, text_y, stroke_order_text)
    
    def _draw_character_box(self, c: canvas.Canvas, x: float, y: float, 
                            character: str = "", pinyin_text: str = "",
                            show_pinyin: bool = False):
        """
        绘制生字框（大回字格 + 中间田字格，4cm）
        
        Args:
            c: PDF画布对象
            x: 左下角x坐标
            y: 左下角y坐标
            character: 要显示的汉字
            pinyin_text: 拼音文本
            show_pinyin: 是否显示拼音
        """
        size = CHARACTER_SCENE_CONFIG["CHARACTER_BOX_SIZE_MM"] * mm
        outer_line_width = 2
        inner_margin = size * 0.15
        tianzi_size = size - 2 * inner_margin
        tianzi_x = x + inner_margin
        tianzi_y = y + inner_margin
        
        c.setStrokeColor(Color(self.grid_color[0], self.grid_color[1], self.grid_color[2]))
        c.setLineWidth(outer_line_width)
        c.rect(x, y, size, size)
        
        c.setStrokeColor(Color(self.grid_color[0], self.grid_color[1], self.grid_color[2]))
        c.setLineWidth(1.5)
        c.rect(tianzi_x, tianzi_y, tianzi_size, tianzi_size)
        
        c.setStrokeColor(Color(self.grid_color[0], self.grid_color[1], self.grid_color[2]))
        c.setLineWidth(1)
        c.line(tianzi_x, tianzi_y + tianzi_size / 2, tianzi_x + tianzi_size, tianzi_y + tianzi_size / 2)
        c.line(tianzi_x + tianzi_size / 2, tianzi_y, tianzi_x + tianzi_size / 2, tianzi_y + tianzi_size)
        
        if show_pinyin and pinyin_text:
            pinyin_y = y + size - inner_margin / 2
            pinyin_font_size = max(12, int(inner_margin * 0.6))
            c.setFillColor(Color(self.pinyin_color[0], self.pinyin_color[1], self.pinyin_color[2]))
            c.setFont(self.font_name, pinyin_font_size)
            
            pinyin_width = c.stringWidth(pinyin_text, self.font_name, pinyin_font_size)
            pinyin_x = x + (size - pinyin_width) / 2
            pinyin_baseline_y = pinyin_y - pinyin_font_size * 0.3
            
            c.drawString(pinyin_x, pinyin_baseline_y, pinyin_text)
        
        if character:
            char_font_size = int(tianzi_size * 0.7)
            c.setFillColor(Color(self.character_color[0], self.character_color[1], self.character_color[2]))
            c.setFont(self.font_name, char_font_size)
            
            text_width = c.stringWidth(character, self.font_name, char_font_size)
            text_x = tianzi_x + (tianzi_size - text_width) / 2
            text_y = tianzi_y + (tianzi_size - char_font_size) / 2 + (char_font_size * 0.15)
            
            c.drawString(text_x, text_y, character)
    
    def _draw_right_grid(self, c: canvas.Canvas, x: float, y: float):
        """
        绘制右侧格子（根据类型绘制不同样式）
        
        Args:
            c: PDF画布对象
            x: 左下角x坐标
            y: 左下角y坐标
        """
        size = CHARACTER_SCENE_CONFIG["RIGHT_GRID_SIZE_MM"] * mm
        
        c.setStrokeColor(Color(self.right_grid_color[0], self.right_grid_color[1], self.right_grid_color[2]))
        c.setLineWidth(1)
        c.rect(x, y, size, size)
        
        c.setStrokeColor(Color(self.right_grid_color[0], self.right_grid_color[1], self.right_grid_color[2]))
        c.setLineWidth(0.5)
        
        if self.right_grid_type == GridType.TIANZI or self.right_grid_type == GridType.MIZI:
            c.line(x, y + size / 2, x + size, y + size / 2)
            c.line(x + size / 2, y, x + size / 2, y + size)
        
        if self.right_grid_type == GridType.MIZI:
            c.line(x, y, x + size, y + size)
            c.line(x + size, y, x, y + size)
        
        if self.right_grid_type == GridType.HUIGONG:
            inner_margin = size / 5
            c.rect(x + inner_margin, y + inner_margin, size - inner_margin * 2, size - inner_margin * 2)
    
    def _draw_character_row(self, c: canvas.Canvas, x: float, y: float, 
                            character: str = "", pinyin_text: str = "",
                            show_pinyin: bool = False):
        """
        绘制一整行生字（生字框 + 右侧米字格 + 笔顺行）
        
        Args:
            c: PDF画布对象
            x: 左下角x坐标
            y: 左下角y坐标
            character: 要显示的汉字
            pinyin_text: 拼音文本
            show_pinyin: 是否显示拼音
        """
        layout = self._calculate_character_scene_layout()
        char_box_size = layout["char_box_size"]
        right_grid_size = layout["right_grid_size"]
        gap = layout["gap"]
        right_cols = layout["right_cols"]
        right_rows = layout["right_rows"]
        stroke_order_row_height = layout["stroke_order_row_height"]
        
        self._draw_character_box(c, x, y, character, pinyin_text, show_pinyin)
        
        right_area_x = x + char_box_size + gap
        right_area_width = right_cols * right_grid_size
        
        right_grids_y = y
        stroke_order_row_y = right_grids_y + right_rows * right_grid_size
        
        self._draw_stroke_order_row(c, right_area_x, stroke_order_row_y, right_area_width, character)
        
        for row in range(right_rows):
            for col in range(right_cols):
                grid_x = right_area_x + col * right_grid_size
                grid_y = y + row * right_grid_size
                self._draw_right_grid(c, grid_x, grid_y)
    
    def _draw_page_character_scene(self, c: canvas.Canvas, characters: List[str],
                                    start_char_index: int, page_num: int) -> int:
        """
        绘制生字模式的单页
        
        Args:
            c: PDF画布对象
            characters: 字符列表
            start_char_index: 起始字符索引
            page_num: 页码
            
        Returns:
            int: 下一页起始字符索引
        """
        self._draw_header(c)
        
        pinyin_cache = {}
        if PINYIN_AVAILABLE and self.show_character_pinyin:
            for char in characters:
                if char and char not in pinyin_cache:
                    try:
                        pinyin_result = pinyin(char, style=Style.TONE)
                        if pinyin_result and pinyin_result[0]:
                            pinyin_cache[char] = pinyin_result[0][0]
                        else:
                            pinyin_cache[char] = char
                    except Exception:
                        pinyin_cache[char] = char
        
        layout = self._calculate_character_scene_layout()
        max_rows = layout["max_rows_per_page"]
        row_height = layout["row_height"]
        
        char_index = start_char_index
        total_chars = len(characters)
        
        for row_on_page in range(max_rows):
            if char_index >= total_chars:
                break
            
            current_char = characters[char_index]
            char_pinyin = pinyin_cache.get(current_char, "")
            
            row_y = self.paper_height - self.margin_top - (row_on_page + 1) * row_height + row_height - layout["char_box_size"]
            
            self._draw_character_row(
                c, 
                self.margin_left, 
                row_y, 
                current_char, 
                char_pinyin,
                self.show_character_pinyin
            )
            
            char_index += 1
        
        c.setFont("Helvetica", 10)
        c.setFillColor(gray)
        footer_text = f"第 {page_num} 页"
        c.drawString(self.margin_left, 10 * mm, footer_text)
        
        return char_index
    
    def generate_character_scene(self, characters: List[str], output_path: str) -> Tuple[bool, str]:
        """
        生成生字模式的PDF字帖
        
        Args:
            characters: 要生成的字符列表
            output_path: 输出PDF文件路径
            
        Returns:
            Tuple[bool, str]: (是否成功, 错误信息)
        """
        if not characters:
            return False, "字符列表不能为空"
        
        try:
            c = canvas.Canvas(output_path, pagesize=(self.paper_width, self.paper_height))
            
            char_index = 0
            page_num = 1
            total_chars = len(characters)
            
            while char_index < total_chars:
                char_index = self._draw_page_character_scene(
                    c, characters, char_index, page_num
                )
                c.showPage()
                page_num += 1
            
            c.save()
            return True, f"字帖已成功生成：{output_path}"
            
        except Exception as e:
            return False, f"生成字帖时发生错误：{str(e)}"
    
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
    import argparse
    
    parser = argparse.ArgumentParser(description='字帖生成器 - 生成田字格或米字格字帖')
    parser.add_argument('character', help='要生成字帖的汉字（单个汉字）')
    parser.add_argument('output_path', help='输出PDF文件路径')
    parser.add_argument('-p', '--pages', type=int, default=1, help='生成页数（默认：1）')
    parser.add_argument('-g', '--grid-type', choices=['mizi', 'tianzi'], default='mizi', 
                        help='格子类型：mizi（米字格，默认）或 tianzi（田字格）')
    parser.add_argument('-f', '--font-style', choices=['zhenkai', 'xingkai'], default='zhenkai',
                        help='字体样式：zhenkai（正楷，默认）或 xingkai（行楷）')
    
    args = parser.parse_args()
    
    generator = CopybookGenerator(
        grid_type=args.grid_type,
        font_style=args.font_style
    )
    
    success, message = generator.generate(args.character, args.output_path, args.pages)
    
    if success:
        print(f"✓ {message}")
        print(f"  格子类型：{'米字格' if args.grid_type == 'mizi' else '田字格'}")
        print(f"  请求字体样式：{'正楷' if args.font_style == 'zhenkai' else '行楷'}")
        print(f"  实际使用字体：{generator.font_used_name}")
        if generator.font_used_path:
            print(f"  字体文件：{generator.font_used_path}")
        if generator.font_warning:
            print()
            print(generator.font_warning)
        sys.exit(0)
    else:
        print(f"✗ {message}")
        sys.exit(1)


if __name__ == "__main__":
    main()
