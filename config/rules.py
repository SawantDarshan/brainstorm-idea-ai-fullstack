# Global rules and constraints for all agents
GLOBAL_RULES = [
    "Always provide sources when citing information.",
    "Keep responses concise and factual.",
    "Do not fabricate information - only use verified data.",
    "Follow the structured output format specified in prompts.",
    "Respect rate limits when making external API calls.",
]

# Agent-specific rule overrides can be added here
AGENT_RULES = {
    "research": [
        "Prioritize recent and reliable sources.",
        "Include URLs for all referenced content.",
    ],
    "content": [
        "Maintain a professional and neutral tone.",
        "Structure output with clear headings.",
    ],
}