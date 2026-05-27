# ResearchDraft.ai 项目接手说明

更新时间：2026-05-26

## 当前定位

ResearchDraft.ai 是一个本地优先的科研论文初稿工作流 MVP。它的目标不是替研究者“一键完成论文”，而是把用户输入的研究 idea、data description、Zotero collection 或外部检索文献，整理成可审查、可修改、可编译的英文论文初稿包。

当前生成产物包括：

- Markdown 论文大纲
- LaTeX 初稿
- BibTeX 文献库
- PDF 审阅稿
- 单篇参考文献 HTML 总结
- demo data/method Python 脚本
- 质量检查报告 `quality_report_*.json`

本地 Node.js 已安装到：

```text
D:\DraftAI_agent\.tools\node
```

当前检查前端 JS 时可以临时使用：

```powershell
$env:PATH = 'D:\DraftAI_agent\.tools\node;' + $env:PATH
node --check D:\DraftAI_agent\docs\app.js
```

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

## 本地目录

默认项目目录：

```text
D:\DraftAI_agent
```

后端：

```text
D:\DraftAI_agent\research_paper_agent
```

前端：

```text
D:\DraftAI_agent\docs
```

本地 skills 默认安装目录：

```text
D:\Agent_skills
```

已安装但未注册为当前 Codex 内置 skill tool 的本地资料：

```text
D:\Agent_skills\superpowers
D:\Agent_skills\gstack
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
- `docs/index.html`：前端页面
- `docs/app.js`：前端交互、双语文案、提交、下载和结果展示
- `docs/commercial_readiness_plan.md`：商业化优化审查记录

## 本地运行

后端：

```powershell
cd D:\DraftAI_agent\research_paper_agent
python api.py
```

前端：

```powershell
cd D:\DraftAI_agent\docs
python -m http.server 8000
```

访问：

```text
http://127.0.0.1:8000
```

## Phase 1 已完成内容

本轮完成了稳定核心流程的第一步：

1. 新增质量检查器 `validation/quality_gate.py`
2. 每次保存 draft 时自动生成 `quality_report_*.json`
3. API 响应和 `submissions.json` 会记录：
   - `quality_report_file`
   - `quality_status`
   - `quality_error_count`
   - `quality_warning_count`
4. 前端结果区会显示质量检查状态，并提供质量报告下载。
5. 清理了旧版重复的 `process_research_request`，避免后定义覆盖前定义造成维护混乱。
6. 修复了两个由于历史编码损坏造成的 Python 语法错误。
7. 替换了损坏的 `_parse_ai_response` 兜底解析函数。
8. `.gitignore` 已加入生成文件、用户提交记录、PDF cache、literature summaries 和 Python cache。
9. 本地安装 Node.js，并完成 `docs/app.js` 语法检查。
10. 从 `service.py` 拆出第一批 export 模块：
    - `export/bibtex.py`
    - `export/latex_text.py`
    - `export/pdf.py`
11. 新增 `tests/test_export_helpers.py`，覆盖 BibTeX key、BibTeX 输出、URL 包装和 LaTeX 特殊字符转义。
12. 从 `service.py` 拆出 literature 和 generation 模块：
    - `literature/external_search.py`
    - `literature/zotero.py`
    - `literature/ranking.py`
    - `generation/prompts.py`
13. 新增 `tests/test_literature_and_prompts.py`，覆盖外部检索 query、metadata 清洗、EasyScholar rank 解析、文献权重和 prompt 必备章节。
14. 新增 `docs/code_structure.html`，由 `scripts/update_code_structure_html.py` 根据 `scripts/code_structure_manifest.json` 自动生成，用来追踪拆分后的代码结构。

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
cd D:\DraftAI_agent\research_paper_agent
python -m py_compile service.py api.py models.py validation\quality_gate.py
```

质量检查器单元测试：

```powershell
cd D:\DraftAI_agent\research_paper_agent
python -m unittest tests.test_quality_gate
```

导出 helper 测试：

```powershell
cd D:\DraftAI_agent\research_paper_agent
python -m unittest tests.test_quality_gate tests.test_export_helpers
```

完整本地单元测试：

```powershell
cd D:\DraftAI_agent\research_paper_agent
python -m unittest tests.test_quality_gate tests.test_export_helpers tests.test_literature_and_prompts
```

前端 JS 语法检查：

```powershell
cd D:\DraftAI_agent\docs
$env:PATH = 'D:\DraftAI_agent\.tools\node;' + $env:PATH
node --check app.js
```

更新代码结构 HTML：

```powershell
cd D:\DraftAI_agent
python scripts\update_code_structure_html.py
```

API 状态：

```powershell
curl http://127.0.0.1:9000/api/status
```

Zotero collection：

```powershell
curl http://127.0.0.1:9000/api/zotero/collections
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
