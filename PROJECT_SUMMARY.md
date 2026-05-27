# ResearchDraft.ai 项目接手说明

更新时间：2026-05-27

## 当前定位

ResearchDraft.ai 是一个本地优先的科研论文初稿工作流 MVP。它的目标不是替研究者"一键完成论文"，而是把用户输入的研究 idea、data description、Zotero collection 或外部检索文献，整理成可审查、可修改、可编译的英文论文初稿包。

当前生成产物包括：

- Markdown 论文大纲
- LaTeX 初稿
- BibTeX 文献库
- PDF 审阅稿
- 单篇参考文献 HTML 总结
- demo data/method Python 脚本
- 质量检查报告 `quality_report_*.json`

## 当前路线

1. 文献来源支持两种模式：
   - Zotero collection 导入
   - 外部学术检索
2. Zotero 模式必须选择 collection，后端只读取该 collection，避免引用其他项目文献。
3. Zotero 文献不足 20 篇时，后端会尝试外部补充。
4. 外部检索模式会尝试直接检索至 20 篇相关文献。
5. 当前不再稳定读取或下载参考文献 PDF，文献总结主要基于 metadata、abstract、期刊信息、引用权重和生成后的引用位置。
6. Data 章节根据用户 data description、公开数据 URL 和参考文献中的数据使用方式归纳，不再强行生成公式。
7. Methods 章节允许生成公式，但必须经过 LaTeX 规范化和 PDF 编译验证。

## 项目目录

```text
research_paper_agent/         Flask 后端和研究初稿生成引擎
research_paper_agent/export/  BibTeX、LaTeX 文本处理和 PDF 编译
research_paper_agent/literature/
                              Zotero、外部检索和参考文献权重
research_paper_agent/generation/
                              Prompt 构建
research_paper_agent/validation/
                              质量检查器
research_paper_agent/tests/   单元测试
docs/                         静态前端和文档页面
scripts/                      本地安装、启动、检查和结构文档脚本
```

## 关键文件

- `research_paper_agent/api.py`：Flask API 入口
- `research_paper_agent/service.py`：当前主业务逻辑，仍然偏大，需要继续拆分
- `research_paper_agent/validation/quality_gate.py`：生成质量检查器
- `research_paper_agent/export/bibtex.py`：BibTeX key 与 BibTeX 文件生成
- `research_paper_agent/export/latex_text.py`：LaTeX 文本转义和 URL 包装
- `research_paper_agent/export/pdf.py`：LaTeX 到 PDF 的本地编译
- `research_paper_agent/literature/external_search.py`：Semantic Scholar、arXiv、Crossref 和可选 SerpApi 的外部文献检索
- `research_paper_agent/literature/zotero.py`：Zotero collection 列表、collection 文献读取和补充文献同步
- `research_paper_agent/literature/ranking.py`：相关度、引用量和 EasyScholar 期刊等级加权
- `research_paper_agent/generation/prompts.py`：论文大纲 prompt 和数据集 URL hint
- `research_paper_agent/literature_analyzer.py`：单篇文献和跨文献归纳
- `research_paper_agent/pipeline_generator.py`：生成数据和方法脚本
- `research_paper_agent/models.py`：请求与 draft 数据结构
- `research_paper_agent/pdf_reader.py`：PDF 全文阅读和章节提取
- `research_paper_agent/check_config.py`：配置检查工具
- `docs/index.html`：前端页面
- `docs/app.js`：前端交互、双语文案、提交、下载和结果展示

## 本地运行

后端：

```powershell
cd research_paper_agent
python api.py
```

前端：

```powershell
cd docs
python -m http.server 8000
```

访问：

```text
http://127.0.0.1:8000
```

## 一键安装

```powershell
git clone https://github.com/xiejhhhhhh/ResearchDraft.ai.git
cd ResearchDraft.ai
.\scripts\setup_local.ps1
```

## Phase 1 已完成内容

本轮完成了稳定核心流程的第一步：

1. 新增质量检查器 `validation/quality_gate.py`
2. 每次保存 draft 时自动生成 `quality_report_*.json`
3. API 响应和 `submissions.json` 会记录质量状态
4. 前端结果区会显示质量检查状态，并提供质量报告下载
5. 清理了旧版重复的 `process_research_request`
6. 修复了历史编码损坏的 Python 语法错误
7. `.gitignore` 已加入生成文件、用户提交记录、PDF cache、literature summaries 和 Python cache
8. 从 `service.py` 拆出第一批 export 模块：`export/bibtex.py`, `export/latex_text.py`, `export/pdf.py`
9. 从 `service.py` 拆出 literature 和 generation 模块
10. 新增单元测试覆盖 export/literature/prompt 核心逻辑
11. 新增 PDF 全文阅读支持 (`pdf_reader.py`)
12. 新增配置检查工具 (`check_config.py`)
13. 新增 Dockerfile 和 Render 部署配置
14. 新增双语前端 (中/英文切换)

## 质量检查器当前检查内容

`quality_gate.py` 当前会检查：

- 生成文件是否存在且非空
- Markdown 与 LaTeX 章节是否大体一致
- LaTeX 章节顺序是否与 Markdown 对齐
- 有 source literature 时是否生成 BibTeX
- LaTeX 中引用的 key 是否存在于 BibTeX
- LaTeX 是否包含 bibliography 命令
- 是否加载 natbib、hyperref、xurl
- equation 环境是否成对
- inline math `$` 是否成对
- URL 是否使用 `href/nolinkurl` 形式
- PDF 是否生成

## 本地验证命令

语法检查：

```powershell
cd research_paper_agent
python -m py_compile service.py api.py models.py validation\quality_gate.py
```

完整本地单元测试：

```powershell
cd research_paper_agent
python -m unittest tests.test_quality_gate tests.test_export_helpers tests.test_literature_and_prompts
```

前端 JS 语法检查：

```powershell
cd docs
node --check app.js
```

## 下一步建议

继续 Phase 1 时，建议按以下顺序拆分 `service.py`：

1. `export/markdown.py`
2. `export/latex.py`
3. `generation/llm_clients.py`
4. `jobs/store.py`
5. `literature/html_summary.py`
6. `generation/parsers.py`

拆分原则：一次只迁移一类函数，迁移后立即运行 `py_compile` 和 `tests.test_quality_gate`，避免大重构后难以定位问题。

## 安全约定

- 不要提交 `research_paper_agent/.env`
- 不要在日志、前端或文档中输出真实 API key
- 不要提交用户生成的 drafts、PDF、BibTeX、HTML summaries、submissions.json
- 上线前必须增加用户登录、项目隔离、下载鉴权、CORS 白名单和限流
