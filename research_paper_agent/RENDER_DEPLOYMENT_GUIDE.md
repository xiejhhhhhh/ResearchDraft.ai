# ResearchDraft.ai Docker + Render 完整部署指南

## 前置条件

- GitHub 账户和包含本项目的仓库
- Render 账户（免费注册：https://render.com）
- 本地 Docker（用于本地测试，可选）

---

## 第一步：本地 Docker 测试（可选但推荐）

### 1.1 构建 Docker 镜像

在项目根目录执行：

```powershell
cd c:\Python_code
docker build -t research-draft-backend ./research_paper_agent
```

### 1.2 运行容器测试

```powershell
docker run --rm -p 9000:9000 research-draft-backend
```

### 1.3 验证服务

在浏览器中访问：
```
http://localhost:9000/api/status
```

应该返回：
```json
{"status":"ok","service":"ResearchDraft.ai backend"}
```

### 1.4 测试 API

用 PowerShell 测试提交 Idea：

```powershell
$body = @{
    idea = "构建AI驱动的文献管理系统"
    field = "计算机科学"
    journal = "IEEE Transactions"
    output_format = "tex"
    email = "your-email@example.com"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:9000/api/submit-idea" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

返回示例：
```json
{
  "status": "success",
  "message": "研究Idea已成功接收，后端服务会继续处理并通过邮箱与您联系。"
}
```

---

## 第二步：准备 GitHub 仓库

### 2.1 确认文件结构

你的 GitHub 仓库应该包含：

```
.
├── docs/                          # 前端页面（GitHub Pages）
│   ├── index.html
│   ├── styles.css
│   └── app.js
│
├── research_paper_agent/          # 后端服务（Render 部署）
│   ├── Dockerfile
│   ├── Procfile
│   ├── requirements.txt
│   ├── api.py
│   ├── service.py
│   ├── config.py
│   ├── models.py
│   ├── __init__.py
│   └── .dockerignore
│
└── README.md
```

### 2.2 提交到 GitHub

```powershell
git add .
git commit -m "Add Docker configuration for backend deployment"
git push origin main
```

---

## 第三步：Render 部署详细步骤

### 3.1 登录 Render

1. 打开 https://render.com
2. 用 GitHub 账户登录（或注册后连接 GitHub）

### 3.2 创建新 Web Service

1. 点击 Dashboard 右上角 `New` 按钮
2. 选择 `Web Service`（不是 Static Site）

![Render New](./img/render-new.png)

### 3.3 连接 GitHub 仓库

1. 在"Connect a repository"区域，选择你的仓库
2. 如果第一次部署，需要授予 Render 对 GitHub 的访问权限
3. 点击 `Connect`

### 3.4 配置服务

#### 基本配置

| 配置项 | 值 |
|--------|---|
| Name | `research-draft-backend` |
| Environment | `Docker` |
| Region | `Singapore` 或 `Frankfurt`（根据目标地域） |
| Branch | `main` |

#### Root Path（根目录）

如果 Render 要求指定，填写：
```
research_paper_agent
```

#### Runtime Logs

勾选"Enable autoscaling"（可选，用于生产环境）

### 3.5 设置运行命令（Docker 方式）

如果平台支持直接使用 Dockerfile：
- Render 会自动识别 `research_paper_agent/` 中的 `Dockerfile`
- 无需手动填写启动命令

如果平台要求填写，使用：
```bash
gunicorn -w 2 -b 0.0.0.0:9000 research_paper_agent.api:create_app()
```

### 3.6 设置环境变量

在 Environment 标签页添加：

| 键 | 值 |
|----|---|
| `RESEARCH_AGENT_PORT` | `9000` |
| `RESEARCH_AGENT_HOST` | `0.0.0.0` |

（可选，如果 Docker 已在 config.py 中配置默认值，此步骤可跳过）

### 3.7 点击 Deploy

1. 检查所有配置无误
2. 点击 `Deploy` 按钮
3. 等待构建完成（通常 2-5 分钟）

### 3.8 查看部署进度

Render 会显示构建日志：
- 应该看到 `FROM python:3.12-slim`
- 然后 `pip install` 依赖
- 最后 `CMD gunicorn...`

部署完成后，Render 会提供一个 URL，类似：
```
https://research-draft-backend.onrender.com
```

---

## 第四步：验证部署

### 4.1 测试后端 API

#### 状态检查
```
https://research-draft-backend.onrender.com/api/status
```

应返回：
```json
{"status":"ok","service":"ResearchDraft.ai backend"}
```

#### 测试提交 Idea

```powershell
$backendUrl = "https://research-draft-backend.onrender.com/api/submit-idea"
$body = @{
    idea = "AI 与教育融合的研究"
    field = "教育技术"
    journal = "Journal of Educational Computing Research"
    output_format = "tex"
    email = "test@example.com"
} | ConvertTo-Json

Invoke-WebRequest -Uri $backendUrl `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

### 4.2 查看数据

已提交的 Idea 会保存在：
```
research_paper_agent/data/submissions.json
```

此文件可在 Render 的文件系统中查看（或添加数据库后端来持久化）。

---

## 第五步：连接前端页面

现在需要更新前端页面，让它调用 Render 上的后端服务。

### 5.1 修改前端 API 地址

编辑 `docs/app.js`，找到这一行：

```javascript
const apiEndpoint = 'http://localhost:9000/api/submit-idea';
```

修改为你的 Render URL：

```javascript
const apiEndpoint = 'https://research-draft-backend.onrender.com/api/submit-idea';
```

### 5.2 提交更改

```powershell
git add docs/app.js
git commit -m "Update backend API URL to Render service"
git push origin main
```

### 5.3 刷新 GitHub Pages

GitHub Pages 会自动更新，访问你的页面：
```
https://xiejhhhhh.github.io/ResearchDraft.ai/
```

### 5.4 测试完整流程

1. 打开前端页面
2. 填写表单并提交
3. 应该看到"研究Idea已成功接收"的提示
4. 检查 Render 后端日志确认收到请求

---

## 第六步：监控与维护

### 6.1 查看日志

在 Render Dashboard：
1. 选择你的服务
2. 点击 `Logs` 标签页
3. 可以看到实时的服务日志

### 6.2 重启服务

如果需要重启：
1. 在 Dashboard 找到你的服务
2. 点击 `Manual Deploy` 重新部署
3. 或点击 `Restart` 重启当前版本

### 6.3 监控成本

Render 免费计划：
- 静态网站：无限
- Web 服务：有使用限制但通常够小项目用
- 如果流量增加，可升级到付费计划

---

## 常见问题排查

### Q1: 部署失败，错误为 "ModuleNotFoundError"

**原因**：根目录指定错误

**解决**：
- 确认在 Render 中设置服务根目录为 `research_paper_agent/`
- 或者确认 `requirements.txt` 在正确位置

### Q2: API 返回 CORS 错误

**原因**：前后端跨域请求问题

**现状**：`api.py` 已配置 CORS 头

**验证**：
```javascript
fetch('https://your-backend/api/status')
  .then(r => r.json())
  .then(console.log)
```

### Q3: 提交后没有收到邮件通知

**原因**：当前实现是测试版，只保存到 JSON 文件

**后续**：
- 可添加邮件发送功能（使用 SendGrid / SMTP）
- 或添加数据库后端（PostgreSQL）

### Q4: 如何查看提交的数据？

当前数据保存在：
```
research_paper_agent/data/submissions.json
```

后续可通过以下方式改进：
1. 添加 `/api/submissions` 查询端点
2. 连接数据库（PostgreSQL / MongoDB）
3. 集成支付系统

---

## 下一步扩展

### Phase 1：完善当前部署（推荐）
- [ ] 测试 Render 部署是否正常
- [ ] 验证前端能正确调用后端
- [ ] 监控初期使用情况

### Phase 2：添加功能
- [ ] Consensus API 集成
- [ ] Zotero 同步
- [ ] 研究文案生成逻辑
- [ ] LaTeX 模板填充

### Phase 3：生产化
- [ ] 添加数据库（PostgreSQL）
- [ ] 配置支付系统（Stripe）
- [ ] 添加用户认证
- [ ] 绑定自定义域名

---

## 快速命令参考

| 任务 | 命令 |
|------|------|
| 本地测试后端 | `python scripts\run_research_agent.py` |
| 本地 Docker 构建 | `docker build -t research-draft-backend ./research_paper_agent` |
| 本地 Docker 运行 | `docker run --rm -p 9000:9000 research-draft-backend` |
| 推送到 GitHub | `git push origin main` |
| Render 手动部署 | Render Dashboard → Manual Deploy |
| 查看 Render 日志 | Render Dashboard → Logs |

---

## 支持与反馈

如有问题，可以：
1. 检查本文的"常见问题排查"部分
2. 查看 Render Dashboard 的 Logs 标签页
3. 查看本地启动时的错误日志
