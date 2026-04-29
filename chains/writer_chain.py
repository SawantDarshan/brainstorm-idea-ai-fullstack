# Writer chain - prompt | llm | output parser
from langchain_core.output_parsers import StrOutputParser
from prompts.templates.writer_prompt import writer_prompt
from engine import default_engine

llm = default_engine.create_llm()
writer_chain = writer_prompt | llm | StrOutputParser()