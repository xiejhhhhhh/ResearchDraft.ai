from service import process_research_request

# 测试数据
test_data = {
    'idea': '测试研究主题',
    'field': '计算机科学',
    'journal': 'Nature',
    'output_format': 'tex',
    'add_to_zotero': False,
    'email': 'test@example.com'
}

result = process_research_request(test_data)

print('API Response:')
print(f'Status: {result["status"]}')
print(f'Message: {result["message"]}')
if 'draft' in result:
    print(f'Draft Title: {result["draft"]["title"]}')
    print(f'Has Full Content: {"introduction" in result["draft"]}')
    print(f'Word Count: {result["draft"]["word_count"]}')
    print('Available fields:', list(result["draft"].keys()))