#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
字帖生成器 GUI 版本
生成田字格、米字格、回宫格、方格格式的字帖
"""

import sys
import os
from datetime import datetime
from typing import List, Tuple, Optional

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import ImageTk

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from copybook_generator import GridType, CopybookPreview, StudentInfoValidator


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
        self.root.columnconfigure(2, weight=7)
        self.root.columnconfigure(3, weight=0)
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
        grid_label_frame.pack(fill=tk.X, pady=(0, 10))
        
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
        
        student_info_frame = ttk.LabelFrame(left_frame, text="学员信息", padding=5)
        student_info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.student_name_var = tk.StringVar()
        name_frame = ttk.Frame(student_info_frame)
        name_frame.pack(fill=tk.X, pady=2)
        name_label = ttk.Label(name_frame, text="姓名：", width=6)
        name_label.pack(side="left")
        self.student_name_entry = ttk.Entry(name_frame, textvariable=self.student_name_var)
        self.student_name_entry.pack(side="left", fill=tk.X, expand=True)
        name_hint = ttk.Label(name_frame, text="(中英文)", foreground="gray", font=("Arial", 9))
        name_hint.pack(side="left", padx=2)
        
        self.student_class_var = tk.StringVar()
        class_frame = ttk.Frame(student_info_frame)
        class_frame.pack(fill=tk.X, pady=2)
        class_label = ttk.Label(class_frame, text="班级：", width=6)
        class_label.pack(side="left")
        self.student_class_entry = ttk.Entry(class_frame, textvariable=self.student_class_var)
        self.student_class_entry.pack(side="left", fill=tk.X, expand=True)
        class_hint = ttk.Label(class_frame, text="(汉字/数字/括号)", foreground="gray", font=("Arial", 9))
        class_hint.pack(side="left", padx=2)
        
        self.student_id_var = tk.StringVar()
        id_frame = ttk.Frame(student_info_frame)
        id_frame.pack(fill=tk.X, pady=2)
        id_label = ttk.Label(id_frame, text="学号：", width=6)
        id_label.pack(side="left")
        self.student_id_entry = ttk.Entry(id_frame, textvariable=self.student_id_var)
        self.student_id_entry.pack(side="left", fill=tk.X, expand=True)
        id_hint = ttk.Label(id_frame, text="(字母/数字)", foreground="gray", font=("Arial", 9))
        id_hint.pack(side="left", padx=2)
        
        self.validation_label = ttk.Label(student_info_frame, text="", foreground="red", font=("Arial", 9))
        self.validation_label.pack(anchor="w", pady=(2, 0))
        
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
        
        self.prev_button = ttk.Button(navigation_frame, text="上一页", command=self._prev_page, state="disabled")
        self.prev_button.pack(side="left", padx=(0, 10))
        
        self.next_button = ttk.Button(navigation_frame, text="下一页", command=self._next_page, state="disabled")
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
        
        self._update_navigation_buttons()
        
    def _bind_events(self):
        """绑定事件"""
        self.input_text.bind("<KeyRelease>", self._on_input_change)
        self.root.bind("<Configure>", self._on_window_resize)
        
        self.student_name_entry.bind("<KeyRelease>", self._on_student_info_change)
        self.student_class_entry.bind("<KeyRelease>", self._on_student_info_change)
        self.student_id_entry.bind("<KeyRelease>", self._on_student_info_change)
        
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
    
    def _on_student_info_change(self, event=None):
        """学生信息输入变化时的处理"""
        if event and event.keysym in ('Left', 'Right', 'Up', 'Down', 
                                       'Shift_L', 'Shift_R', 'Control_L', 'Control_R',
                                       'Alt_L', 'Alt_R', 'Caps_Lock', 'Tab'):
            self._schedule_update()
            return
        
        self._validate_and_update_preview()
    
    def _clean_student_info_entry(self, entry: tk.Entry, validator_func):
        """清理单个输入框中的无效字符，保留光标位置"""
        try:
            cursor_pos = entry.index(tk.INSERT)
            current_text = entry.get()
            cleaned_text = validator_func(current_text)
            
            if cleaned_text != current_text:
                removed_chars = len(current_text) - len(cleaned_text)
                new_cursor_pos = max(0, cursor_pos - removed_chars)
                
                entry.delete(0, tk.END)
                entry.insert(0, cleaned_text)
                entry.icursor(new_cursor_pos)
        except Exception as e:
            print(f"清理输入框时出错: {e}")
    
    def _validate_and_update_preview(self):
        """验证学生信息并更新预览"""
        name = self.student_name_var.get()
        class_name = self.student_class_var.get()
        student_id = self.student_id_var.get()
        
        valid, error_msg = StudentInfoValidator.is_valid_name(name)
        if not valid:
            self.validation_label.config(text=error_msg)
            self._clean_student_info_entry(self.student_name_entry, StudentInfoValidator.clean_name)
            return
        
        valid, error_msg = StudentInfoValidator.is_valid_class(class_name)
        if not valid:
            self.validation_label.config(text=error_msg)
            self._clean_student_info_entry(self.student_class_entry, StudentInfoValidator.clean_class)
            return
        
        valid, error_msg = StudentInfoValidator.is_valid_student_id(student_id)
        if not valid:
            self.validation_label.config(text=error_msg)
            self._clean_student_info_entry(self.student_id_entry, StudentInfoValidator.clean_student_id)
            return
        
        self.validation_label.config(text="")
        
        name = self.student_name_var.get()
        class_name = self.student_class_var.get()
        student_id = self.student_id_var.get()
        
        self.preview.set_student_info(name, class_name, student_id)
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
            
            name = self.student_name_var.get()
            class_name = self.student_class_var.get()
            student_id = self.student_id_var.get()
            self.preview.set_student_info(name, class_name, student_id)
            
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
            name = self.student_name_var.get()
            class_name = self.student_class_var.get()
            student_id = self.student_id_var.get()
            self.preview.set_student_info(name, class_name, student_id)
            
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
