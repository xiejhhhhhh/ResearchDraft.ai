# ResearchDraft.ai

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Backend-Flask-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![LaTeX](https://img.shields.io/badge/Export-LaTeX%20%2B%20PDF-008080)](https://www.latex-project.org/)
[![Zotero](https://img.shields.io/badge/Literature-Zotero-CC2936)](https://www.zotero.org/)
[![Local First](https://img.shields.io/badge/Mode-Local--First-2E7D32)](#为什么是-researchdraftai)

中文说明 | [English](README.md)

ResearchDraft.ai 是一个本地优先的科研写作工作流工具，用于把研究 idea、data description、Zotero 或外部检索文献整理成可审查、可修改、可编译的 draft package。

它不是“AI 代写论文”工具。它的目标是帮助科研用户把早期写作材料整理成透明、可追踪、可人工修改的论文初稿材料包，包括 Markdown、LaTeX、BibTeX、PDF、单篇文献总结和质量检查报告。

## 为什么是 ResearchDraft.ai

科研写作的起点通常不是一段完整 prompt，而是分散的信息：研究想法、数据说明、Zotero 文件夹、公开数据链接、方法草图和目标期刊要求。ResearchDraft.ai 试图把这些信息连接成一个本地流程，让生成结果不是黑箱回答，而是可检查、可修改、可复现的材料包。

当前 MVP 面向重视以下能力的科研用户：

- 同时基于 idea 和 data description 生成论文初稿；
- 通过 Zotero collection 控制每篇文章使用哪些文献；
- 当本地参考文献不足时，可以用外部学术检索补充；
- 通过 BibTeX 和 LaTeX citation key 保持引用可追踪；
- 生成 PDF 方便人工检阅；
- 在云端商业化之前，先跑通本地可控流程。

## 核心功能

- 从指定 Zotero collection 导入项目文献。
- 在文献不足时支持外部学术检索补充。
- 生成英文、面向可发表论文结构的研究初稿。
- 导出 Markdown、LaTeX、BibTeX 和 PDF。
- 为单篇参考文献生成 HTML 总结。
- 生成质量检查报告，检查章节一致性、引用与 BibTeX 对应关系、URL 处理、公式格式和 PDF 编译状态。
- 静态前端加本地 Flask 后端，方便本地测试和二次开发。

## 项目结构

```text
docs/                         静态前端和文档页面
research_paper_agent/         Flask 后端和论文初稿生成引擎
research_paper_agent/export/  BibTeX、LaTeX 文本处理和 PDF 编译
research_paper_agent/literature/
                              Zotero、外部检索和参考文献权重
research_paper_agent/generation/
                              Prompt 构建
research_paper_agent/validation/
                              质量检查器
scripts/                      本地安装、启动、检查和结构文档脚本
PROJECT_SUMMARY.md            项目接手说明
```

可以打开 `docs/code_structure.html` 查看当前 Python 模块结构图。

## 环境要求

- Windows PowerShell
- Python 3.10+
- 可选但推荐：MiKTeX 或 TeX Live，用于 PDF 编译
- 可选：Node.js，用于前端语法检查
- 可选：Zotero 账号和 API key，用于按 collection 导入文献

## 一键本地安装

```powershell
git clone https://github.com/xiejhhhhhh/ResearchDraft.ai.git
cd ResearchDraft.ai
.\scripts\setup_local.ps1
```

该脚本会创建虚拟环境、安装 Python 依赖、在需要时准备本地 `.env` 模板，并运行基础后端检查。

然后编辑：

```text
research_paper_agent\.env
```

至少配置一个 AI 服务。如果使用 Zotero 模式，还需要配置 Zotero：

```text
VOLCENGINE_API_KEY=your_key_here
VOLCENGINE_MODEL_ID=your_model_or_endpoint_id
ZOTERO_LIBRARY_ID=your_zotero_library_id
ZOTERO_API_KEY=your_zotero_api_key
ZOTERO_LIBRARY_TYPE=user
```

## 启动服务

终端 1：

```powershell
.\scripts\start_backend.ps1
```

终端 2：

```powershell
.\scripts\start_frontend.ps1
```

浏览器打开：

```text
http://127.0.0.1:8000
```

后端健康检查：

```text
http://127.0.0.1:9000/api/status
```

Zotero collection 列表：

```text
http://127.0.0.1:9000/api/zotero/collections
```

## 使用流程

1. 启动后端和前端。
2. 选择文献来源：
   - Zotero collection，或
   - 外部学术检索。
3. 填写研究 idea、研究领域或目标、数据描述、目标期刊和输出格式。
4. 提交表单。
5. 查看并下载生成材料：
   - `.md`
   - `.tex`
   - `.bib`
   - `.pdf`
   - 单篇文献 HTML 总结
   - 质量检查 JSON

生成文件会保存在本地：

```text
research_paper_agent\data\
```

## 运行检查

```powershell
.\scripts\run_checks.ps1
```

手动运行后端检查：

```powershell
cd research_paper_agent
python -m py_compile service.py api.py models.py literature\external_search.py literature\zotero.py literature\ranking.py generation\prompts.py export\bibtex.py export\latex_text.py export\pdf.py validation\quality_gate.py
python -m unittest tests.test_quality_gate tests.test_export_helpers tests.test_literature_and_prompts
```

如果已经安装 Node.js，可以检查前端语法：

```powershell
cd docs
node --check app.js
```

## 产品方向

当前版本聚焦本地单用户科研写作流程，用于验证从 idea、data description、文献组织到 draft package 的完整路径。后续托管版本会在此基础上补齐多用户协作、数据治理和可信 AI 使用能力。

后续如果开发商业化托管版，重点应该补齐科研用户信任和生产环境能力：

- 用户登录和项目级用户隔离；
- 下载鉴权和 API 限流；
- AI 与文献检索的费用统计；
- 用户可控的数据删除和保留策略；
- 外部 URL 与文件访问中的 SSRF 防护；
- 处理上传或检索文本时的 prompt injection 防护；
- 用于配置 AI key、Zotero、LaTeX 和 PDF 编译的 Setup 页面；
- Trust Dashboard，用于展示引用溯源、AI disclosure、来源证据和质量检查结果。

不同地区科研用户关注点不同。欧美用户通常更在意 data privacy、citation traceability 和 AI disclosure；中国用户通常更在意可用性、中文环境成本、Zotero 便利性和本地部署。ResearchDraft.ai 的路线应同时保留本地透明性，并逐步准备更安全的托管体验。

## 适用边界

ResearchDraft.ai 适合作为科研规划和初稿整理助手。它帮助用户把结构化输入转化为可审查、可修改、可引用、可编译的材料包，但不能替代专家判断、领域验证、实验设计、作者责任或期刊合规审查。
