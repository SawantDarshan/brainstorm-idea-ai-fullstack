# Critic prompt template
from langchain_core.prompts import ChatPromptTemplate
from prompts.skills.writer import CRITIC_SKILL

critic_prompt = ChatPromptTemplate.from_messages([
    ("system", CRITIC_SKILL),
    ("human", """Critique the following summary based on the research provided.
Provide feedback on the accuracy, completeness, and clarity of the summary.
Suggest improvements if necessary.

Report: {report}

Score: x/10
Strength: {strength}
Topic: {topic}
Summary: {summary}
"""),
])