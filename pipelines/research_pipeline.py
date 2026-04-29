# Research pipeline - orchestrates agents
from state.pipeline_state import PipelineState
from agents.research.search_agent import build_search_agent
from agents.research.scrape_agent import build_scrape_agent
from agents.content.writer_agent import run_writer
from agents.content.critic_agent import run_critic
from config.global_context import ENABLE_SCRAPING, ENABLE_CRITIQUE, DEBUG
from guardrails.input_guard import validate_input
from guardrails.output_guard import validate_output

def run_pipeline(topic: str) -> PipelineState:
    # Input guardrail
    input_check = validate_input(topic)
    if not input_check.passed:
        raise ValueError(f"Input rejected: {input_check.message}")
    topic = input_check.sanitized_content or topic

    state = PipelineState(topic=topic)

    print(f"Running pipeline for topic: {topic}")

    # Step 1: Search
    search_agent = build_search_agent()
    search_results = search_agent.invoke({
        "messages": [
            ("user", f"Search the web for recent and reliable information on the topic: {topic}. Provide titles, urls, and snippets.")
        ]
    })
    state.research = search_results["messages"][-1].content
    if DEBUG:
        print("Search results:", state.research)
    print("Search results obtained.")

    # Step 2: Scrape (optional via ENABLE_SCRAPING)
    if ENABLE_SCRAPING:
        reader_agent = build_scrape_agent()
        scraped_content = reader_agent.invoke({
            "messages": [
                ("user", f"Scrape the content from the URLs obtained in the search results for the topic: {topic}.")
            ]
        })
        state.scraped_content = scraped_content["messages"][-1].content
        if DEBUG:
            print("Scraped content:", state.scraped_content)
        print("Scraped content obtained.")

    # Step 3: Write
    print("Generating summary...")
    state.report = run_writer(topic, state.get_combined_research())

    # Output guardrail on report
    output_check = validate_output(state.report)
    if not output_check.passed:
        print(f"Output guard warning: {output_check.message}")
    if output_check.sanitized_content:
        state.report = output_check.sanitized_content
    if output_check.message and DEBUG:
        print(f"Output guard: {output_check.message}")

    if DEBUG:
        print("Report:", state.report)
    print("Summary generated.")

    # Step 4: Critique (optional via ENABLE_CRITIQUE)
    if ENABLE_CRITIQUE:
        print("Critiquing summary...")
        state.critique = run_critic(topic, state.report, state.report)

        # Output guardrail on critique
        critique_check = validate_output(state.critique)
        if critique_check.sanitized_content:
            state.critique = critique_check.sanitized_content

        if DEBUG:
            print("Critique:", state.critique)
        print("Critique obtained.")

    return state
