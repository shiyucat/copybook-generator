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

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color, black, gray, red, blue
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


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
        usable_height = self.paper_height - self.margin_top - self.margin_bottom
        
        self.grid_size = min(
            usable_width / self.grid_cols,
            usable_height / self.grid_rows
        )
        
        self.grid_padding = (usable_width - self.grid_size * self.grid_cols) / 2
    
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
        绘制笔顺标准功能：
        1. 每个笔画标注笔顺数字序号（从1开始递增）
        2. 每一笔绘制跟随笔画走向的书写方向引导箭头
        3. 直线笔画：直线箭头，完全贴合笔画走向
        4. 弧形笔画：弧形箭头，完全贴合圆弧笔画走向
        5. 数字序号标注在笔画外侧相邻空白处
        
        Args:
            c: PDF画布对象
            character: 汉字字符
            grid_x: 田字格左下角x坐标
            grid_y: 田字格左下角y坐标
            grid_size: 田字格大小
        """
        hanzi_data = self._get_hanzi_writer_data(character)
        
        if hanzi_data is None:
            self._draw_default_stroke_order(c, character, grid_x, grid_y, grid_size)
            return
        
        medians = hanzi_data.get('medians', [])
        
        if not medians:
            self._draw_default_stroke_order(c, character, grid_x, grid_y, grid_size)
            return
        
        for stroke_index, median in enumerate(medians):
            stroke_order = stroke_index + 1
            
            transformed_median = self._transform_medians_to_grid(
                median, grid_x, grid_y, grid_size
            )
            
            if len(transformed_median) < 2:
                continue
            
            stroke_type = StrokeAnalyzer.analyze_stroke_type(transformed_median)
            
            start_point, end_point = StrokeAnalyzer.get_stroke_endpoints(transformed_median)
            
            if stroke_type == StrokeType.LINEAR:
                ArrowDrawer.draw_linear_arrow(
                    c, start_point, end_point,
                    color=red, line_width=1.5
                )
            else:
                ArrowDrawer.draw_curved_arrow(
                    c, transformed_median,
                    color=red, line_width=1.5
                )
            
            self._draw_stroke_number(
                c, stroke_order, transformed_median, 
                stroke_type, grid_x, grid_y, grid_size
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
    
    def _draw_grid(self, c: canvas.Canvas, x: float, y: float, 
                   is_stroke_demo: bool = False, 
                   is_highlight: bool = False, 
                   character: str = ""):
        """
        绘制单个田字格
        
        Args:
            c: PDF画布对象
            x: 田字格左下角x坐标
            y: 田字格左下角y坐标
            is_stroke_demo: 是否为笔画展示模式（第一个格子）
            is_highlight: 是否为高亮模式（描红）
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
        
        if character and is_stroke_demo:
            c.setFillColor(Color(0.95, 0.95, 0.95))
            c.rect(x, y, grid_size, grid_size, fill=1, stroke=0)
            
            c.setFillColor(Color(0.7, 0.7, 0.7))
            c.setFont(self.font_name, self.font_size)
            
            text_width = c.stringWidth(character, self.font_name, self.font_size)
            text_x = x + (grid_size - text_width) / 2
            text_y = y + (grid_size - self.font_size) / 2 + 5
            
            c.drawString(text_x, text_y, character)
            
            self._draw_stroke_order_standard(c, character, x, y, grid_size)
            
            c.setStrokeColor(gray)
            c.setLineWidth(1)
            c.rect(x, y, grid_size, grid_size)
        
        if character and is_highlight and not is_stroke_demo:
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
                
                is_first_cell = (row == 0 and col == 0)
                
                self._draw_grid(c, x, y, 
                               is_stroke_demo=is_first_cell,
                               is_highlight=is_first_cell,
                               character=character if is_first_cell else "")
        
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
