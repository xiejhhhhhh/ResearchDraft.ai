import sys
from pathlib import Path
import os
from flask import Flask, jsonify, request, send_file

# Add current directory to path for imports
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))

from service import list_zotero_collections, process_research_request


def create_app() -> Flask:
    app = Flask(__name__)

    @app.after_request
    def add_cors_headers(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
        return response

    @app.route('/', methods=['GET'])
    def home():
        return jsonify({
            'service': 'ResearchDraft.ai Backend',
            'version': '1.0',
            'endpoints': {
                'status': 'GET /api/status',
                'zotero_collections': 'GET /api/zotero/collections',
                'submit_idea': 'POST /api/submit-idea',
                'download_file': 'GET /api/download/<file_path>'
            }
        })

    @app.route('/api/submit-idea', methods=['POST'])
    def submit_idea():
        data = request.get_json(force=True, silent=True) or {}
        result = process_research_request(data)
        status_code = 400 if result.get('status') == 'error' else 200
        return jsonify(result), status_code

    @app.route('/api/status', methods=['GET'])
    def status():
        return jsonify({
            'status': 'ok',
            'service': 'ResearchDraft.ai backend',
            'pid': os.getpid(),
            'debug': app.debug,
        })

    @app.route('/api/zotero/collections', methods=['GET'])
    def zotero_collections():
        collections = list_zotero_collections()
        return jsonify({
            'status': 'success',
            'collections': collections,
            'count': len(collections),
        })

    @app.route('/api/download/<path:file_path>', methods=['GET'])
    def download_file(file_path):
        """下载生成的文件"""
        try:
            # 确保文件路径在data/drafts目录内，防止目录遍历攻击
            drafts_dir = (current_dir / 'data' / 'drafts').resolve()
            full_path = (drafts_dir / file_path).resolve()

            # 检查文件是否在允许的目录内
            try:
                full_path.relative_to(drafts_dir)
            except ValueError:
                return jsonify({'error': 'Invalid file path'}), 403

            # 检查文件是否存在
            if not full_path.exists():
                return jsonify({'error': 'File not found'}), 404

            # 发送文件
            return send_file(
                str(full_path),
                as_attachment=True,
                download_name=full_path.name
            )

        except Exception as e:
            return jsonify({'error': f'Download failed: {str(e)}'}), 500

    @app.route('/api/download-literature/<path:file_path>', methods=['GET'])
    def download_literature_summary(file_path):
        try:
            summaries_dir = (current_dir / 'data' / 'literature_summaries').resolve()
            full_path = (summaries_dir / file_path).resolve()
            try:
                full_path.relative_to(summaries_dir)
            except ValueError:
                return jsonify({'error': 'Invalid file path'}), 403
            if not full_path.exists():
                return jsonify({'error': 'File not found'}), 404
            return send_file(str(full_path), as_attachment=True, download_name=full_path.name)
        except Exception as e:
            return jsonify({'error': f'Download failed: {str(e)}'}), 500

    return app


if __name__ == '__main__':
    print("Starting ResearchDraft.ai backend on http://0.0.0.0:9000")
    print("API endpoints:")
    print("  GET  /api/status")
    print("  POST /api/submit-idea")
    app = create_app()
    app.run(host='0.0.0.0', port=9000, debug=False, use_reloader=False, threaded=True)
