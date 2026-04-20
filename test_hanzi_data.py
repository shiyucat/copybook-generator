#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import urllib.request
    HAS_URLLIB = True
except ImportError:
    HAS_URLLIB = False

def fetch_hanzi_data(char):
    if not HAS_URLLIB:
        print("urllib not available")
        return None
    
    try:
        from urllib.parse import quote
        encoded_char = quote(char)
    except ImportError:
        encoded_char = char
    
    url = f"https://cdn.jsdelivr.net/npm/hanzi-writer-data@2.0/{encoded_char}.json"
    
    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
        return data
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def analyze_data(data, char):
    if not data:
        return
    
    print(f"\n{'='*60}")
    print(f"汉字「{char}」的数据结构分析")
    print(f"{'='*60}")
    
    print(f"\n1. 顶层键：{list(data.keys())}")
    
    if 'strokes' in data:
        print(f"\n2. strokes（笔画SVG路径）：")
        print(f"   笔画数量：{len(data['strokes'])}")
        for i, stroke in enumerate(data['strokes'][:3], 1):
            print(f"   第{i}笔：{stroke[:100]}...")
        if len(data['strokes']) > 3:
            print(f"   ... 共{len(data['strokes'])}笔")
    
    if 'medians' in data:
        print(f"\n3. medians（笔画中线，用于动画）：")
        print(f"   数量：{len(data['medians'])}")
        for i, median in enumerate(data['medians'][:2], 1):
            print(f"   第{i}笔中线：{median[:5]}...（共{len(median)}个点）")
    
    if 'radStrokes' in data:
        print(f"\n4. radStrokes（部首笔画索引）：{data['radStrokes']}")
    
    if 'width' in data:
        print(f"\n5. width：{data['width']}")
    
    if 'height' in data:
        print(f"\n6. height：{data['height']}")
    
    print(f"\n{'='*60}")
    print(f"完整数据示例（前3笔）：")
    print(f"{'='*60}")
    
    if 'strokes' in data:
        for i in range(min(3, len(data['strokes']))):
            print(f"\n--- 第{i+1}笔 ---")
            print(f"SVG路径：{data['strokes'][i]}")
            if 'medians' in data and i < len(data['medians']):
                print(f"中线点：{data['medians'][i]}")

def main():
    test_chars = ['一', '二', '三', '模', '人']
    
    for char in test_chars[:2]:
        print(f"\n\n{'#'*60}")
        print(f"## 正在获取汉字「{char}」的数据")
        print(f"{'#'*60}")
        
        data = fetch_hanzi_data(char)
        if data:
            analyze_data(data, char)
            
            output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), f'{char}_data.json')
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"\n数据已保存到：{output_file}")
        else:
            print(f"无法获取汉字「{char}」的数据")

if __name__ == "__main__":
    main()
