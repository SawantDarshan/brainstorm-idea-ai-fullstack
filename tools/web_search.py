# Web search tool
from langchain.tools import tool
from apis.tavily_client import search


@tool("web_search", return_direct=True)
def web_search(query: str) -> str:
    """Search the web for recent and reliable information on a topic. Returns titles, urls and snippets."""
    from config.global_context import SEARCH_NUM_RESULTS
    results = search(query, num_results=SEARCH_NUM_RESULTS)
    return str(results)