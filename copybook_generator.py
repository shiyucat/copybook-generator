#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
字帖生成器
生成田字格格式的字帖，包含笔画步骤展示和描红功能
"""

import sys
import os
import json
import math
from typing import List, Tuple, Optional, Dict, Any
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color, black, gray, red, blue, green
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
        
        stroke_data_path = Path(__file__).parent / "stroke_data" / "strokes.json"
        
        if stroke_data_path.exists():
            try:
                with open(stroke_data_path, 'r', encoding='utf-8') as f:
                    self.stroke_data = json.load(f)
            except Exception as e:
                print(f"加载笔画数据失败: {e}")
    
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
                    line_width: float = 2,
                    arrow_size: float = 6):
        """
        绘制箭头（只在终点画箭头，不画整条线）
        
        Args:
            c: PDF画布对象
            start_x: 起点x坐标
            start_y: 起点y坐标
            end_x: 终点x坐标
            end_y: 终点y坐标
            color: 箭头颜色
            line_width: 线宽
            arrow_size: 箭头大小
        """
        c.setStrokeColor(color)
        c.setLineWidth(line_width)
        
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
            
            strokes = self.detailed_stroke_data.get(character, [])
            if strokes:
                for stroke in strokes:
                    start_x = x + stroke["start_x"] * grid_size
                    start_y = y + stroke["start_y"] * grid_size
                    end_x = x + stroke["end_x"] * grid_size
                    end_y = y + stroke["end_y"] * grid_size
                    
                    mid_x = (start_x + end_x) / 2
                    mid_y = (start_y + end_y) / 2
                    
                    c.setFillColor(red)
                    c.setFont("Helvetica-Bold", 10)
                    order_text = f"{stroke['order']}"
                    order_width = c.stringWidth(order_text, "Helvetica-Bold", 10)
                    
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
                    
                    c.drawString(label_x, label_y, order_text)
            
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
