"""Shared dependencies for investment research agents."""

from pydantic import BaseModel
from typing import Optional, Any
import chromadb
import aiohttp
import asyncio
import time
import logfire
import os
from pathlib import Path
from typing import Tuple


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
    """Enhanced client for ChromaDB vector database with async operations and metrics."""
    
    def __init__(self, persist_directory: str = "./investment_chroma_db", embedding_model: str = "text-embedding-3-small"):
        self.persist_directory = persist_directory
        self.embedding_model = embedding_model
        self.client = None
        self.collection = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize ChromaDB client with error handling."""
        try:
            self.client = chromadb.PersistentClient(path=self.persist_directory)
            logfire.info("ChromaDB client initialized", path=self.persist_directory)
        except Exception as e:
            logfire.error("Failed to initialize ChromaDB client", error=str(e), path=self.persist_directory)
            raise
    
    def get_collection(self, name: str = "investment_research"):
        """Get or create collection with enhanced error handling."""
        try:
            self.collection = self.client.get_collection(name)
            logfire.info("ChromaDB collection retrieved", name=name)
        except Exception:
            try:
                self.collection = self.client.create_collection(name)
                logfire.info("ChromaDB collection created", name=name)
            except Exception as e:
                logfire.error("Failed to create ChromaDB collection", name=name, error=str(e))
                raise
        return self.collection
    
    async def query(self, query_text: str, n_results: int = 5, filters: Optional[dict] = None) -> dict:
        """Async query the vector database."""
        if not self.collection:
            self.get_collection()
        
        query_params = {
            "query_texts": [query_text],
            "n_results": n_results
        }
        if filters:
            query_params["where"] = filters
        
        try:
            # Run sync ChromaDB operations in thread pool for true async
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                lambda: self.collection.query(**query_params)
            )
            logfire.info("ChromaDB query successful", query=query_text[:100], n_results=n_results)
            return result
        except Exception as e:
            logfire.error("ChromaDB query failed", query=query_text[:100], error=str(e))
            raise
    
    async def query_with_metrics(self, query_text: str, n_results: int = 5, filters: Optional[dict] = None) -> Tuple[dict, 'RAGMetrics']:
        """Query with performance metrics tracking."""
        from models.schemas import RAGMetrics
        
        start_time = time.time()
        
        try:
            results = await self.query(query_text, n_results, filters)
            
            # Calculate metrics
            retrieval_time = (time.time() - start_time) * 1000
            distances = results.get("distances", [[]])[0] if results.get("distances") else []
            similarity_scores = [max(0.0, 1.0 - score) for score in distances] if distances else []
            
            metrics = RAGMetrics(
                query=query_text,
                num_results=len(similarity_scores),
                avg_relevance_score=sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.0,
                top_score=max(similarity_scores) if similarity_scores else 0.0,
                retrieval_time_ms=retrieval_time
            )
            
            logfire.info("RAG metrics calculated", **metrics.model_dump())
            return results, metrics
            
        except Exception as e:
            retrieval_time = (time.time() - start_time) * 1000
            logfire.error("Query with metrics failed", query=query_text[:100], time_ms=retrieval_time, error=str(e))
            raise
    
    async def hybrid_search(
        self, 
        query: str, 
        n_results: int = 5, 
        semantic_weight: float = 0.7,
        filters: Optional[dict] = None
    ) -> dict:
        """Hybrid semantic + keyword search (basic implementation)."""
        try:
            # For now, just do semantic search with expanded results
            # TODO: Implement true hybrid search with keyword matching
            semantic_results = await self.query(query, n_results * 2, filters)
            
            # Simple reranking based on semantic scores
            if semantic_results.get("distances"):
                # Keep top n_results after reranking
                documents = semantic_results.get("documents", [[]])[0][:n_results]
                metadatas = semantic_results.get("metadatas", [[]])[0][:n_results]
                distances = semantic_results.get("distances", [[]])[0][:n_results]
                
                return {
                    "documents": [documents],
                    "metadatas": [metadatas],
                    "distances": [distances]
                }
            
            return semantic_results
            
        except Exception as e:
            logfire.error("Hybrid search failed", query=query[:100], error=str(e))
            raise


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


class FinancialDataClient:
    """Client for real-time financial data via Alpha Vantage API."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self._session = None
        
    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()
    
    async def get_quote(self, symbol: str) -> dict:
        """Get real-time stock quote."""
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": self.api_key
        }
        
        try:
            if not self._session:
                self._session = aiohttp.ClientSession()
                
            async with self._session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logfire.info("Financial data API call successful", symbol=symbol)
                    return data
                else:
                    raise Exception(f"API request failed with status {response.status}")
        except Exception as e:
            logfire.error("Financial data API call failed", symbol=symbol, error=str(e))
            raise
    
    def is_available(self) -> bool:
        """Check if financial data client is properly configured."""
        return bool(self.api_key)


class ResearchDependencies(BaseModel):
    """Shared context and resources for investment research agents."""
    
    vector_db: ChromaDBClient
    searxng_client: SearxNGClient  
    knowledge_base: KnowledgeBase
    financial_data_client: Optional[FinancialDataClient] = None
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
    
    # Initialize financial data client if API key is available
    financial_client = None
    alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if alpha_vantage_key:
        financial_client = FinancialDataClient(alpha_vantage_key)
        logfire.info("Financial data client initialized with Alpha Vantage")
    else:
        logfire.warning("ALPHA_VANTAGE_API_KEY not found - financial data features disabled")
    
    return ResearchDependencies(
        vector_db=ChromaDBClient(chroma_path),
        searxng_client=SearxNGClient(searxng_url),
        knowledge_base=KnowledgeBase(knowledge_path),
        financial_data_client=financial_client,
        current_query=query,
        research_context=context
    )