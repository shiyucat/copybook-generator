#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库模块 - 用于存储和管理字帖模版
使用 SQLite 数据库
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path


class Template:
    """模版数据类"""
    
    def __init__(self, 
                 template_id: int = None,
                 template_name: str = "",
                 config_data: Dict[str, Any] = None,
                 created_at: str = None,
                 updated_at: str = None):
        self.template_id = template_id
        self.template_name = template_name
        self.config_data = config_data or {}
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or self.created_at
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "template_id": self.template_id,
            "template_name": self.template_name,
            "config_data": self.config_data,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Template":
        config_data = data.get("config_data")
        if isinstance(config_data, str):
            config_data = json.loads(config_data)
        return cls(
            template_id=data.get("template_id"),
            template_name=data.get("template_name", ""),
            config_data=config_data or {},
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )


class ExportHistory:
    """导出历史数据类"""
    
    def __init__(self, 
                 history_id: int = None,
                 scene_type: str = "normal",
                 student_name: str = "",
                 student_id: str = "",
                 input_text: str = "",
                 page_size: str = "A4",
                 export_count: int = 1,
                 created_at: str = None,
                 updated_at: str = None,
                 config_data: Dict[str, Any] = None):
        self.history_id = history_id
        self.scene_type = scene_type
        self.student_name = student_name
        self.student_id = student_id
        self.input_text = input_text
        self.page_size = page_size
        self.export_count = export_count
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or self.created_at
        self.config_data = config_data or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "history_id": self.history_id,
            "scene_type": self.scene_type,
            "student_name": self.student_name,
            "student_id": self.student_id,
            "input_text": self.input_text,
            "page_size": self.page_size,
            "export_count": self.export_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "config_data": self.config_data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExportHistory":
        config_data = data.get("config_data")
        if isinstance(config_data, str):
            config_data = json.loads(config_data)
        return cls(
            history_id=data.get("history_id"),
            scene_type=data.get("scene_type", "normal"),
            student_name=data.get("student_name", ""),
            student_id=data.get("student_id", ""),
            input_text=data.get("input_text", ""),
            page_size=data.get("page_size", "A4"),
            export_count=data.get("export_count", 1),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            config_data=config_data or {}
        )


class TemplateDatabase:
    """模版数据库管理类"""
    
    _instance = None
    
    def __new__(cls, db_path: str = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db_path: str = None):
        if self._initialized:
            return
        
        if db_path is None:
            db_path = self._get_default_db_path()
        
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()
        self._initialized = True
    
    def _get_default_db_path(self) -> str:
        """获取默认数据库路径"""
        project_dir = Path(__file__).parent
        data_dir = project_dir / "data"
        return str(data_dir / "copybook_templates.db")
    
    def _ensure_db_directory(self):
        """确保数据库目录存在"""
        db_path = Path(self.db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_database(self):
        """初始化数据库表"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_name TEXT NOT NULL UNIQUE,
                config_data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_template_name 
            ON templates(template_name)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at 
            ON templates(created_at)
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS export_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scene_type TEXT NOT NULL DEFAULT 'normal',
                student_name TEXT NOT NULL DEFAULT '',
                student_id TEXT NOT NULL DEFAULT '',
                input_text TEXT NOT NULL DEFAULT '',
                page_size TEXT NOT NULL DEFAULT 'A4',
                export_count INTEGER NOT NULL DEFAULT 1,
                config_data TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_export_history_created_at 
            ON export_history(created_at)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_export_history_updated_at 
            ON export_history(updated_at)
        """)
        
        conn.commit()
        conn.close()
    
    def save_template(self, template: Template) -> int:
        """
        保存模版
        如果 template_id 存在且不为 None，则根据 ID 更新
        否则，如果 template_name 已存在，则更新；否则创建新模版
        
        Args:
            template: 模版对象
            
        Returns:
            模版ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        if template.template_id is not None:
            existing_by_id = self.get_template_by_id(template.template_id)
            if existing_by_id:
                cursor.execute("""
                    UPDATE templates 
                    SET template_name = ?, config_data = ?, updated_at = ?
                    WHERE id = ?
                """, (
                    template.template_name,
                    json.dumps(template.config_data, ensure_ascii=False),
                    now,
                    template.template_id
                ))
                conn.commit()
                conn.close()
                return template.template_id
        
        existing_by_name = self.get_template_by_name(template.template_name)
        
        if existing_by_name:
            cursor.execute("""
                UPDATE templates 
                SET config_data = ?, updated_at = ?
                WHERE template_name = ?
            """, (
                json.dumps(template.config_data, ensure_ascii=False),
                now,
                template.template_name
            ))
            template_id = existing_by_name.template_id
        else:
            cursor.execute("""
                INSERT INTO templates (template_name, config_data, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            """, (
                template.template_name,
                json.dumps(template.config_data, ensure_ascii=False),
                now,
                now
            ))
            template_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return template_id
    
    def get_template_by_name(self, template_name: str) -> Optional[Template]:
        """
        根据名称获取模版
        
        Args:
            template_name: 模版名称
            
        Returns:
            模版对象，如果不存在返回 None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id as template_id, template_name, config_data, created_at, updated_at
            FROM templates 
            WHERE template_name = ?
        """, (template_name,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return Template.from_dict(dict(row))
        return None
    
    def get_template_by_id(self, template_id: int) -> Optional[Template]:
        """
        根据ID获取模版
        
        Args:
            template_id: 模版ID
            
        Returns:
            模版对象，如果不存在返回 None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id as template_id, template_name, config_data, created_at, updated_at
            FROM templates 
            WHERE id = ?
        """, (template_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return Template.from_dict(dict(row))
        return None
    
    def get_all_templates(self) -> List[Template]:
        """
        获取所有模版
        
        Returns:
            模版列表，按创建时间降序排列
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id as template_id, template_name, config_data, created_at, updated_at
            FROM templates 
            ORDER BY created_at DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [Template.from_dict(dict(row)) for row in rows]
    
    def get_templates_paginated(self, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """
        分页获取模版
        
        Args:
            page: 页码，从1开始
            page_size: 每页数量
            
        Returns:
            包含分页信息的字典：{
                "templates": [Template...],
                "total": 总数,
                "page": 当前页码,
                "page_size": 每页数量,
                "total_pages": 总页数
            }
        """
        page = max(1, page)
        page_size = max(1, min(100, page_size))
        
        total = self.get_template_count()
        
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        
        offset = (page - 1) * page_size
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id as template_id, template_name, config_data, created_at, updated_at
            FROM templates 
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (page_size, offset))
        
        rows = cursor.fetchall()
        conn.close()
        
        templates = [Template.from_dict(dict(row)) for row in rows]
        
        return {
            "templates": templates,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    
    def delete_template(self, template_id: int) -> bool:
        """
        删除模版
        
        Args:
            template_id: 模版ID
            
        Returns:
            是否成功删除
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM templates WHERE id = ?", (template_id,))
        affected = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return affected > 0
    
    def delete_template_by_name(self, template_name: str) -> bool:
        """
        根据名称删除模版
        
        Args:
            template_name: 模版名称
            
        Returns:
            是否成功删除
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM templates WHERE template_name = ?", (template_name,))
        affected = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return affected > 0
    
    def template_exists(self, template_name: str) -> bool:
        """
        检查模版名称是否存在
        
        Args:
            template_name: 模版名称
            
        Returns:
            是否存在
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM templates WHERE template_name = ?", (template_name,))
        count = cursor.fetchone()[0]
        
        conn.close()
        
        return count > 0
    
    def get_template_count(self) -> int:
        """
        获取模版总数
        
        Returns:
            模版数量
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM templates")
        count = cursor.fetchone()[0]
        
        conn.close()
        
        return count
    
    def find_same_export_history(self, history: ExportHistory) -> Optional[ExportHistory]:
        """
        查找相同的导出历史记录
        判断条件：场景类型 + 姓名 + 学号 + 文字内容 + 页面大小 都相同
        
        Args:
            history: 导出历史对象
            
        Returns:
            找到的历史记录，如果不存在返回 None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                id as history_id,
                scene_type,
                student_name,
                student_id,
                input_text,
                page_size,
                export_count,
                config_data,
                created_at,
                updated_at
            FROM export_history 
            WHERE scene_type = ? 
              AND student_name = ? 
              AND student_id = ? 
              AND input_text = ? 
              AND page_size = ?
            LIMIT 1
        """, (
            history.scene_type,
            history.student_name,
            history.student_id,
            history.input_text,
            history.page_size
        ))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return ExportHistory.from_dict(dict(row))
        return None
    
    def save_export_history(self, history: ExportHistory) -> int:
        """
        保存导出历史（编辑页面导出时使用）
        判断规则：场景类型 + 姓名 + 学号 + 文字内容 + 页面大小 都相同则视为同一个字帖
        如果已存在相同字帖，则导出次数+1；否则创建新记录
        
        Args:
            history: 导出历史对象
            
        Returns:
            历史记录ID
        """
        existing = self.find_same_export_history(history)
        
        if existing:
            self.increment_export_count(existing.history_id)
            return existing.history_id
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO export_history (
                scene_type, student_name, student_id, input_text, 
                page_size, export_count, config_data, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            history.scene_type,
            history.student_name,
            history.student_id,
            history.input_text,
            history.page_size,
            1,
            json.dumps(history.config_data, ensure_ascii=False),
            now,
            now
        ))
        
        history_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return history_id
    
    def increment_export_count(self, history_id: int) -> bool:
        """
        增加导出次数（导出历史页面重新导出时使用）
        更新指定记录的导出次数和更新时间
        
        Args:
            history_id: 历史记录ID
            
        Returns:
            是否成功更新
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        cursor.execute("""
            UPDATE export_history 
            SET export_count = export_count + 1, updated_at = ?
            WHERE id = ?
        """, (now, history_id))
        
        affected = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return affected > 0
    
    def get_export_history_by_id(self, history_id: int) -> Optional[ExportHistory]:
        """
        根据ID获取导出历史
        
        Args:
            history_id: 历史记录ID
            
        Returns:
            导出历史对象，如果不存在返回 None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                id as history_id,
                scene_type,
                student_name,
                student_id,
                input_text,
                page_size,
                export_count,
                config_data,
                created_at,
                updated_at
            FROM export_history 
            WHERE id = ?
        """, (history_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return ExportHistory.from_dict(dict(row))
        return None
    
    def get_export_history_paginated(self, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """
        分页获取导出历史
        
        Args:
            page: 页码，从1开始
            page_size: 每页数量
            
        Returns:
            包含分页信息的字典：{
                "history": [ExportHistory...],
                "total": 总数,
                "page": 当前页码,
                "page_size": 每页数量,
                "total_pages": 总页数
            }
        """
        page = max(1, page)
        page_size = max(1, min(100, page_size))
        
        total = self.get_export_history_count()
        
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        
        offset = (page - 1) * page_size
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                id as history_id,
                scene_type,
                student_name,
                student_id,
                input_text,
                page_size,
                export_count,
                config_data,
                created_at,
                updated_at
            FROM export_history 
            ORDER BY updated_at DESC
            LIMIT ? OFFSET ?
        """, (page_size, offset))
        
        rows = cursor.fetchall()
        conn.close()
        
        history_list = [ExportHistory.from_dict(dict(row)) for row in rows]
        
        return {
            "history": history_list,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    
    def search_export_history_paginated(
        self, 
        keyword: str, 
        page: int = 1, 
        page_size: int = 10
    ) -> Dict[str, Any]:
        """
        按关键字搜索导出历史（支持姓名或学号的模糊匹配）
        
        Args:
            keyword: 搜索关键字
            page: 页码，从1开始
            page_size: 每页数量
            
        Returns:
            包含分页信息的字典
        """
        page = max(1, page)
        page_size = max(1, min(100, page_size))
        
        search_pattern = f'%{keyword}%'
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) 
            FROM export_history 
            WHERE student_name LIKE ? OR student_id LIKE ?
        """, (search_pattern, search_pattern))
        total = cursor.fetchone()[0]
        
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        
        offset = (page - 1) * page_size
        
        cursor.execute("""
            SELECT 
                id as history_id,
                scene_type,
                student_name,
                student_id,
                input_text,
                page_size,
                export_count,
                config_data,
                created_at,
                updated_at
            FROM export_history 
            WHERE student_name LIKE ? OR student_id LIKE ?
            ORDER BY updated_at DESC
            LIMIT ? OFFSET ?
        """, (search_pattern, search_pattern, page_size, offset))
        
        rows = cursor.fetchall()
        conn.close()
        
        history_list = [ExportHistory.from_dict(dict(row)) for row in rows]
        
        return {
            "history": history_list,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    
    def get_export_history_count(self, keyword: str = None) -> int:
        """
        获取导出历史总数
        
        Args:
            keyword: 可选的搜索关键字（用于搜索时计数）
            
        Returns:
            导出历史数量
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if keyword:
            search_pattern = f'%{keyword}%'
            cursor.execute(
                "SELECT COUNT(*) FROM export_history WHERE student_name LIKE ? OR student_id LIKE ?",
                (search_pattern, search_pattern)
            )
        else:
            cursor.execute("SELECT COUNT(*) FROM export_history")
        
        count = cursor.fetchone()[0]
        
        conn.close()
        
        return count
