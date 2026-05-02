#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
合并重复的导出历史记录
判断规则：场景类型 + 姓名 + 学号 + 文字内容 + 页面大小 都相同
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime


def merge_duplicate_history():
    db_path = Path('data/copybook_templates.db')
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    print('=== 开始合并重复的导出历史记录 ===')
    
    # 首先检查所有重复记录
    cursor.execute('''
        SELECT 
            scene_type, 
            student_name, 
            student_id, 
            input_text, 
            page_size, 
            COUNT(*) as cnt,
            GROUP_CONCAT(id) as ids,
            SUM(export_count) as total_count,
            MAX(updated_at) as latest_update,
            MIN(created_at) as earliest_create
        FROM export_history 
        GROUP BY scene_type, student_name, student_id, input_text, page_size 
        HAVING COUNT(*) > 1
    ''')
    duplicates = cursor.fetchall()
    
    if not duplicates:
        print('没有发现重复记录，无需合并')
        conn.close()
        return
    
    print(f'发现 {len(duplicates)} 组重复记录')
    
    for dup in duplicates:
        scene_type = dup[0]
        student_name = dup[1]
        student_id = dup[2]
        input_text = dup[3]
        page_size = dup[4]
        count = dup[5]
        ids_str = dup[6]
        total_count = dup[7]
        latest_update = dup[8]
        earliest_create = dup[9]
        
        ids = [int(id.strip()) for id in ids_str.split(',')]
        
        print(f'\n处理重复记录:')
        print(f'  场景类型: {scene_type}')
        print(f'  姓名: {student_name}')
        print(f'  学号: {student_id}')
        print(f'  文字内容: {input_text}')
        print(f'  页面大小: {page_size}')
        print(f'  涉及ID: {ids}')
        print(f'  当前总导出次数: {total_count}')
        print(f'  最早创建时间: {earliest_create}')
        print(f'  最新更新时间: {latest_update}')
        
        # 获取最早创建的记录的配置数据（保留最早的配置）
        cursor.execute('''
            SELECT config_data FROM export_history 
            WHERE id = ?
        ''', (min(ids),))
        config_row = cursor.fetchone()
        config_data = config_row[0] if config_row else '{}'
        
        try:
            # 开始事务
            conn.execute('BEGIN TRANSACTION')
            
            # 删除所有重复记录
            for id in ids:
                cursor.execute('DELETE FROM export_history WHERE id = ?', (id,))
            
            # 创建新的合并记录
            now = datetime.now().isoformat()
            cursor.execute('''
                INSERT INTO export_history (
                    scene_type, student_name, student_id, input_text, 
                    page_size, export_count, config_data, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                scene_type,
                student_name,
                student_id,
                input_text,
                page_size,
                total_count,
                config_data,
                earliest_create,
                latest_update if latest_update else now
            ))
            
            new_id = cursor.lastrowid
            
            # 提交事务
            conn.commit()
            
            print(f'  合并成功!')
            print(f'  已删除 {len(ids)} 条重复记录')
            print(f'  新建记录ID: {new_id}')
            print(f'  总导出次数: {total_count}')
            
        except Exception as e:
            conn.rollback()
            print(f'  合并失败: {e}')
            raise
    
    conn.close()
    print('\n=== 合并完成 ===')


if __name__ == '__main__':
    merge_duplicate_history()
