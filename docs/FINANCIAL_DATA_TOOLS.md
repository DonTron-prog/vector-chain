# Financial Data Tools Integration

This document describes the real-time financial data tools integrated into the investment research agent.

## Overview

The financial data tools provide real-time market data, historical analysis, and fundamental financial information through the Alpha Vantage API. These tools are seamlessly integrated into the research agent's natural tool loop.

## Setup

1. **Get an API Key**: Register for a free Alpha Vantage API key at https://www.alphavantage.co/support/#api-key

2. **Set Environment Variable**:
   ```bash
   export ALPHA_VANTAGE_API_KEY="your-api-key-here"
   ```

3. **Verify Setup**: Run the test script to verify the integration:
   ```bash
   python test_financial_tools.py
   ```

## Available Tools

### 1. get_stock_quote
Retrieves real-time stock quotes with current market data.

**Returns:**
- Current price
- Price change and percentage
- Trading volume
- Day's high/low
- Previous close

**Example Usage in Agent:**
```python
"Get the current stock price for AAPL"
```

### 2. get_stock_history
Analyzes historical price trends for technical analysis.

**Parameters:**
- `symbol`: Stock ticker (e.g., 'AAPL')
- `period`: Time interval ('daily', 'weekly', 'monthly')

**Returns:**
- Recent price performance
- Average volume
- Price range analysis
- Trend indicators

**Example Usage in Agent:**
```python
"Analyze the weekly price trends for MSFT"
```

### 3. get_stock_fundamentals
Retrieves financial statement data for fundamental analysis.

**Returns:**
- Total revenue
- Net income
- Earnings per share (EPS)
- Operating income
- Gross profit

**Example Usage in Agent:**
```python
"Get the latest financial fundamentals for GOOGL"
```

## Integration with Research Agent

The financial data tools are automatically available to the research agent and can be used naturally within the agent's tool loop. The agent will intelligently decide when to use these tools based on the research query.

### Example Research Queries:

1. **Basic Quote Request**:
   ```
   "What's the current price of Apple stock?"
   ```

2. **Trend Analysis**:
   ```
   "Analyze Tesla's price performance over the last month"
   ```

3. **Fundamental Analysis**:
   ```
   "Compare the revenue growth of Microsoft and Google"
   ```

4. **Comprehensive Analysis**:
   ```
   "Should I invest in NVDA? Analyze current price, trends, and fundamentals"
   ```

## Rate Limits

The free Alpha Vantage API tier has the following limits:
- 5 API calls per minute
- 500 API calls per day

The implementation includes automatic rate limiting to stay within these limits.

## Error Handling

If the ALPHA_VANTAGE_API_KEY is not set:
- The agent will log a warning
- Financial data tools will be disabled
- The agent will continue functioning with other tools

## Data Models

The financial data is structured using Pydantic models:

- `StockQuote`: Real-time quote data
- `HistoricalData`: Historical price information
- `FinancialStatement`: Income statements, balance sheets, cash flow
- `TechnicalIndicators`: SMA, EMA, RSI, MACD, etc.
- `FinancialDataResponse`: Comprehensive response wrapper

## Testing

Run the included test script to verify the integration:

```bash
python test_financial_tools.py
```

This will test:
1. Real-time quote retrieval
2. Historical data analysis
3. Financial fundamentals
4. Combined multi-tool analysis

## Best Practices

1. **Use Specific Symbols**: Always use exact stock ticker symbols (e.g., 'AAPL' not 'Apple')
2. **Batch Requests**: When analyzing multiple stocks, the agent will batch similar requests
3. **Cache Results**: The agent maintains context to avoid redundant API calls
4. **Combine with Other Tools**: Financial data works best when combined with document search and web scraping

## Troubleshooting

1. **"API key not found" error**: Ensure ALPHA_VANTAGE_API_KEY is set in your environment
2. **"Rate limit exceeded" error**: Wait 60 seconds between batches of requests
3. **"Symbol not found" error**: Verify the stock ticker symbol is correct
4. **"No data available" error**: Some international stocks may not be available

## Future Enhancements

- Additional technical indicators (Bollinger Bands, VWAP, etc.)
- Options chain data
- Cryptocurrency support
- Economic indicators (GDP, inflation, etc.)
- Sector comparison tools