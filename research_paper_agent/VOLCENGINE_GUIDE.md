# 火山引擎（Volcengine）集成指南

## 概述

火山引擎提供高性价比的AI模型服务，特别适合国内用户。本项目已集成火山引擎的豆包（Doubao）系列模型。

## 支持的模型

| 模型 | 特点 | 适用场景 |
|------|------|----------|
| `doubao-lite-32k` | 轻量级，性价比高 | 一般学术写作 |
| `doubao-pro-32k` | 专业版，更强的推理能力 | 复杂研究设计 |
| `doubao-pro-128k` | 长上下文版本 | 大型文献综述 |

## 配置步骤

### 1. 获取API密钥

1. 访问[火山引擎控制台](https://console.volcengine.com/)
2. 注册/登录账号
3. 进入 **云服务** > **AI** > **大模型推理**
4. 点击 **创建API Key**
5. 选择合适的模型（如豆包-lite-32k）
6. 复制生成的API Key

### 2. 配置环境变量

创建 `.env` 文件：

```env
# 火山引擎配置
VOLCENGINE_API_KEY=你的API密钥
VOLCENGINE_MODEL_ID=doubao-lite-32k
VOLCENGINE_ENDPOINT=https://ark.cn-beijing.volces.com/api/v3/chat/completions
```

### 3. 测试配置

运行测试脚本：

```bash
python test_ai.py
```

如果看到 "Draft generated successfully!" 且没有 "Warning: No AI API keys configured"，说明配置成功。

## API调用流程

系统会按以下优先级尝试AI服务：

1. **火山引擎** (如果配置了 `VOLCENGINE_API_KEY`)
2. **OpenAI** (如果配置了 `OPENAI_API_KEY`)
3. **Anthropic** (如果配置了 `ANTHROPIC_API_KEY`)
4. **Mock生成** (用于测试，无需API密钥)

## 费用说明

火山引擎按量计费，价格实惠：

- **豆包-lite-32k**: ¥0.003/千tokens
- **豆包-pro-32k**: ¥0.006/千tokens

生成一篇2500字的学术论文大约消耗2000-3000 tokens，费用约¥0.006-0.018。

## 故障排除

### 常见问题

1. **API密钥无效**
   ```
   错误: Volcengine generation failed: 401 Unauthorized
   解决: 检查API密钥是否正确，是否已过期
   ```

2. **模型不存在**
   ```
   错误: model not found
   解决: 检查VOLCENGINE_MODEL_ID是否正确
   ```

3. **网络连接问题**
   ```
   错误: Connection timeout
   解决: 检查网络连接，或更换endpoint
   ```

### 调试模式

启用详细日志：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 性能优化

1. **选择合适的模型**: 简单任务用lite，复杂任务用pro
2. **调整参数**: 在代码中可以调整temperature和max_tokens
3. **缓存结果**: 考虑对相同请求进行缓存

## 企业级部署

对于企业用户，火山引擎还提供：
- 专属实例（更稳定）
- 私有化部署
- SLA保证
- 更高的并发限制

## 联系支持

- 火山引擎文档: https://www.volcengine.com/docs
- 技术支持: 在控制台提交工单