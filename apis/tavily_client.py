# Tavily API client adapter
from tavily import TavilyClient
from config.global_context import TAVILY_API_KEY

tavily = TavilyClient(api_key=TAVILY_API_KEY)

def search(query: str, num_results: int = 5) -> list:
    """Search using Tavily API and return structured results."""
    results = tavily.search(query, num_results=num_results)["results"]
    output = []
    for result in results:
        output.append({
            "title": result["title"],
            "url": result["url"],
            "snippet": result["content"],
        })
    return output