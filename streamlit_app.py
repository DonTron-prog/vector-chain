"""Streamlit app for Investment Research System."""

import streamlit as st
import asyncio
import os
from pathlib import Path
import tempfile
import pandas as pd
from datetime import datetime
from typing import Optional, List

# Import the research system
from main import research_investment, display_analysis_summary
from models.schemas import InvestmentAnalysis, DocumentSearchResult
from agents.dependencies import ChromaDBClient, initialize_dependencies
from tools.vector_search import search_internal_docs

# Page configuration
st.set_page_config(
    page_title="Investment Research System",
    page_icon="📊",
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
if 'research_results' not in st.session_state:
    st.session_state.research_results = None
if 'uploaded_documents' not in st.session_state:
    st.session_state.uploaded_documents = []
if 'vector_db' not in st.session_state:
    st.session_state.vector_db = ChromaDBClient()

def main():
    """Main Streamlit app function."""
    st.markdown('<h1 class="main-header">📊 Investment Research System</h1>', unsafe_allow_html=True)
    
    # Sidebar for configuration and document management
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Environment variables check
        openai_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
        if not openai_key:
            st.error("❌ OPENAI_API_KEY or OPENROUTER_API_KEY not found in environment")
            st.stop()
        else:
            st.success("✅ API Key configured")
        
        # SearxNG configuration
        searxng_url = st.text_input("SearxNG URL", value="http://localhost:8080")
        
        # ChromaDB configuration
        chroma_path = st.text_input("ChromaDB Path", value="./investment_chroma_db")
        
        st.divider()
        
        # Document management section
        st.header("📁 Document Management")
        show_document_manager()
    
    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["🔍 Research Query", "📈 Results", "📋 Document Viewer"])
    
    with tab1:
        show_research_interface(searxng_url, chroma_path)
    
    with tab2:
        show_results_display()
    
    with tab3:
        show_document_viewer()

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
            # For PDF files, you'd need to install PyPDF2 or similar
            st.warning("PDF support requires additional dependencies. Please convert to TXT format.")
            return ""
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

def show_research_interface(searxng_url: str, chroma_path: str):
    """Research query interface."""
    st.markdown('<h2 class="section-header">Investment Research Query</h2>', unsafe_allow_html=True)
    
    # Query input
    col1, col2 = st.columns([2, 1])
    
    with col1:
        query = st.text_area(
            "Investment Question",
            placeholder="e.g., Should I invest in AAPL for long-term growth?",
            height=100,
            help="Enter your investment question or analysis request"
        )
    
    with col2:
        context = st.text_area(
            "Additional Context",
            placeholder="e.g., 3-5 year horizon, moderate risk tolerance",
            height=100,
            help="Provide additional context about your investment goals"
        )
    
    # Advanced options
    with st.expander("🔧 Advanced Options"):
        col1, col2 = st.columns(2)
        with col1:
            custom_searxng = st.text_input("Custom SearxNG URL", value=searxng_url)
            custom_chroma = st.text_input("Custom ChromaDB Path", value=chroma_path)
        with col2:
            knowledge_path = st.text_input("Knowledge Base Path", value="./knowledge_base")
    
    # Research button
    if st.button("🔍 Start Investment Research", type="primary", disabled=not query.strip()):
        if query.strip():
            run_research(query, context, custom_searxng, custom_chroma, knowledge_path)
        else:
            st.error("Please enter an investment question")

def run_research(query: str, context: str, searxng_url: str, chroma_path: str, knowledge_path: str):
    """Execute the investment research process."""
    progress_container = st.container()
    
    with progress_container:
        st.info("🔍 Starting investment research...")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Create an event loop for async execution
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Update progress
            progress_bar.progress(25)
            status_text.text("📋 Creating research plan...")
            
            # Run the research
            analysis = loop.run_until_complete(
                research_investment(
                    query=query,
                    context=context,
                    searxng_url=searxng_url,
                    chroma_path=chroma_path,
                    knowledge_path=knowledge_path
                )
            )
            
            progress_bar.progress(100)
            status_text.text("✅ Research completed!")
            
            # Store results in session state
            st.session_state.research_results = analysis
            
            st.success("🎯 Investment research completed successfully!")
            st.info("Check the 'Results' tab to view the analysis.")
            
        except Exception as e:
            st.error(f"❌ Research failed: {str(e)}")
            st.session_state.research_results = None
        finally:
            loop.close()

def show_results_display():
    """Display research results."""
    st.markdown('<h2 class="section-header">Research Results</h2>', unsafe_allow_html=True)
    
    if st.session_state.research_results is None:
        st.info("No research results yet. Run a query in the Research tab.")
        return
    
    analysis: InvestmentAnalysis = st.session_state.research_results
    
    # Display query and context
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**Query:** {analysis.query}")
    with col2:
        if analysis.context:
            st.info(f"**Context:** {analysis.context}")
    
    # Research plan
    with st.expander("📋 Research Plan", expanded=False):
        st.write(f"**Reasoning:** {analysis.plan.reasoning}")
        for i, step in enumerate(analysis.plan.steps, 1):
            st.write(f"{i}. **{step.description}**")
            st.write(f"   - Focus: {step.focus_area}")
            st.write(f"   - Expected: {step.expected_outcome}")
    
    # Main findings
    st.subheader("📊 Analysis Summary")
    st.write(analysis.findings.summary)
    
    # Financial metrics
    if any([
        analysis.findings.financial_metrics.pe_ratio,
        analysis.findings.financial_metrics.debt_to_equity,
        analysis.findings.financial_metrics.return_on_equity
    ]):
        st.subheader("💰 Financial Metrics")
        
        metrics_data = []
        metrics = analysis.findings.financial_metrics
        
        if metrics.pe_ratio:
            metrics_data.append({"Metric": "P/E Ratio", "Value": f"{metrics.pe_ratio:.2f}"})
        if metrics.debt_to_equity:
            metrics_data.append({"Metric": "Debt/Equity", "Value": f"{metrics.debt_to_equity:.2f}"})
        if metrics.return_on_equity:
            metrics_data.append({"Metric": "ROE", "Value": f"{metrics.return_on_equity:.2%}"})
        if metrics.profit_margin:
            metrics_data.append({"Metric": "Profit Margin", "Value": f"{metrics.profit_margin:.2%}"})
        if metrics.revenue_growth:
            metrics_data.append({"Metric": "Revenue Growth", "Value": f"{metrics.revenue_growth:.2%}"})
        
        if metrics_data:
            df = pd.DataFrame(metrics_data)
            st.dataframe(df, use_container_width=True)
    
    # Key insights and risks
    col1, col2 = st.columns(2)
    
    with col1:
        if analysis.findings.key_insights:
            st.subheader("🔑 Key Insights")
            for insight in analysis.findings.key_insights:
                st.write(f"• {insight}")
    
    with col2:
        if analysis.findings.risk_factors:
            st.subheader("⚠️ Risk Factors")
            for risk in analysis.findings.risk_factors:
                st.write(f"• {risk}")
    
    # Opportunities
    if analysis.findings.opportunities:
        st.subheader("🚀 Opportunities")
        for opportunity in analysis.findings.opportunities:
            st.write(f"• {opportunity}")
    
    # Recommendation
    st.subheader("🎯 Investment Recommendation")
    st.success(analysis.findings.recommendation)
    
    # Metadata
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Confidence Score", f"{analysis.findings.confidence_score:.1%}")
    with col2:
        st.metric("Sources Used", len(analysis.findings.sources))
    with col3:
        st.metric("Analysis Date", analysis.created_at.strftime("%Y-%m-%d %H:%M"))
    
    # Sources
    if analysis.findings.sources:
        with st.expander("📚 Sources", expanded=False):
            for i, source in enumerate(analysis.findings.sources, 1):
                st.write(f"{i}. {source}")
    
    # Download options
    st.subheader("📥 Download Results")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Download JSON"):
            download_json(analysis)
    
    with col2:
        if st.button("Download Summary"):
            download_summary(analysis)

def show_document_viewer():
    """Document search and viewing interface."""
    st.markdown('<h2 class="section-header">Document Search & Viewer</h2>', unsafe_allow_html=True)
    
    # Search interface
    search_query = st.text_input("Search Documents", placeholder="Enter search terms...")
    
    col1, col2 = st.columns(2)
    with col1:
        doc_type_filter = st.selectbox("Document Type", ["all", "10K", "10Q", "earnings", "analyst", "news"])
    with col2:
        num_results = st.slider("Number of Results", 1, 20, 5)
    
    if st.button("🔍 Search Documents") and search_query:
        search_documents(search_query, doc_type_filter, num_results)

def search_documents(query: str, doc_type: str, num_results: int):
    """Search documents in the vector database."""
    try:
        with st.spinner("Searching documents..."):
            # Use the existing vector search function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            results = loop.run_until_complete(
                search_internal_docs(
                    st.session_state.vector_db,
                    query,
                    doc_type=doc_type,
                    n_results=num_results
                )
            )
            loop.close()
        
        if results:
            st.success(f"Found {len(results)} results")
            
            for i, result in enumerate(results, 1):
                with st.expander(f"Result {i} (Score: {result.score:.3f})", expanded=i==1):
                    if result.metadata:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**Company:** {result.metadata.get('company', 'Unknown')}")
                        with col2:
                            st.write(f"**Type:** {result.metadata.get('doc_type', 'Unknown')}")
                        with col3:
                            st.write(f"**File:** {result.metadata.get('filename', 'Unknown')}")
                    
                    st.write("**Content:**")
                    st.write(result.content)
        else:
            st.info("No documents found matching your search.")
            
    except Exception as e:
        st.error(f"Search failed: {str(e)}")

def download_json(analysis: InvestmentAnalysis):
    """Download analysis as JSON."""
    import json
    
    json_data = analysis.model_dump_json(indent=2)
    st.download_button(
        label="📄 Download JSON",
        data=json_data,
        file_name=f"investment_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )

def download_summary(analysis: InvestmentAnalysis):
    """Download analysis summary as text."""
    summary_text = f"""Investment Analysis Summary
Generated: {analysis.created_at.strftime('%Y-%m-%d %H:%M:%S')}

Query: {analysis.query}
Context: {analysis.context}

SUMMARY:
{analysis.findings.summary}

RECOMMENDATION:
{analysis.findings.recommendation}

CONFIDENCE: {analysis.findings.confidence_score:.1%}

KEY INSIGHTS:
{chr(10).join(f"• {insight}" for insight in analysis.findings.key_insights)}

RISK FACTORS:
{chr(10).join(f"• {risk}" for risk in analysis.findings.risk_factors)}

FINANCIAL METRICS:
{f"P/E Ratio: {analysis.findings.financial_metrics.pe_ratio:.2f}" if analysis.findings.financial_metrics.pe_ratio else ""}
{f"Debt/Equity: {analysis.findings.financial_metrics.debt_to_equity:.2f}" if analysis.findings.financial_metrics.debt_to_equity else ""}
{f"ROE: {analysis.findings.financial_metrics.return_on_equity:.2%}" if analysis.findings.financial_metrics.return_on_equity else ""}
"""
    
    st.download_button(
        label="📝 Download Summary",
        data=summary_text,
        file_name=f"investment_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain"
    )

if __name__ == "__main__":
    main()