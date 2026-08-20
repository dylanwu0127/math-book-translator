#!/usr/bin/env python3
"""
批量交付打包工具
功能：
- 自动生成全书目录索引（含章节链接）
- 汇总术语表
- 生成翻译说明文档
- 按部分打包为zip
- 支持生成合并的完整Markdown文件
"""
import os
import sys
import re
import json
import argparse
import zipfile
from datetime import datetime

def extract_chapter_info(filepath):
    """从文件中提取章节信息"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    info = {
        'filename': os.path.basename(filepath),
        'filepath': filepath,
        'size': os.path.getsize(filepath),
        'chars': len(content),
        'chapter_num': None,
        'chapter_title': '',
        'part': '',
        'sections': []
    }
    
    # 提取章标题
    match = re.search(r'^##\s+第([\d]+)章\s+(.+)$', content, re.MULTILINE)
    if match:
        info['chapter_num'] = int(match.group(1))
        info['chapter_title'] = match.group(2).strip()
    
    # 提取节标题
    sections = re.findall(r'^###\s+(\d+\.\d+)\s+(.+)$', content, re.MULTILINE)
    info['sections'] = [{'num': s[0], 'title': s[1].strip()} for s in sections]
    
    # 判断部分
    filename = info['filename']
    if 'Part1' in filename or '第1章' in filename or '第2章' in filename or '第3章' in filename or '第4章' in filename or '第5章' in filename or '第6章' in filename or '第7章' in filename or '第8章' in filename or '第9章' in filename or '第10章' in filename or '第11章' in filename:
        info['part'] = 'Part 1 整数'
    elif 'Part2' in filename or (info['chapter_num'] and 12 <= info['chapter_num'] <= 24):
        info['part'] = 'Part 2 分数'
    elif 'Part3' in filename or (info['chapter_num'] and 25 <= info['chapter_num'] <= 31):
        info['part'] = 'Part 3 有理数'
    elif 'Part4' in filename or (info['chapter_num'] and 32 <= info['chapter_num'] <= 37):
        info['part'] = 'Part 4 数论'
    elif 'Part5' in filename or (info['chapter_num'] and 38 <= info['chapter_num'] <= 42):
        info['part'] = 'Part 5 小数'
    elif '前言' in filename:
        info['part'] = '前言'
    else:
        info['part'] = '其他'
    
    return info

def generate_toc(chapters, output_path='目录索引.md'):
    """生成目录索引"""
    # 按部分分组
    parts = {}
    for c in chapters:
        part = c['part']
        if part not in parts:
            parts[part] = []
        parts[part].append(c)
    
    toc = []
    toc.append("# 全书目录索引")
    toc.append("")
    toc.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    toc.append("")
    
    total_chars = sum(c['chars'] for c in chapters)
    toc.append(f"**总章节数**: {len(chapters)} 章")
    toc.append(f"**总字符数**: {total_chars:,}")
    toc.append("")
    toc.append("---")
    toc.append("")
    
    # 按部分顺序输出
    part_order = ['前言', 'Part 1 整数', 'Part 2 分数', 'Part 3 有理数', 'Part 4 数论', 'Part 5 小数', '其他']
    for part in part_order:
        if part not in parts:
            continue
        part_chapters = parts[part]
        part_chars = sum(c['chars'] for c in part_chapters)
        
        toc.append(f"## {part}")
        toc.append("")
        toc.append(f"共 {len(part_chapters)} 章，{part_chars:,} 字符")
        toc.append("")
        
        for c in sorted(part_chapters, key=lambda x: x['chapter_num'] or 0):
            if c['chapter_num']:
                title = f"第{c['chapter_num']}章 {c['chapter_title']}"
            else:
                title = c['chapter_title'] or os.path.splitext(c['filename'])[0]
            
            # 相对路径链接
            link = f"./{c['filename']}"
            toc.append(f"- [{title}]({link}) ({c['chars']:,} 字)")
            
            # 列出节标题
            if c['sections']:
                for s in c['sections'][:5]:  # 最多显示5节
                    toc.append(f"  - {s['num']} {s['title']}")
                if len(c['sections']) > 5:
                    toc.append(f"  - ... 还有 {len(c['sections']) - 5} 节")
        
        toc.append("")
    
    toc_text = '\n'.join(toc)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(toc_text)
    
    print(f"目录索引已生成: {output_path}")
    return toc_text

def generate_translation_notes(chapters, glossary_path=None, output_path='翻译说明.md'):
    """生成翻译说明文档"""
    notes = []
    notes.append("# 翻译说明")
    notes.append("")
    notes.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    notes.append("")
    
    notes.append("## 翻译规范")
    notes.append("")
    notes.append("### 术语约定")
    notes.append("- Activity → 互动练习")
    notes.append("- Exercise → 习题")
    notes.append("- Theorem → 定理")
    notes.append("- Lemma → 引理")
    notes.append("- Proof → 证明")
    notes.append("- Definition → 定义")
    notes.append("")
    
    notes.append("### 格式约定")
    notes.append("- 章标题使用 `## 第X章 标题`")
    notes.append("- 节标题使用 `### X.X 标题`")
    notes.append("- 习题使用 `### 习题`")
    notes.append("- 行内公式使用 `$...$`")
    notes.append("- 独立公式使用 `$$...$$`")
    notes.append("- 美元金额使用 `\\$` 转义")
    notes.append("- 证明结束使用 `\\square` 或 `□`")
    notes.append("")
    
    if glossary_path and os.path.exists(glossary_path):
        with open(glossary_path, 'r', encoding='utf-8') as f:
            glossary = json.load(f)
        notes.append("### 核心术语表")
        notes.append("")
        notes.append("| 英文 | 中文 |")
        notes.append("|------|------|")
        for en, zh in sorted(glossary.items()):
            if en.startswith('_'):
                continue
            if len(en) > 3:  # 只显示较长的术语
                notes.append(f"| {en} | {zh} |")
        notes.append("")
    
    notes.append("## 翻译统计")
    notes.append("")
    total_chars = sum(c['chars'] for c in chapters)
    notes.append(f"- 总章节数: {len(chapters)}")
    notes.append(f"- 总字符数: {total_chars:,}")
    notes.append("")
    
    # 按部分统计
    parts = {}
    for c in chapters:
        part = c['part']
        if part not in parts:
            parts[part] = []
        parts[part].append(c)
    
    notes.append("### 各部分统计")
    notes.append("")
    notes.append("| 部分 | 章节数 | 字符数 |")
    notes.append("|------|--------|--------|")
    for part, part_chapters in sorted(parts.items()):
        part_chars = sum(c['chars'] for c in part_chapters)
        notes.append(f"| {part} | {len(part_chapters)} | {part_chars:,} |")
    notes.append("")
    
    notes_text = '\n'.join(notes)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(notes_text)
    
    print(f"翻译说明已生成: {output_path}")
    return notes_text

def merge_chapters(chapters, output_path='完整译稿.md'):
    """合并所有章节为一个完整Markdown文件"""
    merged = []
    merged.append("# 完整译稿")
    merged.append("")
    merged.append(f"合并时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    merged.append("")
    merged.append("---")
    merged.append("")
    
    for c in sorted(chapters, key=lambda x: x['chapter_num'] or 0):
        with open(c['filepath'], 'r', encoding='utf-8') as f:
            content = f.read()
        merged.append(content)
        merged.append("")
        merged.append("---")
        merged.append("")
    
    merged_text = '\n'.join(merged)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(merged_text)
    
    print(f"完整译稿已合并: {output_path} ({len(merged_text):,} 字符)")
    return output_path

def package_zip(chapters, output_path='翻译交付包.zip', include_toc=True, include_notes=True):
    """打包为zip文件"""
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # 添加章节文件
        for c in chapters:
            arcname = f"译文/{c['filename']}"
            zf.write(c['filepath'], arcname)
        
        # 添加目录索引
        if include_toc and os.path.exists('目录索引.md'):
            zf.write('目录索引.md', '目录索引.md')
        
        # 添加翻译说明
        if include_notes and os.path.exists('翻译说明.md'):
            zf.write('翻译说明.md', '翻译说明.md')
    
    print(f"交付包已打包: {output_path}")
    print(f"  包含 {len(chapters)} 个章节文件")
    return output_path

def main():
    parser = argparse.ArgumentParser(description='批量交付打包工具')
    parser.add_argument('files', nargs='+', help='译文Markdown文件')
    parser.add_argument('--output-dir', '-o', default='.', help='输出目录')
    parser.add_argument('--glossary', '-g', help='术语表JSON路径')
    parser.add_argument('--toc', action='store_true', default=True, help='生成目录索引')
    parser.add_argument('--notes', action='store_true', default=True, help='生成翻译说明')
    parser.add_argument('--merge', action='store_true', help='合并为完整译稿')
    parser.add_argument('--zip', action='store_true', help='打包为zip')
    parser.add_argument('--all', action='store_true', help='执行所有操作')
    
    args = parser.parse_args()
    
    # 收集文件信息
    chapters = []
    for f in args.files:
        if not os.path.exists(f):
            print(f"⚠️  文件不存在: {f}")
            continue
        info = extract_chapter_info(f)
        chapters.append(info)
    
    if not chapters:
        print("未找到可处理的文件")
        sys.exit(1)
    
    print(f"已加载 {len(chapters)} 个章节文件")
    os.makedirs(args.output_dir, exist_ok=True)
    
    # 生成目录索引
    if args.toc or args.all:
        toc_path = os.path.join(args.output_dir, '目录索引.md')
        generate_toc(chapters, toc_path)
    
    # 生成翻译说明
    if args.notes or args.all:
        notes_path = os.path.join(args.output_dir, '翻译说明.md')
        generate_translation_notes(chapters, args.glossary, notes_path)
    
    # 合并完整译稿
    if args.merge or args.all:
        merge_path = os.path.join(args.output_dir, '完整译稿.md')
        merge_chapters(chapters, merge_path)
    
    # 打包zip
    if args.zip or args.all:
        zip_path = os.path.join(args.output_dir, '翻译交付包.zip')
        package_zip(chapters, zip_path, args.toc, args.notes)
    
    print("\n✅ 交付打包完成")

if __name__ == '__main__':
    main()
