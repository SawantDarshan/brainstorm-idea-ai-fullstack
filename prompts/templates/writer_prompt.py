# Writer prompt template
from langchain_core.prompts import ChatPromptTemplate
from prompts.skills.writer import WRITER_SKILL

writer_prompt = ChatPromptTemplate.from_messages([
    ("system", WRITER_SKILL),
    ("human", """Write a concise summary of the following information:

Topic: {topic}

Research: {research}

Structure the report as:
    1. Introduction
    2. Key Findings
    3. Conclusion
    4. Sources (include urls if available)
"""),
])