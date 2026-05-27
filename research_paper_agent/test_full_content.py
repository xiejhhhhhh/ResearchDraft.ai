from service import _generate_mock_draft
from models import ResearchIdeaRequest

# 创建测试请求
request = ResearchIdeaRequest(
    idea='测试研究主题',
    field='计算机科学',
    journal='Nature',
    output_format='tex',
    add_to_zotero=False,
    email='test@example.com'
)

# 生成mock draft
draft = _generate_mock_draft(request)

print('Mock Draft Generated:')
print(f'Title: {draft.title}')
print(f'Abstract: {draft.abstract[:100]}...')
print(f'Introduction: {draft.introduction[:100]}...')
print(f'Literature Review: {draft.literature_review[:100]}...')
print(f'Methodology: {draft.methodology[:100]}...')
print(f'Expected Results: {draft.expected_results[:100]}...')
print(f'Conclusion: {draft.conclusion[:100]}...')
print(f'References count: {len(draft.references)}')
print(f'Word count: {draft.word_count}')

# 模拟API响应格式
api_response = {
    'status': 'success',
    'message': f'研究初稿已生成完成！标题：{draft.title}，共{draft.word_count}字。我们将通过邮箱 {request.email} 发送完整版本。',
    'draft': {
        'title': draft.title,
        'abstract': draft.abstract,
        'introduction': draft.introduction,
        'literature_review': draft.literature_review,
        'methodology': draft.methodology,
        'expected_results': draft.expected_results,
        'conclusion': draft.conclusion,
        'references': draft.references,
        'generated_at': draft.generated_at,
        'word_count': draft.word_count
    }
}

print('\nAPI Response Structure:')
print(f'Status: {api_response["status"]}')
print(f'Message: {api_response["message"][:100]}...')
print(f'Draft fields: {list(api_response["draft"].keys())}')
print(f'Has literature_review: {"literature_review" in api_response["draft"]}')
print(f'Has introduction: {"introduction" in api_response["draft"]}')
print(f'Has methodology: {"methodology" in api_response["draft"]}')