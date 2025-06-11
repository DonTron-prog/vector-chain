# Tests Directory

This directory contains all test files organized by category to eliminate duplication and improve maintainability.

## Directory Structure

```
tests/
├── README_TESTS.md        # This file
├── test_utils.py          # Shared test utilities and common functions
├── conftest.py            # Pytest fixtures (existing)
├── 
├── rag/                   # RAG and vector search tests
│   ├── simple_rag_test.py        # Interactive RAG testing
│   ├── test_rag_only.py          # Comprehensive RAG functionality tests
│   ├── test_rag_agent_only.py    # RAG-only agent tests
│   ├── test_chromadb_direct.py   # Direct ChromaDB testing
│   └── verify_rag_integration.py # RAG system verification
│
├── agents/                # Agent-specific tests
│   ├── test_research_agent_full.py # Full research agent with all tools
│   └── test_pydantic_ai.py         # Basic pydantic-ai functionality
│
├── integration/           # Integration and workflow tests
│   ├── main_with_rag_logging.py   # Main workflow with tool logging
│   └── test_main_force_rag.py     # Tests to force RAG usage in main.py
│
├── manual/                # Manual testing utilities
│   └── test_rag_with_logging.py   # Manual RAG testing with detailed logging
│
├── unit/                  # Unit tests (existing structure)
├── integration/           # Integration tests (existing structure)
└── e2e/                   # End-to-end tests (existing structure)
```

## Usage

### Quick RAG Testing
```bash
# Interactive RAG testing
python tests/rag/simple_rag_test.py

# Comprehensive RAG test suite
python tests/rag/test_rag_only.py

# Verify RAG integration
python tests/rag/verify_rag_integration.py
```

### Agent Testing
```bash
# Test RAG-only agent behavior
python tests/rag/test_rag_agent_only.py

# Test full research agent with all tools
python tests/agents/test_research_agent_full.py
```

### Integration Testing
```bash
# Test main.py workflow with logging
python tests/integration/main_with_rag_logging.py

# Force RAG usage in main.py
python tests/integration/test_main_force_rag.py
```

### Shared Utilities

All test files now use shared utilities from `test_utils.py` to eliminate duplication:

- `setup_test_dependencies()` - Standard dependency initialization
- `run_vector_search_test()` - Consistent vector search testing
- `print_search_results()` - Standardized result formatting
- `TestQueries` - Common test queries
- `TestDocumentTypes` - Standard document type filters
- `run_comprehensive_rag_test()` - Full test suite
- `add_rag_logging_to_function()` - Tool logging utilities

### Benefits of New Structure

1. **Reduced Duplication**: Common functionality moved to shared utilities
2. **Better Organization**: Tests grouped by functionality area
3. **Easier Maintenance**: Changes to test patterns only need to be made in one place
4. **Consistent Interface**: All tests use the same patterns and utilities
5. **Clear Purpose**: Each test file has a specific, well-defined purpose

## Test Categories

### RAG Tests (`rag/`)
Focus on vector search, ChromaDB functionality, and RAG system behavior:
- Direct vector search testing
- Agent-based RAG testing  
- ChromaDB integration verification
- Performance and edge case testing

### Agent Tests (`agents/`)
Test pydantic-ai agent behavior and tool usage:
- Individual agent functionality
- Tool selection and usage patterns
- Agent response quality and structure

### Integration Tests (`integration/`)
Test complete workflows and system integration:
- Main application workflow testing
- Multi-tool agent behavior
- End-to-end research workflows

### Manual Tests (`manual/`)
Utilities for manual testing and debugging:
- Detailed logging and debugging tools
- Interactive testing interfaces
- Development and troubleshooting utilities