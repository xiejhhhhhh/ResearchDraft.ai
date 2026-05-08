import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)

PORT = int(os.getenv('RESEARCH_AGENT_PORT', '9000'))
API_HOST = os.getenv('RESEARCH_AGENT_HOST', '0.0.0.0')
