# ResearchDraft.ai 商业化优化审查记录

更新时间：2026-05-26

## 当前结论

ResearchDraft.ai 已经具备本地 MVP 的核心能力：前端提交 idea、data description、Zotero collection 或外部检索来源，后端生成英文论文大纲、Markdown、LaTeX、BibTeX 和 PDF，并保存文献总结 HTML 与生成记录。

但如果面向商业用户，当前最需要优化的不是继续堆叠功能，而是提高可信度、稳定性、可追踪性和用户隔离能力。产品应暂时定位为“科研论文初稿与研究大纲工作流助手”，而不是“完全自动写论文系统”。

## Skill 使用状态

`D:\Agent_skills\superpowers` 和 `D:\Agent_skills\gstack` 已作为本地技能资料安装。当前会话无法把它们作为 Codex 内置 Skill tool 自动调用，只能读取本地 `SKILL.md` 和相关文档后，按其方法论手动执行分析。

若要让 Codex 自动发现这些技能，需要后续把它们安装进当前 Codex runtime 的正式 skill/plugin 路径，或使用这些项目自带的 Codex setup 流程。

## 修改建议总结

1. 文献来源逻辑应保留两类入口：Zotero collection 导入与外部学术检索。Zotero 模式下文献不足 20 篇时自动补齐；外部检索模式下直接检索至 20 篇。
2. 生成内容必须默认英文，且要保证 `.md`、`.tex`、`.bib`、`.pdf` 四类产物章节结构一致。
3. 参考文献总结 HTML 不应伪装成全文阅读结果。当前没有稳定读取 PDF 时，应保留 Abstract Summary、Data Used、Methods、Scientific Results、Keywords、Citation Position，删除容易误导的 Core Figures and Tables、Paper Outline、Current Limitations。
4. Data 章节不再强行生成公式，应根据用户 data description、公开数据 URL 和参考文献中的数据使用方式归纳生成。
5. Methods 章节可以使用公式，但必须经过 LaTeX 规范化，避免 PDF 中公式断裂或不显示。
6. Figure and Table Plan 应作为结果章节后的独立叙事模块，按研究不足、创新点和行文顺序给出 Fig. 1、Fig. 2、Table 1 等图表名称与作用。
7. PDF 必须能正确展示 URL 换行、超链接、正文引用和 References 的链接关系。
8. `.env`、API key、用户生成文件和临时文件必须避免进入公开仓库。

## Superpowers 风格头脑风暴

当前最强的商业切入点不是“自动写完整论文”，而是“把研究者已有的 idea、data 和文献库整理成可审查、可修改、可编译的论文初稿包”。

早期用户应聚焦：

- 博士生、博士后和青年教师，需要把研究想法快速整理成英文论文框架。
- 有 Zotero 文献管理习惯的研究者，希望从文献库直接生成可追踪引用的大纲。
- 课题组内部需要反复修改研究方案、proposal 或 manuscript outline 的用户。

产品的 10 分体验应是：

- 用户输入 idea 和 data description。
- 选择 Zotero collection 或外部检索。
- 系统生成论文大纲、文献总结、BibTeX、LaTeX 和 PDF。
- 每个引用都能追踪到来源。
- PDF 能直接用于导师或合作者审阅。

## gstack CEO Review

商业化的核心差异化应是“可信科研写作工作流”，而不是泛泛的 AI 写作。

需要强化的价值主张：

- 文献来源可控。
- 引用可追踪。
- LaTeX/PDF 可编译。
- 章节结构符合发表论文逻辑。
- 用户能快速看出哪些内容来自文献、哪些内容来自 data description、哪些是模型推断。

建议增加一个 Trust Dashboard：

- 使用了多少篇 Zotero 文献。
- 外部补充了多少篇文献。
- 哪些文献被引用，分别出现在 Introduction、Methods、Discussion 的第几段。
- BibTeX 是否完整。
- PDF 是否成功编译。
- 是否存在 URL、公式、引用或参考文献链接错误。

## gstack Engineering Review

当前后端最大工程风险是 `service.py` 过大，已经混合了 Zotero、外部检索、权重、AI prompt、LaTeX、PDF、文件存储和提交记录逻辑。后续应拆分模块。

建议拆分为：

- `literature/zotero.py`：Zotero collection、item、BibTeX。
- `literature/external_search.py`：外部检索与补齐。
- `literature/ranking.py`：EasyScholar、相关度、引用权重。
- `generation/prompts.py`：论文大纲、文献总结、图表计划 prompt。
- `generation/llm_clients.py`：火山引擎、OpenAI、Claude。
- `export/markdown.py`：Markdown 输出。
- `export/latex.py`：LaTeX 与 BibTeX 输出。
- `export/pdf.py`：xelatex/bibtex 编译。
- `validation/quality_gate.py`：生成后质量检查。
- `jobs/store.py`：任务状态、文件路径、元数据。
- `api/routes.py`：API 路由。

同时应删除重复定义的核心函数，尤其是重复的 `process_research_request`，避免后定义覆盖前定义导致行为不一致。

## gstack Developer Experience Review

当前首次使用门槛偏高：用户需要配置 API key、Zotero、collection、LaTeX、前后端本地服务。商业化前应增加引导。

建议新增：

- `/api/health/full`：检查 AI key、Zotero、LaTeX、EasyScholar、外部检索是否可用。
- 前端 Setup 页面：逐项显示配置状态。
- 示例项目：Potato disease detection 和 AGN prediction。
- 一键测试按钮：生成短版 draft，验证所有链路。
- 错误信息从“Failed to fetch”改为具体诊断，如后端未启动、Zotero 未配置、collection 为空、外部检索失败。

## gstack CSO Security Review

商业化前必须补齐安全能力：

- 用户登录和项目隔离。
- 每个用户只能访问自己的 draft、PDF、BibTeX、HTML summary。
- 下载链接需要签名或鉴权。
- CORS 白名单不能长期保持全开放。
- API 需要速率限制，防止刷接口和刷模型费用。
- 外部 URL 抓取要防 SSRF。
- Prompt 中要加入防 prompt injection 的文献处理规则。
- `.env`、生成文件、缓存、用户数据要在 `.gitignore` 和部署策略中明确排除。
- 生成文件需要设置保留期限和删除策略。

## 施行步骤

### Phase 1：稳定本地核心流程

1. 重构 `service.py`，先拆出 literature、generation、export、validation 四类模块。
2. 修复重复函数定义。
3. 增加质量检查：Markdown/TeX 章节一致、BibTeX key 是否存在、PDF 是否编译、URL 是否可换行、引用是否链接到 References。
4. 增加针对 Potato 和 AGN 两个样例的回归测试。

### Phase 2：产品化前端体验

1. 增加 Setup/Health Check 页面。
2. 增加任务状态页，显示 running、failed、succeeded 和错误原因。
3. 增加 Trust Dashboard。
4. 增加生成文件列表和下载状态。

### Phase 3：文献与引用质量

1. Zotero 模式文献不足 20 篇时自动补齐。
2. 外部检索模式稳定检索 20 篇，并保存来源和 BibTeX。
3. 引用权重结合相关度和 EasyScholar 期刊等级。
4. 每篇文献 summary 明确来源：Zotero metadata、abstract、外部检索 metadata，避免假装读了全文。

### Phase 4：商业化安全底座

1. 增加登录系统。
2. 增加用户与项目数据隔离。
3. 增加下载鉴权。
4. 增加限流、日志、费用统计。
5. 增加隐私政策、数据保留策略和用户删除数据能力。

### Phase 5：付费测试

1. 先做邀请制 beta。
2. 以“每月生成次数 + 外部检索次数 + PDF 编译次数”为计费指标。
3. 收集用户修改最多的段落和失败最多的任务类型。
4. 根据真实反馈再决定是否做全文论文写作、代码生成和数据分析自动化。

