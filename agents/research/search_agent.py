# Search agent - uses web_search tool
from engine import default_engine
from tools.web_search import web_search

def build_search_agent():
    return default_engine.create_agent(tools=[web_search])