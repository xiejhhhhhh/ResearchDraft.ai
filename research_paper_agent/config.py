import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)

PORT = int(os.getenv('RESEARCH_AGENT_PORT', '9000'))
API_HOST = os.getenv('RESEARCH_AGENT_HOST', '0.0.0.0')

# AI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
VOLCENGINE_API_KEY = os.getenv('VOLCENGINE_API_KEY')
VOLCENGINE_MODEL_ID = os.getenv('VOLCENGINE_MODEL_ID', 'doubao-lite-32k')
VOLCENGINE_ENDPOINT = os.getenv('VOLCENGINE_ENDPOINT', 'https://ark.cn-beijing.volces.com/api/v3/chat/completions')

# Academic Tools Configuration
ZOTERO_LIBRARY_ID = os.getenv('ZOTERO_LIBRARY_ID')
ZOTERO_API_KEY = os.getenv('ZOTERO_API_KEY')
ZOTERO_LIBRARY_TYPE = os.getenv('ZOTERO_LIBRARY_TYPE', 'user')
