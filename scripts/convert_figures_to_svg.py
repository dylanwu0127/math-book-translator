#!/usr/bin/env python3
"""
数学图形SVG转换工具（改进版）
自动检测译文中的简单图形代码块（数轴、坐标系等）并转换为SVG格式，
保证与原书视觉一致。

改进点：
- 更接近原书的数轴样式（细线条、小刻度、数字位置）
- 统一的边距和比例
- 更好的字体设置（serif，接近原书）
- 标记点样式优化
"""
import re
import os
import glob

def parse_number_line(line):
    """解析一行数字，返回数字列表"""
    parts = line.strip().split()
    numbers = []
    for p in parts:
        if '/' in p:
            numbers.append(p)
        else:
            try:
                float(p)
                numbers.append(p)
            except:
                pass
    return numbers

def generate_svg_simple(numbers, width=500, height=50):
    """生成简单的整数数轴SVG - 改进版，更接近原书样式"""
    if not numbers:
        return ""
    
    margin = 25
    usable_width = width - 2 * margin
    n = len(numbers)
    if n <= 1:
        step = usable_width
    else:
        step = usable_width / (n - 1)
    
    y_axis = height // 2 - 8
    
    svg = f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">\n'
    # 水平线 - 较细，接近原书
    svg += f'  <line x1="{margin}" y1="{y_axis}" x2="{width - margin}" y2="{y_axis}" stroke="black" stroke-width="0.8"/>\n'
    
    for i, num in enumerate(numbers):
        x = margin + i * step
        # 刻度线 - 小竖线，长度5px
        svg += f'  <line x1="{x:.1f}" y1="{y_axis - 4}" x2="{x:.1f}" y2="{y_axis + 4}" stroke="black" stroke-width="0.8"/>\n'
        # 数字标签 - 在刻度正下方，serif字体，大小12
        svg += f'  <text x="{x:.1f}" y="{y_axis + 18}" font-family="Times New Roman, serif" font-size="12" text-anchor="middle">{num}</text>\n'
    
    svg += '</svg>'
    return svg

def generate_svg_two_lines(top_numbers, bottom_numbers, width=600, height=70):
    """生成两行数轴SVG（整数+分数）- 改进版"""
    if not top_numbers and not bottom_numbers:
        return ""
    
    margin = 25
    usable_width = width - 2 * margin
    
    all_numbers = bottom_numbers if bottom_numbers else top_numbers
    n = len(all_numbers)
    if n <= 1:
        step = usable_width
    else:
        step = usable_width / (n - 1)
    
    y_axis = height // 2 - 10
    
    svg = f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">\n'
    svg += f'  <line x1="{margin}" y1="{y_axis}" x2="{width - margin}" y2="{y_axis}" stroke="black" stroke-width="0.8"/>\n'
    
    # 绘制顶部整数标记（较大的刻度）
    if top_numbers:
        for i, num in enumerate(top_numbers):
            try:
                idx = bottom_numbers.index(num) if num in bottom_numbers else i
                x = margin + idx * step
            except:
                x = margin + i * step * (len(bottom_numbers) // max(len(top_numbers), 1))
            
            # 整数刻度 - 稍长
            svg += f'  <line x1="{x:.1f}" y1="{y_axis - 6}" x2="{x:.1f}" y2="{y_axis + 6}" stroke="black" stroke-width="1"/>\n'
            svg += f'  <text x="{x:.1f}" y="{y_axis - 10}" font-family="Times New Roman, serif" font-size="12" text-anchor="middle">{num}</text>\n'
    
    # 绘制底部分数标记
    if bottom_numbers:
        for i, num in enumerate(bottom_numbers):
            x = margin + i * step
            # 分数刻度 - 较短
            svg += f'  <line x1="{x:.1f}" y1="{y_axis - 3}" x2="{x:.1f}" y2="{y_axis + 3}" stroke="black" stroke-width="0.8"/>\n'
            svg += f'  <text x="{x:.1f}" y="{y_axis + 18}" font-family="Times New Roman, serif" font-size="10" text-anchor="middle">{num}</text>\n'
    
    svg += '</svg>'
    return svg

def generate_svg_with_marker(numbers, marker_value, marker_label, width=500, height=60):
    """生成带有标记点的数轴SVG - 改进版"""
    if not numbers:
        return ""
    
    margin = 25
    usable_width = width - 2 * margin
    n = len(numbers)
    if n <= 1:
        step = usable_width
    else:
        step = usable_width / (n - 1)
    
    y_axis = height // 2 - 8
    
    svg = f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">\n'
    svg += f'  <line x1="{margin}" y1="{y_axis}" x2="{width - margin}" y2="{y_axis}" stroke="black" stroke-width="0.8"/>\n'
    
    for i, num in enumerate(numbers):
        x = margin + i * step
        svg += f'  <line x1="{x:.1f}" y1="{y_axis - 4}" x2="{x:.1f}" y2="{y_axis + 4}" stroke="black" stroke-width="0.8"/>\n'
        svg += f'  <text x="{x:.1f}" y="{y_axis + 18}" font-family="Times New Roman, serif" font-size="12" text-anchor="middle">{num}</text>\n'
    
    # 绘制标记点
    try:
        if '/' in str(marker_value):
            parts = marker_value.split('/')
            ratio = float(parts[0]) / float(parts[1])
            x = margin + ratio * step
        else:
            idx = numbers.index(str(marker_value)) if str(marker_value) in numbers else float(marker_value)
            x = margin + idx * step
    except:
        x = margin + step
    
    # 标记点 - 实心圆点，半径3
    svg += f'  <circle cx="{x:.1f}" cy="{y_axis}" r="3" fill="black"/>\n'
    svg += f'  <text x="{x:.1f}" y="{y_axis - 10}" font-family="Times New Roman, serif" font-size="12" text-anchor="middle">{marker_label}</text>\n'
    
    svg += '</svg>'
    return svg

def convert_number_lines_in_file(filepath):
    """转换文件中的数轴代码块为SVG"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 匹配代码块
    pattern = r'```\n(.*?)\n```'
    matches = list(re.finditer(pattern, content, re.DOTALL))
    
    if not matches:
        return content, 0
    
    count = 0
    new_content = content
    
    for match in reversed(matches):
        code_block = match.group(1)
        lines = code_block.strip().split('\n')
        
        # 判断是否为数轴
        is_number_line = False
        if len(lines) >= 1:
            first_line = lines[0].strip()
            if first_line.startswith('0') and re.search(r'\d', first_line):
                non_space = re.sub(r'[\d\s/\.%-]', '', first_line)
                if len(non_space) <= 2:
                    is_number_line = True
        
        if not is_number_line:
            continue
        
        # 解析数轴
        if len(lines) == 1:
            numbers = parse_number_line(lines[0])
            if numbers:
                svg = generate_svg_simple(numbers)
                if svg:
                    new_content = new_content[:match.start()] + svg + new_content[match.end():]
                    count += 1
        elif len(lines) == 2:
            top_numbers = parse_number_line(lines[0])
            bottom_numbers = parse_number_line(lines[1])
            
            if len(bottom_numbers) == 1 and '/' in bottom_numbers[0]:
                svg = generate_svg_with_marker(top_numbers, bottom_numbers[0], bottom_numbers[0])
            else:
                svg = generate_svg_two_lines(top_numbers, bottom_numbers)
            
            if svg:
                new_content = new_content[:match.start()] + svg + new_content[match.end():]
                count += 1
    
    return new_content, count

def main():
    import sys
    if len(sys.argv) > 1:
        target = sys.argv[1]
        if os.path.isdir(target):
            files = sorted(glob.glob(os.path.join(target, '*.md')))
        elif os.path.isfile(target):
            files = [target]
        else:
            print(f"错误: {target} 不存在")
            return
    else:
        output_dir = r'D:\资料\个人\project\翻译\prealgebra译文'
        files = sorted(glob.glob(os.path.join(output_dir, '*.md')))
        files = [f for f in files if '完整译文' not in f]
    
    total_converted = 0
    
    for filepath in files:
        filename = os.path.basename(filepath)
        new_content, count = convert_number_lines_in_file(filepath)
        
        if count > 0:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f'  {filename}: 转换了 {count} 个数轴')
            total_converted += count
        else:
            print(f'  {filename}: 无数轴需要转换')
    
    print(f'\n总共转换了 {total_converted} 个数轴')
    
    # 重新生成完整译文
    if len(sys.argv) <= 1:
        print('\n正在重新生成完整译文...')
        output_dir = r'D:\资料\个人\project\翻译\prealgebra译文'
        output_file = os.path.join(output_dir, '完整译文-伍鸿熙预代数.md')
        files = sorted(glob.glob(os.path.join(output_dir, '*.md')))
        files = [f for f in files if '完整译文' not in f]
        
        content = ''
        for f in files:
            with open(f, 'r', encoding='utf-8') as file:
                content += file.read()
                content += '\n\n---\n\n'
        
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(content)
        
        print(f'完整译文已更新: {output_file}')

if __name__ == '__main__':
    main()
