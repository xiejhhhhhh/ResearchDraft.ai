#!/usr/bin/env python3
"""
Simple server runner for ResearchDraft.ai backend
"""
import sys
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))

from api import create_app

if __name__ == '__main__':
    app = create_app()
    print("Starting ResearchDraft.ai backend on http://0.0.0.0:9000")
    print("API endpoints:")
    print("  GET  /api/status")
    print("  POST /api/submit-idea")
    app.run(host='0.0.0.0', port=9000, debug=True)