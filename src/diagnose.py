"""
Script de diagnóstico: puxa o prompt v2 do hub e roda contra
os exemplos problemáticos para ver o output real do modelo.

Uso:
    python src/diagnose.py

Imprime: BUG, OUTPUT do modelo, REFERENCE — para os 3 exemplos
que mais derrubaram a média na última avaliação.
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from langchain_openai import ChatOpenAI

load_dotenv()


def main():
    username = os.getenv("USERNAME_LANGSMITH_HUB", "").strip()
    if not username:
        print("❌ USERNAME_LANGSMITH_HUB não configurado")
        return 1

    prompt_name = f"{username}/bug_to_user_story_v3"
    print(f"📥 Puxando prompt: {prompt_name}")
    template = hub.pull(prompt_name)

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    chain = template | llm

    # Carregar dataset
    examples = []
    with open("datasets/bug_to_user_story.jsonl", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                examples.append(json.loads(line))

    # Exemplos com F1 mais baixo na iteração 8 (rodada 2):
    # #2 (0.75), #3 (0.75), #5 (0.65), #12 (0.60)
    # Índices 0-based:
    problematic_indices = [1, 2, 4, 11]

    for idx in problematic_indices:
        ex = examples[idx]
        bug = ex["inputs"]["bug_report"]
        reference = ex["outputs"]["reference"]

        print("\n" + "=" * 80)
        print(f"=== EXEMPLO #{idx + 1} ===")
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
