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
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageDraw, ImageFont, ImageTk

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


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


class CopybookGUI:
    """字帖生成器 GUI 主类 - 负责界面交互"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("字帖生成器")
        self.root.geometry("1200x800")
        self.root.minsize(900, 600)
        
        self.preview = CopybookPreview()
        self.debounce_job = None
        self.debounce_delay = 200
        
        self.current_page = 1
        self.total_pages = 1
        
        self._create_ui()
        self._bind_events()
        self._schedule_initial_update()
        
    def _create_ui(self):
        """创建UI界面"""
        self.root.columnconfigure(0, weight=2)
        self.root.columnconfigure(1, weight=1)
        self.root.columnconfigure(2, weight=6)
        self.root.columnconfigure(3, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        left_frame = ttk.Frame(self.root)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        input_label = ttk.Label(left_frame, text="输入文字", font=("Arial", 12, "bold"))
        input_label.pack(anchor="w", pady=(0, 5))
        
        self.input_text = tk.Text(left_frame, wrap=tk.WORD, font=("Arial", 14), 
                                   relief=tk.SOLID, borderwidth=1, height=10)
        self.input_text.pack(fill=tk.X, pady=(0, 10))
        
        input_hint = ttk.Label(left_frame, text="支持：中文、英文、数字\n空格和换行不占格\n不支持：标点符号、特殊字符", 
                                foreground="gray", font=("Arial", 10), justify="left")
        input_hint.pack(anchor="w", pady=(0, 10))
        
        grid_label_frame = ttk.LabelFrame(left_frame, text="格子类型", padding=5)
        grid_label_frame.pack(fill=tk.X, pady=(0, 0))
        
        self.grid_type_var = tk.StringVar(value=GridType.TIANZI)
        
        grid_types = [
            (GridType.TIANZI, "田字格"),
            (GridType.MIZI, "米字格"),
            (GridType.HUIGONG, "回宫格"),
            (GridType.FANGGE, "方格"),
        ]
        
        for value, text in grid_types:
            rb = ttk.Radiobutton(grid_label_frame, text=text, value=value, 
                                  variable=self.grid_type_var,
                                  command=self._on_grid_type_change)
            rb.pack(anchor="w", pady=2)
        
        export_label_frame = ttk.LabelFrame(left_frame, text="导出", padding=5)
        export_label_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.export_button = ttk.Button(export_label_frame, text="导出 PDF", 
                                          command=self._export_pdf)
        self.export_button.pack(fill=tk.X, pady=5)
        
        if not REPORTLAB_AVAILABLE:
            self.export_button.config(state="disabled")
            hint_label = ttk.Label(export_label_frame, text="需要安装 reportlab 库\npip install reportlab", 
                                     foreground="red", font=("Arial", 9), justify="center")
            hint_label.pack(pady=2)
        
        spacer_frame = ttk.Frame(self.root)
        spacer_frame.grid(row=0, column=1, sticky="nsew")
        
        preview_frame = ttk.Frame(self.root, relief=tk.SOLID, borderwidth=1)
        preview_frame.grid(row=0, column=2, sticky="nsew", padx=(0, 0), pady=10)
        preview_frame.rowconfigure(0, weight=0)
        preview_frame.rowconfigure(1, weight=1)
        preview_frame.rowconfigure(2, weight=0)
        preview_frame.columnconfigure(0, weight=1)
        
        preview_top_frame = ttk.Frame(preview_frame)
        preview_top_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 0))
        
        preview_label = ttk.Label(preview_top_frame, text="预览", font=("Arial", 12, "bold"))
        preview_label.pack(side="left")
        
        self.page_label = ttk.Label(preview_top_frame, text="第 1 页 / 共 1 页", font=("Arial", 10))
        self.page_label.pack(side="right")
        
        canvas_frame = ttk.Frame(preview_frame)
        canvas_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        canvas_frame.rowconfigure(0, weight=1)
        canvas_frame.columnconfigure(0, weight=1)
        
        self.preview_canvas = tk.Canvas(canvas_frame, bg="white", highlightthickness=0)
        self.preview_canvas.grid(row=0, column=0, sticky="nsew")
        
        navigation_frame = ttk.Frame(preview_frame)
        navigation_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=(0, 5))
        
        self.prev_button = ttk.Button(navigation_frame, text="上一页", command=self._prev_page)
        self.prev_button.pack(side="left", padx=(0, 10))
        
        self.next_button = ttk.Button(navigation_frame, text="下一页", command=self._next_page)
        self.next_button.pack(side="left")
        
        self.page_entry_label = ttk.Label(navigation_frame, text="跳转到页：", font=("Arial", 10))
        self.page_entry_label.pack(side="left", padx=(20, 5))
        
        self.page_var = tk.StringVar(value="1")
        self.page_entry = ttk.Entry(navigation_frame, textvariable=self.page_var, width=5)
        self.page_entry.pack(side="left", padx=(0, 5))
        
        self.go_button = ttk.Button(navigation_frame, text="跳转", command=self._go_to_page)
        self.go_button.pack(side="left")
        
        right_spacer_frame = ttk.Frame(self.root)
        right_spacer_frame.grid(row=0, column=3, sticky="nsew")
        
    def _bind_events(self):
        """绑定事件"""
        self.input_text.bind("<KeyRelease>", self._on_input_change)
        self.root.bind("<Configure>", self._on_window_resize)
        
    def _clean_input(self):
        """清理输入框中的特殊字符"""
        try:
            current_text = self.input_text.get("1.0", tk.END)
            cleaned_text = CopybookPreview.clean_input_text(current_text)
            
            if cleaned_text != current_text:
                self.input_text.delete("1.0", tk.END)
                self.input_text.insert("1.0", cleaned_text.rstrip('\n'))
        except Exception as e:
            print(f"清理输入时出错: {e}")
        
    def _on_input_change(self, event=None):
        """输入变化时的处理"""
        if event and event.keysym in ('Left', 'Right', 'Up', 'Down', 
                                       'Shift_L', 'Shift_R', 'Control_L', 'Control_R',
                                       'Alt_L', 'Alt_R', 'Caps_Lock', 'Tab'):
            self._schedule_update()
            return
        
        self._clean_input()
        self.current_page = 1
        self._schedule_update()
        
    def _on_grid_type_change(self):
        """格子类型变化时的处理"""
        self._schedule_update()
    
    def _on_window_resize(self, event=None):
        """窗口大小变化时的处理"""
        if event and event.widget == self.root:
            self._schedule_update()
    
    def _prev_page(self):
        """上一页"""
        if self.current_page > 1:
            self.current_page -= 1
            self._update_preview()
    
    def _next_page(self):
        """下一页"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self._update_preview()
    
    def _go_to_page(self):
        """跳转到指定页"""
        try:
            page = int(self.page_var.get())
            if 1 <= page <= self.total_pages:
                self.current_page = page
                self._update_preview()
            else:
                messagebox.showwarning("提示", f"请输入1到{self.total_pages}之间的页码")
        except ValueError:
            messagebox.showwarning("提示", "请输入有效的页码")
    
    def _update_navigation_buttons(self):
        """更新导航按钮状态"""
        self.prev_button.config(state="normal" if self.current_page > 1 else "disabled")
        self.next_button.config(state="normal" if self.current_page < self.total_pages else "disabled")
        self.page_var.set(str(self.current_page))
        self.page_label.config(text=f"第 {self.current_page} 页 / 共 {self.total_pages} 页")
        
    def _schedule_update(self):
        """调度更新预览（防抖）"""
        if self.debounce_job:
            self.root.after_cancel(self.debounce_job)
        self.debounce_job = self.root.after(self.debounce_delay, self._update_preview)
        
    def _schedule_initial_update(self):
        """调度初始更新"""
        self.root.after(100, self._update_preview)
        
    def _update_preview(self):
        """更新预览"""
        try:
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()
            
            if canvas_width < 10 or canvas_height < 10:
                self.root.after(100, self._update_preview)
                return
            
            text = self.input_text.get("1.0", tk.END)
            characters = CopybookPreview.filter_valid_characters(text)
            grid_type = self.grid_type_var.get()
            
            self.total_pages = self.preview.calculate_total_pages(characters, canvas_width, canvas_height)
            
            if self.current_page > self.total_pages:
                self.current_page = self.total_pages
            
            self._update_navigation_buttons()
            
            img = self.preview.generate_preview_page(characters, self.current_page, grid_type, canvas_width, canvas_height)
            
            if img:
                self.preview_image = ImageTk.PhotoImage(img)
                self.preview_canvas.delete("all")
                self.preview_canvas.create_image(0, 0, anchor=tk.NW, image=self.preview_image)
            
        except Exception as e:
            print(f"更新预览时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def _export_pdf(self):
        """导出PDF文件"""
        if not REPORTLAB_AVAILABLE:
            messagebox.showerror("错误", "需要安装 reportlab 库\n请运行: pip install reportlab")
            return
        
        text = self.input_text.get("1.0", tk.END)
        characters = CopybookPreview.filter_valid_characters(text)
        
        if not characters:
            messagebox.showwarning("提示", "请先输入要生成字帖的文字")
            return
        
        default_filename = datetime.now().strftime("%Y%m%d_%H%M%S") + ".pdf"
        
        save_path = filedialog.asksaveasfilename(
            title="保存 PDF",
            initialfile=default_filename,
            defaultextension=".pdf",
            filetypes=[("PDF 文件", "*.pdf"), ("所有文件", "*.*")]
        )
        
        if not save_path:
            return
        
        try:
            page_width = int(A4[0] - 20 * mm)
            page_height = int(A4[1] - 20 * mm)
            
            grid_type = self.grid_type_var.get()
            pages = self.preview.generate_all_pages(characters, grid_type, page_width, page_height)
            
            c = canvas.Canvas(save_path, pagesize=A4)
            
            margin_x = 10 * mm
            margin_y = 10 * mm
            
            temp_files = []
            try:
                for page_idx, page_img in enumerate(pages):
                    if page_idx > 0:
                        c.showPage()
                    
                    temp_img_path = os.path.join(os.path.dirname(save_path), f"_temp_copybook_page_{page_idx}.png")
                    page_img.save(temp_img_path, "PNG")
                    temp_files.append(temp_img_path)
                    
                    c.drawImage(temp_img_path, margin_x, margin_y, 
                                width=page_width, height=page_height, 
                                preserveAspectRatio=True)
                
                c.save()
                
                messagebox.showinfo("成功", f"PDF 已成功导出:\n{save_path}")
                
            finally:
                for temp_file in temp_files:
                    if os.path.exists(temp_file):
                        try:
                            os.remove(temp_file)
                        except:
                            pass
            
        except Exception as e:
            messagebox.showerror("错误", f"导出 PDF 时出错:\n{str(e)}")
            import traceback
            traceback.print_exc()


def main():
    """主函数"""
    root = tk.Tk()
    app = CopybookGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
