#!/usr/bin/env python3
"""
翻译进度追踪工具
统计已翻译章节、字数、生成进度报告
"""
import re
import os
import sys
import glob
from datetime import datetime

def get_chapter_info(filepath):
    """获取章节信息"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    info = {
        'filename': os.path.basename(filepath),
        'filepath': filepath,
        'size': os.path.getsize(filepath),
        'chars': len(content),
        'lines': content.count('\n') + 1,
        'chapter_title': '',
        'has_exercises': '### 习题' in content or '## 习题' in content,
        'formula_count': content.count('$') - content.count('\\$'),
    }
    
    # 提取章标题
    match = re.search(r'^##\s+第([\d]+)章\s+(.+)$', content, re.MULTILINE)
    if match:
        info['chapter_num'] = int(match.group(1))
        info['chapter_title'] = match.group(2).strip()
    else:
        info['chapter_num'] = None
    
    # 提取部分信息
    if 'Part1' in filepath or '第1章' in filepath or '整数' in content[:500]:
        info['part'] = 'Part 1 整数'
    elif 'Part2' in filepath or '分数' in content[:500]:
        info['part'] = 'Part 2 分数'
    elif 'Part3' in filepath or '有理数' in content[:500]:
        info['part'] = 'Part 3 有理数'
    elif 'Part4' in filepath or '数论' in content[:500]:
        info['part'] = 'Part 4 数论'
    elif 'Part5' in filepath or '小数' in content[:500]:
        info['part'] = 'Part 5 小数'
    else:
        info['part'] = '其他'
    
    return info

def generate_report(chapters, output_path=None):
    """生成进度报告"""
    total_chars = sum(c['chars'] for c in chapters)
    total_lines = sum(c['lines'] for c in chapters)
    total_formulas = sum(c['formula_count'] for c in chapters)
    
    # 按部分分组
    parts = {}
    for c in chapters:
        part = c['part']
        if part not in parts:
            parts[part] = []
        parts[part].append(c)
    
    report = []
    report.append("=" * 60)
    report.append("翻译进度报告")
    report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 60)
    report.append("")
    
    # 总览
    report.append("【总览】")
    report.append(f"  已翻译文件: {len(chapters)} 个")
    report.append(f"  总字符数: {total_chars:,}")
    report.append(f"  总行数: {total_lines:,}")
    report.append(f"  公式总数: {total_formulas:,}")
    report.append("")
    
    # 按部分统计
    report.append("【按部分统计】")
    for part, part_chapters in sorted(parts.items()):
        part_chars = sum(c['chars'] for c in part_chapters)
        report.append(f"  {part}: {len(part_chapters)} 章, {part_chars:,} 字符")
    report.append("")
    
    # 章节详情
    report.append("【章节详情】")
    for c in sorted(chapters, key=lambda x: x['chapter_num'] or 999):
        num = f"第{c['chapter_num']}章" if c['chapter_num'] else "  前言"
        title = c['chapter_title'] or os.path.splitext(c['filename'])[0]
        exercise_mark = "✓" if c['has_exercises'] else " "
        report.append(f"  {num:>6} [{exercise_mark}] {title:<30} {c['chars']:>6,} 字")
    report.append("")
    
    # 检查项
    report.append("【检查项】")
    no_exercises = [c for c in chapters if c['chapter_num'] and not c['has_exercises']]
    if no_exercises:
        no_ex_list = ', '.join('第' + str(c['chapter_num']) + '章' for c in no_exercises)
        report.append(f"  ⚠️  以下章节无习题部分: {no_ex_list}")
    else:
        report.append("  ✅ 所有章节均包含习题部分")
    
    report.append("")
    report.append("=" * 60)
    
    report_text = '\n'.join(report)
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        print(f"报告已保存: {output_path}")
    
    return report_text

def main():
    import argparse
    parser = argparse.ArgumentParser(description='翻译进度追踪工具')
    parser.add_argument('path', help='译文目录或文件路径')
    parser.add_argument('--output', '-o', help='输出报告到文件')
    
    args = parser.parse_args()
    
    # 收集文件
    files = []
    if os.path.isdir(args.path):
        files = glob.glob(os.path.join(args.path, '*.md'))
    else:
        files = [args.path]
    
    if not files:
        print("未找到匹配的文件")
        sys.exit(1)
    
    print(f"正在分析 {len(files)} 个文件...\n")
    
    chapters = []
    for filepath in sorted(files):
        if not os.path.exists(filepath):
            continue
        try:
            info = get_chapter_info(filepath)
            chapters.append(info)
        except Exception as e:
            print(f"⚠️  读取失败: {filepath} - {e}")
    
    report = generate_report(chapters, args.output)
    print(report)

if __name__ == '__main__':
    main()
