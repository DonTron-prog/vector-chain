"""
Integration tests for web search + scraper workflow.
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from models.schemas import WebSearchResult
from tools.web_search import search_web, format_search_results
from tools.web_scraper import scrape_webpage, extract_article_content, extract_tables
from bs4 import BeautifulSoup


class TestWebSearchScraperIntegration:
    """Test integration between web search and scraper tools."""
    
    @pytest.mark.asyncio
    async def test_search_to_scrape_workflow(self):
        """Test complete workflow from search to content scraping."""
        # Mock SearxNG client with investment-related results
        mock_searxng_client = AsyncMock()
        mock_searxng_client.search.return_value = {
            "results": [
                {
                    "url": "https://investornews.com/apple-q3-2023-earnings",
                    "title": "Apple Reports Strong Q3 2023 Earnings",
                    "content": "Apple Inc. announced quarterly results beating analyst expectations...",
                    "publishedDate": "2023-08-03"
                },
                {
                    "url": "https://financialanalysis.com/apple-investment-outlook",
                    "title": "Apple Investment Outlook: Buy or Hold?",
                    "content": "Following strong earnings, analysts are divided on Apple's future...",
                    "publishedDate": "2023-08-04"
                }
            ]
        }
        
        # Step 1: Search for investment-related content
        search_results = await search_web(
            mock_searxng_client,
            "Apple Q3 2023 earnings investment analysis",
            category="news",
            max_results=2
        )
        
        assert len(search_results) == 2
        assert isinstance(search_results[0], WebSearchResult)
        assert "apple-q3-2023-earnings" in search_results[0].url
        assert "Strong Q3 2023 Earnings" in search_results[0].title
        
        # Step 2: Scrape detailed content from first result
        mock_detailed_html = """
        <html>
            <body>
                <article>
                    <h1>Apple Reports Strong Q3 2023 Earnings</h1>
                    <div class="article-content">
                        <p>Apple Inc. (NASDAQ: AAPL) today announced financial results for Q3 2023.</p>
                        <p>Key highlights include:</p>
                        <ul>
                            <li>Total revenue of $81.8 billion, up 1% year-over-year</li>
                            <li>Quarterly earnings per share of $1.26, up 5% year-over-year</li>
                            <li>iPhone revenue of $39.7 billion</li>
                            <li>Services revenue of $21.2 billion, up 8% year-over-year</li>
                        </ul>
                        <blockquote>"We are pleased with our Q3 results," said Tim Cook, Apple's CEO.</blockquote>
                        <h3>Financial Analysis</h3>
                        <p>The company's gross margin expanded to 44.5%, demonstrating pricing power.</p>
                        <p>Free cash flow for the quarter was $20.9 billion.</p>
                    </div>
                </article>
                <aside>Advertisement content</aside>
            </body>
        </html>
        """
        
        with patch('tools.web_scraper.fetch_and_parse') as mock_fetch:
            mock_fetch.return_value = BeautifulSoup(mock_detailed_html, 'html.parser')
            
            scraped_content = await scrape_webpage(
                search_results[0].url,
                content_type="article"
            )
            
            # Verify comprehensive content extraction
            assert "Content from https://investornews.com/apple-q3-2023-earnings:" in scraped_content
            assert "Total revenue of $81.8 billion" in scraped_content
            assert "earnings per share of $1.26" in scraped_content
            assert "Tim Cook" in scraped_content
            assert "Free cash flow for the quarter was $20.9 billion" in scraped_content
            
            # Verify unwanted content was filtered out
            assert "Advertisement content" not in scraped_content
        
        # Step 3: Scrape financial table from second result
        mock_table_html = """
        <html>
            <body>
                <div class="financial-data">
                    <h2>Apple Financial Metrics Comparison</h2>
                    <table class="metrics-table">
                        <thead>
                            <tr>
                                <th>Metric</th>
                                <th>Q3 2023</th>
                                <th>Q3 2022</th>
                                <th>Change</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>Revenue</td>
                                <td>$81.8B</td>
                                <td>$82.9B</td>
                                <td>-1.3%</td>
                            </tr>
                            <tr>
                                <td>Gross Margin</td>
                                <td>44.5%</td>
                                <td>43.3%</td>
                                <td>+1.2pp</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </body>
        </html>
        """
        
        with patch('tools.web_scraper.fetch_and_parse') as mock_fetch_table:
            mock_fetch_table.return_value = BeautifulSoup(mock_table_html, 'html.parser')
            
            table_content = await scrape_webpage(
                search_results[1].url,
                content_type="table"
            )
            
            # Verify table extraction
            assert "Content from https://financialanalysis.com/apple-investment-outlook:" in table_content
            assert "Table 1:" in table_content
            assert "Metric | Q3 2023 | Q3 2022 | Change" in table_content
            assert "Revenue | $81.8B | $82.9B | -1.3%" in table_content
            assert "Gross Margin | 44.5% | 43.3% | +1.2pp" in table_content
    
    @pytest.mark.asyncio
    async def test_investment_research_search_scrape_pipeline(self):
        """Test realistic investment research pipeline."""
        # Mock comprehensive investment search
        mock_searxng_client = AsyncMock()
        mock_searxng_client.search.return_value = {
            "results": [
                {
                    "url": "https://seekingalpha.com/article/apple-investment-thesis",
                    "title": "Apple: A Compelling Long-Term Investment Thesis",
                    "content": "Apple's ecosystem and brand loyalty create sustainable competitive advantages...",
                    "publishedDate": "2023-08-05"
                },
                {
                    "url": "https://motleyfool.com/apple-stock-analysis-2023",
                    "title": "Is Apple Stock a Buy in 2023?",
                    "content": "With strong financials and growing services revenue...",
                    "publishedDate": "2023-08-06"
                },
                {
                    "url": "https://marketwatch.com/apple-earnings-reaction",
                    "title": "Wall Street Reacts to Apple's Q3 Earnings",
                    "content": "Analysts raise price targets following solid quarterly results...",
                    "publishedDate": "2023-08-04"
                }
            ]
        }
        
        # Search for investment analysis
        investment_search_results = await search_web(
            mock_searxng_client,
            "Apple stock investment analysis buy recommendation 2023",
            category="general",
            max_results=3
        )
        
        assert len(investment_search_results) == 3
        
        # Scrape investment thesis content
        investment_thesis_html = """
        <html>
            <body>
                <main>
                    <article>
                        <h1>Apple: A Compelling Long-Term Investment Thesis</h1>
                        <div class="investment-analysis">
                            <h2>Key Investment Strengths</h2>
                            <ul>
                                <li><strong>Ecosystem Lock-in:</strong> Apple's integrated hardware and software create high switching costs</li>
                                <li><strong>Brand Premium:</strong> Consistent ability to charge premium prices across product lines</li>
                                <li><strong>Services Growth:</strong> High-margin services segment growing at 15%+ annually</li>
                                <li><strong>Capital Allocation:</strong> Strong track record of shareholder returns via dividends and buybacks</li>
                            </ul>
                            
                            <h2>Financial Highlights</h2>
                            <p>Apple maintains a fortress balance sheet with over $160 billion in cash and investments.</p>
                            <p>Return on invested capital consistently exceeds 25%, demonstrating efficient capital deployment.</p>
                            
                            <h2>Valuation Assessment</h2>
                            <p>Trading at 28x forward earnings, Apple commands a premium but justifiable valuation.</p>
                            <p>Price-to-sales ratio of 7.2x reflects market confidence in sustainable growth.</p>
                            
                            <h2>Investment Recommendation</h2>
                            <p><strong>Rating: BUY</strong></p>
                            <p>Target Price: $210 (12-month horizon)</p>
                            <p>Apple remains a core holding for long-term wealth creation despite near-term headwinds.</p>
                        </div>
                    </article>
                </main>
            </body>
        </html>
        """
        
        with patch('tools.web_scraper.fetch_and_parse') as mock_fetch:
            mock_fetch.return_value = BeautifulSoup(investment_thesis_html, 'html.parser')
            
            investment_content = await scrape_webpage(
                investment_search_results[0].url,
                content_type="article"
            )
            
            # Verify comprehensive investment analysis extraction
            assert "Compelling Long-Term Investment Thesis" in investment_content
            assert "Ecosystem Lock-in" in investment_content
            assert "Services Growth" in investment_content
            assert "Return on invested capital consistently exceeds 25%" in investment_content
            assert "Trading at 28x forward earnings" in investment_content
            assert "Rating: BUY" in investment_content
            assert "Target Price: $210" in investment_content
    
    @pytest.mark.asyncio
    async def test_market_news_search_and_content_extraction(self):
        """Test market news search and detailed content extraction."""
        # Mock news search results
        mock_searxng_client = AsyncMock()
        mock_searxng_client.search.return_value = {
            "results": [
                {
                    "url": "https://reuters.com/markets/apple-stock-rises-earnings",
                    "title": "Apple stock rises 3% after strong quarterly earnings",
                    "content": "Apple shares gained in after-hours trading following better-than-expected results...",
                    "publishedDate": "2023-08-03"
                },
                {
                    "url": "https://bloomberg.com/apple-services-growth-outlook",
                    "title": "Apple's Services Business Shows Resilience Amid iPhone Slowdown",
                    "content": "The tech giant's services revenue continues to grow despite hardware challenges...",
                    "publishedDate": "2023-08-03"
                }
            ]
        }
        
        # Search for market news
        news_results = await search_web(
            mock_searxng_client,
            "Apple stock market reaction earnings Q3 2023",
            category="news",
            max_results=2
        )
        
        # Verify news search parameters
        mock_searxng_client.search.assert_called_once()
        call_args = mock_searxng_client.search.call_args
        assert call_args[1]["categories"] == "news"
        assert "engines" in call_args[1]
        
        # Scrape detailed market reaction content
        market_reaction_html = """
        <html>
            <body>
                <article class="news-article">
                    <h1>Apple stock rises 3% after strong quarterly earnings</h1>
                    <div class="article-meta">
                        <span class="timestamp">August 3, 2023 4:15 PM EDT</span>
                        <span class="author">By Tech Reporter</span>
                    </div>
                    <div class="article-body">
                        <p>Apple Inc. shares surged 3% in extended trading Thursday after the iPhone maker reported quarterly results that exceeded Wall Street expectations.</p>
                        
                        <h3>Key Market Reactions:</h3>
                        <ul>
                            <li>Stock price up 3% to $189.70 in after-hours trading</li>
                            <li>Options market implies 4-5% move by Friday close</li>
                            <li>Institutional investors adding positions post-earnings</li>
                        </ul>
                        
                        <h3>Analyst Commentary:</h3>
                        <blockquote>"Apple continues to demonstrate resilience in a challenging macro environment," said Morgan Stanley analyst Katy Huberty.</blockquote>
                        <blockquote>"The Services segment strength offsets iPhone weakness," noted Wedbush analyst Dan Ives.</blockquote>
                        
                        <h3>Key Financial Metrics:</h3>
                        <p>Revenue of $81.8 billion beat estimates of $81.7 billion.</p>
                        <p>Earnings per share of $1.26 exceeded forecasts of $1.19.</p>
                        <p>Gross margin of 44.5% showed continued pricing power.</p>
                    </div>
                </article>
            </body>
        </html>
        """
        
        with patch('tools.web_scraper.fetch_and_parse') as mock_fetch:
            mock_fetch.return_value = BeautifulSoup(market_reaction_html, 'html.parser')
            
            market_content = await scrape_webpage(
                news_results[0].url,
                content_type="article"
            )
            
            # Verify market reaction details
            assert "surged 3% in extended trading" in market_content
            assert "Stock price up 3% to $189.70" in market_content
            assert "Morgan Stanley analyst Katy Huberty" in market_content
            assert "Revenue of $81.8 billion beat estimates" in market_content
            assert "Earnings per share of $1.26 exceeded forecasts" in market_content
    
    @pytest.mark.asyncio
    async def test_error_handling_in_search_scrape_workflow(self):
        """Test error handling across search and scraping workflow."""
        
        # Test 1: Search returns no results
        mock_searxng_empty = AsyncMock()
        mock_searxng_empty.search.return_value = {"results": []}
        
        empty_results = await search_web(
            mock_searxng_empty,
            "very specific query with no results"
        )
        
        assert len(empty_results) == 0
        
        # Test 2: Search succeeds but scraping fails
        mock_searxng_client = AsyncMock()
        mock_searxng_client.search.return_value = {
            "results": [
                {
                    "url": "https://example.com/protected-content",
                    "title": "Protected Content",
                    "content": "Content preview...",
                    "publishedDate": "2023-08-01"
                }
            ]
        }
        
        search_results = await search_web(mock_searxng_client, "test query")
        assert len(search_results) == 1
        
        # Mock scraping failure
        with patch('tools.web_scraper.fetch_and_parse') as mock_fetch:
            mock_fetch.side_effect = Exception("403 Forbidden - Access denied")
            
            failed_scrape = await scrape_webpage(
                search_results[0].url,
                content_type="article"
            )
            
            assert "Failed to scrape" in failed_scrape
            assert "403 Forbidden" in failed_scrape
        
        # Test 3: Successful search and scrape but no meaningful content
        minimal_html = """
        <html>
            <body>
                <div>Very minimal content with no substantial information.</div>
            </body>
        </html>
        """
        
        with patch('tools.web_scraper.fetch_and_parse') as mock_fetch:
            mock_fetch.return_value = BeautifulSoup(minimal_html, 'html.parser')
            
            minimal_content = await scrape_webpage(
                search_results[0].url,
                content_type="article"
            )
            
            # Should still return content, just minimal
            assert "Very minimal content" in minimal_content
            assert len(minimal_content) > 50  # Should include URL prefix
    
    @pytest.mark.asyncio
    async def test_search_result_prioritization_and_scraping(self):
        """Test prioritizing high-quality search results for scraping."""
        # Mock search with mixed quality results
        mock_searxng_client = AsyncMock()
        mock_searxng_client.search.return_value = {
            "results": [
                {
                    "url": "https://reputable-source.com/detailed-analysis",
                    "title": "Comprehensive Apple Investment Analysis 2023",
                    "content": "In-depth analysis of Apple's investment prospects with detailed financial metrics and outlook...",
                    "publishedDate": "2023-08-05"
                },
                {
                    "url": "https://blog.example.com/quick-thoughts",
                    "title": "Quick thoughts on Apple",
                    "content": "Brief opinion piece...",
                    "publishedDate": "2023-08-01"
                },
                {
                    "url": "https://financial-times.com/apple-deep-dive",
                    "title": "Apple's Strategic Position: A Deep Dive Analysis",
                    "content": "Comprehensive examination of Apple's competitive position, financial health, and future prospects...",
                    "publishedDate": "2023-08-04"
                }
            ]
        }
        
        # Search for comprehensive analysis
        search_results = await search_web(
            mock_searxng_client,
            "Apple comprehensive investment analysis 2023",
            max_results=3
        )
        
        assert len(search_results) == 3
        
        # Prioritize scraping based on content quality indicators
        high_quality_results = [
            result for result in search_results 
            if any(keyword in result.title.lower() for keyword in ["comprehensive", "detailed", "analysis", "deep dive"])
            and len(result.content) > 50
        ]
        
        assert len(high_quality_results) >= 2
        
        # Scrape the highest quality result
        comprehensive_html = """
        <html>
            <body>
                <article>
                    <h1>Comprehensive Apple Investment Analysis 2023</h1>
                    <div class="executive-summary">
                        <h2>Executive Summary</h2>
                        <p>Apple remains a compelling long-term investment despite near-term challenges.</p>
                    </div>
                    <div class="financial-analysis">
                        <h2>Financial Analysis</h2>
                        <p>Revenue growth has moderated but remains positive at 1-3% annually.</p>
                        <p>Margin expansion opportunities exist through services mix shift.</p>
                    </div>
                    <div class="investment-recommendation">
                        <h2>Investment Recommendation</h2>
                        <p>We maintain a BUY rating with a 12-month price target of $205.</p>
                    </div>
                </article>
            </body>
        </html>
        """
        
        with patch('tools.web_scraper.fetch_and_parse') as mock_fetch:
            mock_fetch.return_value = BeautifulSoup(comprehensive_html, 'html.parser')
            
            detailed_content = await scrape_webpage(
                high_quality_results[0].url,
                content_type="article"
            )
            
            # Verify comprehensive content extraction
            assert "Executive Summary" in detailed_content
            assert "Financial Analysis" in detailed_content
            assert "Investment Recommendation" in detailed_content
            assert "BUY rating with a 12-month price target of $205" in detailed_content