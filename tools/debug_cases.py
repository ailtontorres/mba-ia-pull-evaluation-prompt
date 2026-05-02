"""
Script de debug isolado.

Executa o prompt atual (puxado do LangSmith Hub) apenas nos casos 5, 9, 10, 11,
12 e 15 do dataset e imprime lado a lado:

- número do caso
- input/bug
- expected/ground truth
- output gerado
- diferenças prováveis (fatos omitidos, fatos inventados, termos do expected
  que o output não reproduziu, seções/formato divergentes)

NÃO altera evaluate.py, metrics.py nem o dataset.

Uso:
    python tools/debug_cases.py
"""

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv
from langchain import hub

from utils import get_llm

load_dotenv(ROOT / ".env")

DATASET_PATH = ROOT / "datasets" / "bug_to_user_story.jsonl"
TARGET_CASES = [5, 9, 10, 11, 12, 15]

SECTION_HEADERS = [
    "Critérios de Aceitação",
    "Critérios Técnicos",
    "Critérios de Acessibilidade",
    "Critérios de Prevenção",
    "Critérios Adicionais",
    "Contexto Técnico",
    "Contexto do Bug",
    "Contexto de Segurança",
    "Exemplo de Cálculo",
    "USER STORY PRINCIPAL",
    "CRITÉRIOS DE ACEITAÇÃO",
    "CRITÉRIOS TÉCNICOS",
    "CONTEXTO DO BUG",
    "TASKS TÉCNICAS SUGERIDAS",
    "MÉTRICAS DE SUCESSO",
    "Tasks Técnicas",
    "Métricas de Sucesso",
    "Severidade",
    "Impacto",
    "Problemas Técnicos",
]

# Termos de domínio que costumam discriminar fidelidade (extraídos do reference).
DOMAIN_TERMS_PATTERN = re.compile(
    r"\b("
    r"RecyclerView|ViewHolder|paginação|scroll infinito|background thread|"
    r"CRDT|Vector Clock|chunked upload|checkpoint|client_timestamp|"
    r"Sidekiq|Bull|WatermelonDB|React Native|materialized view|eager loading|"
    r"SELECT FOR UPDATE|Redis|exponential backoff|circuit breaker|"
    r"Content Security Policy|DOMPurify|sanitiza[çc][ãa]o|"
    r"middleware|OWASP|HTTP 200|HTTP 403|HTTP 500|HTTP 504|"
    r"timeout|retry|webhook|TTL|cache|"
    r"NPS|MRR|churn|connection pool|N\+1|race condition|"
    r"backdrop|z-index|ESC|foco do teclado|"
    r"Subtotal|Desconto|Total"
    r")\b",
    re.IGNORECASE,
)

# Stopwords pt-BR para reduzir ruído.
STOPWORDS = {
    "a", "o", "as", "os", "um", "uma", "uns", "umas", "de", "do", "da", "dos",
    "das", "no", "na", "nos", "nas", "em", "para", "por", "com", "sem", "que",
    "se", "ser", "ter", "está", "estar", "este", "esta", "esse", "essa",
    "aquele", "aquela", "ao", "à", "às", "aos", "e", "ou", "mas", "como",
    "quando", "então", "dado", "quero", "eu", "ele", "ela", "eles", "elas",
    "pelo", "pela", "pelos", "pelas", "isso", "deve", "ser", "fica", "ficar",
    "muito", "também", "já", "mais", "menos", "todo", "toda", "todos", "todas",
    "ainda", "ali", "aqui", "lá", "não", "sim", "sua", "seu", "suas", "seus",
    "user", "story", "como", "para", "que", "etc",
}


def load_dataset():
    examples = []
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            data["case_number"] = idx
            examples.append(data)
    return examples


def extract_sections(text: str):
    """Detecta cabeçalhos de seção presentes no texto (case-insensitive)."""
    found = set()
    lower = text.lower()
    for header in SECTION_HEADERS:
        if header.lower() in lower:
            found.add(header)
    return sorted(found)


def extract_domain_terms(text: str):
    """Extrai termos de domínio relevantes presentes no texto."""
    return sorted({m.lower() for m in DOMAIN_TERMS_PATTERN.findall(text)})


def tokenize(text: str):
    """Tokeniza minimamente para comparação lexical."""
    tokens = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9_/\-]+", text.lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) > 2]


def discriminative_terms(reference: str, generated: str, top_k: int = 25):
    """
    Termos do reference (que aparecem no reference) e que NÃO aparecem na saída.
    Mostra os top_k mais "incomuns" (mais longos = mais específicos).
    """
    ref_tokens = set(tokenize(reference))
    gen_tokens = set(tokenize(generated))
    missing = ref_tokens - gen_tokens
    # Priorizar termos longos (mais específicos), com dígitos ou maiúsculas no original.
    return sorted(missing, key=lambda t: (-len(t), t))[:top_k]


def invented_terms(reference: str, generated: str, bug: str, top_k: int = 25):
    """
    Termos da saída que NÃO estão nem no reference nem no bug.
    Indício (não prova) de invenção/extrapolação.
    """
    ref_tokens = set(tokenize(reference))
    bug_tokens = set(tokenize(bug))
    gen_tokens = set(tokenize(generated))
    extra = gen_tokens - ref_tokens - bug_tokens
    return sorted(extra, key=lambda t: (-len(t), t))[:top_k]


def diff_sections(reference: str, generated: str):
    ref_secs = set(extract_sections(reference))
    gen_secs = set(extract_sections(generated))
    return {
        "expected_only": sorted(ref_secs - gen_secs),
        "generated_only": sorted(gen_secs - ref_secs),
        "shared": sorted(ref_secs & gen_secs),
    }


def diff_domain(reference: str, generated: str):
    ref_terms = set(extract_domain_terms(reference))
    gen_terms = set(extract_domain_terms(generated))
    return {
        "missing_in_output": sorted(ref_terms - gen_terms),
        "extra_in_output": sorted(gen_terms - ref_terms),
        "shared": sorted(ref_terms & gen_terms),
    }


def count_acceptance_criteria(text: str):
    """Conta itens com '- Dado/Quando/Então/E ' no início (Gherkin)."""
    pattern = re.compile(
        r"^\s*-\s*(dado|quando|então|entao|e)\b", re.IGNORECASE | re.MULTILINE
    )
    return len(pattern.findall(text))


def hr(char="-", width=80):
    print(char * width)


def section(title):
    print()
    hr("=")
    print(title)
    hr("=")


def main():
    prompt_name = (
        f"{os.getenv('USERNAME_LANGSMITH_HUB', '')}/bug_to_user_story_v2"
    )
    print(f"Pulling prompt: {prompt_name}")
    prompt_template = hub.pull(prompt_name)
    print("Prompt carregado.\n")

    llm = get_llm(temperature=0)
    chain = prompt_template | llm

    examples = load_dataset()
    targets = [ex for ex in examples if ex["case_number"] in TARGET_CASES]

    for ex in targets:
        case_num = ex["case_number"]
        bug = ex["inputs"]["bug_report"]
        expected = ex["outputs"]["reference"]
        complexity = ex.get("metadata", {}).get("complexity", "?")
        domain = ex.get("metadata", {}).get("domain", "?")

        section(
            f"CASO {case_num}  |  complexidade={complexity}  |  domínio={domain}"
        )

        print("\n--- BUG (input) ---")
        print(bug)

        print("\n--- EXPECTED (ground truth) ---")
        print(expected)

        print("\n--- OUTPUT GERADO ---")
        try:
            response = chain.invoke({"bug_report": bug})
            generated = response.content
        except Exception as e:
            generated = f"[ERRO ao chamar LLM: {e}]"
        print(generated)

        # Diffs estruturais
        print("\n--- DIFF: SEÇÕES ---")
        sec = diff_sections(expected, generated)
        print(f"  expected only:   {sec['expected_only']}")
        print(f"  generated only:  {sec['generated_only']}")
        print(f"  shared:          {sec['shared']}")

        # Diffs de termos de domínio (RecyclerView, CRDT, OWASP, etc)
        print("\n--- DIFF: TERMOS DE DOMÍNIO ---")
        dom = diff_domain(expected, generated)
        print(f"  missing in output: {dom['missing_in_output']}")
        print(f"  extra in output:   {dom['extra_in_output']}")

        # Diffs lexicais discriminativos
        print("\n--- TERMOS DO EXPECTED OMITIDOS NO OUTPUT (top 20) ---")
        for t in discriminative_terms(expected, generated, top_k=20):
            print(f"  - {t}")

        print("\n--- TERMOS NOVOS NO OUTPUT (NÃO estão no expected nem no bug, top 20) ---")
        print("    (pista de invenção/extrapolação — não prova)")
        for t in invented_terms(expected, generated, bug, top_k=20):
            print(f"  - {t}")

        # Métricas estruturais
        ref_criteria = count_acceptance_criteria(expected)
        gen_criteria = count_acceptance_criteria(generated)
        print("\n--- MÉTRICAS ESTRUTURAIS ---")
        print(f"  critérios Gherkin no expected: {ref_criteria}")
        print(f"  critérios Gherkin no output:   {gen_criteria}")
        print(f"  tamanho expected:  {len(expected)} chars")
        print(f"  tamanho output:    {len(generated)} chars")
        print(
            f"  começa com 'Como ': "
            f"expected={expected.lstrip().lower().startswith('como ')}, "
            f"output={generated.lstrip().lower().startswith('como ')}"
        )

    print()
    hr("=")
    print("Concluído.")
    hr("=")


if __name__ == "__main__":
    main()
