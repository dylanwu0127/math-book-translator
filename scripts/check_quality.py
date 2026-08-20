#!/usr/bin/env python3
"""
数学翻译文档综合质量检查工具
检测: LaTeX $符号未闭合、标题层级异常、连续空行、术语遗漏
"""
import re
import sys
import glob
import os

def check_dollar_pairs(content):
    r"""检查$符号配对，跳过\$转义和$$块"""
    in_block = False
    in_math = False
    i = 0
    issues = []
    start_line = 0
    
    while i < len(content):
        # 跳过转义的\$
        if content[i] == '\\' and i + 1 < len(content) and content[i+1] == '$':
            i += 2
            continue
        if content[i] == '$':
            # 处理$$块
            if i + 1 < len(content) and content[i+1] == '$':
                in_block = not in_block
                if in_block:
                    block_start = content[:i].count('\n') + 1
                i += 2
                continue
            # 处理单个$（不在$$块内）
            elif not in_block:
                in_math = not in_math
                if in_math:
                    start_line = content[:i].count('\n') + 1
        i += 1
    
    if in_math:
        issues.append(f"未闭合的单个$，开始于第{start_line}行")
    if in_block:
        issues.append(f"未闭合的$$块，开始于第{block_start}行")
    return issues

def check_heading_levels(content):
    """检查标题层级"""
    issues = []
    lines = content.split('\n')
    chapter_count = 0
    
    for j, line in enumerate(lines, 1):
        stripped = line.strip()
        # 一级标题只应在文件开头（部分标题）
        if stripped.startswith('# ') and j > 5:
            issues.append(f"第{j}行: 一级标题'# '不应出现在文件中间")
        # 章标题应为##
        if re.match(r'^##\s+第\d+章', stripped):
            chapter_count += 1
        # 节标题应为###
        if re.match(r'^##\s+\d+\.\d+', stripped):
            issues.append(f"第{j}行: 节标题应使用### 而非##")
    
    if chapter_count > 1:
        issues.append(f"文件包含 {chapter_count} 个章标题，建议每章一个文件")
    
    return issues

def check_blank_lines(content):
    """检查连续空行"""
    issues = []
    if re.search(r'\n{4,}', content):
        matches = list(re.finditer(r'\n{4,}', content))
        for m in matches[:3]:  # 只报告前3个
            line = content[:m.start()].count('\n') + 1
            issues.append(f"第{line}行附近: 存在连续3行以上空行")
    return issues

def check_terms(content):
    """检查常见术语遗漏"""
    issues = []
    # Activity应译为互动练习
    if re.search(r'\bActivity\b', content, re.IGNORECASE):
        issues.append("发现未翻译的'Activity'（应为'互动练习'）")
    if '活动' in content and '互动练习' not in content:
        issues.append("发现'活动'但无'互动练习'，请确认是否需要替换")
    # Exercise应译为习题
    if re.search(r'\bExercise\b', content, re.IGNORECASE):
        issues.append("发现未翻译的'Exercise'（应为'习题'）")
    return issues

def check_dollar_escaping(content):
    """检查美元符号是否需要转义（$后面跟数字且不在公式中）"""
    issues = []
    # 简单检测：行内出现 $数字 模式但该行$数量为奇数
    lines = content.split('\n')
    for j, line in enumerate(lines, 1):
        # 跳过代码块
        if line.strip().startswith('```'):
            continue
        # 检测美元金额模式（$后跟数字，数字中有逗号或小数点后两位）
        if re.search(r'\$\d{1,3}(,\d{3})+(\.\d{2})?', line):
            dollar_count = line.count('$') - line.count('\\$')
            if dollar_count % 2 != 0:
                issues.append(f"第{j}行: 可能存在未转义的美元符号（使用\\$转义）")
    return issues

def check_file(filepath):
    """检查单个文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    issues = []
    issues.extend(check_dollar_pairs(content))
    issues.extend(check_heading_levels(content))
    issues.extend(check_blank_lines(content))
    issues.extend(check_terms(content))
    issues.extend(check_dollar_escaping(content))
    
    return issues

def main():
    if len(sys.argv) < 2:
        print("用法: python check_quality.py <文件1> <文件2> ...")
        print("示例: python check_quality.py 译文/*.md")
        sys.exit(1)
    
    files = []
    for arg in sys.argv[1:]:
        # 支持通配符
        if '*' in arg or '?' in arg:
            files.extend(glob.glob(arg))
        elif os.path.isdir(arg):
            files.extend(glob.glob(os.path.join(arg, '*.md')))
        else:
            files.append(arg)
    
    if not files:
        print("未找到匹配的文件")
        sys.exit(1)
    
    total_issues = 0
    passed = 0
    
    for filepath in sorted(files):
        if not os.path.exists(filepath):
            print(f"⚠️  文件不存在: {filepath}")
            continue
        issues = check_file(filepath)
        filename = os.path.basename(filepath)
        if issues:
            print(f"\n❌ {filename}:")
            for issue in issues:
                print(f"   - {issue}")
            total_issues += len(issues)
        else:
            print(f"✅ {filename}")
            passed += 1
    
    print(f"\n{'='*50}")
    print(f"检查完成: {len(files)} 个文件, {passed} 个通过, {total_issues} 个问题")

if __name__ == '__main__':
    main()
