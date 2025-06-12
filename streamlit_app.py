"""Streamlit app for Investment Research Chat System."""

import streamlit as st
import asyncio
import os
from pathlib import Path
import tempfile
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict, Any
import json

# Import the research system
from main import research_investment, display_analysis_summary
from models.schemas import InvestmentAnalysis, DocumentSearchResult
from agents.dependencies import ChromaDBClient, initialize_dependencies
from tools.vector_search import search_internal_docs
from config import get_openai_model

# Page configuration
st.set_page_config(
    page_title="Investment Research Chat",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        color: #2e8b57;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-message {
        color: #28a745;
        font-weight: bold;
    }
    .error-message {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []
if 'research_mode' not in st.session_state:
    st.session_state.research_mode = "simple_chat"
if 'chat_context' not in st.session_state:
    st.session_state.chat_context = ""
if 'research_results' not in st.session_state:
    st.session_state.research_results = None
if 'uploaded_documents' not in st.session_state:
    st.session_state.uploaded_documents = []
if 'vector_db' not in st.session_state:
    st.session_state.vector_db = ChromaDBClient()
if 'openai_client' not in st.session_state:
    st.session_state.openai_client = get_openai_model()
if 'deps' not in st.session_state:
    st.session_state.deps = None

def main():
    """Main Streamlit app function."""
    st.markdown('<h1 class="main-header">💬 Investment Research Chat</h1>', unsafe_allow_html=True)
    
    # Sidebar for configuration and research modes
    with st.sidebar:
        show_sidebar_configuration()
    
    # Main chat interface
    show_chat_interface()

def show_sidebar_configuration():
    """Sidebar configuration and mode selection."""
    st.header("⚙️ Configuration")
    
    # Environment variables check
    openai_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    if not openai_key:
        st.error("❌ OPENAI_API_KEY or OPENROUTER_API_KEY not found in environment")
        st.stop()
    else:
        st.success("✅ API Key configured")
    
    st.divider()
    
    # Research Mode Selection
    st.header("🎛️ Research Mode")
    
    mode_options = {
        "simple_chat": "💬 Simple Chat",
        "rag_only": "📚 RAG Only", 
        "deep_research": "🔍 Deep Research",
        "full_planning": "🎯 Full Planning"
    }
    
    current_mode = st.radio(
        "Select Research Mode:",
        options=list(mode_options.keys()),
        format_func=lambda x: mode_options[x],
        index=list(mode_options.keys()).index(st.session_state.research_mode),
        help="""
        - **Simple Chat**: Quick Q&A with LLM
        - **RAG Only**: Search internal documents + analysis  
        - **Deep Research**: Web search + scraping + calculations
        - **Full Planning**: Complete research workflow with planning
        """
    )
    
    if current_mode != st.session_state.research_mode:
        st.session_state.research_mode = current_mode
        st.rerun()
    
    st.divider()
    
    # Context Settings
    st.header("📊 Context Settings")
    
    # SearxNG configuration (for deep research and full planning)
    if st.session_state.research_mode in ["deep_research", "full_planning"]:
        searxng_url = st.text_input("SearxNG URL", value="http://localhost:8080")
        st.session_state.searxng_url = searxng_url
    
    # ChromaDB configuration (for RAG and full planning)
    if st.session_state.research_mode in ["rag_only", "full_planning"]:
        chroma_path = st.text_input("ChromaDB Path", value="./investment_chroma_db")
        st.session_state.chroma_path = chroma_path
    
    # Additional context for all modes
    chat_context = st.text_area(
        "Additional Context",
        value=st.session_state.chat_context,
        placeholder="e.g., 3-5 year investment horizon, moderate risk tolerance",
        help="Provide additional context that will be used across the conversation"
    )
    
    if chat_context != st.session_state.chat_context:
        st.session_state.chat_context = chat_context
    
    st.divider()
    
    # Document management section
    st.header("📁 Document Management")
    show_document_manager()
    
    st.divider()
    
    # Chat management
    st.header("💬 Chat Management")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear Chat", help="Clear all chat messages"):
            st.session_state.chat_messages = []
            st.rerun()
    
    with col2:
        if st.button("📥 Export Chat", help="Export chat history"):
            export_chat_history()


def show_chat_interface():
    """Main chat interface."""
    # Display current mode
    mode_labels = {
        "simple_chat": "💬 Simple Chat Mode",
        "rag_only": "📚 RAG Only Mode", 
        "deep_research": "🔍 Deep Research Mode",
        "full_planning": "🎯 Full Planning Mode"
    }
    
    st.subheader(mode_labels[st.session_state.research_mode])
    
    # Chat messages container
    chat_container = st.container()
    
    with chat_container:
        # Display chat messages
        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
                
                # Show metadata if available
                if message.get("metadata"):
                    metadata = message["metadata"]
                    if metadata.get("mode"):
                        st.caption(f"Mode: {mode_labels.get(metadata['mode'], metadata['mode'])}")
                    if metadata.get("sources"):
                        with st.expander("📚 Sources", expanded=False):
                            for source in metadata["sources"]:
                                st.write(f"• {source}")
                    if metadata.get("confidence_score"):
                        st.caption(f"Confidence: {metadata['confidence_score']:.1%}")
    
    # Chat input
    if prompt := st.chat_input("Ask an investment question..."):
        # Add user message
        user_message = {
            "role": "user",
            "content": prompt,
            "mode": st.session_state.research_mode,
            "timestamp": datetime.now(),
            "metadata": {}
        }
        st.session_state.chat_messages.append(user_message)
        
        # Display user message immediately
        with st.chat_message("user"):
            st.write(prompt)
        
        # Generate and display assistant response
        with st.chat_message("assistant"):
            with st.spinner(get_loading_message(st.session_state.research_mode)):
                response = asyncio.run(generate_response(prompt))
                
                if response:
                    st.write(response["content"])
                    
                    # Show metadata
                    if response.get("metadata"):
                        metadata = response["metadata"]
                        if metadata.get("sources"):
                            with st.expander("📚 Sources", expanded=False):
                                for source in metadata["sources"]:
                                    st.write(f"• {source}")
                        if metadata.get("confidence_score"):
                            st.caption(f"Confidence: {metadata['confidence_score']:.1%}")
                    
                    # Add assistant message to chat history
                    st.session_state.chat_messages.append(response)


def get_loading_message(mode: str) -> str:
    """Get loading message based on research mode."""
    messages = {
        "simple_chat": "Thinking...",
        "rag_only": "Searching internal documents...",
        "deep_research": "Conducting web research...",
        "full_planning": "Creating research plan and conducting analysis..."
    }
    return messages.get(mode, "Processing...")


async def generate_response(prompt: str) -> Dict[str, Any]:
    """Generate response based on current research mode."""
    mode = st.session_state.research_mode
    
    try:
        if mode == "simple_chat":
            return await simple_chat_response(prompt)
        elif mode == "rag_only":
            return await rag_only_response(prompt)
        elif mode == "deep_research":
            return await deep_research_response(prompt)
        elif mode == "full_planning":
            return await full_planning_response(prompt)
        else:
            return {
                "role": "assistant",
                "content": "Unknown research mode. Please select a valid mode.",
                "mode": mode,
                "timestamp": datetime.now(),
                "metadata": {}
            }
    except Exception as e:
        return {
            "role": "assistant", 
            "content": f"Sorry, I encountered an error: {str(e)}",
            "mode": mode,
            "timestamp": datetime.now(),
            "metadata": {"error": str(e)}
        }


def export_chat_history():
    """Export chat history as JSON."""
    if not st.session_state.chat_messages:
        st.warning("No chat messages to export.")
        return
    
    chat_export = {
        "export_date": datetime.now().isoformat(),
        "total_messages": len(st.session_state.chat_messages),
        "research_mode": st.session_state.research_mode,
        "context": st.session_state.chat_context,
        "messages": st.session_state.chat_messages
    }
    
    json_data = json.dumps(chat_export, indent=2, default=str)
    
    st.download_button(
        label="📥 Download Chat History",
        data=json_data,
        file_name=f"investment_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )


async def simple_chat_response(prompt: str) -> Dict[str, Any]:
    """Generate simple chat response using LLM only."""
    try:
        # Create a simple client for direct LLM interaction
        import openai
        from config import get_required_env_var
        
        # Get API configuration
        api_key = get_required_env_var("OPENROUTER_API_KEY")
        
        client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        
        # Build conversation context
        messages = [{"role": "system", "content": "You are a helpful investment advisor. Provide clear, informative responses about investment topics. Be conversational and helpful."}]
        
        # Add context if available
        if st.session_state.chat_context:
            messages.append({"role": "system", "content": f"Additional context: {st.session_state.chat_context}"})
        
        # Add recent chat history for context (last 5 messages)
        recent_messages = st.session_state.chat_messages[-10:] if len(st.session_state.chat_messages) > 10 else st.session_state.chat_messages
        for msg in recent_messages:
            if msg["role"] in ["user", "assistant"]:
                messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Add current prompt
        messages.append({"role": "user", "content": prompt})
        
        # Generate response
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        content = response.choices[0].message.content
        
        return {
            "role": "assistant",
            "content": content,
            "mode": "simple_chat",
            "timestamp": datetime.now(),
            "metadata": {
                "model": "gpt-4o-mini",
                "mode_name": "Simple Chat"
            }
        }
        
    except Exception as e:
        raise Exception(f"Simple chat failed: {str(e)}")


async def rag_only_response(prompt: str) -> Dict[str, Any]:
    """Generate RAG-only response using vector search + LLM."""
    try:
        # Search internal documents
        search_results = await search_internal_docs(
            st.session_state.vector_db,
            prompt,
            doc_type="all",
            n_results=5
        )
        
        # Format search results
        context_text = ""
        sources = []
        
        if search_results:
            context_text = "Relevant information from internal documents:\n\n"
            for i, result in enumerate(search_results, 1):
                context_text += f"{i}. {result.content[:500]}...\n"
                if result.metadata:
                    company = result.metadata.get("company", "Unknown")
                    doc_type = result.metadata.get("doc_type", "Unknown")
                    filename = result.metadata.get("filename", "Unknown")
                    sources.append(f"{company} - {doc_type} ({filename})")
                context_text += "\n"
        else:
            context_text = "No relevant internal documents found for this query."
        
        # Generate LLM response with context
        import openai
        from config import get_required_env_var
        
        api_key = get_required_env_var("OPENROUTER_API_KEY")
        client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        
        system_prompt = """You are an investment research analyst. Use the provided document context to answer investment questions.
        
        Guidelines:
        - Base your analysis primarily on the provided document context
        - If the context doesn't contain relevant information, say so clearly
        - Cite specific information from the documents when making points
        - Provide confidence levels based on the quality and relevance of available data
        - Be clear about limitations of the analysis based on available documents"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion: {prompt}"}
        ]
        
        # Add chat context if available
        if st.session_state.chat_context:
            messages.insert(1, {"role": "system", "content": f"Additional context: {st.session_state.chat_context}"})
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3,
            max_tokens=1200
        )
        
        content = response.choices[0].message.content
        
        # Calculate confidence based on search results quality
        confidence_score = min(0.9, len(search_results) * 0.15 + 0.3) if search_results else 0.2
        
        return {
            "role": "assistant",
            "content": content,
            "mode": "rag_only", 
            "timestamp": datetime.now(),
            "metadata": {
                "sources": sources,
                "confidence_score": confidence_score,
                "documents_found": len(search_results),
                "mode_name": "RAG Only"
            }
        }
        
    except Exception as e:
        raise Exception(f"RAG search failed: {str(e)}")


async def deep_research_response(prompt: str) -> Dict[str, Any]:
    """Generate deep research response using web tools."""
    try:
        # Initialize dependencies for web research
        searxng_url = getattr(st.session_state, 'searxng_url', 'http://localhost:8080')
        deps = initialize_dependencies(
            query=prompt,
            context=st.session_state.chat_context,
            searxng_url=searxng_url,
            chroma_path="./investment_chroma_db",
            knowledge_path="./knowledge_base"
        )
        
        # Use web search and scraping tools
        from tools.web_search import search_web, format_search_results
        from tools.web_scraper import scrape_webpage
        from tools.calculator import perform_financial_calculations
        
        # Search web for current information
        try:
            web_results = await search_web(
                deps.searxng_client,
                prompt,
                category="general",
                max_results=6
            )
        except Exception as search_error:
            # If web search fails, provide analysis without web data
            web_results = []
            web_context = f"Web search unavailable (Error: {str(search_error)}). Providing analysis based on general knowledge."
        else:
            web_context = format_search_results(web_results) if web_results else "No web results found."
        
        # Generate analysis with web context
        import openai
        from config import get_required_env_var
        
        api_key = get_required_env_var("OPENROUTER_API_KEY")
        client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        
        system_prompt = """You are an investment research analyst with access to web information.
        
        Use the provided web search results (if available) to answer investment questions with current market data.
        
        Guidelines:
        - If web results are available, focus on recent market developments and news
        - If web search is unavailable, provide analysis based on general financial knowledge
        - Incorporate current trends and sentiment when possible
        - Mention specific sources when citing information
        - Provide analysis based on the most recent available data
        - Be clear about the limitations of your analysis (whether you have current web data or not)
        - Always provide valuable insights even if web data is unavailable"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Web Research Results:\n{web_context}\n\nQuestion: {prompt}"}
        ]
        
        if st.session_state.chat_context:
            messages.insert(1, {"role": "system", "content": f"Additional context: {st.session_state.chat_context}"})
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.4,
            max_tokens=1300
        )
        
        content = response.choices[0].message.content
        
        # Extract sources from web results
        sources = []
        if web_results:
            for result in web_results[:5]:  # Top 5 sources
                # Handle both WebSearchResult objects and dictionaries
                if hasattr(result, 'title'):
                    title = result.title or 'Unknown'
                    url = result.url or 'No URL'
                else:
                    title = result.get('title', 'Unknown') if isinstance(result, dict) else 'Unknown'
                    url = result.get('url', 'No URL') if isinstance(result, dict) else 'No URL'
                sources.append(f"{title} - {url}")
        
        confidence_score = min(0.85, len(web_results) * 0.1 + 0.4) if web_results else 0.3
        
        return {
            "role": "assistant",
            "content": content,
            "mode": "deep_research",
            "timestamp": datetime.now(),
            "metadata": {
                "sources": sources,
                "confidence_score": confidence_score,
                "web_results_count": len(web_results) if web_results else 0,
                "mode_name": "Deep Research"
            }
        }
        
    except Exception as e:
        raise Exception(f"Deep research failed: {str(e)}")


async def full_planning_response(prompt: str) -> Dict[str, Any]:
    """Generate full planning response using existing research workflow."""
    try:
        # Use existing research workflow
        searxng_url = getattr(st.session_state, 'searxng_url', 'http://localhost:8080')
        chroma_path = getattr(st.session_state, 'chroma_path', './investment_chroma_db')
        
        analysis = await research_investment(
            query=prompt,
            context=st.session_state.chat_context,
            searxng_url=searxng_url,
            chroma_path=chroma_path,
            knowledge_path="./knowledge_base"
        )
        
        # Format the comprehensive analysis for chat
        content = f"""## Investment Analysis Summary

**Query:** {analysis.query}

**Summary:**
{analysis.findings.summary}

**Key Insights:**
{chr(10).join(f'• {insight}' for insight in analysis.findings.key_insights)}

**Risk Factors:**
{chr(10).join(f'• {risk}' for risk in analysis.findings.risk_factors)}

**Investment Recommendation:**
{analysis.findings.recommendation}

**Confidence Score:** {analysis.findings.confidence_score:.1%}"""
        
        # Add financial metrics if available
        metrics = analysis.findings.financial_metrics
        if any([metrics.pe_ratio, metrics.debt_to_equity, metrics.return_on_equity]):
            content += "\n\n**Financial Metrics:**\n"
            if metrics.pe_ratio:
                content += f"• P/E Ratio: {metrics.pe_ratio:.2f}\n"
            if metrics.debt_to_equity:
                content += f"• Debt/Equity: {metrics.debt_to_equity:.2f}\n"
            if metrics.return_on_equity:
                content += f"• ROE: {metrics.return_on_equity:.2%}\n"
            if metrics.profit_margin:
                content += f"• Profit Margin: {metrics.profit_margin:.2%}\n"
        
        # Store full analysis in session state for potential export
        st.session_state.research_results = analysis
        
        return {
            "role": "assistant",
            "content": content,
            "mode": "full_planning",
            "timestamp": datetime.now(),
            "metadata": {
                "sources": analysis.findings.sources,
                "confidence_score": analysis.findings.confidence_score,
                "plan_steps": len(analysis.plan.steps),
                "mode_name": "Full Planning",
                "full_analysis": True  # Flag to indicate full analysis is available
            }
        }
        
    except Exception as e:
        raise Exception(f"Full planning research failed: {str(e)}")


def show_document_manager():
    """Document upload and management interface."""
    st.subheader("Upload Documents")
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Choose investment documents",
        type=['txt', 'pdf'],
        accept_multiple_files=True,
        help="Upload SEC filings, earnings reports, analyst reports, etc."
    )
    
    if uploaded_files:
        col1, col2 = st.columns(2)
        
        with col1:
            company_symbol = st.text_input("Company Symbol", placeholder="e.g., AAPL", key="company_symbol")
        
        with col2:
            doc_type = st.selectbox(
                "Document Type",
                ["10K", "10Q", "earnings", "analyst", "news", "other"],
                key="doc_type"
            )
        
        if st.button("📤 Upload Documents", type="primary"):
            if company_symbol:
                upload_documents(uploaded_files, company_symbol.upper(), doc_type)
            else:
                st.error("Please enter a company symbol")
    
    # Show existing documents
    st.subheader("Existing Documents")
    show_existing_documents()

def upload_documents(uploaded_files, company_symbol: str, doc_type: str):
    """Process and upload documents to vector database."""
    with st.spinner("Processing and uploading documents..."):
        try:
            success_count = 0
            
            for uploaded_file in uploaded_files:
                # Save file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name
                
                # Process the file
                content = extract_text_from_file(tmp_path, uploaded_file.type)
                
                if content:
                    # Add to vector database
                    add_document_to_vectordb(
                        content=content,
                        company=company_symbol,
                        doc_type=doc_type,
                        filename=uploaded_file.name
                    )
                    success_count += 1
                
                # Clean up temp file
                os.unlink(tmp_path)
            
            if success_count > 0:
                st.success(f"✅ Successfully uploaded {success_count} documents")
                st.rerun()
            else:
                st.error("❌ Failed to process any documents")
                
        except Exception as e:
            st.error(f"❌ Upload failed: {str(e)}")

def extract_text_from_file(file_path: str, file_type: str) -> str:
    """Extract text content from uploaded file."""
    try:
        if file_type.startswith('text/') or file_path.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif file_type == 'application/pdf' or file_path.endswith('.pdf'):
            # Use hybrid PDF extractor
            from tools.pdf_extractor import extract_pdf_text_sync
            with st.spinner("Extracting text from PDF (trying pymupdf first, VLM fallback if needed)..."):
                return extract_pdf_text_sync(file_path, use_vlm_fallback=True)
        else:
            st.error(f"Unsupported file type: {file_type}")
            return ""
    except Exception as e:
        st.error(f"Error reading file: {str(e)}")
        return ""

def add_document_to_vectordb(content: str, company: str, doc_type: str, filename: str):
    """Add document to ChromaDB vector database."""
    try:
        # Get or create collection
        collection = st.session_state.vector_db.get_collection()
        
        # Split content into chunks (simple approach)
        chunk_size = 1000
        chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
        
        # Prepare data for ChromaDB
        documents = chunks
        metadatas = [
            {
                "company": company,
                "doc_type": doc_type,
                "filename": filename,
                "chunk_index": i,
                "upload_date": datetime.now().isoformat()
            }
            for i in range(len(chunks))
        ]
        ids = [f"{company}_{doc_type}_{filename}_{i}" for i in range(len(chunks))]
        
        # Add to collection
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
    except Exception as e:
        raise Exception(f"Failed to add document to vector database: {str(e)}")

def show_existing_documents():
    """Display existing documents in the vector database."""
    try:
        collection = st.session_state.vector_db.get_collection()
        
        # Get all documents (this is a simplified approach)
        results = collection.get()
        
        if results and results['documents']:
            # Group by company and document type
            docs_by_company = {}
            for i, metadata in enumerate(results.get('metadatas', [])):
                company = metadata.get('company', 'Unknown')
                doc_type = metadata.get('doc_type', 'Unknown')
                filename = metadata.get('filename', 'Unknown')
                
                if company not in docs_by_company:
                    docs_by_company[company] = {}
                if doc_type not in docs_by_company[company]:
                    docs_by_company[company][doc_type] = set()
                
                docs_by_company[company][doc_type].add(filename)
            
            # Display documents
            for company, doc_types in docs_by_company.items():
                st.write(f"**{company}**")
                for doc_type, filenames in doc_types.items():
                    st.write(f"  - {doc_type}: {len(filenames)} files")
                    for filename in filenames:
                        st.write(f"    • {filename}")
        else:
            st.info("No documents uploaded yet")
            
    except Exception as e:
        st.error(f"Error loading documents: {str(e)}")


if __name__ == "__main__":
    main()