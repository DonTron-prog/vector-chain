"""Vector database search functionality."""

from typing import List, Optional, Dict, Any
from models.schemas import DocumentSearchResult


async def search_internal_docs(
    vector_db,
    query: str,
    doc_type: str = "all",
    n_results: int = 5
) -> List[DocumentSearchResult]:
    """Search internal investment documents using vector database.
    
    Args:
        vector_db: ChromaDB client instance
        query: Search query
        doc_type: Type of document (10k, 10q, earnings, analyst, all)
        n_results: Number of results to return
        
    Returns:
        List of document search results
    """
    try:
        # Prepare filters
        filters = None
        if doc_type != "all":
            filters = {"doc_type": doc_type}
        
        # Query vector database
        results = await vector_db.query(
            query_text=query,
            n_results=n_results,
            filters=filters
        )
        
        # Format results
        doc_results = []
        if results and "documents" in results:
            documents = results["documents"][0] if results["documents"] else []
            metadatas = results["metadatas"][0] if results.get("metadatas") else []
            distances = results["distances"][0] if results.get("distances") else []
            
            for i, doc in enumerate(documents):
                metadata = metadatas[i] if i < len(metadatas) else {}
                # Convert distance to similarity score (lower distance = higher similarity)
                score = 1.0 - (distances[i] if i < len(distances) else 0.5)
                
                result = DocumentSearchResult(
                    content=doc,
                    metadata=metadata,
                    score=score
                )
                doc_results.append(result)
        
        return doc_results
        
    except Exception as e:
        print(f"Vector search failed: {e}")
        return []


def format_document_results(results: List[DocumentSearchResult]) -> str:
    """Format document search results for LLM consumption.
    
    Args:
        results: List of document search results
        
    Returns:
        Formatted string for LLM
    """
    if not results:
        return "No internal documents found matching the query."
    
    formatted = "Internal Document Search Results:\n\n"
    
    for i, result in enumerate(results, 1):
        formatted += f"{i}. Document Excerpt (Score: {result.score:.2f})\n"
        
        # Add metadata info if available
        if result.metadata:
            company = result.metadata.get("company", "Unknown")
            doc_type = result.metadata.get("doc_type", "Unknown")
            formatted += f"   Source: {company} - {doc_type}\n"
        
        # Add content (limit to reasonable length)
        content = result.content[:800] + "..." if len(result.content) > 800 else result.content
        formatted += f"   Content: {content}\n\n"
    
    return formatted


def extract_financial_data(content: str) -> Dict[str, Any]:
    """Extract financial data from document content.
    
    Args:
        content: Document content to analyze
        
    Returns:
        Dictionary of extracted financial metrics with parsed values
    """
    import re
    from .calculator import parse_financial_value
    
    financial_data = {}
    
    # Look for common financial metrics
    patterns = {
        "revenue": r"revenue.*?(\$[\d,\.]+\s*(?:billion|million|B|M))",
        "net_income": r"net income.*?(\$[\d,\.]+\s*(?:billion|million|B|M))",
        "pe_ratio": r"P/E ratio.*?(\d+\.?\d*)",
        "market_cap": r"market cap.*?(\$[\d,\.]+\s*(?:billion|million|B|M))"
    }
    
    for metric, pattern in patterns.items():
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            raw_value = match.group(1)
            # Use shared parsing function for consistency
            parsed_value = parse_financial_value(raw_value)
            financial_data[metric] = {
                "raw": raw_value,
                "parsed": parsed_value
            }
    
    return financial_data