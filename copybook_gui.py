#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
字帖生成器 GUI 版本
生成田字格、米字格、回宫格、方格格式的字帖
使用 PyQt5 替代 tkinter
"""

import sys
import os
from datetime import datetime
from typing import List, Tuple, Optional

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QComboBox, QRadioButton, QButtonGroup,
    QLineEdit, QPushButton, QGroupBox, QFrame, QSplitter,
    QMessageBox, QFileDialog, QSpinBox
)
from PyQt5.QtCore import Qt, QTimer, QSize, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor, QImage, QPixmap

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from copybook_generator import GridType, CopybookPreview, StudentInfoValidator, PaperSize, GridSize


class CopybookGUI(QMainWindow):
    """字帖生成器 GUI 主类 - 负责界面交互"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("字帖生成器")
        self.setMinimumSize(900, 600)
        self.resize(1200, 800)
        
        self.preview = CopybookPreview()
        self.debounce_timer = QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self._update_preview)
        self.debounce_delay = 300
        
        self.current_page = 1
        self.total_pages = 1
        
        self.paper_size_var = "A4"
        self.grid_size_var = "1.8cm"
        
        self._last_canvas_width = 0
        self._last_canvas_height = 0
        
        self._create_ui()
        self._bind_events()
        self._schedule_initial_update()
        
    def _create_ui(self):
        """创建UI界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        
        input_group = QGroupBox("输入文字")
        input_layout = QVBoxLayout(input_group)
        
        self.input_text = QTextEdit()
        self.input_text.setWrapMode(QTextEdit.WidgetWidth)
        font = QFont("Arial", 14)
        self.input_text.setFont(font)
        self.input_text.setMinimumHeight(200)
        input_layout.addWidget(self.input_text)
        
        input_hint = QLabel("支持：中文、英文、数字\n空格和换行不占格\n不支持：标点符号、特殊字符")
        input_hint.setStyleSheet("color: gray; font-size: 10px;")
        input_layout.addWidget(input_hint)
        
        left_layout.addWidget(input_group)
        
        paper_size_group = QGroupBox("纸张选择")
        paper_size_layout = QVBoxLayout(paper_size_group)
        
        paper_size_options = ["A4", "16开", "B5", "A5", "A6"]
        self.paper_size_combobox = QComboBox()
        self.paper_size_combobox.addItems(paper_size_options)
        self.paper_size_combobox.setCurrentText("A4")
        paper_size_layout.addWidget(self.paper_size_combobox)
        
        left_layout.addWidget(paper_size_group)
        
        grid_size_group = QGroupBox("格子大小")
        grid_size_layout = QVBoxLayout(grid_size_group)
        
        grid_size_options = ["1.5cm", "1.8cm", "2.0cm"]
        self.grid_size_combobox = QComboBox()
        self.grid_size_combobox.addItems(grid_size_options)
        self.grid_size_combobox.setCurrentText("1.8cm")
        grid_size_layout.addWidget(self.grid_size_combobox)
        
        left_layout.addWidget(grid_size_group)
        
        grid_type_group = QGroupBox("格子类型")
        grid_type_layout = QVBoxLayout(grid_type_group)
        
        self.grid_type_group = QButtonGroup()
        
        grid_types = [
            (GridType.TIANZI, "田字格"),
            (GridType.MIZI, "米字格"),
            (GridType.HUIGONG, "回宫格"),
            (GridType.FANGGE, "方格"),
        ]
        
        for i, (value, text) in enumerate(grid_types):
            rb = QRadioButton(text)
            self.grid_type_group.addButton(rb, i)
            rb.setProperty("grid_type", value)
            if value == GridType.TIANZI:
                rb.setChecked(True)
            grid_type_layout.addWidget(rb)
        
        left_layout.addWidget(grid_type_group)
        
        student_info_group = QGroupBox("学员信息")
        student_info_layout = QVBoxLayout(student_info_group)
        
        name_layout = QHBoxLayout()
        name_label = QLabel("姓名：")
        name_label.setFixedWidth(40)
        self.student_name_entry = QLineEdit()
        name_hint = QLabel("(中英文)")
        name_hint.setStyleSheet("color: gray; font-size: 9px;")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.student_name_entry, 1)
        name_layout.addWidget(name_hint)
        student_info_layout.addLayout(name_layout)
        
        class_layout = QHBoxLayout()
        class_label = QLabel("班级：")
        class_label.setFixedWidth(40)
        self.student_class_entry = QLineEdit()
        class_hint = QLabel("(汉字/数字/括号)")
        class_hint.setStyleSheet("color: gray; font-size: 9px;")
        class_layout.addWidget(class_label)
        class_layout.addWidget(self.student_class_entry, 1)
        class_layout.addWidget(class_hint)
        student_info_layout.addLayout(class_layout)
        
        id_layout = QHBoxLayout()
        id_label = QLabel("学号：")
        id_label.setFixedWidth(40)
        self.student_id_entry = QLineEdit()
        id_hint = QLabel("(字母/数字)")
        id_hint.setStyleSheet("color: gray; font-size: 9px;")
        id_layout.addWidget(id_label)
        id_layout.addWidget(self.student_id_entry, 1)
        id_layout.addWidget(id_hint)
        student_info_layout.addLayout(id_layout)
        
        self.validation_label = QLabel("")
        self.validation_label.setStyleSheet("color: red; font-size: 9px;")
        student_info_layout.addWidget(self.validation_label)
        
        left_layout.addWidget(student_info_group)
        
        export_group = QGroupBox("导出")
        export_layout = QVBoxLayout(export_group)
        
        self.export_button = QPushButton("导出 PDF")
        export_layout.addWidget(self.export_button)
        
        if not REPORTLAB_AVAILABLE:
            self.export_button.setEnabled(False)
            hint_label = QLabel("需要安装 reportlab 库\npip install reportlab")
            hint_label.setStyleSheet("color: red; font-size: 9px;")
            hint_label.setAlignment(Qt.AlignCenter)
            export_layout.addWidget(hint_label)
        
        left_layout.addWidget(export_group)
        
        left_layout.addStretch(1)
        
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(5)
        
        preview_top_frame = QFrame()
        preview_top_layout = QHBoxLayout(preview_top_frame)
        preview_top_layout.setContentsMargins(5, 5, 5, 5)
        
        preview_label = QLabel("预览")
        preview_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        preview_top_layout.addWidget(preview_label)
        
        preview_top_layout.addStretch(1)
        
        self.page_label = QLabel("第 1 页 / 共 1 页")
        self.page_label.setStyleSheet("font-size: 10px;")
        preview_top_layout.addWidget(self.page_label)
        
        right_layout.addWidget(preview_top_frame)
        
        self.preview_frame = QFrame()
        self.preview_frame.setStyleSheet("background-color: #f0f0f0; border: 1px solid #888;")
        preview_frame_layout = QVBoxLayout(self.preview_frame)
        preview_frame_layout.setContentsMargins(10, 10, 10, 10)
        
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(400, 500)
        preview_frame_layout.addWidget(self.preview_label)
        
        right_layout.addWidget(self.preview_frame, 1)
        
        navigation_frame = QFrame()
        navigation_layout = QHBoxLayout(navigation_frame)
        navigation_layout.setContentsMargins(5, 5, 5, 5)
        
        self.prev_button = QPushButton("上一页")
        self.prev_button.setEnabled(False)
        navigation_layout.addWidget(self.prev_button)
        
        self.next_button = QPushButton("下一页")
        self.next_button.setEnabled(False)
        navigation_layout.addWidget(self.next_button)
        
        navigation_layout.addSpacing(20)
        
        page_entry_label = QLabel("跳转到页：")
        page_entry_label.setStyleSheet("font-size: 10px;")
        navigation_layout.addWidget(page_entry_label)
        
        self.page_spinbox = QSpinBox()
        self.page_spinbox.setMinimum(1)
        self.page_spinbox.setMaximum(1)
        self.page_spinbox.setValue(1)
        self.page_spinbox.setFixedWidth(60)
        navigation_layout.addWidget(self.page_spinbox)
        
        self.go_button = QPushButton("跳转")
        navigation_layout.addWidget(self.go_button)
        
        navigation_layout.addStretch(1)
        
        right_layout.addWidget(navigation_frame)
        
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 700])
        
        self._update_navigation_buttons()
        
    def _bind_events(self):
        """绑定事件"""
        self.input_text.textChanged.connect(self._on_input_change)
        
        self.student_name_entry.textChanged.connect(self._on_student_info_change)
        self.student_class_entry.textChanged.connect(self._on_student_info_change)
        self.student_id_entry.textChanged.connect(self._on_student_info_change)
        
        self.paper_size_combobox.currentTextChanged.connect(self._on_paper_size_change)
        self.grid_size_combobox.currentTextChanged.connect(self._on_grid_size_change)
        
        for button in self.grid_type_group.buttons():
            button.clicked.connect(self._on_grid_type_change)
        
        self.prev_button.clicked.connect(self._prev_page)
        self.next_button.clicked.connect(self._next_page)
        self.go_button.clicked.connect(self._go_to_page)
        
        self.export_button.clicked.connect(self._export_pdf)
        
    def _clean_input(self):
        """清理输入框中的特殊字符"""
        try:
            cursor = self.input_text.textCursor()
            cursor_pos = cursor.position()
            
            current_text = self.input_text.toPlainText()
            cleaned_text = CopybookPreview.clean_input_text(current_text)
            
            if cleaned_text != current_text:
                self.input_text.blockSignals(True)
                self.input_text.setPlainText(cleaned_text.rstrip('\n'))
                cursor = self.input_text.textCursor()
                cursor.setPosition(min(cursor_pos, len(cleaned_text.rstrip('\n'))))
                self.input_text.setTextCursor(cursor)
                self.input_text.blockSignals(False)
        except Exception as e:
            print(f"清理输入时出错: {e}")
        
    def _on_input_change(self):
        """输入变化时的处理"""
        self._clean_input()
        self.current_page = 1
        self._schedule_update()
        
    def _on_grid_type_change(self):
        """格子类型变化时的处理"""
        self._schedule_update()
    
    def _on_paper_size_change(self, text):
        """纸张大小变化时的处理"""
        self.paper_size_var = text
        self.current_page = 1
        self._schedule_update()
    
    def _on_grid_size_change(self, text):
        """格子大小变化时的处理"""
        self.grid_size_var = text
        grid_size_cm = GridSize.get_size_by_name(text)
        self.preview.set_grid_size(grid_size_cm)
        self.current_page = 1
        self._schedule_update()
    
    def _on_student_info_change(self):
        """学生信息输入变化时的处理"""
        self._validate_and_update_preview()
    
    def _clean_student_info_entry(self, entry: QLineEdit, validator_func):
        """清理单个输入框中的无效字符"""
        try:
            cursor_pos = entry.cursorPosition()
            current_text = entry.text()
            cleaned_text = validator_func(current_text)
            
            if cleaned_text != current_text:
                removed_chars = len(current_text) - len(cleaned_text)
                new_cursor_pos = max(0, cursor_pos - removed_chars)
                
                entry.blockSignals(True)
                entry.setText(cleaned_text)
                entry.setCursorPosition(new_cursor_pos)
                entry.blockSignals(False)
        except Exception as e:
            print(f"清理输入框时出错: {e}")
    
    def _validate_and_update_preview(self):
        """验证学生信息并更新预览"""
        name = self.student_name_entry.text()
        class_name = self.student_class_entry.text()
        student_id = self.student_id_entry.text()
        
        valid, error_msg = StudentInfoValidator.is_valid_name(name)
        if not valid:
            self.validation_label.setText(error_msg)
            self._clean_student_info_entry(self.student_name_entry, StudentInfoValidator.clean_name)
            return
        
        valid, error_msg = StudentInfoValidator.is_valid_class(class_name)
        if not valid:
            self.validation_label.setText(error_msg)
            self._clean_student_info_entry(self.student_class_entry, StudentInfoValidator.clean_class)
            return
        
        valid, error_msg = StudentInfoValidator.is_valid_student_id(student_id)
        if not valid:
            self.validation_label.setText(error_msg)
            self._clean_student_info_entry(self.student_id_entry, StudentInfoValidator.clean_student_id)
            return
        
        self.validation_label.setText("")
        
        name = self.student_name_entry.text()
        class_name = self.student_class_entry.text()
        student_id = self.student_id_entry.text()
        
        self.preview.set_student_info(name, class_name, student_id)
        self._schedule_update()
    
    def _check_resize(self):
        """检查窗口大小变化"""
        canvas_width = self.preview_frame.width() - 20
        canvas_height = self.preview_frame.height() - 20
        
        if canvas_width != self._last_canvas_width or canvas_height != self._last_canvas_height:
            self._last_canvas_width = canvas_width
            self._last_canvas_height = canvas_height
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
            page = self.page_spinbox.value()
            if 1 <= page <= self.total_pages:
                self.current_page = page
                self._update_preview()
            else:
                QMessageBox.warning(self, "提示", f"请输入1到{self.total_pages}之间的页码")
        except ValueError:
            QMessageBox.warning(self, "提示", "请输入有效的页码")
    
    def _update_navigation_buttons(self):
        """更新导航按钮状态"""
        self.prev_button.setEnabled(self.current_page > 1)
        self.next_button.setEnabled(self.current_page < self.total_pages)
        self.page_spinbox.setValue(self.current_page)
        self.page_spinbox.setMaximum(self.total_pages)
        self.page_label.setText(f"第 {self.current_page} 页 / 共 {self.total_pages} 页")
        
    def _schedule_update(self):
        """调度更新预览（防抖）"""
        self.debounce_timer.start(self.debounce_delay)
        
    def _schedule_initial_update(self):
        """调度初始更新"""
        QTimer.singleShot(100, self._update_preview)
        
    def _calculate_page_size(self, canvas_width: int, canvas_height: int) -> Tuple[int, int, float, float]:
        """
        根据画布尺寸和选择的纸张大小，计算预览页面的实际尺寸
        
        Args:
            canvas_width: 画布宽度
            canvas_height: 画布高度
            
        Returns:
            (页面宽度, 页面高度, 水平偏移, 垂直偏移)
        """
        paper_size_name = self.paper_size_var
        paper_width_mm, paper_height_mm = PaperSize.get_size_by_name(paper_size_name)
        
        paper_aspect_ratio = paper_width_mm / paper_height_mm
        canvas_aspect_ratio = canvas_width / canvas_height
        
        if paper_aspect_ratio > canvas_aspect_ratio:
            page_width = canvas_width - 20
            page_height = int(page_width / paper_aspect_ratio)
        else:
            page_height = canvas_height - 20
            page_width = int(page_height * paper_aspect_ratio)
        
        offset_x = (canvas_width - page_width) / 2
        offset_y = (canvas_height - page_height) / 2
        
        return page_width, page_height, offset_x, offset_y
    
    def _update_preview(self):
        """更新预览"""
        try:
            self._check_resize()
            
            canvas_width = self.preview_frame.width() - 20
            canvas_height = self.preview_frame.height() - 20
            
            if canvas_width < 10 or canvas_height < 10:
                QTimer.singleShot(100, self._update_preview)
                return
            
            name = self.student_name_entry.text()
            class_name = self.student_class_entry.text()
            student_id = self.student_id_entry.text()
            self.preview.set_student_info(name, class_name, student_id)
            
            grid_size_name = self.grid_size_var
            grid_size_cm = GridSize.get_size_by_name(grid_size_name)
            self.preview.set_grid_size(grid_size_cm)
            
            page_width, page_height, offset_x, offset_y = self._calculate_page_size(canvas_width, canvas_height)
            
            text = self.input_text.toPlainText()
            characters = CopybookPreview.filter_valid_characters(text)
            
            selected_button = self.grid_type_group.checkedButton()
            grid_type = selected_button.property("grid_type") if selected_button else GridType.TIANZI
            
            self.total_pages = self.preview.calculate_total_pages(characters, page_width, page_height)
            
            if self.current_page > self.total_pages:
                self.current_page = self.total_pages
            
            self._update_navigation_buttons()
            
            img = self.preview.generate_preview_page(characters, self.current_page, grid_type, page_width, page_height)
            
            if img:
                img = img.convert("RGBA")
                data = img.tobytes("raw", "RGBA")
                qimage = QImage(data, img.width, img.height, QImage.Format_RGBA8888)
                pixmap = QPixmap.fromImage(qimage)
                self.preview_label.setPixmap(pixmap)
            
        except Exception as e:
            print(f"更新预览时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def _export_pdf(self):
        """导出PDF文件"""
        if not REPORTLAB_AVAILABLE:
            QMessageBox.critical(self, "错误", "需要安装 reportlab 库\n请运行: pip install reportlab")
            return
        
        text = self.input_text.toPlainText()
        characters = CopybookPreview.filter_valid_characters(text)
        
        if not characters:
            QMessageBox.warning(self, "提示", "请先输入要生成字帖的文字")
            return
        
        default_filename = datetime.now().strftime("%Y%m%d_%H%M%S") + ".pdf"
        
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存 PDF",
            default_filename,
            "PDF 文件 (*.pdf);;所有文件 (*.*)"
        )
        
        if not save_path:
            return
        
        try:
            name = self.student_name_entry.text()
            class_name = self.student_class_entry.text()
            student_id = self.student_id_entry.text()
            self.preview.set_student_info(name, class_name, student_id)
            
            grid_size_name = self.grid_size_var
            grid_size_cm = GridSize.get_size_by_name(grid_size_name)
            self.preview.set_grid_size(grid_size_cm)
            
            paper_size_name = self.paper_size_var
            paper_width_mm, paper_height_mm = PaperSize.get_size_by_name(paper_size_name)
            
            paper_width_points = paper_width_mm * mm
            paper_height_points = paper_height_mm * mm
            custom_page_size = (paper_width_points, paper_height_points)
            
            margin = 10 * mm
            content_width = int(paper_width_points - 2 * margin)
            content_height = int(paper_height_points - 2 * margin)
            
            selected_button = self.grid_type_group.checkedButton()
            grid_type = selected_button.property("grid_type") if selected_button else GridType.TIANZI
            pages = self.preview.generate_all_pages(characters, grid_type, content_width, content_height)
            
            c = canvas.Canvas(save_path, pagesize=custom_page_size)
            
            margin_x = margin
            margin_y = margin
            
            temp_files = []
            try:
                for page_idx, page_img in enumerate(pages):
                    if page_idx > 0:
                        c.showPage()
                    
                    temp_img_path = os.path.join(os.path.dirname(save_path), f"_temp_copybook_page_{page_idx}.png")
                    page_img.save(temp_img_path, "PNG")
                    temp_files.append(temp_img_path)
                    
                    page_width, page_height = page_img.size
                    
                    c.drawImage(temp_img_path, margin_x, margin_y, 
                                width=page_width, height=page_height, 
                                preserveAspectRatio=True)
                
                c.save()
                
                QMessageBox.information(self, "成功", f"PDF 已成功导出:\n{save_path}")
                
            finally:
                for temp_file in temp_files:
                    if os.path.exists(temp_file):
                        try:
                            os.remove(temp_file)
                        except:
                            pass
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出 PDF 时出错:\n{str(e)}")
            import traceback
            traceback.print_exc()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    app.setStyle('Fusion')
    
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(240, 240, 240))
    palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
    palette.setColor(QPalette.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.AlternateBase, QColor(245, 245, 245))
    palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
    palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
    palette.setColor(QPalette.Text, QColor(0, 0, 0))
    palette.setColor(QPalette.Button, QColor(240, 240, 240))
    palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
    palette.setColor(QPalette.BrightText, QColor(255, 255, 255))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)
    
    window = CopybookGUI()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
