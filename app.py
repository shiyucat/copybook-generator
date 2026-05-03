#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Flask 后端 API
提供 Web 端与数据库交互的 REST API
"""

import os
import json
import re
import sqlite3
import urllib.parse
from datetime import datetime
from typing import Tuple
from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from pathlib import Path

try:
    from pypinyin import pinyin, Style
    PINYIN_AVAILABLE = True
except ImportError:
    PINYIN_AVAILABLE = False
    pinyin = None
    Style = None

from database import TemplateDatabase, Template, ExportHistory, Student, Assignment
from copybook_generator import (
    CopybookGenerator, 
    PAGE_SIZES, 
    DEFAULT_PAGE_SIZE,
    DEFAULT_GRID_SIZE_CM,
    DEFAULT_LINES_PER_CHAR,
    DEFAULT_SHOW_PINYIN
)


app = Flask(__name__)
CORS(app)

db = TemplateDatabase()


def hex_to_rgb(hex_color: str) -> Tuple[float, float, float]:
    """
    将HEX颜色转换为RGB元组（值为0.0-1.0）
    
    Args:
        hex_color: HEX颜色字符串，如 "#FF0000"
        
    Returns:
        RGB元组，如 (1.0, 0.0, 0.0)
    """
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 6:
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        return (r, g, b)
    return (0.0, 0.0, 0.0)


@app.route('/api/templates', methods=['GET'])
def get_templates():
    """
    获取模版列表（支持分页）
    
    Query Parameters:
        page: 页码（从1开始，可选，不传则返回所有）
        page_size: 每页数量（可选，默认10，可选值：10,20,40,100）
    
    Returns:
        JSON 格式的模版列表
    """
    try:
        page = request.args.get('page', type=int)
        page_size = request.args.get('page_size', 10, type=int)
        
        if page is not None and page > 0:
            page_size = max(10, min(100, page_size))
            if page_size not in [10, 20, 40, 100]:
                page_size = 10
            
            paginated = db.get_templates_paginated(page=page, page_size=page_size)
            
            result = []
            for template in paginated['templates']:
                result.append({
                    'template_id': template.template_id,
                    'template_name': template.template_name,
                    'config_data': template.config_data,
                    'created_at': template.created_at,
                    'updated_at': template.updated_at
                })
            
            return jsonify({
                'success': True,
                'data': result,
                'count': len(result),
                'pagination': {
                    'page': paginated['page'],
                    'page_size': paginated['page_size'],
                    'total': paginated['total'],
                    'total_pages': paginated['total_pages']
                }
            })
        else:
            templates = db.get_all_templates()
            
            result = []
            for template in templates:
                result.append({
                    'template_id': template.template_id,
                    'template_name': template.template_name,
                    'config_data': template.config_data,
                    'created_at': template.created_at,
                    'updated_at': template.updated_at
                })
            
            return jsonify({
                'success': True,
                'data': result,
                'count': len(result)
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/templates/<int:template_id>', methods=['GET'])
def get_template(template_id):
    """
    根据 ID 获取单个模版
    
    Args:
        template_id: 模版 ID
        
    Returns:
        JSON 格式的模版数据
    """
    try:
        template = db.get_template_by_id(template_id)
        
        if template is None:
            return jsonify({
                'success': False,
                'error': '模版不存在'
            }), 404
        
        result = {
            'template_id': template.template_id,
            'template_name': template.template_name,
            'config_data': template.config_data,
            'created_at': template.created_at,
            'updated_at': template.updated_at
        }
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/templates', methods=['POST'])
def create_template():
    """
    创建或更新模版
    
    Request Body:
        {
            "template_name": "模版名称",
            "config_data": {
                "grid_size": 60,
                "grid_type": "田字格",
                "input_text": "输入的文字",
                "student_name": "姓名",
                "student_id": "学号",
                "class_name": "班级"
            }
        }
        
    Returns:
        创建结果
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
        
        template_name = data.get('template_name', '').strip()
        
        if not template_name:
            return jsonify({
                'success': False,
                'error': '模版名称不能为空'
            }), 400
        
        config_data = data.get('config_data', {})
        
        if not isinstance(config_data, dict):
            return jsonify({
                'success': False,
                'error': 'config_data 必须是对象'
            }), 400
        
        existing = db.get_template_by_name(template_name)
        
        template = Template(
            template_name=template_name,
            config_data=config_data
        )
        
        template_id = db.save_template(template)
        
        if existing:
            message = f'已更新模版: {template_name}'
        else:
            message = f'已创建模版: {template_name}'
        
        return jsonify({
            'success': True,
            'message': message,
            'template_id': template_id,
            'is_update': existing is not None
        }), 201 if not existing else 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/templates/<int:template_id>', methods=['PUT'])
def update_template(template_id):
    """
    更新指定 ID 的模版
    
    Args:
        template_id: 模版 ID
        
    Request Body:
        {
            "template_name": "新的模版名称（可选）",
            "config_data": { ... } （可选）
        }
        
    Returns:
        更新结果
    """
    try:
        existing = db.get_template_by_id(template_id)
        
        if existing is None:
            return jsonify({
                'success': False,
                'error': '模版不存在'
            }), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
        
        template_name = data.get('template_name', existing.template_name).strip()
        config_data = data.get('config_data', existing.config_data)
        
        if not template_name:
            return jsonify({
                'success': False,
                'error': '模版名称不能为空'
            }), 400
        
        if not isinstance(config_data, dict):
            return jsonify({
                'success': False,
                'error': 'config_data 必须是对象'
            }), 400
        
        if template_name != existing.template_name:
            name_exists = db.get_template_by_name(template_name)
            if name_exists and name_exists.template_id != template_id:
                return jsonify({
                    'success': False,
                    'error': '模版名称已存在'
                }), 400
        
        template = Template(
            template_id=template_id,
            template_name=template_name,
            config_data=config_data,
            created_at=existing.created_at
        )
        
        new_id = db.save_template(template)
        
        return jsonify({
            'success': True,
            'message': f'已更新模版: {template_name}',
            'template_id': new_id
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/templates/<int:template_id>', methods=['DELETE'])
def delete_template(template_id):
    """
    删除指定 ID 的模版
    
    Args:
        template_id: 模版 ID
        
    Returns:
        删除结果
    """
    try:
        template = db.get_template_by_id(template_id)
        
        if template is None:
            return jsonify({
                'success': False,
                'error': '模版不存在'
            }), 404
        
        success = db.delete_template(template_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'已删除模版: {template.template_name}'
            })
        else:
            return jsonify({
                'success': False,
                'error': '删除失败'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/templates/check-name/<template_name>', methods=['GET'])
def check_template_name(template_name):
    """
    检查模版名称是否已存在
    
    Args:
        template_name: 模版名称
        
    Returns:
        名称是否存在
    """
    try:
        template_name = urllib.parse.unquote(template_name)
        exists = db.template_exists(template_name)
        
        return jsonify({
            'success': True,
            'exists': exists
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/templates/count', methods=['GET'])
def get_template_count():
    """
    获取模版总数
    
    Returns:
        模版数量
    """
    try:
        count = db.get_template_count()
        
        return jsonify({
            'success': True,
            'count': count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/export/pdf', methods=['POST'])
def export_pdf():
    """
    导出PDF字帖（按预览方式生成，每行一个字符）
    
    Request Body:
        {
            "characters": ["一", "二", "三"],
            "scene_type": "normal",
            "grid_type": "田字格",
            "grid_size_cm": 2.0,
            "lines_per_char": 1,
            "show_pinyin": false,
            "font_style": "zhenkai",
            "student_name": "学生姓名",
            "student_id": "学号",
            "class_name": "班级",
            "page_size": "A4",
            "font_color": "#000000",
            "pinyin_color": "#000000"
        }
    
    Returns:
        PDF文件下载
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
        
        characters = data.get('characters', [])
        if not characters:
            return jsonify({
                'success': False,
                'error': '请输入要生成的汉字'
            }), 400
        
        if not isinstance(characters, list):
            characters = [characters]
        
        scene_type = data.get('scene_type', 'normal')
        
        grid_type = data.get('grid_type', '田字格')
        if grid_type in ['田字格', 'tianzi']:
            grid_type_code = 'tianzi'
        elif grid_type in ['米字格', 'mizi']:
            grid_type_code = 'mizi'
        elif grid_type in ['回宫格', 'huigong']:
            grid_type_code = 'huigong'
        elif grid_type in ['方格', 'fangge']:
            grid_type_code = 'fangge'
        else:
            grid_type_code = 'tianzi'
        
        font_style = data.get('font_style', 'zhenkai')
        
        grid_size_cm = data.get('grid_size_cm', DEFAULT_GRID_SIZE_CM)
        try:
            grid_size_cm = float(grid_size_cm)
        except (TypeError, ValueError):
            grid_size_cm = DEFAULT_GRID_SIZE_CM
        
        lines_per_char = data.get('lines_per_char', DEFAULT_LINES_PER_CHAR)
        try:
            lines_per_char = int(lines_per_char)
            lines_per_char = max(1, min(50, lines_per_char))
        except (TypeError, ValueError):
            lines_per_char = DEFAULT_LINES_PER_CHAR
        
        show_pinyin = data.get('show_pinyin', DEFAULT_SHOW_PINYIN)
        
        student_name = data.get('student_name', '')
        student_id = data.get('student_id', '')
        class_name = data.get('class_name', '')
        page_size_key = data.get('page_size', DEFAULT_PAGE_SIZE)
        paper_size = PAGE_SIZES.get(page_size_key, PAGE_SIZES[DEFAULT_PAGE_SIZE])
        
        font_color_hex = data.get('font_color', '#000000')
        if not isinstance(font_color_hex, str) or not re.match(r'^#[0-9A-Fa-f]{6}$', font_color_hex):
            font_color_hex = '#000000'
        font_color = hex_to_rgb(font_color_hex)
        
        pinyin_color_hex = data.get('pinyin_color', '#000000')
        if not isinstance(pinyin_color_hex, str) or not re.match(r'^#[0-9A-Fa-f]{6}$', pinyin_color_hex):
            pinyin_color_hex = '#000000'
        pinyin_color = hex_to_rgb(pinyin_color_hex)
        
        grid_color_hex = data.get('grid_color', '#808080')
        if not isinstance(grid_color_hex, str) or not re.match(r'^#[0-9A-Fa-f]{6}$', grid_color_hex):
            grid_color_hex = '#808080'
        grid_color = hex_to_rgb(grid_color_hex)
        
        show_character_pinyin = data.get('show_character_pinyin', True)
        
        character_color_hex = data.get('character_color', '#000000')
        if not isinstance(character_color_hex, str) or not re.match(r'^#[0-9A-Fa-f]{6}$', character_color_hex):
            character_color_hex = '#000000'
        character_color = hex_to_rgb(character_color_hex)
        
        right_grid_color_hex = data.get('right_grid_color', '#000000')
        if not isinstance(right_grid_color_hex, str) or not re.match(r'^#[0-9A-Fa-f]{6}$', right_grid_color_hex):
            right_grid_color_hex = '#000000'
        right_grid_color = hex_to_rgb(right_grid_color_hex)
        
        right_grid_type = data.get('right_grid_type', '米字格')
        if right_grid_type not in ['田字格', '米字格', '回宫格', '方格']:
            right_grid_type = '米字格'
        
        stroke_order_color_hex = data.get('stroke_order_color', '#000000')
        if not isinstance(stroke_order_color_hex, str) or not re.match(r'^#[0-9A-Fa-f]{6}$', stroke_order_color_hex):
            stroke_order_color_hex = '#000000'
        stroke_order_color = hex_to_rgb(stroke_order_color_hex)
        
        show_trace_copy = data.get('show_trace_copy', False)
        if not isinstance(show_trace_copy, bool):
            show_trace_copy = False
        
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            output_path = tmp.name
        
        try:
            generator = CopybookGenerator(
                paper_size=paper_size,
                grid_type=grid_type_code,
                font_style=font_style,
                grid_color=grid_color,
                font_color=font_color,
                pinyin_color=pinyin_color,
                character_color=character_color,
                right_grid_color=right_grid_color,
                right_grid_type=right_grid_type,
                stroke_order_color=stroke_order_color,
                grid_size_cm=grid_size_cm,
                lines_per_char=lines_per_char,
                show_pinyin=show_pinyin,
                show_character_pinyin=show_character_pinyin,
                student_name=student_name,
                student_id=student_id,
                class_name=class_name,
                show_trace_copy=show_trace_copy
            )
            
            if scene_type == 'character':
                success, message = generator.generate_character_scene(characters, output_path)
            else:
                success, message = generator.generate_from_chars(characters, output_path)
            
            if not success:
                os.unlink(output_path)
                return jsonify({
                    'success': False,
                    'error': message
                }), 500
            
            with open(output_path, 'rb') as f:
                pdf_data = f.read()
            
            os.unlink(output_path)
            
            try:
                input_text = ''.join(characters) if isinstance(characters, list) else str(characters)
                config_data = {
                    'scene_type': scene_type,
                    'grid_type': grid_type,
                    'grid_color': grid_color_hex,
                    'grid_size_cm': grid_size_cm,
                    'lines_per_char': lines_per_char,
                    'show_pinyin': show_pinyin,
                    'pinyin_color': pinyin_color_hex,
                    'font_style': font_style,
                    'font_color': font_color_hex,
                    'student_name': student_name,
                    'student_id': student_id,
                    'class_name': class_name,
                    'page_size': page_size_key,
                    'show_character_pinyin': show_character_pinyin,
                    'character_color': character_color_hex,
                    'right_grid_color': right_grid_color_hex,
                    'right_grid_type': right_grid_type,
                    'stroke_order_color': stroke_order_color_hex,
                    'show_trace_copy': show_trace_copy,
                    'characters': characters,
                    'input_text': input_text,
                }
                
                export_history = ExportHistory(
                    scene_type=scene_type,
                    student_name=student_name,
                    student_id=student_id,
                    input_text=input_text,
                    page_size=page_size_key,
                    config_data=config_data
                )
                db.save_export_history(export_history)
            except Exception as history_err:
                print(f"保存导出历史失败: {history_err}")
            
            first_char = characters[0] if characters else ''
            filename = f"{first_char}_字帖.pdf" if first_char else "字帖.pdf"
            encoded_filename = urllib.parse.quote(filename)
            
            response = make_response(pdf_data)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f"attachment; filename*=UTF-8''{encoded_filename}"
            
            return response
            
        except Exception as e:
            if os.path.exists(output_path):
                os.unlink(output_path)
            raise e
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/pinyin', methods=['POST'])
def get_pinyin():
    """
    获取汉字拼音
    
    Request Body:
        {
            "characters": ["一", "二", "三"]
        }
    
    Returns:
        {
            "success": true,
            "data": {
                "一": "yī",
                "二": "èr",
                "三": "sān"
            }
        }
    """
    if not PINYIN_AVAILABLE:
        return jsonify({
            'success': False,
            'error': '拼音功能不可用，请安装 pypinyin：pip install pypinyin'
        }), 500
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
        
        characters = data.get('characters', [])
        if not characters:
            return jsonify({
                'success': False,
                'error': '请输入汉字'
            }), 400
        
        if not isinstance(characters, list):
            characters = [characters]
        
        result = {}
        for char in characters:
            if char:
                try:
                    pinyin_list = pinyin(char, style=Style.TONE)
                    if pinyin_list and pinyin_list[0]:
                        result[char] = pinyin_list[0][0]
                    else:
                        result[char] = char
                except Exception:
                    result[char] = char
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/export-history', methods=['GET'])
def get_export_history():
    """
    获取导出历史列表（支持分页和搜索）
    
    Query Parameters:
        page: 页码（从1开始，可选，不传则返回所有）
        page_size: 每页数量（可选，默认10，可选值：10,20,50,100）
        keyword: 搜索关键字（可选，用于姓名或学号的模糊匹配）
    
    Returns:
        JSON 格式的导出历史列表
    """
    try:
        page = request.args.get('page', type=int)
        page_size = request.args.get('page_size', 10, type=int)
        keyword = request.args.get('keyword', '', type=str).strip()
        
        if page is not None and page > 0:
            page_size = max(10, min(100, page_size))
            if page_size not in [10, 20, 50, 100]:
                page_size = 10
            
            if keyword:
                paginated = db.search_export_history_paginated(
                    keyword=keyword,
                    page=page, 
                    page_size=page_size
                )
            else:
                paginated = db.get_export_history_paginated(page=page, page_size=page_size)
            
            result = []
            for history in paginated['history']:
                result.append({
                    'history_id': history.history_id,
                    'scene_type': history.scene_type,
                    'student_name': history.student_name,
                    'student_id': history.student_id,
                    'input_text': history.input_text,
                    'page_size': history.page_size,
                    'export_count': history.export_count,
                    'config_data': history.config_data,
                    'created_at': history.created_at,
                    'updated_at': history.updated_at
                })
            
            return jsonify({
                'success': True,
                'data': result,
                'count': len(result),
                'pagination': {
                    'page': paginated['page'],
                    'page_size': paginated['page_size'],
                    'total': paginated['total'],
                    'total_pages': paginated['total_pages']
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': '请指定页码参数'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/export-history/<int:history_id>', methods=['GET'])
def get_export_history_by_id(history_id):
    """
    根据 ID 获取单个导出历史
    
    Args:
        history_id: 历史记录 ID
        
    Returns:
        JSON 格式的历史记录数据
    """
    try:
        history = db.get_export_history_by_id(history_id)
        
        if history is None:
            return jsonify({
                'success': False,
                'error': '历史记录不存在'
            }), 404
        
        result = {
            'history_id': history.history_id,
            'scene_type': history.scene_type,
            'student_name': history.student_name,
            'student_id': history.student_id,
            'input_text': history.input_text,
            'page_size': history.page_size,
            'export_count': history.export_count,
            'config_data': history.config_data,
            'created_at': history.created_at,
            'updated_at': history.updated_at
        }
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/export-history/<int:history_id>/export', methods=['POST'])
def re_export_from_history(history_id):
    """
    根据历史记录重新导出PDF
    
    Args:
        history_id: 历史记录 ID
        
    Returns:
        PDF文件下载
    """
    try:
        history = db.get_export_history_by_id(history_id)
        
        if history is None:
            return jsonify({
                'success': False,
                'error': '历史记录不存在'
            }), 404
        
        config_data = history.config_data or {}
        
        characters = config_data.get('characters', [])
        if not characters:
            return jsonify({
                'success': False,
                'error': '历史记录中没有文字内容'
            }), 400
        
        scene_type = config_data.get('scene_type', 'normal')
        grid_type = config_data.get('grid_type', '田字格')
        grid_color_hex = config_data.get('grid_color', '#808080')
        grid_size_cm = config_data.get('grid_size_cm', DEFAULT_GRID_SIZE_CM)
        lines_per_char = config_data.get('lines_per_char', DEFAULT_LINES_PER_CHAR)
        show_pinyin = config_data.get('show_pinyin', DEFAULT_SHOW_PINYIN)
        pinyin_color_hex = config_data.get('pinyin_color', '#000000')
        font_style = config_data.get('font_style', 'zhenkai')
        font_color_hex = config_data.get('font_color', '#000000')
        student_name = config_data.get('student_name', '')
        student_id = config_data.get('student_id', '')
        class_name = config_data.get('class_name', '')
        page_size_key = config_data.get('page_size', DEFAULT_PAGE_SIZE)
        show_character_pinyin = config_data.get('show_character_pinyin', True)
        character_color_hex = config_data.get('character_color', '#000000')
        right_grid_color_hex = config_data.get('right_grid_color', '#000000')
        right_grid_type = config_data.get('right_grid_type', '米字格')
        stroke_order_color_hex = config_data.get('stroke_order_color', '#000000')
        
        if grid_type in ['田字格', 'tianzi']:
            grid_type_code = 'tianzi'
        elif grid_type in ['米字格', 'mizi']:
            grid_type_code = 'mizi'
        elif grid_type in ['回宫格', 'huigong']:
            grid_type_code = 'huigong'
        elif grid_type in ['方格', 'fangge']:
            grid_type_code = 'fangge'
        else:
            grid_type_code = 'tianzi'
        
        if right_grid_type not in ['田字格', '米字格', '回宫格', '方格']:
            right_grid_type = '米字格'
        
        paper_size = PAGE_SIZES.get(page_size_key, PAGE_SIZES[DEFAULT_PAGE_SIZE])
        
        if not isinstance(grid_color_hex, str) or not re.match(r'^#[0-9A-Fa-f]{6}$', grid_color_hex):
            grid_color_hex = '#808080'
        grid_color = hex_to_rgb(grid_color_hex)
        
        if not isinstance(font_color_hex, str) or not re.match(r'^#[0-9A-Fa-f]{6}$', font_color_hex):
            font_color_hex = '#000000'
        font_color = hex_to_rgb(font_color_hex)
        
        if not isinstance(pinyin_color_hex, str) or not re.match(r'^#[0-9A-Fa-f]{6}$', pinyin_color_hex):
            pinyin_color_hex = '#000000'
        pinyin_color = hex_to_rgb(pinyin_color_hex)
        
        if not isinstance(character_color_hex, str) or not re.match(r'^#[0-9A-Fa-f]{6}$', character_color_hex):
            character_color_hex = '#000000'
        character_color = hex_to_rgb(character_color_hex)
        
        if not isinstance(right_grid_color_hex, str) or not re.match(r'^#[0-9A-Fa-f]{6}$', right_grid_color_hex):
            right_grid_color_hex = '#000000'
        right_grid_color = hex_to_rgb(right_grid_color_hex)
        
        if not isinstance(stroke_order_color_hex, str) or not re.match(r'^#[0-9A-Fa-f]{6}$', stroke_order_color_hex):
            stroke_order_color_hex = '#000000'
        stroke_order_color = hex_to_rgb(stroke_order_color_hex)
        
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            output_path = tmp.name
        
        try:
            generator = CopybookGenerator(
                paper_size=paper_size,
                grid_type=grid_type_code,
                font_style=font_style,
                grid_color=grid_color,
                font_color=font_color,
                pinyin_color=pinyin_color,
                character_color=character_color,
                right_grid_color=right_grid_color,
                right_grid_type=right_grid_type,
                stroke_order_color=stroke_order_color,
                grid_size_cm=grid_size_cm,
                lines_per_char=lines_per_char,
                show_pinyin=show_pinyin,
                show_character_pinyin=show_character_pinyin,
                student_name=student_name,
                student_id=student_id,
                class_name=class_name
            )
            
            if scene_type == 'character':
                success, message = generator.generate_character_scene(characters, output_path)
            else:
                success, message = generator.generate_from_chars(characters, output_path)
            
            if not success:
                os.unlink(output_path)
                return jsonify({
                    'success': False,
                    'error': message
                }), 500
            
            with open(output_path, 'rb') as f:
                pdf_data = f.read()
            
            os.unlink(output_path)
            
            try:
                db.increment_export_count(history_id)
            except Exception as update_err:
                print(f"更新导出次数失败: {update_err}")
            
            first_char = characters[0] if characters else ''
            filename = f"{first_char}_字帖.pdf" if first_char else "字帖.pdf"
            encoded_filename = urllib.parse.quote(filename)
            
            response = make_response(pdf_data)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f"attachment; filename*=UTF-8''{encoded_filename}"
            
            return response
            
        except Exception as e:
            if os.path.exists(output_path):
                os.unlink(output_path)
            raise e
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """
    健康检查接口
    
    Returns:
        服务状态
    """
    return jsonify({
        'success': True,
        'status': 'ok',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/students', methods=['GET'])
def get_students():
    """
    获取学生列表（支持分页和搜索）
    
    Query Parameters:
        page: 页码（从1开始，可选，不传则返回所有）
        page_size: 每页数量（可选，默认10）
        keyword: 搜索关键字（可选，用于姓名、学号、班级的模糊匹配）
    
    Returns:
        JSON 格式的学生列表
    """
    try:
        page = request.args.get('page', type=int)
        page_size = request.args.get('page_size', 10, type=int)
        keyword = request.args.get('keyword', '', type=str).strip()
        
        if page is not None and page > 0:
            page_size = max(10, min(100, page_size))
            if page_size not in [10, 20, 40, 100]:
                page_size = 10
            
            if keyword:
                paginated = db.search_students_paginated(
                    keyword=keyword,
                    page=page, 
                    page_size=page_size
                )
            else:
                paginated = db.get_students_paginated(page=page, page_size=page_size)
            
            result = []
            for student in paginated['students']:
                result.append({
                    'student_id': student.student_id,
                    'name': student.name,
                    'student_no': student.student_no,
                    'class_name': student.class_name,
                    'created_at': student.created_at,
                    'updated_at': student.updated_at
                })
            
            return jsonify({
                'success': True,
                'data': result,
                'count': len(result),
                'pagination': {
                    'page': paginated['page'],
                    'page_size': paginated['page_size'],
                    'total': paginated['total'],
                    'total_pages': paginated['total_pages']
                }
            })
        else:
            students = db.get_all_students()
            
            result = []
            for student in students:
                result.append({
                    'student_id': student.student_id,
                    'name': student.name,
                    'student_no': student.student_no,
                    'class_name': student.class_name,
                    'created_at': student.created_at,
                    'updated_at': student.updated_at
                })
            
            return jsonify({
                'success': True,
                'data': result,
                'count': len(result)
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/students/<int:student_id>', methods=['GET'])
def get_student(student_id):
    """
    根据 ID 获取单个学生
    
    Args:
        student_id: 学生 ID
        
    Returns:
        JSON 格式的学生数据
    """
    try:
        student = db.get_student_by_id(student_id)
        
        if student is None:
            return jsonify({
                'success': False,
                'error': '学生不存在'
            }), 404
        
        result = {
            'student_id': student.student_id,
            'name': student.name,
            'student_no': student.student_no,
            'class_name': student.class_name,
            'created_at': student.created_at,
            'updated_at': student.updated_at
        }
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/students/by-no/<student_no>', methods=['GET'])
def get_student_by_no(student_no):
    """
    根据学号获取学生
    
    Args:
        student_no: 学号
        
    Returns:
        JSON 格式的学生数据
    """
    try:
        student_no_decoded = urllib.parse.unquote(student_no)
        student = db.get_student_by_no(student_no_decoded)
        
        if student is None:
            return jsonify({
                'success': False,
                'error': '学生不存在'
            }), 404
        
        result = {
            'student_id': student.student_id,
            'name': student.name,
            'student_no': student.student_no,
            'class_name': student.class_name,
            'created_at': student.created_at,
            'updated_at': student.updated_at
        }
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/students', methods=['POST'])
def create_student():
    """
    创建或更新学生
    
    Request Body:
        {
            "student_id": null,  // 可选，存在则更新
            "name": "学生姓名",
            "student_no": "学号",
            "class_name": "班级"
        }
        
    Returns:
        创建结果
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
        
        name = data.get('name', '').strip()
        student_no = data.get('student_no', '').strip()
        class_name = data.get('class_name', '').strip()
        student_id = data.get('student_id')
        
        if not name:
            return jsonify({
                'success': False,
                'error': '学生姓名不能为空'
            }), 400
        
        if not student_no:
            return jsonify({
                'success': False,
                'error': '学号不能为空'
            }), 400
        
        existing = None
        if student_id is not None:
            existing = db.get_student_by_id(student_id)
        
        student = Student(
            student_id=student_id,
            name=name,
            student_no=student_no,
            class_name=class_name
        )
        
        try:
            new_student_id = db.save_student(student)
        except sqlite3.IntegrityError:
            return jsonify({
                'success': False,
                'error': '学号已存在'
            }), 400
        
        if existing:
            message = f'已更新学生: {name}'
        else:
            message = f'已创建学生: {name}'
        
        return jsonify({
            'success': True,
            'message': message,
            'student_id': new_student_id,
            'is_update': existing is not None
        }), 201 if not existing else 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/students/<int:student_id>', methods=['PUT'])
def update_student(student_id):
    """
    更新指定 ID 的学生
    
    Args:
        student_id: 学生 ID
        
    Request Body:
        {
            "name": "新的姓名（可选）",
            "student_no": "新的学号（可选）",
            "class_name": "新的班级（可选）"
        }
        
    Returns:
        更新结果
    """
    try:
        existing = db.get_student_by_id(student_id)
        
        if existing is None:
            return jsonify({
                'success': False,
                'error': '学生不存在'
            }), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
        
        name = data.get('name', existing.name).strip()
        student_no = data.get('student_no', existing.student_no).strip()
        class_name = data.get('class_name', existing.class_name).strip()
        
        if not name:
            return jsonify({
                'success': False,
                'error': '学生姓名不能为空'
            }), 400
        
        if not student_no:
            return jsonify({
                'success': False,
                'error': '学号不能为空'
            }), 400
        
        if student_no != existing.student_no:
            no_exists = db.get_student_by_no(student_no)
            if no_exists and no_exists.student_id != student_id:
                return jsonify({
                    'success': False,
                    'error': '学号已存在'
                }), 400
        
        student = Student(
            student_id=student_id,
            name=name,
            student_no=student_no,
            class_name=class_name,
            created_at=existing.created_at
        )
        
        new_id = db.save_student(student)
        
        return jsonify({
            'success': True,
            'message': f'已更新学生: {name}',
            'student_id': new_id
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/students/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    """
    删除指定 ID 的学生
    
    Args:
        student_id: 学生 ID
        
    Returns:
        删除结果
    """
    try:
        student = db.get_student_by_id(student_id)
        
        if student is None:
            return jsonify({
                'success': False,
                'error': '学生不存在'
            }), 404
        
        success = db.delete_student(student_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'已删除学生: {student.name}'
            })
        else:
            return jsonify({
                'success': False,
                'error': '删除失败'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/students/check-no/<student_no>', methods=['GET'])
def check_student_no(student_no):
    """
    检查学号是否已存在
    
    Args:
        student_no: 学号
        
    Returns:
        学号是否存在
    """
    try:
        student_no_decoded = urllib.parse.unquote(student_no)
        exists = db.get_student_by_no(student_no_decoded) is not None
        
        return jsonify({
            'success': True,
            'exists': exists
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/students/count', methods=['GET'])
def get_student_count():
    """
    获取学生总数
    
    Returns:
        学生数量
    """
    try:
        count = db.get_student_count()
        
        return jsonify({
            'success': True,
            'count': count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/assignments', methods=['GET'])
def get_assignments():
    """
    获取作业列表（支持分页和过滤）
    
    Query Parameters:
        page: 页码（从1开始）
        page_size: 每页数量（可选，默认10）
        student_no: 学号过滤（可选）
        status: 状态过滤（可选，pending 或 completed）
    
    Returns:
        JSON 格式的作业列表
    """
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        student_no = request.args.get('student_no', type=str)
        status = request.args.get('status', type=str)
        
        page = max(1, page)
        page_size = max(10, min(100, page_size))
        
        paginated = db.get_assignments_paginated(
            student_no=student_no,
            status=status,
            page=page,
            page_size=page_size
        )
        
        result = []
        for assignment in paginated['assignments']:
            result.append({
                'assignment_id': assignment.assignment_id,
                'student_no': assignment.student_no,
                'template_id': assignment.template_id,
                'characters': assignment.characters,
                'scene_type': assignment.scene_type,
                'status': assignment.status,
                'assigned_at': assignment.assigned_at,
                'completed_at': assignment.completed_at,
                'config_data': assignment.config_data,
                'created_at': assignment.created_at,
                'updated_at': assignment.updated_at
            })
        
        return jsonify({
            'success': True,
            'data': result,
            'count': len(result),
            'pagination': {
                'page': paginated['page'],
                'page_size': paginated['page_size'],
                'total': paginated['total'],
                'total_pages': paginated['total_pages']
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/assignments/<int:assignment_id>', methods=['GET'])
def get_assignment(assignment_id):
    """
    根据 ID 获取单个作业
    
    Args:
        assignment_id: 作业 ID
        
    Returns:
        JSON 格式的作业数据
    """
    try:
        assignment = db.get_assignment_by_id(assignment_id)
        
        if assignment is None:
            return jsonify({
                'success': False,
                'error': '作业不存在'
            }), 404
        
        result = {
            'assignment_id': assignment.assignment_id,
            'student_no': assignment.student_no,
            'template_id': assignment.template_id,
            'characters': assignment.characters,
            'scene_type': assignment.scene_type,
            'status': assignment.status,
            'assigned_at': assignment.assigned_at,
            'completed_at': assignment.completed_at,
            'config_data': assignment.config_data,
            'created_at': assignment.created_at,
            'updated_at': assignment.updated_at
        }
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/assignments', methods=['POST'])
def create_assignment():
    """
    创建作业（布置作业）
    
    Request Body:
        {
            "student_no": "学号",
            "template_id": 1,  // 可选，模版ID
            "characters": "需要练习的字",
            "scene_type": "normal",  // normal 或 character
            "config_data": {}  // 可选，模版配置数据
        }
        
    Returns:
        创建结果
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
        
        student_no = data.get('student_no', '').strip()
        template_id = data.get('template_id')
        characters = data.get('characters', '').strip()
        scene_type = data.get('scene_type', 'normal')
        config_data = data.get('config_data', {})
        
        if not student_no:
            return jsonify({
                'success': False,
                'error': '学号不能为空'
            }), 400
        
        if not characters:
            return jsonify({
                'success': False,
                'error': '练习文字不能为空'
            }), 400
        
        student = db.get_student_by_no(student_no)
        if student is None:
            return jsonify({
                'success': False,
                'error': '学生不存在'
            }), 404
        
        if template_id is not None:
            template = db.get_template_by_id(template_id)
            if template is None:
                return jsonify({
                    'success': False,
                    'error': '模版不存在'
                }), 404
        
        assignment = Assignment(
            student_no=student_no,
            template_id=template_id,
            characters=characters,
            scene_type=scene_type,
            status=Assignment.STATUS_PENDING,
            config_data=config_data
        )
        
        assignment_id = db.save_assignment(assignment)
        
        return jsonify({
            'success': True,
            'message': f'已布置作业给学生: {student.name}',
            'assignment_id': assignment_id
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/assignments/<int:assignment_id>', methods=['PUT'])
def update_assignment(assignment_id):
    """
    更新作业
    
    Args:
        assignment_id: 作业 ID
        
    Request Body:
        {
            "student_no": "学号（可选）",
            "template_id": 1,  // 可选
            "characters": "需要练习的字（可选）",
            "scene_type": "normal",  // 可选
            "status": "pending",  // 可选
            "config_data": {}  // 可选
        }
        
    Returns:
        更新结果
    """
    try:
        existing = db.get_assignment_by_id(assignment_id)
        
        if existing is None:
            return jsonify({
                'success': False,
                'error': '作业不存在'
            }), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
        
        student_no = data.get('student_no', existing.student_no).strip()
        template_id = data.get('template_id', existing.template_id)
        characters = data.get('characters', existing.characters).strip()
        scene_type = data.get('scene_type', existing.scene_type)
        status = data.get('status', existing.status)
        config_data = data.get('config_data', existing.config_data)
        
        if student_no != existing.student_no:
            student = db.get_student_by_no(student_no)
            if student is None:
                return jsonify({
                    'success': False,
                    'error': '学生不存在'
                }), 404
        
        if template_id is not None and template_id != existing.template_id:
            template = db.get_template_by_id(template_id)
            if template is None:
                return jsonify({
                    'success': False,
                    'error': '模版不存在'
                }), 404
        
        assignment = Assignment(
            assignment_id=assignment_id,
            student_no=student_no,
            template_id=template_id,
            characters=characters,
            scene_type=scene_type,
            status=status,
            assigned_at=existing.assigned_at,
            completed_at=existing.completed_at,
            config_data=config_data
        )
        
        new_id = db.save_assignment(assignment)
        
        return jsonify({
            'success': True,
            'message': '已更新作业',
            'assignment_id': new_id
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/assignments/<int:assignment_id>/complete', methods=['POST'])
def complete_assignment(assignment_id):
    """
    标记作业为已完成
    
    Args:
        assignment_id: 作业 ID
        
    Returns:
        更新结果
    """
    try:
        existing = db.get_assignment_by_id(assignment_id)
        
        if existing is None:
            return jsonify({
                'success': False,
                'error': '作业不存在'
            }), 404
        
        success = db.mark_assignment_completed(assignment_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': '作业已标记为完成'
            })
        else:
            return jsonify({
                'success': False,
                'error': '更新失败'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/assignments/<int:assignment_id>', methods=['DELETE'])
def delete_assignment(assignment_id):
    """
    删除作业
    
    Args:
        assignment_id: 作业 ID
        
    Returns:
        删除结果
    """
    try:
        assignment = db.get_assignment_by_id(assignment_id)
        
        if assignment is None:
            return jsonify({
                'success': False,
                'error': '作业不存在'
            }), 404
        
        success = db.delete_assignment(assignment_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': '已删除作业'
            })
        else:
            return jsonify({
                'success': False,
                'error': '删除失败'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/assignments/count', methods=['GET'])
def get_assignment_count():
    """
    获取作业总数
    
    Query Parameters:
        student_no: 学号过滤（可选）
        status: 状态过滤（可选）
    
    Returns:
        作业数量
    """
    try:
        student_no = request.args.get('student_no', type=str)
        status = request.args.get('status', type=str)
        
        count = db.get_assignment_count(student_no=student_no, status=status)
        
        return jsonify({
            'success': True,
            'count': count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    """404 错误处理"""
    return jsonify({
        'success': False,
        'error': '接口不存在'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """500 错误处理"""
    return jsonify({
        'success': False,
        'error': '服务器内部错误'
    }), 500


if __name__ == '__main__':
    import sqlite3
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    print(f"=" * 50)
    print(f"字帖生成器 API 服务")
    print(f"=" * 50)
    print(f"服务地址: http://localhost:{port}")
    print(f"API 文档:")
    print(f"  GET    /api/templates          获取所有模版")
    print(f"  GET    /api/templates/<id>     获取单个模版")
    print(f"  POST   /api/templates          创建/更新模版")
    print(f"  PUT    /api/templates/<id>     更新模版")
    print(f"  DELETE /api/templates/<id>     删除模版")
    print(f"  POST   /api/export/pdf         导出PDF字帖")
    print(f"  GET    /api/students           获取所有学生")
    print(f"  POST   /api/students           创建/更新学生")
    print(f"  GET    /api/assignments        获取作业列表")
    print(f"  POST   /api/assignments        创建作业")
    print(f"  GET    /api/health             健康检查")
    print(f"=" * 50)
    
    app.run(host='0.0.0.0', port=port, debug=debug)
