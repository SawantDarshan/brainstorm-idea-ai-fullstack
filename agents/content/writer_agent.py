# Writer agent - uses writer chain
from chains.writer_chain import writer_chain

def run_writer(topic: str, research: str) -> str:
    return writer_chain.invoke({"topic": topic, "research": research})