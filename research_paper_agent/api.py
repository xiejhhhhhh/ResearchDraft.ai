import sys
from pathlib import Path
from flask import Flask, jsonify, request

# Add current directory to path for imports
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))

from service import process_research_request


def create_app() -> Flask:
    app = Flask(__name__)

    @app.after_request
    def add_cors_headers(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
        return response

    @app.route('/api/submit-idea', methods=['POST'])
    def submit_idea():
        data = request.get_json(force=True, silent=True) or {}
        result = process_research_request(data)
        status_code = 400 if result.get('status') == 'error' else 200
        return jsonify(result), status_code

    @app.route('/api/status', methods=['GET'])
    def status():
        return jsonify({'status': 'ok', 'service': 'ResearchDraft.ai backend'})

    return app


if __name__ == '__main__':
    print("Starting ResearchDraft.ai backend on http://0.0.0.0:9000")
    print("API endpoints:")
    print("  GET  /api/status")
    print("  POST /api/submit-idea")
    app = create_app()
    app.run(host='0.0.0.0', port=9000, debug=True)
