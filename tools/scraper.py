# URL scraper tool
from langchain.tools import tool
import requests
from bs4 import BeautifulSoup

@tool("scrape_url", return_direct=True)
def scrape_url(url: str) -> str:
    """Scrape the content of a URL and return the text."""
    try:
        from config.global_context import SCRAPE_TIMEOUT, SCRAPE_MAX_CHARS
        response = requests.get(url, timeout=SCRAPE_TIMEOUT, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        return soup.get_text(separator="\n", strip=True)[:SCRAPE_MAX_CHARS]
    except Exception as e:
        return f"Error scraping URL: {e}"