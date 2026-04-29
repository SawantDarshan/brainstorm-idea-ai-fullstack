# Critic chain - prompt | llm | output parser
from langchain_core.output_parsers import StrOutputParser
from prompts.templates.critic_prompt import critic_prompt
from engine import default_engine

llm = default_engine.create_llm()
critic_chain = critic_prompt | llm | StrOutputParser()