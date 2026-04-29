# Scrape agent - uses scrape_url tool
from engine import default_engine
from tools.scraper import scrape_url

def build_scrape_agent():
    return default_engine.create_agent(tools=[scrape_url])