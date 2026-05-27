#!/usr/bin/env python3
"""
Test script for ResearchDraft.ai academic tools integration
"""

import os
from service import get_zotero_client, get_zotero_items

def test_academic_tools():
    """Test academic tools functionality"""

    print("🔍 Testing Academic Tools Integration")
    print("=" * 50)

    # Test Zotero
    print("\n1. Testing Zotero Integration...")
    try:
        zotero_client = get_zotero_client()
        if zotero_client:
            print("✅ Zotero client initialized")
            items = get_zotero_items(zotero_client, collection='Potato disease detection', limit=5)
            print(f"   Found {len(items)} items in Zotero collection 'Potato disease detection'")
            if items:
                for i, item in enumerate(items[:2], 1):
                    print(f"   {i}. {item.get('title', 'No title')[:60]}...")
        else:
            print("⚠️  Zotero not configured")
    except Exception as e:
        print(f"❌ Zotero failed: {e}")

    print("\n" + "=" * 50)
    print("📝 To enable full functionality:")
    print("   1. Edit .env file with your Zotero credentials")
    print("   2. For AI: Add OpenAI, Anthropic, or Volcengine API keys")
    print("   3. Store your literature in Zotero and use the 'Potato disease detection' collection for this example")

if __name__ == "__main__":
    test_academic_tools()