"""
Unit tests for web scraper tool.
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from bs4 import BeautifulSoup
from tools.web_scraper import (
    fetch_and_parse,
    extract_article_content,
    extract_tables,
    clean_text,
    scrape_webpage
)


class AsyncContextManager:
    """Helper class to create proper async context managers for mocking."""
    
    def __init__(self, return_value):
        self.return_value = return_value
    
    async def __aenter__(self):
        return self.return_value
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None


class TestFetchAndParse:
    """Test webpage fetching and parsing."""
    
    @pytest.mark.asyncio
    async def test_fetch_success(self):
        """Test successful webpage fetch and parse."""
        mock_html = """
        <html>
            <body>
                <h1>Test Article</h1>
                <p>This is test content.</p>
            </body>
        </html>
        """
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            # Create a mock response
            mock_response = AsyncMock()
            mock_response.text = AsyncMock(return_value=mock_html)
            mock_response.status = 200
            
            # Create a mock session instance
            mock_session = AsyncMock()
            
            # Use our helper class for proper async context manager
            mock_session.get = MagicMock(return_value=AsyncContextManager(mock_response))
            
            # Make the session itself a context manager
            mock_session_class.return_value = AsyncContextManager(mock_session)
            
            soup = await fetch_and_parse("https://example.com/article")
            
            assert isinstance(soup, BeautifulSoup)
            assert soup.find('h1').text == "Test Article"
            assert soup.find('p').text == "This is test content."
    
    @pytest.mark.asyncio
    async def test_fetch_with_custom_timeout(self):
        """Test fetch with custom timeout."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            # Create a mock response
            mock_response = AsyncMock()
            mock_response.text = AsyncMock(return_value="<html></html>")
            mock_response.status = 200
            
            # Create a mock session instance
            mock_session = AsyncMock()
            
            # Use our helper class for proper async context manager
            mock_session.get = MagicMock(return_value=AsyncContextManager(mock_response))
            
            # Make the session itself a context manager
            mock_session_class.return_value = AsyncContextManager(mock_session)
            
            await fetch_and_parse("https://example.com", timeout=60)
            
            # Verify timeout was passed to the request
            mock_session.get.assert_called_once()
            call_args = mock_session.get.call_args
            assert call_args[1]['timeout'] == 60


class TestExtractArticleContent:
    """Test article content extraction."""
    
    def test_extract_from_article_tag(self):
        """Test extraction from article tag."""
        html = """
        <html>
            <body>
                <article>
                    <h1>Investment Analysis</h1>
                    <p>Apple Inc. reported strong quarterly results with revenue of $81.8 billion.</p>
                    <p>The company's services segment continued to show robust growth.</p>
                </article>
                <footer>Copyright notice</footer>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        content = extract_article_content(soup)
        
        assert "Investment Analysis" in content
        assert "Apple Inc. reported strong quarterly results" in content
        assert "services segment continued" in content
        assert "Copyright notice" not in content
    
    def test_extract_from_main_tag(self):
        """Test extraction from main tag when no article tag."""
        html = """
        <html>
            <body>
                <nav>Navigation menu</nav>
                <main>
                    <h2>Market Update</h2>
                    <p>Technology stocks gained ground today as investors showed renewed confidence.</p>
                </main>
                <aside>Sidebar content</aside>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        print("DEBUG: Original HTML structure:")
        print(soup.prettify())
        
        content = extract_article_content(soup)
        print("DEBUG: Extracted content:")
        print(repr(content))
        print("DEBUG: Content length:", len(content))
        
        # Check what's actually in the content
        print("DEBUG: Checking content assertions:")
        print("  'Market Update' in content:", "Market Update" in content)
        print("  'Technology stocks gained ground' in content:", "Technology stocks gained ground" in content)
        print("  'Navigation menu' in content:", "Navigation menu" in content)
        print("  'Sidebar content' in content:", "Sidebar content" in content)
        
        assert "Market Update" in content
        assert "Technology stocks gained ground" in content
        assert "Navigation menu" not in content
        assert "Sidebar content" not in content
    
    def test_extract_from_content_class(self):
        """Test extraction from elements with content classes."""
        html = """
        <html>
            <body>
                <div class="header">Site header</div>
                <div class="article-content">
                    <h1>Financial News</h1>
                    <p>Microsoft announced its quarterly earnings, beating analyst expectations with revenue of $56.2 billion.</p>
                </div>
                <div class="sidebar">Advertisement</div>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        content = extract_article_content(soup)
        
        assert "Financial News" in content
        assert "Microsoft announced its quarterly earnings" in content
        assert "Site header" not in content
        assert "Advertisement" not in content
    
    def test_extract_removes_scripts_and_styles(self):
        """Test that scripts and styles are removed."""
        html = """
        <html>
            <body>
                <script>console.log('tracking code');</script>
                <style>body { margin: 0; }</style>
                <article>
                    <p>This is the actual content we want to extract.</p>
                </article>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        content = extract_article_content(soup)
        
        assert "This is the actual content" in content
        assert "console.log" not in content
        assert "margin: 0" not in content
    
    def test_extract_fallback_to_body(self):
        """Test fallback to body content when no specific selectors match."""
        html = """
        <html>
            <body>
                <div>
                    <p>Some content without specific article structure.</p>
                    <p>This should still be extracted as fallback.</p>
                </div>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        content = extract_article_content(soup)
        
        assert "Some content without specific" in content
        assert "This should still be extracted" in content
    
    def test_extract_minimum_content_length(self):
        """Test that short content is skipped in favor of longer content."""
        html = """
        <html>
            <body>
                <article>Short</article>
                <main>
                    <p>This is a much longer piece of content that should be selected over the short article tag because it contains more substantial information about the topic.</p>
                </main>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        content = extract_article_content(soup)
        
        # Should get the longer main content, not the short article
        assert "much longer piece of content" in content
        assert len(content) > 50


class TestExtractTables:
    """Test table data extraction."""
    
    def test_extract_single_table(self):
        """Test extracting a single table."""
        html = """
        <html>
            <body>
                <table>
                    <tr>
                        <th>Metric</th>
                        <th>Q3 2023</th>
                        <th>Q2 2023</th>
                    </tr>
                    <tr>
                        <td>Revenue</td>
                        <td>$81.8B</td>
                        <td>$81.5B</td>
                    </tr>
                    <tr>
                        <td>Net Income</td>
                        <td>$19.9B</td>
                        <td>$19.4B</td>
                    </tr>
                </table>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        tables = extract_tables(soup)
        
        assert "Table 1:" in tables
        assert "Metric | Q3 2023 | Q2 2023" in tables
        assert "Revenue | $81.8B | $81.5B" in tables
        assert "Net Income | $19.9B | $19.4B" in tables
    
    def test_extract_multiple_tables(self):
        """Test extracting multiple tables."""
        html = """
        <html>
            <body>
                <table>
                    <tr><th>Revenue</th><th>Amount</th></tr>
                    <tr><td>Q3</td><td>$81.8B</td></tr>
                </table>
                <p>Some text between tables</p>
                <table>
                    <tr><th>Expenses</th><th>Amount</th></tr>
                    <tr><td>R&D</td><td>$7.8B</td></tr>
                </table>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        tables = extract_tables(soup)
        
        assert "Table 1:" in tables
        assert "Table 2:" in tables
        assert "Revenue | Amount" in tables
        assert "Expenses | Amount" in tables
        assert "$81.8B" in tables
        assert "$7.8B" in tables
    
    def test_extract_no_tables(self):
        """Test when no tables are found."""
        html = """
        <html>
            <body>
                <p>This page has no tables, just regular content.</p>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        tables = extract_tables(soup)
        
        assert tables == "No tables found."
    
    def test_extract_table_limit(self):
        """Test that only first 3 tables are extracted."""
        html = """
        <html>
            <body>
                <table><tr><td>Table 1</td></tr></table>
                <table><tr><td>Table 2</td></tr></table>
                <table><tr><td>Table 3</td></tr></table>
                <table><tr><td>Table 4</td></tr></table>
                <table><tr><td>Table 5</td></tr></table>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        tables = extract_tables(soup)
        
        assert "Table 1:" in tables
        assert "Table 2:" in tables  
        assert "Table 3:" in tables
        assert "Table 4:" not in tables  # Should be limited to first 3


class TestCleanText:
    """Test text cleaning functionality."""
    
    def test_clean_excessive_whitespace(self):
        """Test removal of excessive whitespace."""
        text = "This  has     multiple   spaces\n\n\nand\t\tlines."
        cleaned = clean_text(text)
        
        assert cleaned == "This has multiple spaces and lines."
    
    def test_clean_special_characters(self):
        """Test removal of problematic special characters."""
        text = "Text with émojis 🚀 and special chars ™ © ® etc."
        cleaned = clean_text(text)
        
        # Should keep basic punctuation but remove special symbols
        assert "Text with" in cleaned
        assert "🚀" not in cleaned
        assert "™" not in cleaned
    
    def test_clean_preserves_basic_punctuation(self):
        """Test that basic punctuation is preserved."""
        text = "Keep this: periods, commas; semicolons! And (parentheses) - dashes."
        cleaned = clean_text(text)
        
        assert "Keep this:" in cleaned
        assert "periods, commas;" in cleaned
        assert "(parentheses)" in cleaned
        assert "- dashes." in cleaned
    
    def test_clean_empty_text(self):
        """Test cleaning empty or whitespace-only text."""
        assert clean_text("") == ""
        assert clean_text("   \n\t   ") == ""


class TestScrapeWebpage:
    """Test complete webpage scraping workflow."""
    
    @pytest.mark.asyncio
    async def test_scrape_article_content(self):
        """Test scraping article content."""
        mock_html = """
        <html>
            <body>
                <article>
                    <h1>Apple Stock Analysis</h1>
                    <p>Apple Inc. shares rose 3% following strong quarterly earnings that beat analyst expectations.</p>
                    <p>Revenue for the quarter reached $81.8 billion, up from $81.4 billion year-over-year.</p>
                </article>
            </body>
        </html>
        """
        
        with patch('tools.web_scraper.fetch_and_parse') as mock_fetch:
            mock_fetch.return_value = BeautifulSoup(mock_html, 'html.parser')
            
            result = await scrape_webpage("https://example.com/apple-analysis", "article")
            
            assert "Content from https://example.com/apple-analysis:" in result
            assert "Apple Stock Analysis" in result
            assert "shares rose 3%" in result
            assert "$81.8 billion" in result
    
    @pytest.mark.asyncio
    async def test_scrape_table_content(self):
        """Test scraping table content."""
        mock_html = """
        <html>
            <body>
                <table>
                    <tr><th>Quarter</th><th>Revenue</th><th>Growth</th></tr>
                    <tr><td>Q3 2023</td><td>$81.8B</td><td>1.4%</td></tr>
                    <tr><td>Q2 2023</td><td>$81.5B</td><td>-1.4%</td></tr>
                </table>
            </body>
        </html>
        """
        
        with patch('tools.web_scraper.fetch_and_parse') as mock_fetch:
            mock_fetch.return_value = BeautifulSoup(mock_html, 'html.parser')
            
            result = await scrape_webpage("https://example.com/data", "table")
            
            assert "Content from https://example.com/data:" in result
            assert "Table 1:" in result
            assert "Quarter | Revenue | Growth" in result
            assert "Q3 2023 | $81.8B | 1.4%" in result
    
    @pytest.mark.asyncio
    async def test_scrape_error_handling(self):
        """Test error handling during scraping."""
        with patch('tools.web_scraper.fetch_and_parse') as mock_fetch:
            mock_fetch.side_effect = Exception("Network timeout")
            
            result = await scrape_webpage("https://example.com/error", "article")
            
            assert "Failed to scrape https://example.com/error:" in result
            assert "Network timeout" in result
    
    @pytest.mark.asyncio
    async def test_scrape_full_content_mode(self):
        """Test scraping with full content mode."""
        mock_html = """
        <html>
            <body>
                <div>
                    <h1>Investment Report</h1>
                    <p>Comprehensive analysis of market trends and investment opportunities.</p>
                </div>
            </body>
        </html>
        """
        
        with patch('tools.web_scraper.fetch_and_parse') as mock_fetch:
            mock_fetch.return_value = BeautifulSoup(mock_html, 'html.parser')
            
            result = await scrape_webpage("https://example.com/report", "full")
            
            assert "Investment Report" in result
            assert "Comprehensive analysis" in result


class TestWebScraperIntegration:
    """Integration tests for web scraper functionality."""
    
    @pytest.mark.asyncio
    async def test_realistic_financial_page_scraping(self):
        """Test scraping a realistic financial news page."""
        mock_html = """
        <html>
            <head>
                <title>Apple Q3 Earnings Beat Estimates - Financial News</title>
            </head>
            <body>
                <header>
                    <nav>Site navigation</nav>
                </header>
                <main>
                    <article class="article-content">
                        <h1>Apple Reports Strong Q3 2023 Results</h1>
                        <div class="article-meta">Published: August 3, 2023</div>
                        <p>Apple Inc. (NASDAQ: AAPL) today announced financial results for its fiscal 2023 third quarter ended July 1, 2023.</p>
                        <p>The company posted quarterly revenue of $81.8 billion, down 1 percent year-over-year, and quarterly earnings per share of $1.26, up 5 percent year-over-year.</p>
                        <blockquote>"We are happy to report that we had an all-time revenue record in Services during the quarter," said Tim Cook, Apple's CEO.</blockquote>
                        <div class="financial-highlights">
                            <h3>Key Financial Metrics:</h3>
                            <ul>
                                <li>iPhone revenue: $39.7 billion</li>
                                <li>Services revenue: $21.2 billion</li>
                                <li>Mac revenue: $6.8 billion</li>
                            </ul>
                        </div>
                    </article>
                </main>
                <aside>
                    <div class="ad">Advertisement content</div>
                </aside>
                <footer>Copyright 2023</footer>
            </body>
        </html>
        """
        
        with patch('tools.web_scraper.fetch_and_parse') as mock_fetch:
            mock_fetch.return_value = BeautifulSoup(mock_html, 'html.parser')
            
            result = await scrape_webpage("https://financialnews.com/apple-q3-2023", "article")
            
            # Should extract main article content
            assert "Apple Reports Strong Q3 2023 Results" in result
            assert "quarterly revenue of $81.8 billion" in result
            assert "earnings per share of $1.26" in result
            assert "Tim Cook" in result
            assert "iPhone revenue: $39.7 billion" in result
            
            # Should exclude navigation, ads, and footer
            assert "Site navigation" not in result
            assert "Advertisement content" not in result
            assert "Copyright 2023" not in result
    
    @pytest.mark.asyncio 
    async def test_financial_table_extraction(self):
        """Test extracting financial data tables."""
        mock_html = """
        <html>
            <body>
                <div class="financial-data">
                    <h2>Quarterly Results Comparison</h2>
                    <table class="earnings-table">
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
                                <td>Total Revenue</td>
                                <td>$81.8B</td>
                                <td>$82.9B</td>
                                <td>-1.3%</td>
                            </tr>
                            <tr>
                                <td>Net Income</td>
                                <td>$19.9B</td>
                                <td>$19.4B</td>
                                <td>+2.6%</td>
                            </tr>
                            <tr>
                                <td>EPS</td>
                                <td>$1.26</td>
                                <td>$1.20</td>
                                <td>+5.0%</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </body>
        </html>
        """
        
        with patch('tools.web_scraper.fetch_and_parse') as mock_fetch:
            mock_fetch.return_value = BeautifulSoup(mock_html, 'html.parser')
            
            result = await scrape_webpage("https://earnings.com/apple-data", "table")
            
            assert "Table 1:" in result
            assert "Metric | Q3 2023 | Q3 2022 | Change" in result
            assert "Total Revenue | $81.8B | $82.9B | -1.3%" in result
            assert "Net Income | $19.9B | $19.4B | +2.6%" in result
            assert "EPS | $1.26 | $1.20 | +5.0%" in result