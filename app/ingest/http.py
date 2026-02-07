"""HTTP Client for ingestion."""

import httpx
from httpx import AsyncClient, Timeout
from typing import Optional

async def get_http_client() -> AsyncClient:
    """Get configured HTTP client."""
    timeout = Timeout(30.0, connect=10.0)
    # Some directories block default http clients without a UA.
    headers = {
        "User-Agent": "agent-skills-marketplace/1.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    return AsyncClient(timeout=timeout, follow_redirects=True, headers=headers)

async def fetch_text(url: str, client: Optional[AsyncClient] = None) -> Optional[str]:
    """Fetch text content from URL."""
    should_close = False
    if not client:
        client = await get_http_client()
        should_close = True
        
    try:
        response = await client.get(url)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None
    finally:
        if should_close:
            await client.aclose()
