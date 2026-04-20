from reportlab.lib.units import mm
import config
from validator import InputValidator

class CharacterRenderer:
    def __init__(self, grid_drawer):
        self.grid_drawer = grid_drawer

    def render_stroke_steps(self, x, y, char, available_width):
        stroke_order = self.validator.get_stroke_order(char)
        
        if not stroke_order:
            self.grid_drawer.c.setFillColorRGB(0.6, 0.4, 0.4)
            self.grid_drawer.c.setFont('Helvetica-Bold', 12)
            
            title = f'「{char}」笔画顺序（未收录）'
            self.grid_drawer.c.drawString(x, y, title)
            
            current_y = y - 15
            self.grid_drawer.c.setFont('Helvetica', 9)
            self.grid_drawer.c.setFillColorRGB(0.5, 0.5, 0.5)
            
            hint1 = f'提示：可在 stroke_data.py 中手动添加该字的笔画顺序'
            self.grid_drawer.c.drawString(x, current_y, hint1)
            
            current_y -= 12
            hint2 = f'或使用 InputValidator.add_to_database("{char}", ["笔画1", "笔画2", ...])'
            self.grid_drawer.c.drawString(x, current_y, hint2)
            
            return current_y - 20
        
        self.grid_drawer.c.setFillColorRGB(*config.STROKE_STEP_LABEL_COLOR)
        self.grid_drawer.c.setFont('Helvetica-Bold', 12)
        
        title = f'「{char}」笔画顺序（{len(stroke_order)}笔）'
        self.grid_drawer.c.drawString(x, y, title)
        
        title_width = self.grid_drawer.c.stringWidth(title, 'Helvetica-Bold', 12)
        current_x = x + title_width + 5
        current_y = y
        
        self.grid_drawer.c.setFont('Helvetica', 10)
        
        for idx, stroke in enumerate(stroke_order, 1):
            step_text = f'{idx}.{stroke}'
            text_width = self.grid_drawer.c.stringWidth(step_text, 'Helvetica', 10)
            
            if current_x + text_width > x + available_width:
                current_x = x
                current_y -= 15
            
            self.grid_drawer.c.drawString(current_x, current_y, step_text)
            current_x += text_width + 10
        
        return current_y - 20

    def render_stroke_visualization(self, x, y, char, grid_size):
        stroke_order = InputValidator.get_stroke_order(char)
        
        if not stroke_order:
            self.grid_drawer.draw_grid_cell(x, y, grid_size, is_faint_background=True)
            self.grid_drawer.draw_character_in_grid(x, y, grid_size, char, is_faint=True)
            return
        
        self._draw_colored_character_with_strokes(x, y, char, grid_size, stroke_order)

    def _draw_colored_character_with_strokes(self, x, y, char, grid_size, stroke_order):
        self.grid_drawer.draw_grid_cell(x, y, grid_size, is_faint_background=True)
        
        self.grid_drawer.draw_character_in_grid(x, y, grid_size, char, is_faint=True)
        
        num_strokes = len(stroke_order)
        if num_strokes == 0:
            return
        
        small_box_size = 6 * mm
        margin = 2 * mm
        num_cols = min(6, num_strokes)
        num_rows = (num_strokes + num_cols - 1) // num_cols
        
        legend_x = x + grid_size + margin
        legend_y = y + grid_size - small_box_size
        
        self.grid_drawer.c.setFillColorRGB(0.2, 0.2, 0.8)
        self.grid_drawer.c.setFont('Helvetica-Bold', 10)
        self.grid_drawer.c.drawString(legend_x, legend_y + 2 * mm, "笔画顺序:")
        
        colors = self._generate_rainbow_colors(num_strokes)
        
        for idx, stroke in enumerate(stroke_order):
            row = idx // num_cols
            col = idx % num_cols
            
            box_x = legend_x + col * (small_box_size + margin)
            box_y = legend_y - row * (small_box_size + margin) - 5 * mm
            
            color = colors[idx]
            self.grid_drawer.c.setFillColorRGB(*color)
            self.grid_drawer.c.setStrokeColorRGB(0.5, 0.5, 0.5)
            self.grid_drawer.c.setLineWidth(0.5)
            self.grid_drawer.c.rect(box_x, box_y, small_box_size, small_box_size, fill=1, stroke=1)
            
            self.grid_drawer.c.setFillColorRGB(0, 0, 0)
            self.grid_drawer.c.setFont('Helvetica-Bold', 10)
            
            num_text = str(idx + 1)
            text_width = self.grid_drawer.c.stringWidth(num_text, 'Helvetica-Bold', 10)
            text_x = box_x + (small_box_size - text_width) / 2
            text_y = box_y + (small_box_size - 10) / 2 + 2
            self.grid_drawer.c.drawString(text_x, text_y, num_text)

    def _generate_rainbow_colors(self, num_colors):
        colors = []
        for i in range(num_colors):
            hue = i / max(num_colors, 1)
            if hue < 0.2:
                r, g, b = 1.0, 0.2, 0.2
            elif hue < 0.4:
                r, g, b = 1.0, 0.6, 0.0
            elif hue < 0.6:
                r, g, b = 0.2, 0.8, 0.2
            elif hue < 0.8:
                r, g, b = 0.2, 0.6, 1.0
            else:
                r, g, b = 0.6, 0.2, 1.0
            colors.append((r, g, b))
        return colors

    def render_first_row_with_faint_character(self, start_x, start_y, characters, grid_size, max_chars):
        actual_chars = characters[:max_chars]
        
        for idx, char in enumerate(actual_chars):
            x = start_x + idx * grid_size
            y = start_y
            
            if idx == 0:
                self.render_stroke_visualization(x, y, char, grid_size)
            else:
                self.grid_drawer.draw_grid_cell(x, y, grid_size, is_faint_background=True)
                self.grid_drawer.draw_character_in_grid(x, y, grid_size, char, is_faint=True)

    def render_regular_grid_row(self, start_x, start_y, characters, grid_size, max_chars):
        for idx in range(max_chars):
            x = start_x + idx * grid_size
            y = start_y
            
            self.grid_drawer.draw_grid_cell(x, y, grid_size, is_faint_background=False)
            
            if idx < len(characters):
                self.grid_drawer.draw_character_in_grid(x, y, grid_size, characters[idx], is_faint=False)
