# 众益会计专业知识库

四川众益会计师事务所专业知识库，服务于审计、税务、咨询三大业务主线，为AI智能化审计工具提供底层知识支撑。

在线访问地址：https://auctioneer2022.github.io/knowledge-base/

---

## 一、项目概述

本项目是基于 MkDocs Material 构建的静态文档站点，采用 Markdown + YAML Front Matter 作为内容载体，通过 GitHub Actions 实现自动化构建与部署。知识库覆盖法律法规、会计准则、审计准则、税法法规、行业知识、实务模板、案例库、工具方法、培训资源九大知识域，当前已收录198项知识条目，整体完成率93.0%。

### 1.1 技术栈

| 组件 | 技术选型 | 版本要求 | 说明 |
|------|----------|----------|------|
| 静态站点生成器 | MkDocs | 最新稳定版 | Markdown 静态网站生成 |
| 主题 | MkDocs Material | 最新稳定版 | 响应式主题，支持中文搜索 |
| 运行环境 | Python | 3.12+ | 构建依赖 |
| 部署平台 | GitHub Pages | — | 免费托管，支持自定义域名 |
| CI/CD | GitHub Actions | — | 自动化构建与部署 |
| 版本控制 | Git | — | 内容版本管理 |
| 内容格式 | Markdown + YAML Front Matter | — | 结构化内容存储 |

### 1.2 核心特性

- **中文全文搜索**：基于 MkDocs Material 内置搜索插件，支持中文分词、搜索建议、关键词高亮
- **响应式导航**：顶部标签页导航（sticky）、章节侧边栏、目录展开、返回顶部按钮
- **深浅色模式切换**：支持浅色/深色主题自适应
- **Markdown 增强**：支持提示框（admonition）、可折叠内容、代码块高亮、标签页切换、表格、目录永久链接
- **一键编辑**：每页底部集成"编辑此页"按钮，直达 GitHub 源文件编辑界面
- **自动化部署**：推送至 `main` 分支即自动触发构建与部署

---

## 二、环境搭建指南

### 2.1 前置要求

- Python 3.12 或更高版本
- Git（用于版本控制）
- 操作系统：Windows / macOS / Linux 均可

### 2.2 本地开发环境配置

#### 步骤 1：克隆仓库

```bash
git clone https://github.com/auctioneer2022/knowledge-base.git
cd knowledge-base
```

#### 步骤 2：创建虚拟环境（推荐）

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

#### 步骤 3：安装依赖

```bash
pip install mkdocs-material
```

#### 步骤 4：本地预览

```bash
mkdocs serve
```

本地预览默认地址：`http://127.0.0.1:8000`

支持实时重载（Live Reload），保存 Markdown 文件后浏览器自动刷新。

#### 步骤 5：构建静态站点

```bash
mkdocs build
```

构建输出目录为 `site/`，包含完整的静态 HTML 文件。

### 2.3 依赖版本锁定

建议在项目根目录创建 `requirements.txt`：

```text
mkdocs-material>=9.0.0
```

安装时执行：

```bash
pip install -r requirements.txt
```

---

## 三、项目配置详情

### 3.1 核心配置文件：`mkdocs.yml`

`mkdocs.yml` 是 MkDocs 的全局配置文件，控制站点元数据、主题、导航、插件和 Markdown 扩展。

#### 3.1.1 站点元数据

```yaml
site_name: 众益会计专业知识库
site_description: 四川众益会计师事务所专业知识库 - 审计、税务、咨询业务知识体系
site_author: 四川众益会计师事务所
site_url: https://auctioneer2022.github.io/knowledge-base/
```

| 参数 | 含义 | 自定义方法 |
|------|------|----------|
| `site_name` | 站点标题，显示在浏览器标签页和导航栏 | 直接修改 |
| `site_description` | 站点描述，用于 SEO | 直接修改 |
| `site_author` | 作者信息 | 直接修改 |
| `site_url` | 站点根 URL | 更换域名时修改 |

#### 3.1.2 主题配置

```yaml
theme:
  name: material
  language: zh
  palette:
    - scheme: default
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-7
        name: 切换至深色模式
    - scheme: slate
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-4
        name: 切换至浅色模式
  features:
    - navigation.tabs
    - navigation.tabs.sticky
    - navigation.sections
    - navigation.expand
    - navigation.indexes
    - navigation.top
    - search.suggest
    - search.highlight
    - content.code.copy
    - content.action.edit
```

**功能特性说明**：

| 特性 | 含义 |
|------|------|
| `navigation.tabs` | 启用顶部标签页导航 |
| `navigation.tabs.sticky` | 标签页滚动时固定顶部 |
| `navigation.sections` | 章节级导航展开 |
| `navigation.expand` | 默认展开导航树 |
| `navigation.indexes` | 目录索引页支持 |
| `navigation.top` | 返回顶部按钮 |
| `search.suggest` | 搜索建议 |
| `search.highlight` | 搜索结果关键词高亮 |
| `content.code.copy` | 代码块一键复制 |
| `content.action.edit` | 页面底部显示编辑按钮 |

**自定义主题颜色**：

修改 `primary` 和 `accent` 值可更换主题色，可选值包括：`red`、`pink`、`purple`、`deep purple`、`indigo`、`blue`、`light blue`、`cyan`、`teal`、`green`、`light green`、`lime`、`yellow`、`amber`、`orange`、`deep orange`、`brown`、`grey`、`blue grey`、`white`、`black`。

#### 3.1.3 插件配置

```yaml
plugins:
  - search:
      lang: zh
  - tags
```

| 插件 | 功能 | 配置说明 |
|------|------|----------|
| `search` | 全文搜索 | `lang: zh` 启用中文分词 |
| `tags` | 标签系统 | 为文档添加标签，支持按标签筛选 |

#### 3.1.4 Markdown 扩展

```yaml
markdown_extensions:
  - admonition
  - pymdownx.details
  - pymdownx.superfences
  - pymdownx.highlight:
      anchor_linenums: true
  - pymdownx.inlinehilite
  - pymdownx.tabbed:
      alternate_style: true
  - tables
  - toc:
      permalink: true
  - attr_list
  - def_list
```

| 扩展 | 功能 | 使用场景 |
|------|------|----------|
| `admonition` | 提示框（警告、注意、提示等） | 强调重要信息 |
| `pymdownx.details` | 可折叠内容块 | 隐藏次要内容，保持页面简洁 |
| `pymdownx.superfences` | 增强代码块 | 支持代码块内嵌语法高亮 |
| `pymdownx.highlight` | 语法高亮 | 代码块行号、语言标识 |
| `pymdownx.inlinehilite` | 行内代码高亮 | 行内代码片段着色 |
| `pymdownx.tabbed` | 标签页切换 | 多方案并排展示 |
| `tables` | Markdown 表格 | 数据对比、列表展示 |
| `toc` | 目录生成 | 自动生成页面目录，支持永久链接 |
| `attr_list` | 属性列表 | 为 Markdown 元素添加 HTML 属性 |
| `def_list` | 定义列表 | 术语解释、概念定义 |

#### 3.1.5 导航配置

```yaml
nav:
  - 首页: index.md
  - 法律法规:
    - 01-法律法规/index.md
    - 会计法律:
      - 01-法律法规/01-会计法律/index.md
    # ... 更多导航项
```

**导航配置规则**：

- 导航层级由 YAML 缩进控制
- 每个导航项格式为 `显示名称: 文件路径`
- 文件路径相对于 `docs/` 目录
- 新增知识模块时，需在此配置对应导航项

### 3.2 CI/CD 配置：`.github/workflows/deploy.yml`

GitHub Actions 工作流配置，实现推送至 `main` 分支即自动构建部署。

```yaml
name: Deploy MkDocs to GitHub Pages

on:
  push:
    branches:
      - main
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install MkDocs and dependencies
        run: |
          pip install mkdocs-material

      - name: Build site
        run: |
          mkdocs build

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: site/

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

**工作流说明**：

| 阶段 | 说明 |
|------|------|
| 触发条件 | `push` 至 `main` 分支，或手动触发 `workflow_dispatch` |
| 构建环境 | `ubuntu-latest` + Python 3.12 |
| 构建步骤 | 检出代码 → 安装依赖 → `mkdocs build` → 上传制品 |
| 部署步骤 | 使用 `actions/deploy-pages@v4` 部署至 GitHub Pages |
| 并发控制 | 同一组部署任务排队执行，避免冲突 |

### 3.3 Git 忽略配置：`.gitignore`

```gitignore
# Python
__pycache__/
*.py[cod]
*.pyo
.venv/
venv/

# MkDocs build output
site/

# OS files
Thumbs.db
.DS_Store
desktop.ini

# IDE
.vscode/
.idea/
*.swp
*.swo

# Temporary files
*.tmp
*.bak
```

**注意**：`site/` 目录为 MkDocs 构建输出，已加入 `.gitignore`，不应提交至版本控制。

---

## 四、使用指南

### 4.1 常用命令

| 命令 | 功能 | 示例 |
|------|------|------|
| `mkdocs serve` | 启动本地开发服务器 | `mkdocs serve --dev-addr 0.0.0.0:8000` |
| `mkdocs build` | 构建静态站点 | `mkdocs build --clean` |
| `mkdocs gh-deploy` | 直接部署至 GitHub Pages | `mkdocs gh-deploy` |
| `mkdocs new dir` | 创建新项目 | `mkdocs new my-project` |

### 4.2 内容编写规范

#### 4.2.1 文件格式

所有知识内容以 Markdown（`.md`）格式存储于 `docs/` 目录，每个文件头部必须包含 YAML Front Matter：

```markdown
---
id: CAS-14-001
title: 企业会计准则第14号——收入
category: 会计准则/具体准则
---

# 企业会计准则第14号——收入

正文内容...
```

**Front Matter 字段说明**：

| 字段 | 必填 | 说明 | 示例 |
|------|------|------|------|
| `id` | 是 | 知识条目唯一编码 | `CAS-14-001` |
| `title` | 是 | 文档标题 | `企业会计准则第14号——收入` |
| `category` | 是 | 分类路径 | `会计准则/具体准则` |
| `status` | 否 | 有效性状态 | `现行有效`、`已废止` |
| `effective_date` | 否 | 生效日期 | `2017-07-01` |
| `related_ids` | 否 | 关联条目编码 | `[CAS-14-G01, TAX-02-015]` |
| `keywords` | 否 | 关键词 | `[收入确认, 五步法]` |

#### 4.2.2 知识编码体系

每条知识采用统一编码：`领域编码-模块编号-条目编号`

| 编码前缀 | 知识领域 | 示例 |
|----------|----------|------|
| LAW | 法律法规 | `LAW-01-001` |
| CAS | 会计准则 | `CAS-01-001` |
| CSA | 审计准则 | `CSA-1101-001` |
| TAX | 税法法规 | `TAX-01-001` |
| IND | 行业知识 | `IND-01-001` |
| TPL | 实务模板 | `TPL-01-001` |
| CASE | 案例库 | `CASE-01-001` |
| MTH | 工具方法 | `MTH-01-001` |
| TRN | 培训资源 | `TRN-01-001` |

#### 4.2.3 索引页格式

每个子模块的 `index.md` 应包含：

1. YAML Front Matter（id、title、category）
2. 模块概述
3. 已收录文件表格（含编码、文件名称、发文字号、状态）
4. 说明事项

示例：

```markdown
---
id: LAW-01-INDEX
title: 会计法律
category: 法律法规/会计法律
---

# 会计法律

收录会计领域核心法律文件。

## 已收录文件

| 编码 | 文件名称 | 发文字号 | 状态 |
|------|----------|----------|------|
| LAW-01-001 | [中华人民共和国会计法](中华人民共和国会计法.md) | 主席令第9号（2024修订） | 现行有效 |

## 说明

1. 本模块收录与会计执业直接相关的法律文件。
2. 所有文件均以财政部、国务院等权威来源为准。
```

### 4.3 新增内容流程

```
1. 确定目标模块目录（如 docs/02-会计准则/02-具体准则/）
2. 创建 Markdown 文件，填写 YAML Front Matter 元数据
3. 按照既有格式录入法规/准则正文
4. 更新对应模块的 index.md 索引页（添加文件链接）
5. 如需新增导航项，更新 mkdocs.yml 中的 nav 配置
6. 本地预览验证（mkdocs serve）
7. 提交 Git 并推送至 main 分支
```

### 4.4 四层知识架构

| 层级 | 内容 | 说明 | 当前状态 |
|------|------|------|----------|
| 第一层：法规原文层 | 法律法规、准则原文 | 权威、时效、完整 | 基本完成 |
| 第二层：结构化知识层 | 准则解读、法规速查 | 按主题组织的知识模块 | 部分完成 |
| 第三层：场景应用层 | 实务指引、检查清单 | 可直接执行的操作指引 | 开发中 |
| 第四层：AI应用层 | 智能工具、推理引擎 | 未来产品化方向 | 开发中 |

---

## 五、开发规范

### 5.1 代码风格要求

本项目以 Markdown 内容为主，无传统意义上的代码。内容编写需遵循以下规范：

**Markdown 格式规范**：

- 使用 ATX 风格标题（`#` 前缀），一级标题对应页面主标题
- 列表使用 `-` 无序列表或 `1.` 有序列表，保持层级清晰
- 表格使用标准 Markdown 表格语法，对齐方式保持统一
- 代码块标注语言类型（如 ```python）
- 中文与英文、数字之间保留一个空格

**YAML Front Matter 规范**：

- 字段顺序：id → title → category → status → effective_date → related_ids → keywords
- 字符串值不加引号（除非包含特殊字符）
- 数组使用方括号 `[item1, item2]`

### 5.2 Git 提交规范

采用 Conventional Commits 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**常用类型**：

| 类型 | 含义 | 示例 |
|------|------|------|
| `feat` | 新功能/新内容 | `feat(会计准则): 新增CAS14收入准则全文` |
| `fix` | 修复错误 | `fix(审计准则): 修正CSA1101条文编号` |
| `docs` | 文档更新 | `docs(首页): 更新收录进度表` |
| `style` | 格式调整 | `style(法律法规): 修复表格对齐` |
| `refactor` | 重构 | `refactor(导航): 调整mkdocs.yml层级结构` |
| `chore` | 构建/工具 | `chore(ci): 更新GitHub Actions配置` |

**提交示例**：

```bash
git commit -m "feat(行业知识): 新增制造业成本核算专题

- 补充品种法、分批法、分步法详解
- 添加成本控制策略与差异分析
- 更新制造业index.md索引页"
```

### 5.3 分支管理策略

本项目采用 **GitHub Flow** 简化分支模型：

```
main 分支（保护分支）
  ↑
feature/xxx 特性分支
  ↑
本地开发
```

**分支规则**：

- `main` 为默认分支，受保护，仅通过 Pull Request 合并
- 新内容开发从 `main` 切出 `feature/<模块>-<简述>` 分支
- 特性分支开发完成后，提交 Pull Request 并请求代码审查
- 审查通过后合并至 `main`，自动触发部署

**分支命名示例**：

```
feature/cas-new-standards
feature/ind-manufacturing
fix/law-link-correction
```

### 5.4 协作流程

```
1. Fork 仓库 或 获取写入权限
2. 从 main 切出 feature 分支
3. 本地开发并提交（遵循提交规范）
4. 推送 feature 分支至远程
5. 创建 Pull Request，填写变更说明
6. 指定审查人进行代码审查
7. 审查通过后合并至 main
8. GitHub Actions 自动部署
```

### 5.5 内容审核标准

新增知识条目需经过以下审核：

| 审核项 | 标准 | 责任人 |
|--------|------|--------|
| 法规时效性 | 确保收录现行有效版本，废止文件标注状态 | 法规专员 |
| 条文准确性 | 与权威来源（财政部、中注协等）核对 | 领域专家 |
| 格式规范性 | 符合 Markdown 格式和 Front Matter 规范 | 技术负责人 |
| 链接完整性 | 索引页链接可正常跳转 | 提交者 |

---

## 六、收录进度

| 知识领域 | 计划数量 | 已收录 | 完成率 |
|----------|----------|--------|--------|
| 法律法规 | 19部 | 19部 | 100% |
| 会计准则 | 104项 | 92项 | 88.5% |
| 审计准则 | 70项 | 67项 | 95.7% |
| 税法法规 | 11部 | 11部 | 100% |
| 行业知识 | 17项 | 17项 | 100% |
| 实务模板 | — | — | 开发中 |
| 案例库 | — | — | 开发中 |
| 工具方法 | 12项 | 12项 | 100% |
| 培训资源 | — | — | 开发中 |
| **合计** | **233项** | **218项** | **93.6%** |

---

## 七、常见问题

### Q1：本地预览时中文搜索不生效？

确保 `mkdocs.yml` 中搜索插件配置了 `lang: zh`：

```yaml
plugins:
  - search:
      lang: zh
```

### Q2：新增页面后导航不显示？

检查 `mkdocs.yml` 的 `nav` 配置是否包含新页面的路径。MkDocs 不会自动识别未在导航中配置的文件。

### Q3：构建时提示 Markdown 扩展错误？

确保已安装 `mkdocs-material`，该主题自带所有所需的 PyMdown 扩展。如使用精简版 MkDocs，需单独安装：

```bash
pip install pymdown-extensions
```

### Q4：如何修改站点图标或 Logo？

在 `mkdocs.yml` 的 `theme` 配置中添加：

```yaml
theme:
  logo: assets/logo.png
  favicon: assets/favicon.ico
```

---

## 八、许可与版权

Copyright &copy; 2026 四川众益会计师事务所

---

## 九、相关链接

- 在线站点：https://auctioneer2022.github.io/knowledge-base/
- GitHub 仓库：https://github.com/auctioneer2022/knowledge-base
- MkDocs 官方文档：https://www.mkdocs.org/
- MkDocs Material 文档：https://squidfunk.github.io/mkdocs-material/