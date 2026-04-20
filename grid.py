from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
import config

class GridDrawer:
    def __init__(self, c):
        self.c = c

    def draw_grid_cell(self, x, y, size, is_faint_background=False):
        if is_faint_background:
            self.c.setFillColorRGB(*config.GRID_FAINT_BACKGROUND_COLOR)
        else:
            self.c.setFillColorRGB(*config.GRID_BACKGROUND_COLOR)
        self.c.rect(x, y, size, size, fill=1, stroke=0)

        self.c.setStrokeColorRGB(*config.GRID_LINE_COLOR)
        self.c.setLineWidth(0.5)
        self.c.rect(x, y, size, size, fill=0, stroke=1)

        self.c.setStrokeColorRGB(*config.GRID_CENTER_LINE_COLOR)
        self.c.setLineWidth(0.3)
        center_x = x + size / 2
        center_y = y + size / 2
        self.c.line(center_x, y, center_x, y + size)
        self.c.line(x, center_y, x + size, center_y)

        self.c.setStrokeColorRGB(*config.GRID_CENTER_LINE_COLOR)
        self.c.setLineWidth(0.3)
        self.c.setDash([2, 2])
        self.c.line(x, y, x + size, y + size)
        self.c.line(x, y + size, x + size, y)
        self.c.setDash([])

    def draw_character_in_grid(self, x, y, size, char, is_faint=False):
        try:
            font_name = config.get_registered_font_name()
            if not font_name:
                font_name = 'Helvetica'

            if is_faint:
                self.c.setFillColorRGB(*config.CHARACTER_FAINT_COLOR)
            else:
                self.c.setFillColorRGB(*config.CHARACTER_COLOR)

            self.c.setFont(font_name, config.CHARACTER_FONT_SIZE)
            
            text_width = self.c.stringWidth(char, font_name, config.CHARACTER_FONT_SIZE)
            text_height = config.CHARACTER_FONT_SIZE * 0.8
            
            char_x = x + (size - text_width) / 2
            char_y = y + (size - text_height) / 2
            
            self.c.drawString(char_x, char_y, char)
        except Exception as e:
            print(f"警告：无法在位置({x}, {y})渲染汉字'{char}'：{e}")

    def draw_stroke_step_label(self, x, y, step_number, stroke_name):
        self.c.setFillColorRGB(*config.STROKE_STEP_LABEL_COLOR)
        self.c.setFont('Helvetica', config.STROKE_LABEL_FONT_SIZE)
        
        label = f"第{step_number}笔：{stroke_name}"
        self.c.drawString(x, y, label)
