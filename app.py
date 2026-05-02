#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Flask 后端 API
提供 Web 端与数据库交互的 REST API
"""

import os
import json
import re
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

from database import TemplateDatabase, Template
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
        
        show_character_pinyin = data.get('show_character_pinyin', True)
        
        character_color_hex = data.get('character_color', '#000000')
        if not isinstance(character_color_hex, str) or not re.match(r'^#[0-9A-Fa-f]{6}$', character_color_hex):
            character_color_hex = '#000000'
        character_color = hex_to_rgb(character_color_hex)
        
        right_grid_color_hex = data.get('right_grid_color', '#000000')
        if not isinstance(right_grid_color_hex, str) or not re.match(r'^#[0-9A-Fa-f]{6}$', right_grid_color_hex):
            right_grid_color_hex = '#000000'
        right_grid_color = hex_to_rgb(right_grid_color_hex)
        
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            output_path = tmp.name
        
        try:
            generator = CopybookGenerator(
                paper_size=paper_size,
                grid_type=grid_type_code,
                font_style=font_style,
                font_color=font_color,
                pinyin_color=pinyin_color,
                character_color=character_color,
                right_grid_color=right_grid_color,
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
    print(f"  GET    /api/health             健康检查")
    print(f"=" * 50)
    
    app.run(host='0.0.0.0', port=port, debug=debug)
