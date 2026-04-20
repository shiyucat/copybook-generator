import os
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

PAGE_SIZE = A4
PAGE_WIDTH, PAGE_HEIGHT = PAGE_SIZE

MARGIN_LEFT = 1.5 * cm
MARGIN_RIGHT = 1.5 * cm
MARGIN_TOP = 2 * cm
MARGIN_BOTTOM = 2 * cm

GRID_SIZE = 30 * mm
GRID_PER_ROW = 5
GRID_PER_COL = 10

GRID_LINE_COLOR = (0.7, 0.7, 0.7)
GRID_CENTER_LINE_COLOR = (0.5, 0.5, 0.5)
GRID_BACKGROUND_COLOR = (1.0, 1.0, 1.0)
GRID_FAINT_BACKGROUND_COLOR = (0.95, 0.95, 0.95)

CHARACTER_COLOR = (0.0, 0.0, 0.0)
CHARACTER_FAINT_COLOR = (0.3, 0.3, 0.3)

STROKE_STEP_LABEL_COLOR = (0.0, 0.0, 0.8)

FONT_PATH = None
FONT_NAME = 'SimSun'
CHARACTER_FONT_SIZE = GRID_SIZE * 0.8
STROKE_LABEL_FONT_SIZE = 10

REGISTERED_FONT_NAME = None

def find_system_chinese_fonts():
    font_paths = []
    
    if sys.platform == 'darwin':
        mac_fonts = [
            '/System/Library/Fonts/PingFang.ttc',
            '/System/Library/Fonts/STHeiti Light.ttc',
            '/System/Library/Fonts/STHeiti Medium.ttc',
            '/System/Library/Fonts/Supplemental/Songti.ttc',
            '/System/Library/Fonts/Supplemental/Kaiti.ttc',
            '/Library/Fonts/Songti.ttc',
            '/Library/Fonts/KaiTi.ttf',
            '/Library/Fonts/SimSun.ttf',
        ]
        for path in mac_fonts:
            if os.path.exists(path):
                font_paths.append(path)
    
    elif sys.platform == 'win32':
        win_fonts = [
            'C:\\Windows\\Fonts\\simsun.ttc',
            'C:\\Windows\\Fonts\\simhei.ttf',
            'C:\\Windows\\Fonts\\msyh.ttc',
            'C:\\Windows\\Fonts\\simkai.ttf',
        ]
        for path in win_fonts:
            if os.path.exists(path):
                font_paths.append(path)
    
    else:
        linux_fonts = [
            '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
        ]
        for path in linux_fonts:
            if os.path.exists(path):
                font_paths.append(path)
    
    return font_paths

def register_chinese_font(custom_font_path=None, verbose=False):
    global REGISTERED_FONT_NAME, FONT_PATH, FONT_NAME
    
    if custom_font_path and os.path.exists(custom_font_path):
        font_path = custom_font_path
    elif FONT_PATH and os.path.exists(FONT_PATH):
        font_path = FONT_PATH
    else:
        fonts = find_system_chinese_fonts()
        if fonts:
            font_path = fonts[0]
        else:
            if verbose:
                print("警告：未找到系统中文字体，汉字可能无法正确显示。")
                print("建议在config.py中设置FONT_PATH指定中文字体文件路径。")
            REGISTERED_FONT_NAME = 'Helvetica'
            return REGISTERED_FONT_NAME
    
    font_name = 'CustomChineseFont'
    try:
        pdfmetrics.registerFont(TTFont(font_name, font_path))
        REGISTERED_FONT_NAME = font_name
        FONT_PATH = font_path
        FONT_NAME = font_name
        if verbose:
            print(f"已注册中文字体：{font_path}")
    except Exception as e:
        if verbose:
            print(f"警告：注册字体失败 {font_path}: {e}")
        REGISTERED_FONT_NAME = 'Helvetica'
    
    return REGISTERED_FONT_NAME

def get_registered_font_name():
    return REGISTERED_FONT_NAME
