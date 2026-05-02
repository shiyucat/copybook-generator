#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import json
from pathlib import Path

db_path = Path('data/copybook_templates.db')
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# 查看 ID 13 和 14 的详细信息
cursor.execute('SELECT * FROM export_history WHERE id IN (13, 14)')
rows = cursor.fetchall()

print('=== 详细对比 ID: 13 和 ID: 14 ===')
for row in rows:
    print(f'\nID: {row[0]}')
    print(f'  场景类型: {row[1]}')
    print(f'  姓名: "{row[2]}"')
    print(f'  学号: "{row[3]}"')
    print(f'  文字内容: "{row[4]}"')
    print(f'  页面大小: {row[5]}')
    print(f'  导出次数: {row[6]}')
    print(f'  配置数据类型: {type(row[7])}')
    print(f'  配置数据长度: {len(row[7]) if row[7] else 0}')
    print(f'  创建时间: {row[8]}')
    print(f'  更新时间: {row[9]}')
    
    # 检查字符编码
    print(f'\n  详细字符检查:')
    print(f'  姓名: {repr(row[2])}')
    print(f'  学号: {repr(row[3])}')
    print(f'  文字内容: {repr(row[4])}')
    
    # 检查配置数据
    try:
        config = json.loads(row[7]) if row[7] else {}
        print(f'\n  配置数据解析成功:')
        print(f'  场景类型 (config): {config.get("scene_type")}')
        print(f'  姓名 (config): {repr(config.get("student_name"))}')
        print(f'  学号 (config): {repr(config.get("student_id"))}')
        print(f'  文字内容 (config): {repr(config.get("input_text"))}')
        print(f'  页面大小 (config): {config.get("page_size")}')
    except Exception as e:
        print(f'  配置数据解析失败: {e}')

# 检查是否还有其他重复记录
print('\n\n=== 检查所有可能的重复记录 ===')
cursor.execute('''
    SELECT 
        scene_type, 
        student_name, 
        student_id, 
        input_text, 
        page_size, 
        COUNT(*) as cnt,
        GROUP_CONCAT(id) as ids
    FROM export_history 
    GROUP BY scene_type, student_name, student_id, input_text, page_size 
    HAVING COUNT(*) > 1
''')
duplicates = cursor.fetchall()

if duplicates:
    print('发现以下重复记录:')
    for dup in duplicates:
        print(f'\n  场景类型: {dup[0]}')
        print(f'  姓名: {repr(dup[1])}')
        print(f'  学号: {repr(dup[2])}')
        print(f'  文字内容: {repr(dup[3])}')
        print(f'  页面大小: {dup[4]}')
        print(f'  重复数量: {dup[5]}')
        print(f'  涉及ID: {dup[6]}')
else:
    print('未发现重复记录（基于五个字段判断）')

conn.close()
