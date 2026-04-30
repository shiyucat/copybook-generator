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
from typing import List, Tuple, Optional, Dict, Any

import tkinter as tk
from tkinter import ttk, font, messagebox, simpledialog
from PIL import Image, ImageDraw, ImageFont, ImageTk

from database import TemplateDatabase, Template


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


class TemplateManagerDialog:
    """模版管理对话框"""
    
    def __init__(self, parent, db: TemplateDatabase, on_apply_template=None):
        self.parent = parent
        self.db = db
        self.on_apply_template = on_apply_template
        self.dialog = None
        self.template_listbox = None
        self.selected_template = None
        
        self._create_dialog()
    
    def _create_dialog(self):
        """创建对话框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("模版管理")
        self.dialog.geometry("500x400")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        label = ttk.Label(main_frame, text="已保存的模版", font=("Arial", 12, "bold"))
        label.pack(anchor="w", pady=(0, 5))
        
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("name", "created_at", "updated_at")
        self.template_listbox = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        
        self.template_listbox.heading("name", text="模版名称")
        self.template_listbox.heading("created_at", text="创建时间")
        self.template_listbox.heading("updated_at", text="更新时间")
        
        self.template_listbox.column("name", width=180)
        self.template_listbox.column("created_at", width=140)
        self.template_listbox.column("updated_at", width=140)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.template_listbox.yview)
        self.template_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.template_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.template_listbox.bind("<<TreeviewSelect>>", self._on_select)
        self.template_listbox.bind("<Double-1>", self._on_double_click)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.apply_btn = ttk.Button(button_frame, text="应用模版", command=self._apply_template, state=tk.DISABLED)
        self.apply_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.delete_btn = ttk.Button(button_frame, text="删除模版", command=self._delete_template, state=tk.DISABLED)
        self.delete_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        refresh_btn = ttk.Button(button_frame, text="刷新", command=self._refresh_list)
        refresh_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        close_btn = ttk.Button(button_frame, text="关闭", command=self._close)
        close_btn.pack(side=tk.RIGHT)
        
        self._refresh_list()
    
    def _refresh_list(self):
        """刷新模版列表"""
        for item in self.template_listbox.get_children():
            self.template_listbox.delete(item)
        
        templates = self.db.get_all_templates()
        
        if not templates:
            self.template_listbox.insert("", tk.END, values=("暂无保存的模版", "", ""))
            self.template_listbox.item(self.template_listbox.get_children()[0], tags=("empty",))
        else:
            for template in templates:
                created_at = self._format_datetime(template.created_at)
                updated_at = self._format_datetime(template.updated_at)
                self.template_listbox.insert("", tk.END, iid=str(template.template_id),
                                               values=(template.template_name, created_at, updated_at))
        
        self._update_buttons()
    
    def _format_datetime(self, dt_str: str) -> str:
        """格式化日期时间显示"""
        try:
            if "T" in dt_str:
                dt_str = dt_str.replace("T", " ")
            if "." in dt_str:
                dt_str = dt_str.split(".")[0]
            return dt_str
        except:
            return dt_str
    
    def _on_select(self, event=None):
        """选择变化时更新按钮状态"""
        self._update_buttons()
    
    def _on_double_click(self, event=None):
        """双击应用模版"""
        self._apply_template()
    
    def _update_buttons(self):
        """更新按钮状态"""
        selection = self.template_listbox.selection()
        if selection:
            item = selection[0]
            if item and self.template_listbox.item(item, "values")[0] != "暂无保存的模版":
                self.selected_template = item
                self.apply_btn.config(state=tk.NORMAL)
                self.delete_btn.config(state=tk.NORMAL)
                return
        
        self.selected_template = None
        self.apply_btn.config(state=tk.DISABLED)
        self.delete_btn.config(state=tk.DISABLED)
    
    def _apply_template(self):
        """应用选中的模版"""
        if not self.selected_template:
            return
        
        try:
            template_id = int(self.selected_template)
            template = self.db.get_template_by_id(template_id)
            
            if template and self.on_apply_template:
                self.on_apply_template(template)
                messagebox.showinfo("成功", f"已应用模版: {template.template_name}")
                self._close()
        except Exception as e:
            messagebox.showerror("错误", f"应用模版失败: {e}")
    
    def _delete_template(self):
        """删除选中的模版"""
        if not self.selected_template:
            return
        
        item = self.selected_template
        values = self.template_listbox.item(item, "values")
        template_name = values[0]
        
        if messagebox.askyesno("确认删除", f"确定要删除模版「{template_name}」吗？\n此操作不可恢复。"):
            try:
                template_id = int(item)
                if self.db.delete_template(template_id):
                    self._refresh_list()
                    messagebox.showinfo("成功", f"已删除模版: {template_name}")
                else:
                    messagebox.showerror("错误", "删除失败")
            except Exception as e:
                messagebox.showerror("错误", f"删除失败: {e}")
    
    def _close(self):
        """关闭对话框"""
        self.dialog.destroy()


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
        
        self.db = TemplateDatabase()
        
        self._create_menu()
        self._create_ui()
        self._bind_events()
        self._schedule_initial_update()
    
    def _create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="保存模版", command=self._save_template)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        
        template_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="模版管理", menu=template_menu)
        template_menu.add_command(label="查看所有模版", command=self._show_template_manager)
        template_menu.add_separator()
        template_menu.add_command(label="保存当前配置为模版", command=self._save_template)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self._show_about)
    
    def _create_ui(self):
        """创建UI界面 - 保持原有布局"""
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
        
        save_template_frame = ttk.Frame(left_frame)
        save_template_frame.pack(fill=tk.X, pady=(10, 0))
        
        save_template_btn = ttk.Button(save_template_frame, text="保存模版", 
                                        command=self._save_template)
        save_template_btn.pack(fill=tk.X)
        
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
    
    def _get_current_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return {
            "grid_size": self.preview.grid_size,
            "grid_type": self.grid_type_var.get(),
            "input_text": self.input_text.get("1.0", tk.END).strip(),
        }
    
    def _apply_config(self, template: Template):
        """应用模版配置"""
        config = template.config_data
        
        grid_size = config.get("grid_size", 60)
        self.preview.grid_size = grid_size
        
        grid_type = config.get("grid_type", GridType.TIANZI)
        self.grid_type_var.set(grid_type)
        
        input_text = config.get("input_text", "")
        self.input_text.delete("1.0", tk.END)
        self.input_text.insert("1.0", input_text)
        
        self._schedule_update()
    
    def _save_template(self):
        """保存当前配置为模版"""
        template_name = simpledialog.askstring("保存模版", "请输入模版名称:", parent=self.root)
        
        if not template_name:
            return
        
        template_name = template_name.strip()
        if not template_name:
            messagebox.showwarning("警告", "模版名称不能为空")
            return
        
        existing = self.db.get_template_by_name(template_name)
        if existing:
            if not messagebox.askyesno("确认覆盖", 
                f"模版「{template_name}」已存在。\n是否覆盖原有配置？"):
                return
        
        try:
            config = self._get_current_config()
            template = Template(template_name=template_name, config_data=config)
            template_id = self.db.save_template(template)
            
            if existing:
                messagebox.showinfo("成功", f"已更新模版: {template_name}")
            else:
                messagebox.showinfo("成功", f"已保存模版: {template_name}")
                
        except Exception as e:
            messagebox.showerror("错误", f"保存模版失败: {e}")
    
    def _show_template_manager(self):
        """显示模版管理对话框"""
        TemplateManagerDialog(self.root, self.db, on_apply_template=self._apply_config)
    
    def _show_about(self):
        """显示关于对话框"""
        messagebox.showinfo("关于", 
            "字帖生成器 v1.0\n\n"
            "支持田字格、米字格、回宫格、方格格式\n"
            "支持模版保存和管理功能\n\n"
            "© 2024 Copybook Generator")


def main():
    """主函数"""
    root = tk.Tk()
    app = CopybookGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
