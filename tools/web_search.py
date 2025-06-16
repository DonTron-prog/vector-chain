"""SearxNG web search functionality."""

import aiohttp
from typing import List, Dict, Any
from models.schemas import WebSearchResult


async def search_web(
    searxng_client,
    query: str,
    category: str = "general",
    max_results: int = 10
) -> List[WebSearchResult]:
    """Search web using SearxNG.
    
    Args:
        searxng_client: SearxNG client instance
        query: Search query
        category: Search category (general, news, social media)
        max_results: Maximum number of results
        
    Returns:
        List of web search results
    """
    try:
        search_params = {
            "categories": category,
        }
        
        if category == "news":
            search_params["engines"] = "google news,bing news,yahoo news"
        
        response = await searxng_client.search(query, **search_params)
        
        results = []
        for item in response.get("results", [])[:max_results]:
            result = WebSearchResult(
                url=item.get("url", ""),
                title=item.get("title", ""),
                content=item.get("content", ""),
                published_date=item.get("publishedDate")
            )
            results.append(result)
            
        return results
        
    except Exception as e:
        print(f"Web search failed: {e}")
        return []


def format_search_results(results: List[WebSearchResult]) -> str:
    """Format search results for LLM consumption."""
    if not results:
        return "No search results found."
    
    formatted = "Web Search Results:\n\n"
    for i, result in enumerate(results, 1):
        formatted += f"{i}. {result.title}\n"
        formatted += f"   URL: {result.url}\n"
        if result.content:
            formatted += f"   Summary: {result.content[:200]}...\n"
        if result.published_date:
            formatted += f"   Published: {result.published_date}\n"
        formatted += "\n"
    
    return formatted