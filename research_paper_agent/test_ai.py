#!/usr/bin/env python3
"""
Test script for AI draft generation
"""
from service import generate_research_draft
from models import ResearchIdeaRequest

def test_ai_generation():
    req = ResearchIdeaRequest(
        idea='AI在教育中的应用',
        field='教育技术',
        journal='Journal of Educational Technology',
        output_format='tex',
        email='test@example.com'
    )

    print("Testing AI draft generation...")
    draft = generate_research_draft(req)

    if draft:
        print("✅ Draft generated successfully!")
        print(f"Title: {draft.title}")
        print(f"Word count: {draft.word_count}")
        print(f"Abstract preview: {draft.abstract[:100]}...")
    else:
        print("❌ Draft generation failed")

if __name__ == '__main__':
    test_ai_generation()