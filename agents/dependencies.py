"""Shared dependencies for investment research agents."""

from pydantic import BaseModel
from typing import Optional, Any
import chromadb
import aiohttp
from pathlib import Path


class SearxNGClient:
    """Client for SearxNG search engine."""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
    
    async def search(self, q: str, **params) -> dict:
        """Search using SearxNG."""
        async with aiohttp.ClientSession() as session:
            search_params = {
                "q": q,
                "format": "json",
                "safesearch": "0",
                "language": "en",
                "engines": "bing,duckduckgo,google,startpage",
                **params
            }
            async with session.get(f"{self.base_url}/search", params=search_params) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    raise Exception(f"SearxNG search failed: {resp.status}")


class ChromaDBClient:
    """Client for ChromaDB vector database."""
    
    def __init__(self, persist_directory: str = "./investment_chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = None
    
    def get_collection(self, name: str = "investment_research"):
        """Get or create collection."""
        try:
            self.collection = self.client.get_collection(name)
        except:
            self.collection = self.client.create_collection(name)
        return self.collection
    
    async def query(self, query_text: str, n_results: int = 5, filters: Optional[dict] = None) -> dict:
        """Query the vector database."""
        if not self.collection:
            self.get_collection()
        
        query_params = {
            "query_texts": [query_text],
            "n_results": n_results
        }
        if filters:
            query_params["where"] = filters
            
        return self.collection.query(**query_params)


class KnowledgeBase:
    """Knowledge base for investment documents."""
    
    def __init__(self, base_path: str = "./knowledge_base"):
        self.base_path = Path(base_path)
    
    def get_company_files(self, symbol: str) -> list:
        """Get all files for a company symbol."""
        company_dir = self.base_path / symbol.upper()
        if company_dir.exists():
            return list(company_dir.glob("*.txt"))
        return []


class ResearchDependencies(BaseModel):
    """Shared context and resources for investment research agents."""
    
    vector_db: ChromaDBClient
    searxng_client: SearxNGClient  
    knowledge_base: KnowledgeBase
    current_query: str
    research_context: str = ""
    accumulated_findings: str = ""
    
    class Config:
        arbitrary_types_allowed = True


def initialize_dependencies(
    query: str,
    context: str = "",
    searxng_url: str = "http://localhost:8080",
    chroma_path: str = "./investment_chroma_db",
    knowledge_path: str = "./knowledge_base"
) -> ResearchDependencies:
    """Initialize all dependencies for research agents."""
    
    return ResearchDependencies(
        vector_db=ChromaDBClient(chroma_path),
        searxng_client=SearxNGClient(searxng_url),
        knowledge_base=KnowledgeBase(knowledge_path),
        current_query=query,
        research_context=context
    )