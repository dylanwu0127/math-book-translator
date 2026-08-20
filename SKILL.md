---
name: math-book-translator
description: 数学专业书籍（教材、专著）中英互译全流程工具集。支持PDF智能提取与章节分割（带页码锚点、图表标记）、LaTeX公式保护与回填、术语表管理、翻译记忆库、质量自动检查（$符号配对/标题层级/术语一致性）、翻译质量评分、翻译进度追踪、批量交付打包、Markdown模板化输出。当用户需要翻译数学类书籍（含大量公式、定理、图表）、或需要对已翻译的数学文档进行质量复核、或需要批量处理翻译文档时使用此Skill。
---

# 数学书籍翻译工具集

## 工作流程

### 阶段一：预处理（翻译开始前）

1. **确认PDF完整性**：用 `scripts/extract_pdf.py --info` 确认总页数，不要依赖Read工具的token上限判断内容是否结束。
2. **提取并分割章节**：`scripts/extract_pdf.py <pdf路径> --output <输出目录>`，自动按章标题分割，带页码锚点和图表标记，生成page_map.json。
3. **建立术语表**：复制 `assets/glossary_template.json` 为项目术语表，翻译前确认核心术语译法。
4. **公式保护（可选）**：对公式密集章节，用 `scripts/protect_formulas.py extract <输入文件>` 提取公式为占位符，翻译纯文本后用 `scripts/protect_formulas.py restore <输入文件>` 回填。

### 阶段二：翻译执行

1. 每章使用 `assets/chapter_template.md` 作为结构模板，保持章标题（`##`）、节标题（`###`）、习题（`### 习题`）层级一致。
2. 公式一律使用LaTeX：行内 `$...$`，独立 `$$...$$`。
3. 美元金额必须转义为 `\$`，避免与LaTeX分隔符冲突。
4. 脚注标记 `$^n$` 与后续公式之间必须加空格，避免 `$$` 被误解析为块数学。
5. **图形一致性规范**：原文中的数轴、坐标系、几何图形等不能用简单的文字代码块（如 `0 1 2 3 4`）表示，必须转换为SVG格式，保持与原书一致的视觉效果。SVG图形应包含：轴线、刻度线、标签文字、标记点等元素。翻译完成后运行 `scripts/convert_figures_to_svg.py <译文目录>` 批量检测并转换简单图形为SVG。
6. 每章译完立即运行 `scripts/check_quality.py <文件路径>`，即时修复问题。
7. 翻译记忆库复用：用 `scripts/translation_memory.py build` 从已译文档构建记忆库，用 `scripts/translation_memory.py match` 匹配相似句对。

### 阶段三：部分复核

每完成一个Part（约5-13章），运行：
- `scripts/check_terms.py <译文目录> --glossary <术语表路径>` 检查术语一致性
- `scripts/check_quality.py <译文目录>/*.md` 批量检查格式
- `scripts/quality_score.py <译文目录>/*.md` 生成质量评分

### 阶段四：最终复核与交付

1. 全量运行 `scripts/check_quality.py`、`scripts/check_terms.py`、`scripts/quality_score.py`。
2. 用 `scripts/progress_tracker.py <译文目录>` 生成翻译进度报告。
3. 用 `scripts/package.py <译文目录>/*.md --all` 生成目录索引、翻译说明、完整译稿、交付zip包。

## 脚本说明

### scripts/extract_pdf.py（增强版）
PDF提取与章节分割，带页码锚点和图表标记。依赖PyPDF2。
```bash
python extract_pdf.py --info <pdf路径>          # 仅显示总页数
python extract_pdf.py <pdf路径> --output raw/    # 提取全文，带页码锚点和图表标记
python extract_pdf.py <pdf路径> --no-anchors     # 不添加页码锚点
python extract_pdf.py <pdf路径> --no-figures     # 不检测图表标记
```
输出：按章分割的txt文件 + page_map.json（页码映射表）+ full_text.txt（可选）

### scripts/check_quality.py
综合质量检查，检测：
- LaTeX `$` 符号未闭合（自动跳过 `\$` 转义和 `$$` 块）
- 标题层级异常（章标题应为`##`，节标题应为`###`）
- 连续空行过多
- 术语遗漏（Activity/Exercise未翻译）
- 美元符号未转义

```bash
python check_quality.py file1.md file2.md        # 检查指定文件
python check_quality.py 译文/*.md                  # 批量检查
```

### scripts/check_terms.py（增强版）
术语一致性检查与自动修复。
```bash
python check_terms.py 译文/ --glossary glossary.json           # 检查术语
python check_terms.py 译文/ --glossary glossary.json --dry-run # 预览修复
python check_terms.py 译文/ --glossary glossary.json --fix     # 自动修复
```

### scripts/protect_formulas.py
LaTeX公式保护与回填，避免翻译工具破坏公式。
```bash
python protect_formulas.py extract input.md       # 提取公式，输出 input.protected.md + formulas.json
python protect_formulas.py restore input.md       # 回填公式
```

### scripts/convert_figures_to_svg.py（新增）
数学图形SVG转换工具，自动检测译文中的简单图形代码块（数轴、坐标系等）并转换为SVG格式，保证与原书视觉一致。
支持类型：
- 单行整数数轴（如 `0 1 2 3 4`）
- 两行数轴（整数+分数标签）
- 带标记点的数轴（如标记1/4、5/4位置）

SVG图形包含：水平轴线、刻度线（整数刻度更长更粗）、数字标签（serif字体居中）、标记点（黑色圆点）、分数标签（加粗显示）。

```bash
python convert_figures_to_svg.py                  # 转换当前目录所有md文件
python convert_figures_to_svg.py 译文/             # 转换指定目录的md文件
python convert_figures_to_svg.py file.md           # 转换单个文件
```

### scripts/translation_memory.py（新增）
翻译记忆库工具。
```bash
python translation_memory.py build 译文/*.md --glossary glossary.json  # 构建记忆库
python translation_memory.py match "待匹配文本" --memory translation_memory.json  # 匹配记忆库
python translation_memory.py check 译文/*.md --memory translation_memory.json     # 检查一致性
```

### scripts/quality_score.py（新增）
翻译质量评分，基于四维度加权：
- 术语一致性 (30%)
- 公式完整性 (30%)
- 格式规范度 (20%)
- 章节完整度 (20%)

```bash
python quality_score.py 译文/*.md --glossary glossary.json  # 评分
python quality_score.py 译文/*.md --output report.json       # 输出报告
```

### scripts/progress_tracker.py
翻译进度追踪，统计已翻译章节、字数、生成进度报告。
```bash
python progress_tracker.py 译文/
```

### scripts/package.py（新增）
批量交付打包工具。
```bash
python package.py 译文/*.md --all                  # 全部操作（目录+说明+合并+打包）
python package.py 译文/*.md --toc                  # 仅生成目录索引
python package.py 译文/*.md --merge                # 仅合并完整译稿
python package.py 译文/*.md --zip                  # 仅打包zip
```

## 模板说明

### assets/chapter_template.md
章节翻译模板，包含标准结构：章标题、节列表、各节、习题。

### assets/glossary_template.json
术语表模板，包含120+数学翻译常用术语对照，可直接复制修改。

## 关键注意事项

1. **不要依赖Read工具判断PDF结束**：Read工具有token上限，大PDF必须用extract_pdf.py确认总页数。
2. **美元符号必须转义**：文中的美元金额一律用 `\$`，否则会被解析为LaTeX公式开始。
3. **脚注与公式间加空格**：`$^1$$x$` 会被误解析，必须写为 `$^1$ $x$`。
4. **图形必须用SVG**：原文中的数轴、坐标系、几何图形等不能用简单文字代码块表示，必须转换为SVG格式，保持与原书一致的视觉效果。翻译完成后运行convert_figures_to_svg.py批量转换。
5. **每章即时检查**：不要等到全部译完再复核，每章译完跑一次check_quality.py。
6. **术语表前置**：翻译开始前确认核心术语译法，避免中途调整导致全局替换。
7. **页码锚点回查**：extract_pdf.py生成的page_map.json记录每段对应原书页码，便于校对时回查原文。
8. **翻译记忆库复用**：每完成一部分就更新记忆库，后续章节翻译时自动匹配相似句对，提高一致性。
