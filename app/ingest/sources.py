"""Source ingestion logic."""

import asyncio
from typing import Any, Optional

from app.ingest.http import fetch_text, get_http_client

# Example sources
SOURCES = [
    {
        "id": "awesome-agents",
        "url": "https://raw.githubusercontent.com/kyrolabs/awesome-agents/main/README.md",
        "type": "markdown_list"
    },
    # Add more sources here
]

async def fetch_source_content(source: dict[str, Any]) -> Optional[str]:
    """Fetch content for a source."""
    return await fetch_text(source["url"])

async def run_ingest_sources():
    """Main entry to fetch all sources (stub)."""
    # Real logic would return a list of items to process
    client = await get_http_client()
    results = []
    
    for source in SOURCES:
        content = await fetch_text(source["url"], client)
        if content:
            results.append({
                "source_id": source["id"],
                "content": content,
                "url": source["url"]
            })
            
    await client.aclose()
    return results
