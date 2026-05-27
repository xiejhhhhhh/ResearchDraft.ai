import os
from dotenv import load_dotenv

load_dotenv()

print('AI API Configuration Status:')
volc_key = '✓ Configured' if os.getenv('VOLCENGINE_API_KEY') else '✗ Not configured'
print(f'VOLCENGINE_API_KEY: {volc_key}')
print(f'VOLCENGINE_MODEL_ID: {os.getenv("VOLCENGINE_MODEL_ID", "Not set")}')
openai_key = '✓ Configured' if os.getenv('OPENAI_API_KEY') else '✗ Not configured'
print(f'OPENAI_API_KEY: {openai_key}')
anthropic_key = '✓ Configured' if os.getenv('ANTHROPIC_API_KEY') else '✗ Not configured'
print(f'ANTHROPIC_API_KEY: {anthropic_key}')

print('\nAcademic Tools Configuration:')
print(f'ZOTERO_LIBRARY_ID: {os.getenv("ZOTERO_LIBRARY_ID", "Not set")}')
zotero_key = '✓ Configured' if os.getenv('ZOTERO_API_KEY') else '✗ Not configured'
print(f'ZOTERO_API_KEY: {zotero_key}')
print('Note: This setup uses Zotero-only literature retrieval and does not require Consensus.')