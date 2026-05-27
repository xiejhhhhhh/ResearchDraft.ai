# ResearchDraft.ai Backend

AI-powered research paper draft generation service.

## Features

- 🤖 AI-powered research draft generation
- 📧 Email notifications
- 🔄 Multiple output formats (LaTeX, Markdown, etc.)
- 🌐 RESTful API
- 🐳 Docker support

## AI Providers

The system supports multiple AI providers with automatic fallback:

1. **Volcengine (火山引擎)** - Recommended for Chinese users
   - Models: 豆包-lite, 豆包-pro, etc.
   - Advantages: Fast response, cost-effective, good Chinese support
   - Setup: `VOLCENGINE_API_KEY` and `VOLCENGINE_MODEL_ID`

2. **OpenAI** - GPT models
   - Models: GPT-4, GPT-3.5-turbo
   - Setup: `OPENAI_API_KEY`

3. **Anthropic** - Claude models
   - Models: Claude-3, Claude-2
   - Setup: `ANTHROPIC_API_KEY`

4. **Mock Generation** - For testing without API keys
   - Automatically used when no API keys are configured

## Academic Tools Integration

The system integrates with academic tools for enhanced literature review and bibliography management:

### Zotero Integration

Automatically sync generated drafts and search your Zotero library for relevant references.

**Setup:**
1. Get your Zotero API key from [Zotero API Settings](https://www.zotero.org/settings/keys)
2. Find your Library ID in Zotero settings
3. Add to `.env`:
   ```bash
   ZOTERO_LIBRARY_ID=your_library_id
   ZOTERO_API_KEY=your_api_key
   ZOTERO_LIBRARY_TYPE=user  # or 'group' for group libraries
   ```

**Features:**
- Automatic bibliography syncing
- Search existing Zotero items for literature review
- Add generated drafts to Zotero collections

### Zotero-First Literature Integration

ResearchDraft.ai now uses Zotero as the primary source for literature and references.

**Setup:**
1. Store the papers you want to use in Zotero
2. Add Zotero credentials to `.env`:
   ```bash
   ZOTERO_LIBRARY_ID=your_zotero_library_id
   ZOTERO_API_KEY=your_zotero_api_key
   ZOTERO_LIBRARY_TYPE=user
   ```

### Features:
- Retrieves relevant items from your Zotero library
- Builds AI prompt context from Zotero titles, authors, and abstracts
- Generates literature review content based on Zotero sources
- Uses a named collection like `Potato disease detection` when available

### Notes:
- Zotero is the only literature source used for draft generation in this version
- Google Scholar and Consensus are not used for literature retrieval

## Quick Start with Volcengine (火山引擎)

For Chinese users, we recommend using Volcengine for better performance and cost:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure Volcengine API
cp .env.example .env
# Edit .env and add your Volcengine API key

# 3. Test AI generation
python test_ai.py

# 4. Start server
python api.py
```

See [VOLCENGINE_GUIDE.md](VOLCENGINE_GUIDE.md) for detailed setup instructions.

#### Getting API Keys

**Volcengine (火山引擎) - 推荐国内用户使用:**
1. 访问[火山引擎控制台](https://console.volcengine.com/)
2. 注册账号或登录
3. 进入"云服务" > "AI" > "大模型推理"
4. 创建API Key
5. 选择模型（如豆包-lite-32k，性价比高）
6. 获取API Key和模型ID

**OpenAI:**
1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Create an account or sign in
3. Go to API Keys section
4. Create a new secret key

**Anthropic (Claude):**
1. Visit [Anthropic Console](https://console.anthropic.com/)
2. Create an account or sign in
3. Go to API Keys section
4. Create a new key

**Volcengine (火山引擎) - 推荐国内用户使用:**
1. 访问[火山引擎控制台](https://console.volcengine.com/)
2. 注册账号或登录
3. 进入"云服务" > "AI" > "大模型推理"
4. 创建API Key
5. 选择模型（如豆包-lite-32k，性价比高）
6. 获取API Key和模型ID

### 3. Run the Server

```bash
python run_server.py
```

Or directly:

```bash
python api.py
```

The server will start on `http://localhost:9000`

## API Endpoints

### POST /api/submit-idea

Submit a research idea for draft generation.

**Request Body:**
```json
{
  "idea": "Your research topic",
  "field": "Research field (e.g., Computer Science)",
  "journal": "Target journal (optional)",
  "output_format": "tex|md|docx",
  "email": "your.email@example.com"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Research draft generated successfully!",
  "draft_preview": {
    "title": "Generated Title",
    "abstract": "Abstract preview...",
    "word_count": 2500
  }
}
```

### GET /api/status

Check server status.

**Response:**
```json
{
  "status": "ok",
  "service": "ResearchDraft.ai backend"
}
```

## Data Storage

All submissions are stored in `data/submissions.json` with the following structure:

```json
{
  "idea": "Research topic",
  "field": "Field",
  "journal": "Target journal",
  "output_format": "tex",
  "email": "user@example.com",
  "created_at": "2024-01-01T00:00:00Z",
  "status": "completed",
  "draft": {
    "title": "Generated Title",
    "abstract": "Full abstract...",
    "introduction": "Introduction section...",
    "methodology": "Methodology section...",
    "expected_results": "Expected results...",
    "conclusion": "Conclusion...",
    "references": ["Reference 1", "Reference 2", ...],
    "generated_at": "2024-01-01T00:00:00Z",
    "word_count": 2500
  }
}
```

## Docker Deployment

```bash
# Build image
docker build -t research-draft-agent .

# Run container
docker run -d -p 9000:9000 --env-file .env research-draft-agent
```

## Development

### Project Structure

```
research_paper_agent/
├── api.py              # Flask application
├── service.py          # Business logic, AI integration, and academic tools
├── models.py           # Data models
├── config.py           # Configuration
├── run_server.py      # Server startup script
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables template
├── Dockerfile          # Docker configuration
├── VOLCENGINE_GUIDE.md # Volcengine setup guide
└── data/               # Data storage directory
    └── submissions.json
```

### Adding New AI Providers

1. Add API client in `service.py`
2. Create generation function following the pattern of `_generate_with_openai()`
3. Update `generate_research_draft()` to include the new provider
4. Add API key to `.env.example`

## Troubleshooting

### No AI Generation
- Check that API keys are set in `.env`
- Verify API keys are valid and have credits
- Check console for error messages

### Import Errors
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version (3.8+ recommended)

### Port Already in Use
- Change port in `.env`: `RESEARCH_AGENT_PORT=9001`
- Or kill process using the port

## License

MIT License