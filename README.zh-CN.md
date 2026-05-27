# ResearchDraft.ai

中文说明 | [English](README.md)

ResearchDraft.ai 是一个本地优先的科研论文初稿工作流工具，用于把研究 idea、数据描述和参考文献来源转化为可审查、可修改、可编译的论文初稿材料包。

它适合希望使用 AI 辅助科研写作，但又希望保留文献、LaTeX、BibTeX、PDF 和质量检查控制权的研究者。

## 核心功能

- 从指定 Zotero collection 导入项目文献。
- 当本地文献不足时，支持外部学术元数据检索补充。
- 生成英文、面向可发表论文结构的研究大纲。
- 导出 Markdown、LaTeX、BibTeX 和 PDF。
- 为单篇参考文献生成 HTML 总结。
- 生成质量检查报告，检查章节一致性、引用和 BibTeX 对应关系、URL、公式和 PDF 编译状态。
- 静态前端加本地 Flask 后端，便于本地测试和二次开发。

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

## 一键本地安装

环境要求：

- Windows PowerShell
- Python 3.10+
- 可选但推荐：MiKTeX 或 TeX Live，用于 PDF 生成

运行：

```powershell
git clone https://github.com/xiejhhhhhh/ResearchDraft.ai.git
cd ResearchDraft.ai
.\scripts\setup_local.ps1
```

该脚本会自动：

- 创建 `.venv`
- 安装 Python 依赖
- 如果还没有 `.env`，则从 `research_paper_agent\.env.example` 复制生成
- 运行后端基础检查

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

不要提交 `.env`。

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
3. 填写：
   - 研究 idea；
   - 研究领域或研究目标；
   - 数据描述；
   - 目标期刊，如果已有；
   - 输出格式，通常选择 `tex`。
4. 提交表单。
5. 下载生成文件：
   - `.md`
   - `.tex`
   - `.bib`
   - `.pdf`
   - 单篇文献 HTML 总结
   - 质量检查 JSON

生成文件保存在：

```text
research_paper_agent\data\
```

该目录已被 git 忽略。

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

如果已安装 Node.js，可以检查前端语法：

```powershell
cd docs
node --check app.js
```

## 安全说明

不要提交：

- `research_paper_agent/.env`
- 生成的草稿、PDF、BibTeX 和文献总结
- `research_paper_agent/data/submissions.json`
- 缓存文件
- `.tools/` 下的本地工具

仓库中的 `.gitignore` 已经包含这些路径。

## 当前 MVP 边界

MVP2 是一个本地单用户科研写作工作流，不是完整的云端多用户 SaaS。

如果后续要做商业化托管版，需要继续补充：

- 用户登录
- 用户和项目隔离
- 下载鉴权
- API 限流
- 后台任务队列
- 云端存储策略
- 审计日志
- 隐私政策和数据保留策略

