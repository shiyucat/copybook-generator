#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Flask 后端 API
提供 Web 端与数据库交互的 REST API
"""

import os
import json
import urllib.parse
from datetime import datetime
from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from pathlib import Path

from database import TemplateDatabase, Template


app = Flask(__name__)
CORS(app)

db = TemplateDatabase()


@app.route('/api/templates', methods=['GET'])
def get_templates():
    """
    获取所有模版列表
    
    Returns:
        JSON 格式的模版列表
    """
    try:
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
    print(f"  GET    /api/health             健康检查")
    print(f"=" * 50)
    
    app.run(host='0.0.0.0', port=port, debug=debug)
