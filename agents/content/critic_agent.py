# Critic agent - uses critic chain
from chains.critic_chain import critic_chain

def run_critic(topic: str, report: str, summary: str, strength: str = "N/A") -> str:
    return critic_chain.invoke({
        "topic": topic,
        "report": report,
        "summary": summary,
        "strength": strength,
    })