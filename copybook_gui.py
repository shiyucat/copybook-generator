#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
字帖生成器 GUI 版本
生成田字格、米字格、回宫格、方格格式的字帖
"""

import sys
import os
import re
import math
from pathlib import Path
from typing import List, Tuple, Optional

import tkinter as tk
from tkinter import ttk, font
from PIL import Image, ImageDraw, ImageFont, ImageTk


class GridType:
    """格子类型"""
    TIANZI = "田字格"
    MIZI = "米字格"
    HUIGONG = "回宫格"
    FANGGE = "方格"


class CopybookPreview:
    """字帖预览绘制器"""
    
    def __init__(self):
        self.grid_size = 60
        self.grid_padding = 5
        self.font_size = 40
        self._init_font()
        
    def _init_font(self):
        """初始化字体"""
        self.font = None
        self.font_name = "Default"
        
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
    
    def generate_preview(self, characters: List[str], grid_type: str, 
                         preview_width: int, preview_height: int) -> Image.Image:
        """
        生成预览图像
        
        排版规则：
        - 按"从左到右、从上到下"排版
        - 每个字占一行
        - 每行第一个字为模版字（灰色背景）
        - 支持自动换行分页
        
        Args:
            characters: 字符列表
            grid_type: 格子类型
            preview_width: 预览区域宽度
            preview_height: 预览区域高度
            
        Returns:
            PIL Image对象
        """
        cols = max(1, (preview_width - self.grid_padding * 2) // (self.grid_size + self.grid_padding))
        max_rows = max(1, (preview_height - self.grid_padding * 2) // (self.grid_size + self.grid_padding))
        
        img_width = preview_width
        img_height = preview_height
        
        img = Image.new('RGB', (img_width, img_height), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        if not characters:
            for row in range(max_rows):
                for col in range(cols):
                    x = self.grid_padding + col * (self.grid_size + self.grid_padding)
                    y = self.grid_padding + row * (self.grid_size + self.grid_padding)
                    if x + self.grid_size <= preview_width and y + self.grid_size <= preview_height:
                        self.draw_grid(draw, x, y, grid_type)
            return img
        
        row_index = 0
        char_index = 0
        total_chars = len(characters)
        
        while char_index < total_chars and row_index < max_rows:
            current_char = characters[char_index]
            
            for col in range(cols):
                x = self.grid_padding + col * (self.grid_size + self.grid_padding)
                y = self.grid_padding + row_index * (self.grid_size + self.grid_padding)
                
                if x + self.grid_size > preview_width or y + self.grid_size > preview_height:
                    continue
                
                is_template = (col == 0)
                char_to_draw = current_char if is_template else ""
                
                self.draw_grid(draw, x, y, grid_type, char_to_draw, is_template)
            
            char_index += 1
            row_index += 1
        
        return img


class CopybookGUI:
    """字帖生成器 GUI 主类"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("字帖生成器")
        self.root.geometry("1200x800")
        self.root.minsize(900, 600)
        
        self.preview = CopybookPreview()
        self.debounce_job = None
        self.debounce_delay = 200
        
        self._create_ui()
        self._bind_events()
        self._schedule_initial_update()
        
    def _create_ui(self):
        """创建UI界面"""
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        main_frame.columnconfigure(0, weight=2)
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=6)
        main_frame.columnconfigure(3, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)
        
        input_label = ttk.Label(left_frame, text="输入文字", font=("Arial", 12, "bold"))
        input_label.pack(anchor="w", pady=(0, 5))
        
        self.input_text = tk.Text(left_frame, wrap=tk.WORD, font=("Arial", 14), 
                                   relief=tk.SOLID, borderwidth=1)
        self.input_text.pack(fill=tk.BOTH, expand=True)
        
        input_hint = ttk.Label(left_frame, text="支持：中文、英文、数字\n空格和换行不占格\n不支持：标点符号、特殊字符", 
                                foreground="gray", font=("Arial", 10), justify="left")
        input_hint.pack(anchor="w", pady=(5, 0))
        
        grid_label_frame = ttk.LabelFrame(left_frame, text="格子类型", padding=5)
        grid_label_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.grid_type_var = tk.StringVar(value=GridType.TIANZI)
        
        grid_types = [
            (GridType.TIANZI, "田字格"),
            (GridType.MIZI, "米字格"),
            (GridType.HUIGONG, "回宫格"),
            (GridType.FANGGE, "方格"),
        ]
        
        for value, text in grid_types:
            rb = ttk.Radiobutton(grid_label_frame, text=text, value=value, 
                                  variable=self.grid_type_var)
            rb.pack(anchor="w", pady=2)
        
        spacer_frame = ttk.Frame(main_frame)
        spacer_frame.grid(row=0, column=1, sticky="nsew")
        
        preview_frame = ttk.Frame(main_frame, relief=tk.SOLID, borderwidth=1)
        preview_frame.grid(row=0, column=2, sticky="nsew", padx=(0, 0), pady=10)
        
        preview_label = ttk.Label(preview_frame, text="预览", font=("Arial", 12, "bold"))
        preview_label.pack(anchor="w", pady=(5, 5), padx=5)
        
        self.preview_canvas = tk.Canvas(preview_frame, bg="white", highlightthickness=0)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        right_spacer_frame = ttk.Frame(main_frame)
        right_spacer_frame.grid(row=0, column=3, sticky="nsew")
        
    def _bind_events(self):
        """绑定事件"""
        self.input_text.bind("<KeyRelease>", self._on_input_change)
        self.grid_type_var.trace("w", self._on_grid_type_change)
        self.root.bind("<Configure>", self._on_window_resize)
        self.input_text.bind("<Key>", self._validate_input)
        
    def _validate_input(self, event: tk.Event):
        """验证输入"""
        if event.char:
            if re.match(r'^[\u4e00-\u9fff\u3400-\u4dbf\s\n]$', event.char):
                return
            
            if re.match(r'^[a-zA-Z0-9]$', event.char):
                return
            
            if event.keysym in ('BackSpace', 'Delete', 'Left', 'Right', 'Up', 'Down', 
                                'Return', 'Tab', 'Home', 'End', 'Shift_L', 'Shift_R',
                                'Control_L', 'Control_R', 'Alt_L', 'Alt_R', 'Caps_Lock'):
                return
            
            return "break"
        
    def _on_input_change(self, event=None):
        """输入变化时的处理"""
        self._schedule_update()
        
    def _on_grid_type_change(self, *args):
        """格子类型变化时的处理"""
        self._schedule_update()
        
    def _on_window_resize(self, event=None):
        """窗口大小变化时的处理"""
        if event and event.widget == self.root:
            self._schedule_update()
        
    def _schedule_update(self):
        """调度更新预览"""
        if self.debounce_job:
            self.root.after_cancel(self.debounce_job)
        self.debounce_job = self.root.after(self.debounce_delay, self._update_preview)
        
    def _schedule_initial_update(self):
        """调度初始更新"""
        self.root.after(100, self._update_preview)
        
    def _get_valid_characters(self) -> List[str]:
        """获取有效的字符列表"""
        text = self.input_text.get("1.0", tk.END)
        valid_chars = []
        
        for char in text:
            if re.match(r'^[\u4e00-\u9fff\u3400-\u4dbf]$', char):
                valid_chars.append(char)
            elif re.match(r'^[a-zA-Z0-9]$', char):
                valid_chars.append(char)
        
        return valid_chars
        
    def _update_preview(self):
        """更新预览"""
        try:
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()
            
            if canvas_width < 10 or canvas_height < 10:
                self.root.after(100, self._update_preview)
                return
            
            characters = self._get_valid_characters()
            grid_type = self.grid_type_var.get()
            
            img = self.preview.generate_preview(characters, grid_type, canvas_width, canvas_height)
            
            self.preview_image = ImageTk.PhotoImage(img)
            self.preview_canvas.delete("all")
            self.preview_canvas.create_image(0, 0, anchor=tk.NW, image=self.preview_image)
            
        except Exception as e:
            print(f"更新预览时出错: {e}")
            import traceback
            traceback.print_exc()


def main():
    """主函数"""
    root = tk.Tk()
    app = CopybookGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
