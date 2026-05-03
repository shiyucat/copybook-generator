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


class Student:
    """学生数据类"""
    
    def __init__(self, 
                 student_id: int = None,
                 name: str = "",
                 student_no: str = "",
                 class_name: str = "",
                 created_at: str = None,
                 updated_at: str = None):
        self.student_id = student_id
        self.name = name
        self.student_no = student_no
        self.class_name = class_name
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or self.created_at
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "student_id": self.student_id,
            "name": self.name,
            "student_no": self.student_no,
            "class_name": self.class_name,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Student":
        return cls(
            student_id=data.get("student_id"),
            name=data.get("name", ""),
            student_no=data.get("student_no", ""),
            class_name=data.get("class_name", ""),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )


class Assignment:
    """作业数据类"""
    
    STATUS_PENDING = "pending"
    STATUS_COMPLETED = "completed"
    STATUS_SUBMITTED = "submitted"
    STATUS_REVIEWED = "reviewed"
    STATUS_REJECTED = "rejected"
    
    REVIEW_STATUS_APPROVED = "approved"
    REVIEW_STATUS_REJECTED = "rejected"
    
    def __init__(self, 
                 assignment_id: int = None,
                 student_no: str = "",
                 template_id: int = None,
                 characters: str = "",
                 scene_type: str = "normal",
                 status: str = STATUS_PENDING,
                 assigned_at: str = None,
                 completed_at: str = None,
                 submitted_at: str = None,
                 reviewed_at: str = None,
                 config_data: Dict[str, Any] = None,
                 submitted_image: str = None,
                 review_status: str = None,
                 review_comments: str = None,
                 review_annotations: Dict[str, Any] = None,
                 submission_count: int = 0,
                 created_at: str = None,
                 updated_at: str = None):
        self.assignment_id = assignment_id
        self.student_no = student_no
        self.template_id = template_id
        self.characters = characters
        self.scene_type = scene_type
        self.status = status
        self.assigned_at = assigned_at or datetime.now().isoformat()
        self.completed_at = completed_at
        self.submitted_at = submitted_at
        self.reviewed_at = reviewed_at
        self.config_data = config_data or {}
        self.submitted_image = submitted_image
        self.review_status = review_status
        self.review_comments = review_comments
        self.review_annotations = review_annotations or {}
        self.submission_count = submission_count or 0
        self.created_at = created_at or self.assigned_at
        self.updated_at = updated_at or self.created_at
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "assignment_id": self.assignment_id,
            "student_no": self.student_no,
            "template_id": self.template_id,
            "characters": self.characters,
            "scene_type": self.scene_type,
            "status": self.status,
            "assigned_at": self.assigned_at,
            "completed_at": self.completed_at,
            "submitted_at": self.submitted_at,
            "reviewed_at": self.reviewed_at,
            "config_data": self.config_data,
            "submitted_image": self.submitted_image,
            "review_status": self.review_status,
            "review_comments": self.review_comments,
            "review_annotations": self.review_annotations,
            "submission_count": self.submission_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Assignment":
        config_data = data.get("config_data")
        if isinstance(config_data, str):
            config_data = json.loads(config_data)
        
        review_annotations = data.get("review_annotations")
        if isinstance(review_annotations, str):
            review_annotations = json.loads(review_annotations)
        
        return cls(
            assignment_id=data.get("assignment_id"),
            student_no=data.get("student_no", ""),
            template_id=data.get("template_id"),
            characters=data.get("characters", ""),
            scene_type=data.get("scene_type", "normal"),
            status=data.get("status", cls.STATUS_PENDING),
            assigned_at=data.get("assigned_at"),
            completed_at=data.get("completed_at"),
            submitted_at=data.get("submitted_at"),
            reviewed_at=data.get("reviewed_at"),
            config_data=config_data or {},
            submitted_image=data.get("submitted_image"),
            review_status=data.get("review_status"),
            review_comments=data.get("review_comments"),
            review_annotations=review_annotations or {},
            submission_count=data.get("submission_count", 0),
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
    
    def _migrate_assignments_table(self, conn: sqlite3.Connection, cursor: sqlite3.Cursor):
        """迁移 assignments 表，添加新字段"""
        try:
            cursor.execute("PRAGMA table_info(assignments)")
            columns = [row[1] for row in cursor.fetchall()]
            
            new_columns = [
                ('submitted_at', 'TEXT'),
                ('reviewed_at', 'TEXT'),
                ('submitted_image', 'TEXT'),
                ('review_status', 'TEXT'),
                ('review_comments', 'TEXT'),
                ('review_annotations', "TEXT NOT NULL DEFAULT '{}'"),
                ('submission_count', 'INTEGER NOT NULL DEFAULT 0'),
            ]
            
            for col_name, col_def in new_columns:
                if col_name not in columns:
                    try:
                        cursor.execute(f"ALTER TABLE assignments ADD COLUMN {col_name} {col_def}")
                        print(f"已添加字段: {col_name}")
                    except Exception as e:
                        print(f"添加字段 {col_name} 失败: {e}")
            
            conn.commit()
        except Exception as e:
            print(f"迁移 assignments 表失败: {e}")
    
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
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL DEFAULT '',
                student_no TEXT NOT NULL UNIQUE,
                class_name TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_student_no 
            ON students(student_no)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_student_class 
            ON students(class_name)
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_no TEXT NOT NULL DEFAULT '',
                template_id INTEGER,
                characters TEXT NOT NULL DEFAULT '',
                scene_type TEXT NOT NULL DEFAULT 'normal',
                status TEXT NOT NULL DEFAULT 'pending',
                assigned_at TEXT NOT NULL,
                completed_at TEXT,
                submitted_at TEXT,
                reviewed_at TEXT,
                config_data TEXT NOT NULL DEFAULT '{}',
                submitted_image TEXT,
                review_status TEXT,
                review_comments TEXT,
                review_annotations TEXT NOT NULL DEFAULT '{}',
                submission_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        self._migrate_assignments_table(conn, cursor)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_assignment_student_no 
            ON assignments(student_no)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_assignment_status 
            ON assignments(status)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_assignment_assigned_at 
            ON assignments(assigned_at)
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
        conn = self._get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        try:
            # 开始事务，确保原子性操作
            conn.execute('BEGIN TRANSACTION')
            
            # 检查是否存在相同记录（SQLite不支持FOR UPDATE，使用事务+更新计数来确保原子性）
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
            
            if row:
                # 存在相同记录，更新导出次数
                cursor.execute("""
                    UPDATE export_history 
                    SET export_count = export_count + 1, updated_at = ?
                    WHERE id = ?
                """, (now, row[0]))
                conn.commit()
                conn.close()
                return row[0]
            else:
                # 不存在相同记录，创建新记录
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
                
        except Exception as e:
            try:
                conn.rollback()
            except:
                pass
            try:
                conn.close()
            except:
                pass
            raise e
    
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
    
    def save_student(self, student: Student) -> int:
        """
        保存学生
        如果 student_id 存在且不为 None，则根据 ID 更新
        否则，如果 student_no 已存在，则更新；否则创建新学生
        
        Args:
            student: 学生对象
            
        Returns:
            学生ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        if student.student_id is not None:
            existing_by_id = self.get_student_by_id(student.student_id)
            if existing_by_id:
                cursor.execute("""
                    UPDATE students 
                    SET name = ?, student_no = ?, class_name = ?, updated_at = ?
                    WHERE id = ?
                """, (
                    student.name,
                    student.student_no,
                    student.class_name,
                    now,
                    student.student_id
                ))
                conn.commit()
                conn.close()
                return student.student_id
        
        existing_by_no = self.get_student_by_no(student.student_no)
        
        if existing_by_no:
            cursor.execute("""
                UPDATE students 
                SET name = ?, class_name = ?, updated_at = ?
                WHERE student_no = ?
            """, (
                student.name,
                student.class_name,
                now,
                student.student_no
            ))
            student_id = existing_by_no.student_id
        else:
            cursor.execute("""
                INSERT INTO students (name, student_no, class_name, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                student.name,
                student.student_no,
                student.class_name,
                now,
                now
            ))
            student_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return student_id
    
    def get_student_by_id(self, student_id: int) -> Optional[Student]:
        """
        根据ID获取学生
        
        Args:
            student_id: 学生ID
            
        Returns:
            学生对象，如果不存在返回 None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id as student_id, name, student_no, class_name, created_at, updated_at
            FROM students 
            WHERE id = ?
        """, (student_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return Student.from_dict(dict(row))
        return None
    
    def get_student_by_no(self, student_no: str) -> Optional[Student]:
        """
        根据学号获取学生
        
        Args:
            student_no: 学号
            
        Returns:
            学生对象，如果不存在返回 None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id as student_id, name, student_no, class_name, created_at, updated_at
            FROM students 
            WHERE student_no = ?
        """, (student_no,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return Student.from_dict(dict(row))
        return None
    
    def get_all_students(self) -> List[Student]:
        """
        获取所有学生
        
        Returns:
            学生列表，按创建时间降序排列
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id as student_id, name, student_no, class_name, created_at, updated_at
            FROM students 
            ORDER BY created_at DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [Student.from_dict(dict(row)) for row in rows]
    
    def get_students_paginated(self, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """
        分页获取学生
        
        Args:
            page: 页码，从1开始
            page_size: 每页数量
            
        Returns:
            包含分页信息的字典
        """
        page = max(1, page)
        page_size = max(1, min(100, page_size))
        
        total = self.get_student_count()
        
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        
        offset = (page - 1) * page_size
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id as student_id, name, student_no, class_name, created_at, updated_at
            FROM students 
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (page_size, offset))
        
        rows = cursor.fetchall()
        conn.close()
        
        students = [Student.from_dict(dict(row)) for row in rows]
        
        return {
            "students": students,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    
    def search_students_paginated(
        self, 
        keyword: str, 
        page: int = 1, 
        page_size: int = 10
    ) -> Dict[str, Any]:
        """
        按关键字搜索学生（支持姓名、学号、班级的模糊匹配）
        
        Args:
            keyword: 搜索关键字
            page: 页码
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
            FROM students 
            WHERE name LIKE ? OR student_no LIKE ? OR class_name LIKE ?
        """, (search_pattern, search_pattern, search_pattern))
        total = cursor.fetchone()[0]
        
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        
        offset = (page - 1) * page_size
        
        cursor.execute("""
            SELECT 
                id as student_id, name, student_no, class_name, created_at, updated_at
            FROM students 
            WHERE name LIKE ? OR student_no LIKE ? OR class_name LIKE ?
            ORDER BY updated_at DESC
            LIMIT ? OFFSET ?
        """, (search_pattern, search_pattern, search_pattern, page_size, offset))
        
        rows = cursor.fetchall()
        conn.close()
        
        students = [Student.from_dict(dict(row)) for row in rows]
        
        return {
            "students": students,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    
    def delete_student(self, student_id: int) -> bool:
        """
        删除学生
        
        Args:
            student_id: 学生ID
            
        Returns:
            是否成功删除
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
        affected = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return affected > 0
    
    def get_student_count(self, keyword: str = None) -> int:
        """
        获取学生总数
        
        Args:
            keyword: 可选的搜索关键字
            
        Returns:
            学生数量
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if keyword:
            search_pattern = f'%{keyword}%'
            cursor.execute(
                "SELECT COUNT(*) FROM students WHERE name LIKE ? OR student_no LIKE ? OR class_name LIKE ?",
                (search_pattern, search_pattern, search_pattern)
            )
        else:
            cursor.execute("SELECT COUNT(*) FROM students")
        
        count = cursor.fetchone()[0]
        
        conn.close()
        
        return count
    
    def save_assignment(self, assignment: Assignment) -> int:
        """
        保存作业
        
        Args:
            assignment: 作业对象
            
        Returns:
            作业ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        if assignment.assignment_id is not None:
            existing = self.get_assignment_by_id(assignment.assignment_id)
            if existing:
                cursor.execute("""
                    UPDATE assignments 
                    SET student_no = ?, template_id = ?, characters = ?, scene_type = ?, 
                        status = ?, assigned_at = ?, completed_at = ?, submitted_at = ?, 
                        reviewed_at = ?, config_data = ?, submitted_image = ?, 
                        review_status = ?, review_comments = ?, review_annotations = ?, 
                        submission_count = ?, updated_at = ?
                    WHERE id = ?
                """, (
                    assignment.student_no,
                    assignment.template_id,
                    assignment.characters,
                    assignment.scene_type,
                    assignment.status,
                    assignment.assigned_at,
                    assignment.completed_at,
                    assignment.submitted_at,
                    assignment.reviewed_at,
                    json.dumps(assignment.config_data, ensure_ascii=False),
                    assignment.submitted_image,
                    assignment.review_status,
                    assignment.review_comments,
                    json.dumps(assignment.review_annotations, ensure_ascii=False),
                    assignment.submission_count,
                    now,
                    assignment.assignment_id
                ))
                conn.commit()
                conn.close()
                return assignment.assignment_id
        
        cursor.execute("""
            INSERT INTO assignments (
                student_no, template_id, characters, scene_type, 
                status, assigned_at, completed_at, submitted_at, 
                reviewed_at, config_data, submitted_image, 
                review_status, review_comments, review_annotations, 
                submission_count, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            assignment.student_no,
            assignment.template_id,
            assignment.characters,
            assignment.scene_type,
            assignment.status,
            assignment.assigned_at,
            assignment.completed_at,
            assignment.submitted_at,
            assignment.reviewed_at,
            json.dumps(assignment.config_data, ensure_ascii=False),
            assignment.submitted_image,
            assignment.review_status,
            assignment.review_comments,
            json.dumps(assignment.review_annotations, ensure_ascii=False),
            assignment.submission_count,
            now,
            now
        ))
        assignment_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return assignment_id
    
    def get_assignment_by_id(self, assignment_id: int) -> Optional[Assignment]:
        """
        根据ID获取作业
        
        Args:
            assignment_id: 作业ID
            
        Returns:
            作业对象，如果不存在返回 None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id as assignment_id, student_no, template_id, characters, 
                   scene_type, status, assigned_at, completed_at, submitted_at,
                   reviewed_at, config_data, submitted_image, review_status,
                   review_comments, review_annotations, submission_count,
                   created_at, updated_at
            FROM assignments 
            WHERE id = ?
        """, (assignment_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return Assignment.from_dict(dict(row))
        return None
    
    def get_assignments_by_student_no(self, student_no: str) -> List[Assignment]:
        """
        根据学号获取该学生的所有作业
        
        Args:
            student_no: 学号
            
        Returns:
            作业列表，按布置时间降序排列
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id as assignment_id, student_no, template_id, characters, 
                   scene_type, status, assigned_at, completed_at, submitted_at,
                   reviewed_at, config_data, submitted_image, review_status,
                   review_comments, review_annotations, submission_count,
                   created_at, updated_at
            FROM assignments 
            WHERE student_no = ?
            ORDER BY assigned_at DESC
        """, (student_no,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [Assignment.from_dict(dict(row)) for row in rows]
    
    def get_assignments_paginated(
        self, 
        student_no: str = None,
        status: str = None,
        page: int = 1, 
        page_size: int = 10
    ) -> Dict[str, Any]:
        """
        分页获取作业
        
        Args:
            student_no: 可选的学号过滤
            status: 可选的状态过滤
            page: 页码
            page_size: 每页数量
            
        Returns:
            包含分页信息的字典
        """
        page = max(1, page)
        page_size = max(1, min(100, page_size))
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        conditions = []
        params = []
        
        if student_no:
            conditions.append("student_no = ?")
            params.append(student_no)
        
        if status:
            conditions.append("status = ?")
            params.append(status)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        count_sql = f"SELECT COUNT(*) FROM assignments WHERE {where_clause}"
        cursor.execute(count_sql, params)
        total = cursor.fetchone()[0]
        
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        
        offset = (page - 1) * page_size
        
        select_sql = f"""
            SELECT id as assignment_id, student_no, template_id, characters, 
                   scene_type, status, assigned_at, completed_at, submitted_at,
                   reviewed_at, config_data, submitted_image, review_status,
                   review_comments, review_annotations, submission_count,
                   created_at, updated_at
            FROM assignments 
            WHERE {where_clause}
            ORDER BY assigned_at DESC
            LIMIT ? OFFSET ?
        """
        params.extend([page_size, offset])
        cursor.execute(select_sql, params)
        
        rows = cursor.fetchall()
        conn.close()
        
        assignments = [Assignment.from_dict(dict(row)) for row in rows]
        
        return {
            "assignments": assignments,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    
    def mark_assignment_completed(self, assignment_id: int) -> bool:
        """
        标记作业为已完成
        
        Args:
            assignment_id: 作业ID
            
        Returns:
            是否成功更新
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        cursor.execute("""
            UPDATE assignments 
            SET status = ?, completed_at = ?, updated_at = ?
            WHERE id = ?
        """, (Assignment.STATUS_COMPLETED, now, now, assignment_id))
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected > 0
    
    def delete_assignment(self, assignment_id: int) -> bool:
        """
        删除作业
        
        Args:
            assignment_id: 作业ID
            
        Returns:
            是否成功删除
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM assignments WHERE id = ?", (assignment_id,))
        affected = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return affected > 0
    
    def get_assignment_count(self, student_no: str = None, status: str = None) -> int:
        """
        获取作业总数
        
        Args:
            student_no: 可选的学号过滤
            status: 可选的状态过滤
            
        Returns:
            作业数量
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        conditions = []
        params = []
        
        if student_no:
            conditions.append("student_no = ?")
            params.append(student_no)
        
        if status:
            conditions.append("status = ?")
            params.append(status)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        sql = f"SELECT COUNT(*) FROM assignments WHERE {where_clause}"
        cursor.execute(sql, params)
        
        count = cursor.fetchone()[0]
        
        conn.close()
        
        return count
    
    def submit_assignment(self, assignment_id: int, submitted_image: str = None) -> Optional[Assignment]:
        """
        学生提交作业
        
        Args:
            assignment_id: 作业ID
            submitted_image: 提交的图片（base64编码或文件路径）
            
        Returns:
            更新后的作业对象，如果失败返回 None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        try:
            cursor.execute("""
                UPDATE assignments 
                SET status = ?, submitted_at = ?, submitted_image = ?, 
                    submission_count = submission_count + 1, updated_at = ?
                WHERE id = ?
            """, (Assignment.STATUS_SUBMITTED, now, submitted_image, now, assignment_id))
            
            affected = cursor.rowcount
            conn.commit()
            
            if affected > 0:
                return self.get_assignment_by_id(assignment_id)
            return None
        finally:
            conn.close()
    
    def review_assignment(
        self, 
        assignment_id: int, 
        review_status: str, 
        review_comments: str = None,
        review_annotations: Dict[str, Any] = None
    ) -> Optional[Assignment]:
        """
        老师批改作业
        
        Args:
            assignment_id: 作业ID
            review_status: 批改状态（approved 或 rejected）
            review_comments: 批改评语
            review_annotations: 批改标注数据（画圈位置等）
            
        Returns:
            更新后的作业对象，如果失败返回 None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        try:
            if review_status == Assignment.REVIEW_STATUS_APPROVED:
                status = Assignment.STATUS_REVIEWED
            else:
                status = Assignment.STATUS_REJECTED
            
            cursor.execute("""
                UPDATE assignments 
                SET status = ?, reviewed_at = ?, review_status = ?, 
                    review_comments = ?, review_annotations = ?, updated_at = ?
                WHERE id = ?
            """, (
                status, 
                now, 
                review_status, 
                review_comments, 
                json.dumps(review_annotations or {}, ensure_ascii=False),
                now, 
                assignment_id
            ))
            
            affected = cursor.rowcount
            conn.commit()
            
            if affected > 0:
                return self.get_assignment_by_id(assignment_id)
            return None
        finally:
            conn.close()
    
    def resubmit_assignment(self, assignment_id: int, submitted_image: str = None) -> Optional[Assignment]:
        """
        学生重新提交作业（当作业被拒绝时）
        
        Args:
            assignment_id: 作业ID
            submitted_image: 重新提交的图片
            
        Returns:
            更新后的作业对象，如果失败返回 None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        try:
            cursor.execute("""
                UPDATE assignments 
                SET status = ?, submitted_at = ?, submitted_image = ?, 
                    review_status = NULL, review_comments = NULL, 
                    review_annotations = '{}', reviewed_at = NULL,
                    submission_count = submission_count + 1, updated_at = ?
                WHERE id = ? AND status = ?
            """, (Assignment.STATUS_SUBMITTED, now, submitted_image, now, assignment_id, Assignment.STATUS_REJECTED))
            
            affected = cursor.rowcount
            conn.commit()
            
            if affected > 0:
                return self.get_assignment_by_id(assignment_id)
            return None
        finally:
            conn.close()
