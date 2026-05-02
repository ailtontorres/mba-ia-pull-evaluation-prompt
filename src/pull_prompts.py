"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull dos prompts do Hub
3. Salva localmente em prompts/bug_to_user_story_v1.yml

SIMPLIFICADO: Usa serialização nativa do LangChain para extrair prompts.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()


def extract_prompt_data(prompt_obj) -> dict:
    """
    Extrai system_prompt e user_prompt de um ChatPromptTemplate retornado pelo hub.pull().

    O LangSmith retorna um ChatPromptTemplate com lista de messages (system, human, etc).
    """
    system_prompt = ""
    user_prompt = ""

    # ChatPromptTemplate possui o atributo 'messages' com a lista de message templates
    messages = getattr(prompt_obj, "messages", []) or []

    for msg in messages:
        # Cada message é um SystemMessagePromptTemplate, HumanMessagePromptTemplate, etc.
        msg_type = type(msg).__name__.lower()

        # Extrair o template raw da mensagem
        template_text = ""
        if hasattr(msg, "prompt") and hasattr(msg.prompt, "template"):
            template_text = msg.prompt.template
        elif hasattr(msg, "content"):
            template_text = msg.content

        if "system" in msg_type:
            system_prompt = template_text
        elif "human" in msg_type or "user" in msg_type:
            user_prompt = template_text

    return {
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
    }


def pull_prompts_from_langsmith():
    """
    Faz pull do prompt v1 do LangSmith Hub e salva em YAML.
    """
    prompt_name = "leonanluppi/bug_to_user_story_v1"
    output_path = "prompts/bug_to_user_story_v1.yml"

    print(f"📥 Fazendo pull do prompt: {prompt_name}")

    try:
        prompt_obj = hub.pull(prompt_name)
        print(f"   ✓ Prompt carregado do LangSmith Hub")
    except Exception as e:
        print(f"   ❌ Erro ao fazer pull: {e}")
        return False

    extracted = extract_prompt_data(prompt_obj)

    if not extracted["system_prompt"] and not extracted["user_prompt"]:
        print(f"   ⚠️  Não foi possível extrair conteúdo do prompt (estrutura inesperada)")
        print(f"   Tipo do objeto: {type(prompt_obj).__name__}")
        return False

    yaml_data = {
        "bug_to_user_story_v1": {
            "description": "Prompt original (baixa qualidade) puxado do LangSmith Hub",
            "system_prompt": extracted["system_prompt"],
            "user_prompt": extracted["user_prompt"],
            "version": "v1",
            "source": prompt_name,
        }
    }

    if save_yaml(yaml_data, output_path):
        print(f"   ✓ Prompt salvo em: {output_path}")
        return True
    else:
        print(f"   ❌ Falha ao salvar YAML")
        return False


def main():
    """Função principal"""
    print_section_header("PULL DE PROMPTS DO LANGSMITH HUB")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    success = pull_prompts_from_langsmith()

    if success:
        print("\n✅ Pull concluído com sucesso!")
        print("   Próximo passo: editar prompts/bug_to_user_story_v2.yml com a versão otimizada")
        return 0
    else:
        print("\n❌ Pull falhou. Verifique as credenciais e a conexão.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
