docker# ResearchDraft.ai 后端部署说明

该后端服务位于 `research_paper_agent/`，使用 Flask 提供 REST API。当前已准备好可上线部署的容器配置。

## 目录结构

- `Dockerfile` - 容器构建文件
- `Procfile` - 兼容 Heroku / Render / Railway 的启动声明
- `requirements.txt` - Python 依赖
- `api.py` - Flask Web 服务入口
- `service.py` - 业务处理逻辑
- `config.py` - 运行配置
- `.dockerignore` - Docker 构建忽略项

## 1. 本地测试部署

1. 进入项目目录：
   ```powershell
   cd c:\Python_code\research_paper_agent
   ```

2. 安装依赖：
   ```powershell
   python -m pip install -r requirements.txt
   ```

3. 启动服务：
   ```powershell
   python ..\scripts\run_research_agent.py
   ```

4. 打开浏览器测试：
   - `http://localhost:9000/api/status`

5. 也可以使用 Docker 本地运行：
   ```powershell
   docker build -t research_draft_backend .
   docker run --rm -p 9000:9000 research_draft_backend
   ```

## 2. 云端部署方案

建议使用以下平台之一：

- Render
- Railway
- Fly.io
- DigitalOcean App Platform

这些平台可直接使用仓库中的 `Dockerfile` 或 `Procfile` 部署。

### 推荐方案：Render（最简单）

1. 注册 Render：https://render.com
2. 创建一个新的 Web Service
3. 选择 GitHub 仓库，并指定 `research_paper_agent/` 目录作为服务根目录
4. 设置运行命令：
   - 如果使用 Docker：直接选择 Docker 部署
   - 如果使用 Render 原生 Python：设置 `Start Command` 为：
     ```bash
     gunicorn -w 2 -b 0.0.0.0:9000 research_paper_agent.api:create_app()
     ```
5. 设置环境变量（可选）：
   - `RESEARCH_AGENT_PORT=9000`
   - `RESEARCH_AGENT_HOST=0.0.0.0`
6. 部署完成后，Render 会提供一个线上 URL。

### Railway 部署

1. 注册 Railway：https://railway.app
2. 创建新项目
3. 连接 GitHub 仓库
4. 选择 `research_paper_agent/` 目录
5. Railway 会自动检测 Python / Docker，可使用 `Procfile`
6. 部署完成后会生成一个 URL

## 3. 页面前端与后端连接

由于 GitHub Pages 只能托管静态页面，后端必须部署到云服务。部署完成后：

- 将 `mvp_site` 页面中的 `apiEndpoint` 修改为云端后端 URL
- 例如：
  ```js
  const apiEndpoint = 'https://your-backend-url.onrender.com/api/submit-idea';
  ```

## 4. 线上部署步骤示例（Render）

### 4.1 准备仓库

1. 将 `research_paper_agent/` 目录提交到 GitHub 仓库。
2. 确保 `research_paper_agent/Dockerfile`、`requirements.txt`、`Procfile` 均已提交。

### 4.2 Render 设置

1. 登录 Render
2. 选择 `New > Web Service`
3. 选择 GitHub 仓库
4. 选择 `research_paper_agent/` 作为服务目录
5. 选择 `Docker` 部署或 `Python` 部署
6. 设置端口 `9000`
7. 点击 Deploy

### 4.3 测试 API

部署后访问：
- `https://<render-service-url>/api/status`
- `POST https://<render-service-url>/api/submit-idea`

## 5. 生产环境准备

如果后续需要付费服务和域名：

- 购买自定义域名
- 在 Render / Railway 中绑定域名
- 配置 HTTPS（平台通常自动启用）
- 如果需要更多安全性，可在后端添加 API Key 或访问令牌

## 6. 注意事项

- `GitHub Pages` 只能托管静态前端，不能托管后端 API
- 后端服务必须部署在可以接收 HTTP 请求的平台上
- 前端页面必须调用后端的线上 URL，而不是 `localhost`

## 7. 进一步扩展

后续可对后端继续扩展：
- Consensus 文献检索接口
- Zotero 同步接入
- 研究文案生成队列
- 用户管理与付费下单接口
