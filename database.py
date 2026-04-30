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
        
        conn.commit()
        conn.close()
    
    def save_template(self, template: Template) -> int:
        """
        保存模版
        如果 template_name 已存在，则更新；否则创建新模版
        
        Args:
            template: 模版对象
            
        Returns:
            模版ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        existing = self.get_template_by_name(template.template_name)
        
        if existing:
            cursor.execute("""
                UPDATE templates 
                SET config_data = ?, updated_at = ?
                WHERE template_name = ?
            """, (
                json.dumps(template.config_data, ensure_ascii=False),
                now,
                template.template_name
            ))
            template_id = existing.template_id
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
