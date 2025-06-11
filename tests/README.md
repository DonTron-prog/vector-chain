# Testing Framework for Pydantic-AI Investment Research

This directory contains comprehensive tests for the pydantic-ai investment research system.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests for individual components
│   ├── agents/             # Agent-specific tests
│   ├── tools/              # Tool-specific tests
│   └── models/             # Schema/model tests
├── integration/            # Integration tests between components
├── e2e/                   # End-to-end system tests
├── fixtures/              # Test data and fixtures
└── data/                  # Sample test data files
```

## Running Tests

### Install Testing Dependencies

```bash
poetry install --with dev
```

### Run All Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=agents --cov=tools --cov=models

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m e2e           # End-to-end tests only
```

### Test Categories

Tests are organized with markers:

- `@pytest.mark.unit` - Fast unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.network` - Tests requiring network access

### Environment Variables for Testing

```bash
# Required for E2E tests with real API calls
export OPENROUTER_API_KEY="your-key"
export OPENAI_API_KEY="your-key"

# Optional - enable external service tests
export TEST_EXTERNAL_SERVICES=true

# Test database path (optional)
export CHROMA_DB_PATH="./test_chroma_db"
```

## Test Types

### Unit Tests (`tests/unit/`)

Test individual components in isolation:

- **Models** (`test_schemas.py`): Pydantic model validation
- **Tools** (`test_calculator.py`): Individual tool functionality
- **Agents**: Agent behavior and logic

### Integration Tests (`tests/integration/`)

Test component interactions:

- **Workflow** (`test_research_workflow.py`): Complete research pipeline
- **Agent Integration**: Data flow between agents
- **Tool Coordination**: Multi-tool workflows

### End-to-End Tests (`tests/e2e/`)

Test complete system functionality:

- **Full System** (`test_full_system.py`): Complete user workflows
- **External Services**: Real API integrations (when enabled)
- **Error Recovery**: System resilience testing

## Fixtures and Mocks

### Key Fixtures (`conftest.py`)

- `mock_env_vars` - Mock environment variables
- `mock_openai_client` - Mock OpenAI API client
- `mock_chroma_client` - Mock ChromaDB client
- `mock_searxng_client` - Mock SearxNG client
- `sample_*` - Sample data objects for testing
- `knowledge_base_files` - Temporary test knowledge base

### External Service Mocking

Tests use comprehensive mocking for external services:

- **OpenAI/OpenRouter API**: Mocked responses for different scenarios
- **SearxNG**: Mocked search results
- **ChromaDB**: Mocked vector database operations
- **Web Scraping**: Mocked HTTP responses

## Test Data

### Sample Knowledge Base

Test fixtures include sample financial documents:

```
AAPL/
├── AAPL_10K_2023.txt
└── AAPL_10Q_Q3_2023.txt

MSFT/
├── MSFT_10K_2023.txt
└── MSFT_10Q_Q1_2024.txt
```

### Mock Responses

Realistic mock data for:
- Financial search results
- Company financial statements
- Market analysis content
- Web scraping responses

## Coverage Goals

Target coverage by component:

- **Models**: 95%+ (schema validation)
- **Tools**: 85%+ (core functionality + edge cases)
- **Agents**: 80%+ (main workflows + error handling)
- **Integration**: 70%+ (key user workflows)

## Continuous Integration

### GitHub Actions (Example)

```yaml
- name: Run Tests
  run: |
    poetry install --with dev
    pytest --cov=agents --cov=tools --cov=models --cov-report=xml

- name: Run E2E Tests
  env:
    OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
  run: |
    pytest -m e2e
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest-unit
        name: pytest-unit
        entry: pytest -m unit
        language: system
        pass_filenames: false
```

## Test Development Guidelines

### Writing Tests

1. **Use descriptive test names** that explain what is being tested
2. **Follow AAA pattern**: Arrange, Act, Assert
3. **Mock external dependencies** for unit tests
4. **Use fixtures** for common test data
5. **Test edge cases** and error conditions

### Test Organization

1. **Group related tests** in classes
2. **Use appropriate markers** for test categorization
3. **Keep tests independent** - no test dependencies
4. **Mock at the right level** - unit vs integration vs e2e

### Example Test Structure

```python
class TestCalculator:
    """Test financial calculator functionality."""
    
    def test_parse_valid_currency(self):
        """Test parsing valid currency values."""
        # Arrange
        value = "$1,234.56"
        
        # Act
        result = parse_financial_value(value)
        
        # Assert
        assert result == 1234.56
    
    @pytest.mark.asyncio
    async def test_calculate_ratios_integration(self, mock_dependencies):
        """Test ratio calculation with mocked dependencies."""
        # Test implementation
```

## Debugging Tests

### Running Individual Tests

```bash
# Run specific test file
pytest tests/unit/models/test_schemas.py

# Run specific test method
pytest tests/unit/models/test_schemas.py::TestFinancialMetrics::test_valid_metrics

# Run with verbose output
pytest -v tests/unit/

# Run with debug output
pytest -s tests/unit/
```

### Test Debugging

```bash
# Drop into debugger on failure
pytest --pdb

# Drop into debugger on first failure
pytest -x --pdb

# Show local variables in tracebacks
pytest -l
```

## Performance Testing

### Benchmarking

```bash
# Install pytest-benchmark
poetry add --group dev pytest-benchmark

# Run performance tests
pytest --benchmark-only
```

### Load Testing

For load testing the complete system:

```python
@pytest.mark.asyncio
async def test_concurrent_requests():
    """Test system under concurrent load."""
    tasks = [research_investment(query, context) for _ in range(10)]
    results = await asyncio.gather(*tasks)
    assert all(isinstance(r, InvestmentAnalysis) for r in results)
```

## Troubleshooting

### Common Issues

1. **Mock not working**: Check import paths and patch targets
2. **Async test failures**: Ensure `@pytest.mark.asyncio` decorator
3. **Environment variables**: Use `mock_env_vars` fixture
4. **External service errors**: Check service mocking setup

### Debug Commands

```bash
# Show test collection
pytest --collect-only

# Show fixture usage
pytest --fixtures

# Show available markers
pytest --markers
```