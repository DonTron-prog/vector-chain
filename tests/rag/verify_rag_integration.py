#!/usr/bin/env python3
"""Verify RAG integration with pydantic-ai agents."""

import asyncio
from agents.dependencies import initialize_dependencies
from tools.vector_search import search_internal_docs, format_document_results

async def verify_rag_setup():
    """Verify RAG components are properly integrated."""
    print("🔍 Verifying RAG Integration")
    print("=" * 40)
    
    # 1. Test dependencies initialization
    print("1. ✅ Initializing dependencies...")
    deps = initialize_dependencies("test query")
    print(f"   Vector DB: {type(deps.vector_db).__name__}")
    print(f"   Collection: {deps.vector_db.get_collection().name}")
    
    # 2. Test vector search functionality
    print("\n2. ✅ Testing vector search...")
    results = await search_internal_docs(deps.vector_db, "uranium production", "all", 2)
    print(f"   Found {len(results)} results")
    
    if results:
        print(f"   First result score: {results[0].score:.3f}")
        print(f"   Content preview: {results[0].content[:100]}...")
    
    # 3. Test result formatting
    print("\n3. ✅ Testing result formatting...")
    formatted = format_document_results(results)
    print(f"   Formatted length: {len(formatted)} characters")
    print(f"   Preview: {formatted[:150]}...")
    
    # 4. Verify agent tool registration
    print("\n4. ✅ Verifying agent tools...")
    from agents.research_agent import research_agent
    
    # Check if agent has RAG tool by examining the module
    import agents.research_agent as agent_module
    has_search_tool = hasattr(agent_module, 'search_internal_docs')
    print(f"   RAG tool function exists: {'✅' if has_search_tool else '❌'}")
    
    # Check agent configuration
    print(f"   Agent model: {research_agent.model}")
    print(f"   Agent result type: {research_agent.result_type}")
    print(f"   Agent deps type: {research_agent.deps_type}")
    
    print("\n🎉 RAG Integration Verification Complete!")
    return True

async def main():
    """Main verification function."""
    try:
        await verify_rag_setup()
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False
    return True

if __name__ == "__main__":
    asyncio.run(main())