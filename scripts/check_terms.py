#!/usr/bin/env python3
"""
术语一致性检查与自动修复工具
功能：
- 对比术语表，检测未翻译术语和译法冲突
- 自动修复模式：将非标准译法替换为术语表中的标准译法
- 生成术语使用统计报告
"""
import json
import re
import sys
import os
import glob
import argparse

def load_glossary(glossary_path):
    """加载术语表"""
    with open(glossary_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def check_untranslated_terms(content, glossary):
    """检查未翻译的英文术语"""
    issues = []
    for en, zh in glossary.items():
        if en.startswith('_') or len(en) < 3:
            continue
        pattern = rf'\b{re.escape(en)}\b'
        matches = list(re.finditer(pattern, content, re.IGNORECASE))
        if matches:
            for m in matches[:3]:
                before = content[:m.start()]
                dollar_count = before.count('$') - before.count('\\$')
                if dollar_count % 2 == 1:
                    continue
                line = content[:m.start()].count('\n') + 1
                issues.append({
                    'type': 'untranslated',
                    'term': en,
                    'standard': zh,
                    'line': line,
                    'context': content[max(0,m.start()-20):m.end()+20].strip()
                })
                break
    return issues

def check_translation_variants(content, glossary):
    """检查译法变体（同一术语的不同译法）"""
    issues = []
    # 常见变体映射（可扩展）
    variant_map = {
        '活动': '互动练习',
        '练习': '习题',
        '算法': '算法',  # 标准
        '运算法则': '算法',
        '最大公因子': '最大公约数',
        '最小公倍式': '最小公倍数',
    }
    
    for variant, standard in variant_map.items():
        if variant == standard:
            continue
        if variant in content and standard not in content:
            issues.append({
                'type': 'variant',
                'variant': variant,
                'standard': standard,
                'count': content.count(variant)
            })
    return issues

def fix_terms(content, glossary, dry_run=False):
    """自动修复术语，返回(修复后内容, 修复列表)"""
    fixes = []
    
    # 1. 修复译法变体
    variant_map = {
        '活动': '互动练习',
        '运算法则': '算法',
        '最大公因子': '最大公约数',
        '最小公倍式': '最小公倍数',
    }
    
    for variant, standard in variant_map.items():
        if variant in content:
            count = content.count(variant)
            if not dry_run:
                content = content.replace(variant, standard)
            fixes.append({
                'type': 'variant',
                'from': variant,
                'to': standard,
                'count': count
            })
    
    # 2. 修复未翻译术语（简单替换）
    for en, zh in glossary.items():
        if en.startswith('_') or len(en) < 4:
            continue
        # 只替换不在公式中的术语
        pattern = rf'(?<!\$)\b{re.escape(en)}\b(?!\$)'
        matches = list(re.finditer(pattern, content, re.IGNORECASE))
        if matches and zh not in content:
            count = len(matches)
            if not dry_run:
                content = re.sub(pattern, zh, content, flags=re.IGNORECASE)
            fixes.append({
                'type': 'untranslated',
                'from': en,
                'to': zh,
                'count': count
            })
    
    return content, fixes

def check_file(filepath, glossary):
    """检查单个文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    issues = []
    issues.extend(check_untranslated_terms(content, glossary))
    issues.extend(check_translation_variants(content, glossary))
    
    return issues

def main():
    parser = argparse.ArgumentParser(description='术语一致性检查与自动修复工具')
    parser.add_argument('path', help='文件或目录路径')
    parser.add_argument('--glossary', '-g', required=True, help='术语表JSON文件路径')
    parser.add_argument('--fix', action='store_true', help='自动修复模式（直接修改文件）')
    parser.add_argument('--dry-run', action='store_true', help='预览修复但不修改文件')
    parser.add_argument('--output', '-o', help='输出报告到文件')
    parser.add_argument('--stats', action='store_true', help='生成术语使用统计')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.glossary):
        print(f"错误: 术语表不存在 - {args.glossary}")
        sys.exit(1)
    
    glossary = load_glossary(args.glossary)
    print(f"已加载术语表: {len(glossary)} 条术语")
    
    # 收集文件
    files = []
    if os.path.isdir(args.path):
        files = glob.glob(os.path.join(args.path, '**', '*.md'), recursive=True)
    elif '*' in args.path or '?' in args.path:
        files = glob.glob(args.path)
    else:
        files = [args.path]
    
    if not files:
        print("未找到匹配的文件")
        sys.exit(1)
    
    print(f"检查 {len(files)} 个文件...\n")
    
    total_issues = 0
    total_fixes = 0
    report_lines = []
    
    for filepath in sorted(files):
        if not os.path.exists(filepath):
            continue
        
        filename = os.path.basename(filepath)
        
        if args.fix or args.dry_run:
            # 修复模式
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            fixed_content, fixes = fix_terms(content, glossary, args.dry_run)
            
            if fixes:
                print(f"🔧 {filename}: {len(fixes)} 项修复")
                for fix in fixes:
                    print(f"   - {fix['from']} → {fix['to']} ({fix['count']} 处)")
                    report_lines.append(f"{filename}: {fix['from']} → {fix['to']} ({fix['count']} 处)")
                total_fixes += sum(f['count'] for f in fixes)
                
                if not args.dry_run:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(fixed_content)
            else:
                print(f"✅ {filename}: 无需修复")
        else:
            # 检查模式
            issues = check_file(filepath, glossary)
            if issues:
                print(f"❌ {filename} ({len(issues)} 个问题):")
                for issue in issues:
                    if issue['type'] == 'untranslated':
                        print(f"   - 第{issue['line']}行: 未翻译 '{issue['term']}' (标准: '{issue['standard']}')")
                        print(f"     上下文: ...{issue['context']}...")
                    else:
                        print(f"   - 译法变体: '{issue['variant']}' 出现 {issue['count']} 次 (标准: '{issue['standard']}')")
                total_issues += len(issues)
            else:
                print(f"✅ {filename}")
    
    print(f"\n{'='*50}")
    if args.fix or args.dry_run:
        print(f"修复完成: {len(files)} 个文件, 共 {total_fixes} 处修复")
        if args.dry_run:
            print("(预览模式，未实际修改文件。使用 --fix 执行修复)")
    else:
        print(f"检查完成: {len(files)} 个文件, {total_issues} 个术语问题")
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        print(f"报告已保存: {args.output}")

if __name__ == '__main__':
    main()
