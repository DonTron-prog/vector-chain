"""Enhanced vector database search functionality with async operations and metrics."""

from typing import List, Optional, Dict, Any, Tuple
import logfire
from models.schemas import DocumentSearchResult, DocumentMetadata, RAGMetrics
import hashlib
import time

# Session-level query cache (cache_key -> (results, timestamp))
_query_cache: Dict[str, Tuple[List[DocumentSearchResult], float]] = {}
CACHE_TTL = 300  # 5 minutes cache TTL


async def search_internal_docs(
    vector_db,
    query: str,
    doc_type: str = "all",
    n_results: int = 5,
    enhance_query: bool = True
) -> List[DocumentSearchResult]:
    """Enhanced search of internal investment documents using vector database.
    
    Args:
        vector_db: ChromaDB client instance
        query: Search query
        doc_type: Type of document (10k, 10q, earnings, analyst, all)
        n_results: Number of results to return
        enhance_query: Whether to enhance the query for better retrieval
        
    Returns:
        List of document search results
    """
    # Create cache key from query parameters
    cache_key = hashlib.md5(f"{query}:{doc_type}:{n_results}:{enhance_query}".encode()).hexdigest()
    current_time = time.time()
    
    # Check cache first
    if cache_key in _query_cache:
        cached_results, cache_time = _query_cache[cache_key]
        if current_time - cache_time < CACHE_TTL:
            logfire.info("Cache hit for vector search", query=query[:50], cached_results=len(cached_results))
            return cached_results
        else:
            # Remove expired cache entry
            del _query_cache[cache_key]
    
    try:
        # Prepare filters
        filters = None
        if doc_type != "all":
            filters = {"doc_type": doc_type}
        
        # Query vector database with metrics if available
        if hasattr(vector_db, 'query_with_metrics'):
            try:
                results, metrics = await vector_db.query_with_metrics(
                    query_text=query,
                    n_results=n_results,
                    filters=filters
                )
                logfire.info("Vector search completed with metrics", **metrics.model_dump())
            except Exception:
                # Fallback to regular query if metrics query fails
                results = await vector_db.query(
                    query_text=query,
                    n_results=n_results,
                    filters=filters
                )
        else:
            results = await vector_db.query(
                query_text=query,
                n_results=n_results,
                filters=filters
            )
        
        # Format results with enhanced metadata handling
        doc_results = []
        if results and "documents" in results:
            documents = results["documents"][0] if results["documents"] else []
            metadatas = results["metadatas"][0] if results.get("metadatas") else []
            distances = results["distances"][0] if results.get("distances") else []
            
            for i, doc in enumerate(documents):
                raw_metadata = metadatas[i] if i < len(metadatas) else {}
                
                # Create structured metadata with backward compatibility
                try:
                    if isinstance(raw_metadata, dict):
                        metadata = DocumentMetadata(
                            company=raw_metadata.get("company", "Unknown"),
                            doc_type=raw_metadata.get("doc_type", "Unknown"),
                            date=raw_metadata.get("date"),
                            section=raw_metadata.get("section"),
                            page_number=raw_metadata.get("page_number"),
                            file_path=raw_metadata.get("file_path")
                        )
                    else:
                        # Handle case where metadata might be None or unexpected type
                        metadata = DocumentMetadata(
                            company="Unknown",
                            doc_type="Unknown"
                        )
                except Exception as e:
                    logfire.warning("Failed to parse metadata, using defaults", error=str(e), raw_metadata=raw_metadata)
                    metadata = DocumentMetadata(
                        company="Unknown",
                        doc_type="Unknown"
                    )
                
                # Convert distance to similarity score (lower distance = higher similarity)
                distance = distances[i] if i < len(distances) else 0.5
                score = max(0.0, min(1.0, 1.0 - distance))
                
                result = DocumentSearchResult(
                    content=doc,
                    metadata=metadata,
                    score=score,
                    chunk_id=raw_metadata.get("chunk_id")
                )
                doc_results.append(result)
        
        logfire.info("Document search successful", query=query[:100], results_count=len(doc_results))
        
        # Cache the results for future use
        _query_cache[cache_key] = (doc_results, current_time)
        
        return doc_results
        
    except Exception as e:
        logfire.error("Vector search failed", query=query[:100], error=str(e))
        # Return empty results for backward compatibility with tests
        return []


def format_document_results(results: List[DocumentSearchResult], max_length: int = 1200) -> str:
    """Enhanced formatting of document search results for LLM consumption.
    
    Args:
        results: List of document search results
        max_length: Maximum content length per result
        
    Returns:
        Formatted string for LLM
    """
    if not results:
        return "No internal documents found matching the query."
    
    # Sort by relevance score
    results = sorted(results, key=lambda x: x.score, reverse=True)
    
    formatted = f"Internal Document Search Results (Top {len(results)} matches):\n\n"
    
    for i, result in enumerate(results, 1):
        # Dynamic content length based on relevance
        content_length = max_length if result.score > 0.8 else max_length // 2
        
        formatted += f"{i}. Document Excerpt\n"
        formatted += f"   📊 Relevance: {result.score:.3f} ({result.relevance_level})\n"
        
        # Enhanced metadata display
        metadata = result.metadata
        formatted += f"   📄 Source: {metadata.company} - {metadata.doc_type}"
        if metadata.date:
            formatted += f" ({metadata.date})"
        if metadata.section:
            formatted += f" - {metadata.section}"
        formatted += "\n"
        
        # Smart content truncation
        content = result.content[:content_length]
        if len(result.content) > content_length:
            # Try to end at a sentence boundary
            last_period = content.rfind('.')
            if last_period > content_length * 0.7:
                content = content[:last_period + 1]
            else:
                content += "..."
        
        formatted += f"   📝 Content: {content}\n\n"
    
    return formatted


def extract_financial_data(content: str) -> Dict[str, Any]:
    """Extract financial data from document content with enhanced patterns.
    
    Args:
        content: Document content to analyze
        
    Returns:
        Dictionary of extracted financial metrics with parsed values
    """
    import re
    from .calculator import parse_financial_value
    
    financial_data = {}
    
    # Enhanced patterns for common financial metrics
    patterns = {
        "revenue": r"(?:revenue|net sales|total revenue).*?(\$[\d,\.]+\s*(?:billion|million|B|M|thousand|K))",
        "net_income": r"(?:net income|net earnings|profit).*?(\$[\d,\.]+\s*(?:billion|million|B|M|thousand|K))",
        "pe_ratio": r"(?:P/E ratio|price.to.earnings|PE ratio).*?(\d+\.?\d*)",
        "market_cap": r"(?:market cap|market capitalization).*?(\$[\d,\.]+\s*(?:billion|million|B|M|trillion|T))",
        "eps": r"(?:earnings per share|EPS).*?(\$?\d+\.\d+)",
        "dividend_yield": r"(?:dividend yield).*?(\d+\.?\d*%?)",
        "book_value": r"(?:book value|shareholders.equity).*?(\$[\d,\.]+\s*(?:billion|million|B|M))"
    }
    
    try:
        for metric, pattern in patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                # Take the first match
                raw_value = matches[0]
                try:
                    parsed_value = parse_financial_value(raw_value)
                    financial_data[metric] = {
                        "raw": raw_value,
                        "parsed": parsed_value
                    }
                    logfire.debug("Financial metric extracted", metric=metric, raw=raw_value, parsed=parsed_value)
                except Exception as e:
                    logfire.warning("Failed to parse financial value", metric=metric, raw=raw_value, error=str(e))
    
    except Exception as e:
        logfire.error("Financial data extraction failed", error=str(e))
    
    return financial_data


async def search_with_query_enhancement(
    vector_db,
    query: str,
    doc_type: str = "all",
    n_results: int = 5,
    research_context: str = ""
) -> Tuple[List[DocumentSearchResult], str]:
    """Search with automatic query enhancement for better retrieval.
    
    Args:
        vector_db: ChromaDB client instance
        query: Original search query
        doc_type: Type of document to search
        n_results: Number of results to return
        research_context: Additional context to enhance query
        
    Returns:
        Tuple of (search results, enhanced query)
    """
    try:
        # Simple query enhancement
        enhanced_query = query
        if research_context:
            enhanced_query = f"{query} {research_context}"
        
        # Add domain-specific terms for better retrieval
        if "financial" in query.lower() or "earnings" in query.lower():
            enhanced_query += " revenue profit margin cash flow"
        elif "risk" in query.lower():
            enhanced_query += " volatility uncertainty challenges"
        elif "growth" in query.lower():
            enhanced_query += " expansion market share innovation"
        
        results = await search_internal_docs(
            vector_db, enhanced_query, doc_type, n_results, enhance_query=False
        )
        
        logfire.info("Query enhancement completed", original=query, enhanced=enhanced_query, results_count=len(results))
        return results, enhanced_query
        
    except Exception as e:
        logfire.error("Query enhancement failed", query=query, error=str(e))
        # Fallback to original query
        results = await search_internal_docs(vector_db, query, doc_type, n_results, enhance_query=False)
        return results, query