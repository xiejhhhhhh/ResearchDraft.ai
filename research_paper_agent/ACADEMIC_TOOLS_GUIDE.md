# Academic Tools Integration Guide

This guide explains how to set up and use Zotero integration in ResearchDraft.ai for enhanced literature review and bibliography management.

## Overview

ResearchDraft.ai now uses Zotero as the primary literature source for research draft generation.

## Zotero Integration

### What it does:
- Searches your Zotero library for relevant references
- Uses Zotero item metadata to enrich AI prompts
- Supports Zotero collections and tag-based filtering
- Adds references to generated drafts using Zotero source data

### Setup:

1. **Get Zotero API Credentials:**
   - Go to [Zotero API Settings](https://www.zotero.org/settings/keys)
   - Create a new API key with read access to your library

2. **Find your Library ID:**
   - In Zotero, go to Settings → Advanced → Config Editor
   - Search for `userID` or check your Zotero account page for your user/library ID

3. **Configure Environment Variables:**
   ```bash
   ZOTERO_LIBRARY_ID=1234567
   ZOTERO_API_KEY=your_api_key_here
   ZOTERO_LIBRARY_TYPE=user  # 'user' for personal libraries, 'group' for group libraries
   ```

### Features:

- Retrieves relevant Zotero items for the research topic
- Builds AI prompt context from Zotero titles, authors, abstracts, and collections
- Uses a Zotero collection name like `Potato disease detection` when available
- Keeps Zotero as the sole literature source for generated drafts

## How It Works

### Research Draft Generation Process:

1. User submits a research idea
2. System searches Zotero for relevant items
3. AI prompt is enhanced with Zotero metadata
4. Draft is generated using Zotero-backed context
5. Generated references are returned in the draft output

### Zotero Search Behavior:

- Searches by research idea text across item titles and abstracts
- Attempts to match a Zotero collection name equal to the research topic
- Limits results to the top 10 Zotero items for prompt context

## Configuration Options

### Environment Variables:

```bash
ZOTERO_LIBRARY_ID=your_library_id
ZOTERO_API_KEY=your_api_key
ZOTERO_LIBRARY_TYPE=user
ZOTERO_SEARCH_LIMIT=10
```

### API Endpoints:

The `/api/submit-idea` endpoint now:
- Uses Zotero-only literature retrieval
- Includes Zotero context in the draft generation prompt
- Returns draft references sourced from Zotero items

## Troubleshooting

### Zotero Issues:

**"Failed to initialize Zotero client"**
- Check that `ZOTERO_API_KEY` is correct
- Verify `ZOTERO_LIBRARY_ID` matches your Zotero account or group
- Ensure `ZOTERO_LIBRARY_TYPE` is set to `user` or `group` correctly

**"No items found in Zotero search"**
- Ensure your Zotero library contains papers related to the research topic
- Broaden the search phrases
- Verify item metadata includes titles and abstracts

### General Issues:

**Slow generation times**
- Zotero search may add a few seconds
- Keep Zotero item metadata up to date for better search recall

**Missing references in drafts**
- Confirm Zotero credentials are configured
- Check server logs for Zotero search output

## Best Practices

1. Keep Zotero library organized with relevant collections and tags
2. Use specific research topic wording for better matches
3. Maintain item abstracts and metadata in Zotero
4. Review generated draft references for accuracy

## Security Notes

- API keys are stored locally in `.env`
- Never commit `.env` to version control
- Keep Zotero API keys private and secure
- This version does not use Consensus or Google Scholar for literature retrieval
</content>
<parameter name="filePath">D:\DraftAI_agent\research_paper_agent\ACADEMIC_TOOLS_GUIDE.md
