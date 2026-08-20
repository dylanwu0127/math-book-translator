#!/usr/bin/env python3
"""
翻译质量评分工具
基于多维度自动计算翻译质量评分：
- 术语一致性 (30%)
- 公式完整性 (30%)
- 格式规范度 (20%)
- 章节完整度 (20%)
输出质量报告和改进建议
"""
import re
import os
import sys
import json
import argparse

def check_terms_consistency(content, glossary=None):
    """检查术语一致性，返回(得分, 问题列表)"""
    issues = []
    score = 100
    
    # 检查Activity是否译为互动练习
    if re.search(r'\bActivity\b', content, re.IGNORECASE):
        issues.append("发现未翻译的'Activity'（应为'互动练习'）")
        score -= 10
    if '活动' in content and '互动练习' not in content:
        issues.append("发现'活动'但无'互动练习'，请确认译法")
        score -= 5
    
    # 检查Exercise是否译为习题
    if re.search(r'\bExercise\b', content, re.IGNORECASE):
        issues.append("发现未翻译的'Exercise'（应为'习题'）")
        score -= 10
    
    # 如果有术语表，检查更多术语
    if glossary:
        for en, zh in glossary.items():
            if len(en) < 4:
                continue
            if re.search(rf'\b{re.escape(en)}\b', content, re.IGNORECASE):
                if zh not in content:
                    issues.append(f"术语 '{en}' 出现，但标准译法 '{zh}' 未找到")
                    score -= 3
    
    return max(0, score), issues

def check_formula_integrity(content):
    """检查公式完整性，返回(得分, 问题列表)"""
    issues = []
    score = 100
    
    # 检查$符号配对
    in_block = False
    in_math = False
    i = 0
    while i < len(content):
        if content[i] == '\\' and i+1 < len(content) and content[i+1] == '$':
            i += 2
            continue
        if content[i] == '$':
            if i+1 < len(content) and content[i+1] == '$':
                in_block = not in_block
                i += 2
                continue
            elif not in_block:
                in_math = not in_math
        i += 1
    
    if in_math:
        issues.append("存在未闭合的单个$符号")
        score -= 30
    if in_block:
        issues.append("存在未闭合的$$块")
        score -= 30
    
    # 检查美元符号是否转义
    lines = content.split('\n')
    for j, line in enumerate(lines, 1):
        if re.search(r'\$\d{1,3}(,\d{3})+', line):
            dollar_count = line.count('$') - line.count('\\$')
            if dollar_count % 2 != 0:
                issues.append(f"第{j}行: 可能存在未转义的美元符号")
                score -= 5
                break
    
    # 检查常见LaTeX命令是否完整
    common_commands = ['\\frac', '\\sqrt', '\\sum', '\\int', '\\lim', '\\alpha', '\\beta', '\\gamma']
    for cmd in common_commands:
        if cmd in content:
            # 检查是否在$...$中（简单检测）
            idx = content.find(cmd)
            before = content[:idx]
            dollar_count = before.count('$') - before.count('\\$')
            if dollar_count % 2 == 0:
                issues.append(f"LaTeX命令 '{cmd}' 可能不在公式环境中")
                score -= 2
    
    return max(0, score), issues

def check_format_quality(content):
    """检查格式规范度，返回(得分, 问题列表)"""
    issues = []
    score = 100
    
    # 检查标题层级
    lines = content.split('\n')
    chapter_count = 0
    for j, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith('# ') and j > 5:
            issues.append(f"第{j}行: 一级标题'# '不应出现在文件中间")
            score -= 5
        if re.match(r'^##\s+第\d+章', stripped):
            chapter_count += 1
        if re.match(r'^##\s+\d+\.\d+', stripped):
            issues.append(f"第{j}行: 节标题应使用### 而非##")
            score -= 5
    
    if chapter_count > 1:
        issues.append(f"文件包含 {chapter_count} 个章标题，建议每章一个文件")
        score -= 10
    
    # 检查连续空行
    if re.search(r'\n{4,}', content):
        issues.append("存在连续3行以上空行")
        score -= 5
    
    # 检查列表格式
    # 检查是否有混合的列表符号
    
    # 检查代码块闭合
    code_blocks = content.count('```')
    if code_blocks % 2 != 0:
        issues.append("存在未闭合的代码块")
        score -= 10
    
    # 检查引用格式
    # 检查链接格式
    
    return max(0, score), issues

def check_chapter_completeness(content):
    """检查章节完整度，返回(得分, 问题列表)"""
    issues = []
    score = 100
    
    # 检查是否有章标题
    if not re.search(r'^##\s+第\d+章', content, re.MULTILINE):
        issues.append("未找到章标题（## 第X章）")
        score -= 20
    
    # 检查是否有习题部分（如果原文有）
    # 这是一个启发式检查，不是所有章节都有习题
    
    # 检查是否有节标题
    if not re.search(r'^###\s+\d+\.\d+', content, re.MULTILINE):
        # 短章节可能没有分节，不扣分
        pass
    
    # 检查是否有证明结束标记
    if '证明' in content and '\\square' not in content and '□' not in content:
        issues.append("包含'证明'但未找到证明结束标记（\\square 或 □）")
        score -= 5
    
    # 检查定理/引理/定义格式
    theorem_patterns = ['定理', '引理', '推论', '定义', '命题']
    for pattern in theorem_patterns:
        if pattern in content:
            # 检查是否有编号
            if not re.search(rf'{pattern}\s*\d+', content):
                issues.append(f"找到'{pattern}'但可能缺少编号")
                score -= 2
                break
    
    return max(0, score), issues

def score_file(filepath, glossary=None):
    """评分单个文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    terms_score, terms_issues = check_terms_consistency(content, glossary)
    formula_score, formula_issues = check_formula_integrity(content)
    format_score, format_issues = check_format_quality(content)
    chapter_score, chapter_issues = check_chapter_completeness(content)
    
    # 加权计算总分
    total_score = (
        terms_score * 0.30 +
        formula_score * 0.30 +
        format_score * 0.20 +
        chapter_score * 0.20
    )
    
    all_issues = terms_issues + formula_issues + format_issues + chapter_issues
    
    return {
        'file': os.path.basename(filepath),
        'total_score': round(total_score, 1),
        'dimensions': {
            '术语一致性': terms_score,
            '公式完整性': formula_score,
            '格式规范度': format_score,
            '章节完整度': chapter_score
        },
        'issues': all_issues,
        'issue_count': len(all_issues)
    }

def main():
    parser = argparse.ArgumentParser(description='翻译质量评分工具')
    parser.add_argument('files', nargs='+', help='待评分的Markdown文件')
    parser.add_argument('--glossary', '-g', help='术语表JSON路径')
    parser.add_argument('--output', '-o', help='输出报告到JSON文件')
    parser.add_argument('--threshold', '-t', type=float, default=80, help='及格分数线 (默认80)')
    
    args = parser.parse_args()
    
    # 加载术语表
    glossary = None
    if args.glossary and os.path.exists(args.glossary):
        with open(args.glossary, 'r', encoding='utf-8') as f:
            glossary = json.load(f)
        print(f"已加载术语表: {len(glossary)} 条术语\n")
    
    results = []
    for f in args.files:
        if not os.path.exists(f):
            print(f"⚠️  文件不存在: {f}")
            continue
        result = score_file(f, glossary)
        results.append(result)
    
    if not results:
        print("未找到可评分的文件")
        sys.exit(1)
    
    # 输出报告
    print("=" * 70)
    print("翻译质量评分报告")
    print("=" * 70)
    print(f"{'文件':<35} {'总分':>6} {'术语':>6} {'公式':>6} {'格式':>6} {'章节':>6} {'问题':>4}")
    print("-" * 70)
    
    total_scores = []
    for r in results:
        d = r['dimensions']
        print(f"{r['file']:<35} {r['total_score']:>6.1f} {d['术语一致性']:>6} {d['公式完整性']:>6} {d['格式规范度']:>6} {d['章节完整度']:>6} {r['issue_count']:>4}")
        total_scores.append(r['total_score'])
    
    print("-" * 70)
    avg_score = sum(total_scores) / len(total_scores)
    passed = sum(1 for s in total_scores if s >= args.threshold)
    print(f"平均分数: {avg_score:.1f} | 及格: {passed}/{len(results)} (分数线: {args.threshold})")
    print()
    
    # 输出问题详情
    has_issues = False
    for r in results:
        if r['issues']:
            if not has_issues:
                print("问题详情:")
                print("=" * 70)
                has_issues = True
            print(f"\n📄 {r['file']}:")
            for issue in r['issues']:
                print(f"   ⚠️  {issue}")
    
    if has_issues:
        print("\n" + "=" * 70)
    
    # 改进建议
    print("\n改进建议:")
    avg_dims = {}
    for dim in ['术语一致性', '公式完整性', '格式规范度', '章节完整度']:
        avg_dims[dim] = sum(r['dimensions'][dim] for r in results) / len(results)
    
    weakest = min(avg_dims, key=avg_dims.get)
    if avg_dims[weakest] < 90:
        print(f"  - 最薄弱环节: {weakest} (平均 {avg_dims[weakest]:.1f}分)，建议重点改进")
    
    if avg_dims['公式完整性'] < 90:
        print("  - 公式问题: 运行 check_quality.py 检测未闭合的$符号，美元金额使用\\$转义")
    if avg_dims['术语一致性'] < 90:
        print("  - 术语问题: 使用 translation_memory.py check 检查术语一致性，统一译法")
    if avg_dims['格式规范度'] < 90:
        print("  - 格式问题: 使用 chapter_template.md 模板，保持标题层级一致（章##，节###）")
    
    # 保存报告
    if args.output:
        report = {
            'summary': {
                'total_files': len(results),
                'average_score': round(avg_score, 1),
                'passed': passed,
                'threshold': args.threshold,
                'average_dimensions': {k: round(v, 1) for k, v in avg_dims.items()}
            },
            'details': results
        }
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n报告已保存: {args.output}")

if __name__ == '__main__':
    main()
