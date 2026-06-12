"""
Diagnóstico v3: usa a MESMA fonte e ordem do evaluate.py (client.list_examples)
para mapear exatamente os índices impressos na avaliação.

Uso:
    python src/diagnose_v3.py [indices 1-based separados por espaço]
"""

import os
import sys
from dotenv import load_dotenv
from langchain import hub
from langsmith import Client
from utils import get_llm

load_dotenv()


def main():
    username = os.getenv("USERNAME_LANGSMITH_HUB", "").strip()
    project_name = os.getenv("LANGSMITH_PROJECT", "prompt-optimization-challenge-resolved")
    dataset_name = f"{project_name}-eval"

    indices = [int(a) for a in sys.argv[1:]] or [6, 8, 11, 12]

    template = hub.pull(f"{username}/bug_to_user_story_v3")
    llm = get_llm(temperature=0)
    chain = template | llm

    client = Client()
    examples = list(client.list_examples(dataset_name=dataset_name))
    print(f"Dataset: {dataset_name} ({len(examples)} exemplos)\n")

    for idx in indices:
        ex = examples[idx - 1]
        bug = ex.inputs.get("bug_report", "")
        reference = ex.outputs.get("reference", "")

        print("=" * 80)
        print(f"=== EXEMPLO [{idx}] (ordem do evaluate.py) ===")
        print("=" * 80)
        print("\n--- BUG ---")
        print(bug)
        print("\n--- OUTPUT DO MODELO ---")
        result = chain.invoke({"bug_report": bug})
        print(result.content)
        print("\n--- REFERENCE ---")
        print(reference)
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
