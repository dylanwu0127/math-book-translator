# 数学书籍翻译工具集 (math-book-translator)

数学专业书籍（教材、专著）中英互译全流程自动化工具集。

## 📖 用途

专为数学类书籍翻译设计，解决以下痛点：

- **PDF读取限制**：大PDF无法一次性读取，工具自动提取并按章分割
- **LaTeX公式保护**：翻译时公式容易被破坏，工具自动提取/回填公式
- **术语一致性**：同一术语多种译法，工具自动检查并修复
- **格式规范**：标题层级、$符号配对、空行等格式问题自动检测
- **质量评估**：多维度自动评分，给出改进建议
- **交付打包**：一键生成目录索引、翻译说明、完整译稿、zip包

适用于：数学教材翻译、数学专著翻译、含大量公式/定理/图表的学术文档翻译。

---

## ✨ 功能列表

### 核心工具（8个脚本）

| 工具 | 功能 | 关键特性 |
|------|------|----------|
| `extract_pdf.py` | PDF提取与章节分割 | 页码锚点、图表标记、页码映射表 |
| `check_quality.py` | 综合质量检查 | $符号配对、标题层级、空行、术语、美元符号 |
| `check_terms.py` | 术语检查与修复 | 未翻译术语检测、译法变体、自动修复(--fix) |
| `protect_formulas.py` | 公式保护与回填 | 提取公式为占位符、翻译后回填 |
| `translation_memory.py` | 翻译记忆库 | 句对提取、模糊匹配、一致性检查 |
| `quality_score.py` | 翻译质量评分 | 四维度加权评分、改进建议 |
| `progress_tracker.py` | 翻译进度追踪 | 章节统计、字数统计、进度报告 |
| `package.py` | 批量交付打包 | 目录索引、翻译说明、合并译稿、zip打包 |

### 模板（2个）

| 模板 | 用途 |
|------|------|
| `chapter_template.md` | 章节翻译标准结构模板 |
| `glossary_template.json` | 术语表模板（120+数学常用术语） |

---

## 📦 安装与依赖

### 环境要求

- Python 3.7+
- PyPDF2（PDF提取用，可选）

### 安装依赖

```bash
pip install PyPDF2
```

> 其他脚本仅使用Python标准库，无需额外安装。

### Skill位置

本工具集位于用户skill目录：

```
<用户目录>/.doubao/agent_mode/workspace/.user_skills/math-book-translator/
```

---

## 🚀 快速开始

### 第一步：预处理PDF

```bash
# 1. 查看PDF信息（确认总页数）
python scripts/extract_pdf.py --info 原书.pdf

# 2. 提取全文并按章分割（带页码锚点和图表标记）
python scripts/extract_pdf.py 原书.pdf --output raw_chapters/
```

输出：
- `raw_chapters/chapter_01_*.txt` ~ `chapter_NN_*.txt`（按章分割的文本）
- `raw_chapters/page_map.json`（页码映射表，便于回查原文）
- `raw_chapters/full_text.txt`（可选，加`--full`参数）

### 第二步：建立术语表

```bash
# 复制术语表模板
cp assets/glossary_template.json my_glossary.json

# 编辑术语表，根据具体书籍调整译法
```

### 第三步：逐章翻译

1. 使用 `assets/chapter_template.md` 作为结构模板
2. 公式使用LaTeX：行内 `$...$`，独立 `$$...$$`
3. 每章译完立即检查：

```bash
python scripts/check_quality.py 译文/第1章.md
```

### 第四步：部分复核

每完成一个部分（约5-13章），运行：

```bash
# 术语一致性检查
python scripts/check_terms.py 译文/ --glossary my_glossary.json

# 质量评分
python scripts/quality_score.py 译文/*.md --glossary my_glossary.json
```

### 第五步：最终交付

```bash
# 一键生成所有交付物
python scripts/package.py 译文/*.md --all --glossary my_glossary.json
```

输出：
- `目录索引.md`（含章节链接）
- `翻译说明.md`（术语约定、格式约定、翻译统计）
- `完整译稿.md`（合并所有章节）
- `翻译交付包.zip`（打包所有文件）

---

## 🛠️ 各工具详细用法

### 1. extract_pdf.py — PDF提取与章节分割

```bash
# 基本用法
python scripts/extract_pdf.py <pdf路径> --output <输出目录>

# 仅查看信息
python scripts/extract_pdf.py --info <pdf路径>

# 同时保存完整文本
python scripts/extract_pdf.py <pdf路径> --output raw/ --full

# 不添加页码锚点
python scripts/extract_pdf.py <pdf路径> --no-anchors

# 不检测图表标记
python scripts/extract_pdf.py <pdf路径> --no-figures
```

**输出说明**：

- 每个章节文件开头包含 `<!-- 原书第X页 -->` 页码锚点
- 图表位置插入 `<!-- 图表占位: 图3.1 - 标题 (原书P.45) -->` 标记
- `page_map.json` 记录每页的字符偏移范围和图表数量

**依赖**：需要安装 PyPDF2

---

### 2. check_quality.py — 综合质量检查

```bash
# 检查单个文件
python scripts/check_quality.py 译文/第1章.md

# 批量检查
python scripts/check_quality.py 译文/*.md

# 检查目录下所有md文件
python scripts/check_quality.py 译文/
```

**检测项目**：

| 检测项 | 说明 |
|--------|------|
| $符号配对 | 检测未闭合的单个$和$$块（自动跳过\$转义） |
| 标题层级 | 章标题应为`##`，节标题应为`###`，一级标题不应出现在文件中间 |
| 连续空行 | 检测连续3行以上空行 |
| 术语遗漏 | 检测未翻译的Activity/Exercise |
| 美元符号 | 检测未转义的美元金额（$数字,数字模式） |

**输出示例**：

```
❌ 第1章.md:
   - 未闭合的单个$，开始于第45行
   - 第12行: 可能存在未转义的美元符号（使用\$转义）
✅ 第2章.md
==================================================
检查完成: 2 个文件, 1 个通过, 2 个问题
```

---

### 3. check_terms.py — 术语检查与自动修复

```bash
# 检查术语一致性
python scripts/check_terms.py 译文/ --glossary my_glossary.json

# 预览修复（不修改文件）
python scripts/check_terms.py 译文/ --glossary my_glossary.json --dry-run

# 自动修复
python scripts/check_terms.py 译文/ --glossary my_glossary.json --fix

# 输出报告
python scripts/check_terms.py 译文/ --glossary my_glossary.json --output report.txt
```

**检测项目**：

- 未翻译的英文术语（对比术语表）
- 译法变体（如"活动"应为"互动练习"，"最大公因子"应为"最大公约数"）
- 自动修复模式支持替换非标准译法

**内置译法变体映射**：

| 非标准译法 | 标准译法 |
|------------|----------|
| 活动 | 互动练习 |
| 运算法则 | 算法 |
| 最大公因子 | 最大公约数 |
| 最小公倍式 | 最小公倍数 |

---

### 4. protect_formulas.py — LaTeX公式保护与回填

适用于使用外部翻译工具（如机器翻译）时，避免公式被破坏。

```bash
# 提取公式（生成占位符文件和公式字典）
python scripts/protect_formulas.py extract input.md

# 输出：
#   input.protected.md （公式替换为占位符的文本）
#   input.formulas.json （公式字典）

# 翻译占位符文件后，回填公式
python scripts/protect_formulas.py restore input.protected.md

# 输出：
#   input.protected.restored.md （公式回填后的文本）
```

**工作原理**：

1. `extract`：将 `$...$` 和 `$$...$$` 替换为 `@@FORMULA_INLINE_1@@` 等占位符
2. 翻译占位符文件（翻译工具不会破坏占位符）
3. `restore`：将占位符替换回原始公式

---

### 5. translation_memory.py — 翻译记忆库

```bash
# 从已译文档构建记忆库
python scripts/translation_memory.py build 译文/*.md --glossary my_glossary.json

# 输出：translation_memory.json

# 匹配记忆库（查找相似句对）
python scripts/translation_memory.py match "待匹配的文本" --memory translation_memory.json

# 从文件匹配
python scripts/translation_memory.py match 新章节.md --memory translation_memory.json

# 设置相似度阈值（默认0.7）
python scripts/translation_memory.py match 新章节.md --threshold 0.8

# 检查多个文件的术语一致性
python scripts/translation_memory.py check 译文/*.md --memory translation_memory.json
```

**功能说明**：

- **build**：从已译文档提取句子和术语，构建记忆库
- **match**：基于相似度（SequenceMatcher）模糊匹配相似句对，提示一致译法
- **check**：检查多个文件之间的术语使用一致性

---

### 6. quality_score.py — 翻译质量评分

```bash
# 基本评分
python scripts/quality_score.py 译文/*.md

# 带术语表评分
python scripts/quality_score.py 译文/*.md --glossary my_glossary.json

# 输出JSON报告
python scripts/quality_score.py 译文/*.md --output report.json

# 设置及格分数线（默认80）
python scripts/quality_score.py 译文/*.md --threshold 85
```

**评分维度**：

| 维度 | 权重 | 检测内容 |
|------|------|----------|
| 术语一致性 | 30% | 未翻译术语、译法变体 |
| 公式完整性 | 30% | $符号配对、美元符号转义、LaTeX命令完整性 |
| 格式规范度 | 20% | 标题层级、连续空行、代码块闭合 |
| 章节完整度 | 20% | 章标题、证明结束标记、定理编号 |

**输出示例**：

```
======================================================================
翻译质量评分报告
======================================================================
文件                                总分   术语   公式   格式   章节  问题
----------------------------------------------------------------------
第1章.md                           92.5     90     95     95     90    2
第2章.md                           88.0     85     90     90     85    3
----------------------------------------------------------------------
平均分数: 90.3 | 及格: 2/2 (分数线: 80)

改进建议:
  - 最薄弱环节: 术语一致性 (平均 87.5分)，建议重点改进
  - 术语问题: 使用 translation_memory.py check 检查术语一致性，统一译法
```

---

### 7. progress_tracker.py — 翻译进度追踪

```bash
# 生成进度报告
python scripts/progress_tracker.py 译文/

# 输出到文件
python scripts/progress_tracker.py 译文/ --output progress.md
```

**报告内容**：

- 总览：已翻译文件数、总字符数、总行数、公式总数
- 按部分统计：每个部分的章节数和字符数
- 章节详情：每章的字数、是否包含习题
- 检查项：哪些章节缺少习题部分

---

### 8. package.py — 批量交付打包

```bash
# 一键执行所有操作
python scripts/package.py 译文/*.md --all

# 仅生成目录索引
python scripts/package.py 译文/*.md --toc

# 仅生成翻译说明
python scripts/package.py 译文/*.md --notes --glossary my_glossary.json

# 仅合并完整译稿
python scripts/package.py 译文/*.md --merge

# 仅打包zip
python scripts/package.py 译文/*.md --zip

# 指定输出目录
python scripts/package.py 译文/*.md --all --output-dir 交付/
```

**输出文件**：

| 文件 | 说明 |
|------|------|
| `目录索引.md` | 全书目录，含章节链接、节标题、字数统计 |
| `翻译说明.md` | 术语约定、格式约定、核心术语表、翻译统计 |
| `完整译稿.md` | 合并所有章节的完整Markdown文件 |
| `翻译交付包.zip` | 打包所有译文文件+目录+说明 |

---

## 📋 标准工作流程

### 完整翻译项目流程

```
1. 预处理
   ├─ extract_pdf.py --info 确认总页数
   ├─ extract_pdf.py 提取并分割章节
   └─ 复制 glossary_template.json 建立术语表

2. 逐章翻译
   ├─ 使用 chapter_template.md 模板
   ├─ 公式用LaTeX，美元用\$转义
   ├─ check_quality.py 即时检查
   └─ 每完成一部分更新 translation_memory.py

3. 部分复核
   ├─ check_terms.py 检查术语
   ├─ check_quality.py 批量检查格式
   └─ quality_score.py 质量评分

4. 最终交付
   ├─ progress_tracker.py 进度报告
   ├─ quality_score.py 最终评分
   └─ package.py --all 打包交付
```

---

## ⚠️ 关键注意事项

### 1. 不要依赖Read工具判断PDF结束

Read工具有token上限（约26万tokens，对应PDF约500页）。大PDF必须用 `extract_pdf.py --info` 确认总页数，避免遗漏后续章节。

### 2. 美元符号必须转义

文中的美元金额一律使用 `\$`，否则会被Markdown解析器误认为LaTeX公式开始，导致$符号配对错误。

**错误写法**：
```markdown
价格是 $1,234.56 美元
```

**正确写法**：
```markdown
价格是 \$1,234.56 美元
```

### 3. 脚注标记与公式间加空格

脚注标记 `$^1$` 与后续公式之间必须加空格，否则 `$$` 会被误解析为块数学公式开始。

**错误写法**：
```markdown
根据定理$^1$$x + y = z$，我们得到...
```

**正确写法**：
```markdown
根据定理$^1$ $x + y = z$，我们得到...
```

### 4. 每章即时检查

不要等到全部译完再复核。每章译完立即运行 `check_quality.py`，及早发现问题，避免问题累积。

### 5. 术语表前置

翻译开始前确认核心术语译法，避免中途调整导致全局替换。使用 `check_terms.py --fix` 可以批量修复，但仍建议提前确认。

---

## ❓ 常见问题

### Q: PyPDF2提取的文本格式混乱怎么办？

A: PyPDF2对复杂排版的PDF提取效果有限。可以尝试：
1. 使用 `pdfplumber` 替代PyPDF2（提取效果更好）
2. 手动调整分割后的章节文本
3. 对于扫描版PDF，需要先OCR处理

### Q: 公式保护工具会漏掉某些公式吗？

A: `protect_formulas.py` 使用正则匹配 `$...$` 和 `$$...$$`，对于嵌套公式或特殊格式可能漏匹配。建议使用后检查 `formulas.json` 中的公式数量是否合理。

### Q: 质量评分的权重可以调整吗？

A: 可以。编辑 `quality_score.py` 中的 `total_score` 计算部分，调整各维度权重即可。

### Q: 如何添加自定义术语到术语表？

A: 编辑 `glossary_template.json`，添加 `"英文术语": "中文译法"` 键值对即可。注意跳过以下划线开头的键（这些是说明性字段）。

### Q: 翻译记忆库的匹配准确率如何？

A: 使用Python标准库的 `SequenceMatcher`，基于字符级相似度。对于结构相似的句子匹配效果较好，对于完全不同的表达可能漏匹配。建议将阈值设为0.7-0.8。

---

## 📁 目录结构

```
math-book-translator/
├── README.md                     # 本文件（使用说明）
├── SKILL.md                      # Skill工作流程说明（AI读取）
├── scripts/
│   ├── extract_pdf.py            # PDF提取与章节分割
│   ├── check_quality.py          # 综合质量检查
│   ├── check_terms.py            # 术语检查与修复
│   ├── protect_formulas.py       # 公式保护与回填
│   ├── translation_memory.py     # 翻译记忆库
│   ├── quality_score.py          # 翻译质量评分
│   ├── progress_tracker.py       # 翻译进度追踪
│   └── package.py                # 批量交付打包
└── assets/
    ├── chapter_template.md       # 章节翻译模板
    └── glossary_template.json    # 术语表模板
```

---

## 📝 版本信息

- 版本：1.0
- 适用场景：数学教材/专著中英互译
- Python要求：3.7+
- 可选依赖：PyPDF2

---

## 🤝 使用建议

1. **从小项目开始**：先翻译1-2章熟悉工具流程，再开始全书翻译
2. **定期备份**：译文文件建议使用Git或云存储备份，避免意外丢失
3. **术语表迭代**：翻译过程中持续更新术语表，每完成一部分就更新一次
4. **质量阈值**：建议将质量评分及格线设为85分，低于85分的章节必须返工
5. **交付前终检**：交付前务必运行 `check_quality.py` 和 `quality_score.py` 全量检查
