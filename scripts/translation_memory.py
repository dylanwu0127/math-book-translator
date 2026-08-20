#!/usr/bin/env python3
"""
翻译记忆库工具
功能：
- 从已翻译文档中提取术语和句对，构建翻译记忆库
- 新文档翻译时自动匹配复用，提示一致译法
- 基于相似度的模糊匹配
- 导出/导入记忆库JSON
"""
import json
import re
import os
import sys
import argparse
from difflib import SequenceMatcher

def similarity(a, b):
    """计算两个字符串的相似度"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def extract_terms_from_glossary(glossary_path):
    """从术语表加载术语"""
    if not os.path.exists(glossary_path):
        return {}
    with open(glossary_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_sentence_pairs(md_file):
    """从Markdown文件中提取可能的句对（简单实现）"""
    pairs = []
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 移除公式和代码块
    content = re.sub(r'\$[^$]+\$', '', content)
    content = re.sub(r'\$\$.*?\$\$', '', content, flags=re.DOTALL)
    content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
    
    # 按句子分割
    sentences = re.split(r'[。！？.!?]\s*', content)
    for s in sentences:
        s = s.strip()
        if len(s) > 10 and len(s) < 200:
            pairs.append(s)
    return pairs

def build_memory(input_files, glossary_path=None, output_path='translation_memory.json'):
    """构建翻译记忆库"""
    memory = {
        'terms': {},
        'sentences': [],
        'stats': {
            'total_terms': 0,
            'total_sentences': 0,
            'source_files': []
        }
    }
    
    # 加载术语表
    if glossary_path and os.path.exists(glossary_path):
        memory['terms'] = extract_terms_from_glossary(glossary_path)
        print(f"从术语表加载 {len(memory['terms'])} 条术语")
    
    # 从文件中提取句子
    all_sentences = set()
    for f in input_files:
        if not os.path.exists(f):
            print(f"⚠️  文件不存在: {f}")
            continue
        sentences = extract_sentence_pairs(f)
        all_sentences.update(sentences)
        memory['stats']['source_files'].append(os.path.basename(f))
        print(f"  从 {os.path.basename(f)} 提取 {len(sentences)} 个句子")
    
    memory['sentences'] = sorted(list(all_sentences))
    memory['stats']['total_terms'] = len(memory['terms'])
    memory['stats']['total_sentences'] = len(memory['sentences'])
    
    # 保存记忆库
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)
    
    print(f"\n翻译记忆库已保存: {output_path}")
    print(f"  术语: {memory['stats']['total_terms']} 条")
    print(f"  句子: {memory['stats']['total_sentences']} 条")
    return memory

def match_memory(text, memory_path='translation_memory.json', threshold=0.7):
    """匹配翻译记忆库，返回相似的术语和句子"""
    if not os.path.exists(memory_path):
        print(f"错误: 记忆库不存在 - {memory_path}")
        return []
    
    with open(memory_path, 'r', encoding='utf-8') as f:
        memory = json.load(f)
    
    matches = []
    
    # 术语匹配（精确匹配）
    for en, zh in memory['terms'].items():
        if len(en) < 3:
            continue
        if re.search(rf'\b{re.escape(en)}\b', text, re.IGNORECASE):
            matches.append({
                'type': 'term',
                'source': en,
                'target': zh,
                'similarity': 1.0
            })
    
    # 句子模糊匹配
    text_sentences = re.split(r'[。！？.!?]\s*', text)
    for ts in text_sentences:
        ts = ts.strip()
        if len(ts) < 10:
            continue
        for ms in memory['sentences']:
            sim = similarity(ts, ms)
            if sim >= threshold and sim < 1.0:
                matches.append({
                    'type': 'sentence',
                    'source': ts[:80],
                    'target': ms[:80],
                    'similarity': round(sim, 2)
                })
    
    # 按相似度排序
    matches.sort(key=lambda x: x['similarity'], reverse=True)
    return matches[:20]

def check_consistency(files, memory_path='translation_memory.json'):
    """检查多个文件之间的术语一致性"""
    if not os.path.exists(memory_path):
        print(f"错误: 记忆库不存在 - {memory_path}")
        return
    
    with open(memory_path, 'r', encoding='utf-8') as f:
        memory = json.load(f)
    
    print("术语一致性检查:")
    print("=" * 50)
    
    issues = []
    for f in files:
        if not os.path.exists(f):
            continue
        with open(f, 'r', encoding='utf-8') as fh:
            content = fh.read()
        
        filename = os.path.basename(f)
        for en, zh in memory['terms'].items():
            if len(en) < 3:
                continue
            # 检查英文术语是否出现但未翻译
            if re.search(rf'\b{re.escape(en)}\b', content, re.IGNORECASE):
                # 检查标准译法是否出现
                if zh not in content:
                    issues.append(f"{filename}: 术语 '{en}' 出现，但标准译法 '{zh}' 未找到")
    
    if issues:
        for issue in issues:
            print(f"  ⚠️  {issue}")
    else:
        print("  ✅ 所有文件术语一致")
    
    print(f"\n共检查 {len(files)} 个文件，发现 {len(issues)} 个问题")

def main():
    parser = argparse.ArgumentParser(description='翻译记忆库工具')
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # build 命令
    build_parser = subparsers.add_parser('build', help='构建翻译记忆库')
    build_parser.add_argument('files', nargs='+', help='已翻译的Markdown文件')
    build_parser.add_argument('--glossary', '-g', help='术语表JSON路径')
    build_parser.add_argument('--output', '-o', default='translation_memory.json', help='输出记忆库路径')
    
    # match 命令
    match_parser = subparsers.add_parser('match', help='匹配翻译记忆库')
    match_parser.add_argument('text', help='待匹配的文本或文件路径')
    match_parser.add_argument('--memory', '-m', default='translation_memory.json', help='记忆库路径')
    match_parser.add_argument('--threshold', '-t', type=float, default=0.7, help='相似度阈值 (0-1)')
    
    # check 命令
    check_parser = subparsers.add_parser('check', help='检查术语一致性')
    check_parser.add_argument('files', nargs='+', help='待检查的文件')
    check_parser.add_argument('--memory', '-m', default='translation_memory.json', help='记忆库路径')
    
    args = parser.parse_args()
    
    if args.command == 'build':
        build_memory(args.files, args.glossary, args.output)
    
    elif args.command == 'match':
        # 如果是文件，读取内容
        if os.path.exists(args.text):
            with open(args.text, 'r', encoding='utf-8') as f:
                text = f.read()
        else:
            text = args.text
        
        matches = match_memory(text, args.memory, args.threshold)
        if matches:
            print(f"找到 {len(matches)} 个匹配:")
            print("=" * 50)
            for m in matches:
                if m['type'] == 'term':
                    print(f"  [术语] {m['source']} → {m['target']}")
                else:
                    print(f"  [句子] 相似度 {m['similarity']}:")
                    print(f"    原文: {m['source']}")
                    print(f"    记忆: {m['target']}")
        else:
            print("未找到匹配")
    
    elif args.command == 'check':
        check_consistency(args.files, args.memory)
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
