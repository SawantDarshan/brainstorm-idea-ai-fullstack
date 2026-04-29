# CLI interface for the multi-agent system
from pipelines.research_pipeline import run_pipeline

def main():
    topic = input("Enter a research topic: ")
    print(f"\nRunning pipeline for: {topic}\n")
    state = run_pipeline(topic)
    print("\n=== Final Report ===")
    print(state.report)
    print("\n=== Critique ===")
    print(state.critique)

if __name__ == "__main__":
    main()