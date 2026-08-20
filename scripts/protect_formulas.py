#!/usr/bin/env python3
"""
LaTeX公式保护与回填工具
翻译前提取公式为占位符，翻译后回填，避免公式被翻译工具破坏
"""
import re
import json
import sys
import os

def extract_formulas(content):
    """提取所有LaTeX公式，返回(占位符文本, 公式字典)"""
    formulas = {}
    counter = 0
    
    def replace_block(match):
        nonlocal counter
        counter += 1
        placeholder = f"@@FORMULA_BLOCK_{counter}@@"
        formulas[placeholder] = match.group(0)
        return placeholder
    
    def replace_inline(match):
        nonlocal counter
        counter += 1
        placeholder = f"@@FORMULA_INLINE_{counter}@@"
        formulas[placeholder] = match.group(0)
        return placeholder
    
    # 先提取$$...$$块公式（使用非贪婪匹配，支持跨行）
    content = re.sub(r'\$\$.*?\$\$', replace_block, content, flags=re.DOTALL)
    # 再提取$...$行内公式（跳过已提取的占位符）
    content = re.sub(r'(?<!@)\$[^@$]+?\$(?!@)', replace_inline, content)
    
    return content, formulas

def restore_formulas(content, formulas):
    """回填公式"""
    for placeholder, formula in formulas.items():
        content = content.replace(placeholder, formula)
    return content

def main():
    import argparse
    parser = argparse.ArgumentParser(description='LaTeX公式保护与回填工具')
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # extract 命令
    extract_parser = subparsers.add_parser('extract', help='提取公式')
    extract_parser.add_argument('input', help='输入文件路径')
    extract_parser.add_argument('--output', '-o', help='输出占位符文件路径 (默认: 输入名.protected.md)')
    extract_parser.add_argument('--formulas', '-f', help='公式字典输出路径 (默认: 输入名.formulas.json)')
    
    # restore 命令
    restore_parser = subparsers.add_parser('restore', help='回填公式')
    restore_parser.add_argument('input', help='输入占位符文件路径')
    restore_parser.add_argument('--formulas', '-f', help='公式字典路径 (默认: 输入名.formulas.json)')
    restore_parser.add_argument('--output', '-o', help='输出文件路径 (默认: 输入名.restored.md)')
    
    args = parser.parse_args()
    
    if args.command == 'extract':
        if not os.path.exists(args.input):
            print(f"错误: 文件不存在 - {args.input}")
            sys.exit(1)
        
        with open(args.input, 'r', encoding='utf-8') as f:
            content = f.read()
        
        protected, formulas = extract_formulas(content)
        
        output_path = args.output or args.input.replace('.md', '.protected.md')
        formulas_path = args.formulas or args.input.replace('.md', '.formulas.json')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(protected)
        
        with open(formulas_path, 'w', encoding='utf-8') as f:
            json.dump(formulas, f, ensure_ascii=False, indent=2)
        
        print(f"已提取 {len(formulas)} 个公式")
        print(f"占位符文件: {output_path}")
        print(f"公式字典: {formulas_path}")
        print("\n提示: 翻译占位符文件后，使用 restore 命令回填公式")
    
    elif args.command == 'restore':
        if not os.path.exists(args.input):
            print(f"错误: 文件不存在 - {args.input}")
            sys.exit(1)
        
        formulas_path = args.formulas or args.input.replace('.protected.md', '.formulas.json').replace('.md', '.formulas.json')
        if not os.path.exists(formulas_path):
            print(f"错误: 公式字典不存在 - {formulas_path}")
            sys.exit(1)
        
        with open(args.input, 'r', encoding='utf-8') as f:
            content = f.read()
        
        with open(formulas_path, 'r', encoding='utf-8') as f:
            formulas = json.load(f)
        
        restored = restore_formulas(content, formulas)
        
        output_path = args.output or args.input.replace('.protected.md', '.restored.md').replace('.md', '.restored.md')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(restored)
        
        # 检查是否有未回填的占位符
        remaining = re.findall(r'@@FORMULA_\w+_\d+@@', restored)
        if remaining:
            print(f"⚠️  警告: 还有 {len(remaining)} 个占位符未回填")
        else:
            print(f"✅ 所有公式已回填")
        
        print(f"输出文件: {output_path}")
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
