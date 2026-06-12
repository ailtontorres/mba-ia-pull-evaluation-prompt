"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v3.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

SIMPLIFICADO: Código mais limpo e direto ao ponto.
"""

import os
import sys
from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header

load_dotenv()

PROMPT_PATH = "prompts/bug_to_user_story_v3.yml"
PROMPT_KEY = "bug_to_user_story_v3"


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).
    """
    errors = []

    required_fields = ["description", "system_prompt", "version", "techniques_applied"]
    for field in required_fields:
        if field not in prompt_data:
            errors.append(f"Campo obrigatório faltando: '{field}'")

    system_prompt = prompt_data.get("system_prompt", "")
    if not isinstance(system_prompt, str) or not system_prompt.strip():
        errors.append("'system_prompt' está vazio")

    if "[TODO]" in system_prompt or "TODO:" in system_prompt:
        errors.append("'system_prompt' contém marcadores [TODO] pendentes")

    techniques = prompt_data.get("techniques_applied", [])
    if not isinstance(techniques, list) or len(techniques) < 2:
        errors.append(
            f"Mínimo de 2 técnicas requeridas em 'techniques_applied', encontradas: {len(techniques) if isinstance(techniques, list) else 0}"
        )

    if "{bug_report}" not in system_prompt and "{bug_report}" not in prompt_data.get("user_prompt", ""):
        errors.append("O placeholder '{bug_report}' não foi encontrado nem no system_prompt nem no user_prompt")

    return (len(errors) == 0, errors)


def build_chat_prompt_template(prompt_data: dict) -> ChatPromptTemplate:
    """
    Constrói um ChatPromptTemplate a partir do dicionário do YAML.
    """
    system_prompt = prompt_data["system_prompt"]
    user_prompt = prompt_data.get("user_prompt", "{bug_report}")

    template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", user_prompt),
    ])

    return template


def build_readme(prompt_data: dict) -> str:
    """Constrói um README em Markdown para o prompt no Hub."""
    techniques = prompt_data.get("techniques_applied", [])
    techniques_md = "\n".join(f"- {t}" for t in techniques)

    return f"""# Bug to User Story {prompt_data.get("version", "v3")}

{prompt_data.get("description", "")}

## Técnicas de Prompt Engineering aplicadas

{techniques_md}

## Como usar

Este prompt recebe uma única variável `{{bug_report}}` e produz uma User Story
ágil estruturada, com critérios de aceitação no padrão Gherkin (Dado/Quando/Então).

A profundidade da resposta é adaptativa: bugs simples geram user stories curtas,
bugs complexos geram histórias com seções `=== USER STORY PRINCIPAL ===`,
`=== CRITÉRIOS DE ACEITAÇÃO ===` e `=== CRITÉRIOS TÉCNICOS ===`.

## Versão

{prompt_data.get("version", "v3")}
"""


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Usa a assinatura correta de hub.push() (langsmith >= 0.2):
        hub.push(repo_full_name, object, *,
                 new_repo_is_public, new_repo_description, readme, tags)
    """
    print(f"📤 Fazendo push do prompt: {prompt_name}")

    try:
        template = build_chat_prompt_template(prompt_data)
        print(f"   ✓ Template construído")
    except Exception as e:
        print(f"   ❌ Erro ao construir template: {e}")
        return False

    techniques = prompt_data.get("techniques_applied", [])
    description = prompt_data.get("description", "")
    full_description = (
        f"{description} | Técnicas: {', '.join(techniques)} | "
        f"Versão: {prompt_data.get('version', 'v3')}"
    )
    readme = build_readme(prompt_data)
    tags = prompt_data.get("tags", []) or []

    # IMPORTANTE: new_repo_is_public e new_repo_description só são aplicados
    # na CRIAÇÃO do repo. Em pushes subsequentes (novas versões), são ignorados.
    try:
        url = hub.push(
            prompt_name,
            template,
            new_repo_is_public=True,
            new_repo_description=full_description,
            readme=readme,
            tags=tags if tags else None,
        )
        print(f"   ✓ Prompt publicado em: {url}")
        return True
    except Exception as e:
        print(f"   ⚠️  Push com metadados falhou: {e}")
        print(f"   Tentando push minimalista...")
        try:
            url = hub.push(prompt_name, template, new_repo_is_public=True)
            print(f"   ✓ Prompt publicado em (sem metadados): {url}")
            return True
        except Exception as e2:
            print(f"   ❌ Erro ao fazer push: {e2}")
            return False


def main():
    """Função principal"""
    print_section_header("PUSH DE PROMPTS PARA O LANGSMITH HUB")

    if not check_env_vars(["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]):
        return 1

    username = os.getenv("USERNAME_LANGSMITH_HUB", "").strip()
    if not username:
        print("❌ USERNAME_LANGSMITH_HUB está vazio no .env")
        return 1

    raw = load_yaml(PROMPT_PATH)
    if raw is None:
        print(f"❌ Não foi possível carregar {PROMPT_PATH}")
        return 1

    if PROMPT_KEY in raw:
        prompt_data = raw[PROMPT_KEY]
    else:
        prompt_data = raw

    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("❌ Prompt inválido. Erros encontrados:")
        for err in errors:
            print(f"   - {err}")
        return 1

    print("✓ Prompt validado com sucesso")
    print(f"   Técnicas aplicadas: {', '.join(prompt_data.get('techniques_applied', []))}")

    prompt_name = f"{username}/{PROMPT_KEY}"
    success = push_prompt_to_langsmith(prompt_name, prompt_data)

    if success:
        print(f"\n✅ Push concluído!")
        print(f"   Prompt disponível em: https://smith.langchain.com/hub/{username}/{PROMPT_KEY}")
        print(f"   Próximo passo: rodar 'python src/evaluate.py'")
        return 0
    else:
        print(f"\n❌ Push falhou.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
