"""Web scraping using BeautifulSoup."""

import aiohttp
from bs4 import BeautifulSoup
from typing import Optional
import re


async def fetch_and_parse(url: str, timeout: int = 30) -> BeautifulSoup:
    """Fetch webpage and parse with BeautifulSoup.
    
    Args:
        url: URL to fetch
        timeout: Request timeout in seconds
        
    Returns:
        BeautifulSoup parsed content
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    connector = aiohttp.TCPConnector(limit=100)
    timeout_config = aiohttp.ClientTimeout(total=timeout)
    
    async with aiohttp.ClientSession(
        connector=connector,
        timeout=timeout_config,
        max_line_size=16384  # Increase from default 8190 to 16KB
    ) as session:
        async with session.get(url, headers=headers) as response:
            html = await response.text()
            return BeautifulSoup(html, 'html.parser')


def extract_article_content(soup: BeautifulSoup) -> str:
    """Extract main article content from webpage.
    
    Args:
        soup: BeautifulSoup parsed content
        
    Returns:
        Extracted text content
    """
    # Remove script and style elements and unwanted sections
    for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
        script.decompose()
    
    # Remove elements with common unwanted class names
    unwanted_classes = ['header', 'footer', 'sidebar', 'nav', 'navigation', 'ad', 'advertisement']
    for class_name in unwanted_classes:
        for element in soup.find_all(class_=class_name):
            element.decompose()
    
    # Try common article selectors
    selectors = [
        'article',
        '.article-content', 
        '.post-content',
        '.entry-content',
        'main',
        '.content'
    ]
    
    for selector in selectors:
        content = soup.select_one(selector)
        if content:
            text = content.get_text(strip=True)
            if len(text) > 200:  # Ensure substantial content
                return clean_text(text)
    
    # Fallback: get body text
    body = soup.find('body')
    if body:
        return clean_text(body.get_text(strip=True))[:5000]  # Limit size
    
    return clean_text(soup.get_text(strip=True))[:5000]


def extract_tables(soup: BeautifulSoup) -> str:
    """Extract table data from webpage.
    
    Args:
        soup: BeautifulSoup parsed content
        
    Returns:
        Formatted table data
    """
    tables = soup.find_all('table')
    if not tables:
        return "No tables found."
    
    formatted_tables = []
    for i, table in enumerate(tables[:3]):  # Limit to first 3 tables
        formatted_tables.append(f"Table {i+1}:")
        
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if cells:
                row_text = " | ".join(cell.get_text(strip=True) for cell in cells)
                formatted_tables.append(row_text)
        
        formatted_tables.append("")  # Empty line between tables
    
    return "\n".join(formatted_tables)


def clean_text(text: str) -> str:
    """Clean and normalize text content.
    
    Args:
        text: Raw text to clean
        
    Returns:
        Cleaned text
    """
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters that might cause issues, but preserve financial symbols
    text = re.sub(r'[^\w\s\.\,\!\?\-\:\;\(\)\$\%]', '', text)
    
    return text.strip()


async def scrape_webpage(
    url: str,
    content_type: str = "article"
) -> str:
    """Scrape webpage content.
    
    Args:
        url: URL to scrape
        content_type: Type of content to extract (article, table, full)
        
    Returns:
        Extracted content
    """
    try:
        soup = await fetch_and_parse(url)
        
        if content_type == "article":
            content = extract_article_content(soup)
        elif content_type == "table":
            content = extract_tables(soup)
        else:  # full
            content = extract_article_content(soup)
        
        return f"Content from {url}:\n\n{content}"
        
    except Exception as e:
        return f"Failed to scrape {url}: {str(e)}"