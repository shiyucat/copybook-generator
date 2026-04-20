from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import config
from grid import GridDrawer
from character_renderer import CharacterRenderer

class PageLayout:
    def __init__(self, output_path):
        self.output_path = output_path
        self.c = canvas.Canvas(output_path, pagesize=A4)
        self.page_width, self.page_height = A4
        self.grid_drawer = GridDrawer(self.c)
        self.char_renderer = CharacterRenderer(self.grid_drawer)

    def calculate_grid_start_position(self, stroke_steps_height=0):
        usable_width = self.page_width - config.MARGIN_LEFT - config.MARGIN_RIGHT
        usable_height = self.page_height - config.MARGIN_TOP - config.MARGIN_BOTTOM
        
        total_grid_width = config.GRID_PER_ROW * config.GRID_SIZE
        total_grid_height = config.GRID_PER_COL * config.GRID_SIZE
        
        start_x = config.MARGIN_LEFT + (usable_width - total_grid_width) / 2
        start_y = self.page_height - config.MARGIN_TOP - total_grid_height - stroke_steps_height
        
        return start_x, start_y

    def add_new_page(self):
        self.c.showPage()

    def render_page(self, characters, is_first_page=False, page_first_char=None):
        start_x, start_y = self.calculate_grid_start_position(0)
        
        chars_per_page = config.GRID_PER_ROW * config.GRID_PER_COL
        chars_on_page = characters[:chars_per_page]
        
        for row in range(config.GRID_PER_COL):
            row_chars = chars_on_page[row * config.GRID_PER_ROW : (row + 1) * config.GRID_PER_ROW]
            current_y = start_y + (config.GRID_PER_COL - 1 - row) * config.GRID_SIZE
            
            if row == 0:
                self.char_renderer.render_first_row_with_faint_character(
                    start_x, 
                    current_y, 
                    row_chars, 
                    config.GRID_SIZE, 
                    config.GRID_PER_ROW
                )
            else:
                self.char_renderer.render_regular_grid_row(
                    start_x, 
                    current_y, 
                    row_chars, 
                    config.GRID_SIZE, 
                    config.GRID_PER_ROW
                )
        
        return chars_on_page

    def calculate_total_pages(self, character_count):
        chars_per_page = config.GRID_PER_ROW * config.GRID_PER_COL
        total_pages = (character_count + chars_per_page - 1) // chars_per_page
        return total_pages if total_pages > 0 else 1

    def render_all_pages(self, characters):
        chars_per_page = config.GRID_PER_ROW * config.GRID_PER_COL
        total_chars = len(characters)
        total_pages = self.calculate_total_pages(total_chars)
        
        for page_idx in range(total_pages):
            start_idx = page_idx * chars_per_page
            end_idx = min((page_idx + 1) * chars_per_page, total_chars)
            page_chars = characters[start_idx:end_idx]
            
            is_first_page = (page_idx == 0)
            page_first_char = page_chars[0] if page_chars else None
            
            self.render_page(page_chars, is_first_page, page_first_char)
            
            if page_idx < total_pages - 1:
                self.add_new_page()
        
        self.c.save()
        return total_pages
