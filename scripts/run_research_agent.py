import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from research_paper_agent.api import create_app
from research_paper_agent.config import API_HOST, PORT

app = create_app()

if __name__ == '__main__':
    print(f"Starting ResearchDraft.ai backend on {API_HOST}:{PORT}")
    app.run(host=API_HOST, port=PORT, debug=True)
