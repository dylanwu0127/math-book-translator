#!/usr/bin/env python3
"""
PDF提取与章节分割工具（增强版）
功能：
- 提取PDF全文，带页码锚点标记
- 自动识别表格、图片位置，生成占位标记
- 按章标题分割为独立文件
- 生成页码映射表，便于回查原文
依赖: PyPDF2 (pip install PyPDF2)
"""
import argparse
import re
import os
import sys
import json

def get_pdf_info(pdf_path):
    """获取PDF基本信息"""
    try:
        import PyPDF2
    except ImportError:
        print("错误: 需要安装PyPDF2。运行: pip install PyPDF2")
        sys.exit(1)
    
    reader = PyPDF2.PdfReader(pdf_path)
    print(f"文件: {pdf_path}")
    print(f"总页数: {len(reader.pages)}")
    print(f"文件大小: {os.path.getsize(pdf_path) / 1024 / 1024:.2f} MB")
    return len(reader.pages)

def detect_figures_and_tables(page_text, page_num):
    """检测页面中的图表标题，返回占位标记列表"""
    markers = []
    # 常见图表标题模式
    patterns = [
        (r'(Figure|Fig\.?)\s+(\d+\.\d+|\d+)', '图'),
        (r'(Table|Tab\.?)\s+(\d+\.\d+|\d+)', '表'),
        (r'(图表|图|表)\s*(\d+\.\d+|\d+)', '图表'),
    ]
    for pattern, label in patterns:
        matches = re.finditer(pattern, page_text, re.IGNORECASE)
        for m in matches:
            # 提取标题（到行尾或句号）
            title_end = page_text.find('\n', m.end())
            if title_end == -1:
                title_end = min(m.end() + 100, len(page_text))
            title = page_text[m.end():title_end].strip()[:80]
            markers.append({
                'type': label,
                'id': m.group(0),
                'title': title,
                'page': page_num,
                'position': m.start()
            })
    return markers

def extract_full_text_with_anchors(pdf_path, output_dir):
    """提取PDF全文，带页码锚点和图表标记"""
    try:
        import PyPDF2
    except ImportError:
        print("错误: 需要安装PyPDF2。运行: pip install PyPDF2")
        sys.exit(1)
    
    reader = PyPDF2.PdfReader(pdf_path)
    full_text = ""
    all_markers = []
    page_map = []  # 页码映射: [{page: 1, start_offset: 0, end_offset: 100}]
    
    current_offset = 0
    for i, page in enumerate(reader.pages):
        page_num = i + 1
        page_text = page.extract_text() or ""
        
        # 检测图表
        markers = detect_figures_and_tables(page_text, page_num)
        all_markers.extend(markers)
        
        # 添加页码锚点
        page_header = f"\n<!-- 原书第{page_num}页 -->\n"
        full_text += page_header
        
        # 在图表位置插入占位标记
        if markers:
            # 按位置排序，从后往前插入以避免偏移问题
            for marker in sorted(markers, key=lambda x: x['position'], reverse=True):
                placeholder = f"\n<!-- 图表占位: {marker['type']}{marker['id']} - {marker['title']} (原书P.{page_num}) -->\n"
                page_text = page_text[:marker['position']] + placeholder + page_text[marker['position']:]
        
        full_text += page_text
        
        # 记录页码映射
        page_map.append({
            'page': page_num,
            'start_offset': current_offset,
            'end_offset': current_offset + len(page_header) + len(page_text),
            'markers_count': len(markers)
        })
        current_offset += len(page_header) + len(page_text)
    
    # 保存页码映射表
    os.makedirs(output_dir, exist_ok=True)
    map_path = os.path.join(output_dir, 'page_map.json')
    with open(map_path, 'w', encoding='utf-8') as f:
        json.dump({
            'total_pages': len(reader.pages),
            'page_map': page_map,
            'all_markers': all_markers
        }, f, ensure_ascii=False, indent=2)
    
    print(f"页码映射表已保存: {map_path}")
    if all_markers:
        print(f"检测到 {len(all_markers)} 个图表标记:")
        for m in all_markers[:10]:
            print(f"  P.{m['page']}: {m['type']}{m['id']} - {m['title'][:50]}")
        if len(all_markers) > 10:
            print(f"  ... 还有 {len(all_markers) - 10} 个")
    
    return full_text, len(reader.pages), all_markers

def split_by_chapters(text, output_dir):
    """按章标题分割文本。支持多种章标题模式。"""
    patterns = [
        r'(?=Chapter\s+\d+)',
        r'(?=第\s*\d+\s*章)',
        r'(?=CHAPTER\s+\d+)',
    ]
    
    chapters = [text]
    for pattern in patterns:
        new_chapters = []
        for ch in chapters:
            parts = re.split(pattern, ch)
            new_chapters.extend(parts)
        chapters = new_chapters
    
    chapters = [ch.strip() for ch in chapters if ch.strip() and len(ch.strip()) > 100]
    
    os.makedirs(output_dir, exist_ok=True)
    for i, ch in enumerate(chapters):
        first_line = ch.split('\n')[0][:50].strip()
        safe_name = re.sub(r'[^\w\s-]', '', first_line).strip()
        safe_name = safe_name.replace(' ', '_')[:40]
        filename = f"chapter_{i+1:02d}_{safe_name}.txt"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(ch)
        print(f"  已保存: {filename} ({len(ch)} 字符)")
    
    print(f"\n共分割为 {len(chapters)} 个章节")
    return chapters

def main():
    parser = argparse.ArgumentParser(description='PDF提取与章节分割工具（增强版）')
    parser.add_argument('pdf_path', help='PDF文件路径')
    parser.add_argument('--info', action='store_true', help='仅显示PDF信息，不提取')
    parser.add_argument('--output', '-o', default='raw_chapters', help='输出目录 (默认: raw_chapters)')
    parser.add_argument('--full', action='store_true', help='同时保存完整文本到 full_text.txt')
    parser.add_argument('--no-anchors', action='store_true', help='不添加页码锚点标记')
    parser.add_argument('--no-figures', action='store_true', help='不检测图表标记')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.pdf_path):
        print(f"错误: 文件不存在 - {args.pdf_path}")
        sys.exit(1)
    
    print("=" * 50)
    total_pages = get_pdf_info(args.pdf_path)
    print("=" * 50)
    
    if args.info:
        return
    
    print("\n正在提取全文（带页码锚点）...")
    if args.no_anchors:
        # 简化版提取
        try:
            import PyPDF2
        except ImportError:
            print("错误: 需要安装PyPDF2")
            sys.exit(1)
        reader = PyPDF2.PdfReader(args.pdf_path)
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text() or ""
        all_markers = []
    else:
        full_text, _, all_markers = extract_full_text_with_anchors(args.pdf_path, args.output)
    
    print(f"全文提取完成，共 {len(full_text)} 字符")
    
    if args.full:
        full_path = os.path.join(args.output, 'full_text.txt')
        os.makedirs(args.output, exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(full_text)
        print(f"完整文本已保存: {full_path}")
    
    print("\n正在按章分割...")
    split_by_chapters(full_text, args.output)

if __name__ == '__main__':
    main()
