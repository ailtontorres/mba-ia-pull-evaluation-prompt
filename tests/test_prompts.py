"""
Testes automatizados para validação de prompts.
"""
import pytest
import yaml
import sys
import re
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v3.yml"
PROMPT_KEY = "bug_to_user_story_v3"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def prompt_data():
    """
    Carrega os dados do prompt v3.

    O YAML pode estar no formato:
    a) Direto: { description: ..., system_prompt: ..., ... }
    b) Aninhado: { bug_to_user_story_v3: { description: ..., system_prompt: ..., ... } }
    """
    raw = load_prompts(str(PROMPT_PATH))
    assert raw is not None, f"Arquivo de prompt não pôde ser carregado: {PROMPT_PATH}"

    # Se a chave do prompt existir, desce um nível
    if isinstance(raw, dict) and PROMPT_KEY in raw:
        return raw[PROMPT_KEY]
    return raw


class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt_data):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in prompt_data, \
            "O campo 'system_prompt' está faltando no YAML"
        system_prompt = prompt_data["system_prompt"]
        assert isinstance(system_prompt, str), \
            "'system_prompt' deve ser uma string"
        assert system_prompt.strip() != "", \
            "'system_prompt' não pode estar vazio"
        # Garantia mínima de substância
        assert len(system_prompt.strip()) > 50, \
            "'system_prompt' parece muito curto para ser um prompt funcional"

    def test_prompt_has_role_definition(self, prompt_data):
        """Verifica se o prompt define uma persona (ex: 'Você é um Product Manager')."""
        system_prompt = prompt_data.get("system_prompt", "").lower()
        # Padrões típicos de role prompting em pt-BR e en
        role_patterns = [
            r"você\s+é\s+um[a]?\b",
            r"você\s+atua\s+como\b",
            r"voce\s+é\s+um[a]?\b",
            r"\byou\s+are\s+a[n]?\b",
            r"\bact\s+as\s+a[n]?\b",
            r"\bassuma\s+o\s+papel\b",
        ]
        matched = any(re.search(p, system_prompt) for p in role_patterns)
        assert matched, (
            "Nenhuma definição de persona encontrada no system_prompt. "
            "Esperado padrões como 'Você é um(a)...', 'Você atua como...', 'You are a...'"
        )

    def test_prompt_mentions_format(self, prompt_data):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        # Concatena system + user para checar
        text = (
            prompt_data.get("system_prompt", "")
            + "\n"
            + prompt_data.get("user_prompt", "")
        ).lower()

        format_indicators = [
            "markdown",
            "como um",          # User Story: "Como um <persona>..."
            "como uma",
            "eu quero",         # User Story: "...eu quero <ação>..."
            "para que",         # User Story: "...para que <benefício>"
            "critério de aceitação",
            "critérios de aceitação",
            "criterios de aceitacao",
            "user story",
        ]
        matched = [ind for ind in format_indicators if ind in text]
        assert len(matched) >= 2, (
            f"Prompt não menciona formato Markdown ou estrutura padrão de User Story. "
            f"Indicadores encontrados: {matched}"
        )

    def test_prompt_has_few_shot_examples(self, prompt_data):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        system_prompt = prompt_data.get("system_prompt", "").lower()

        # Few-shot tipicamente usa marcadores como "exemplo", "exemplo 1", "input/output", "bug:" etc.
        example_markers = [
            "exemplo 1",
            "exemplo 2",
            "exemplo:",
            "## exemplo",
            "### exemplo",
            "example 1",
            "example 2",
            "input:",
            "output:",
            "entrada:",
            "saída:",
            "saida:",
            "bug report:",
        ]
        markers_found = [m for m in example_markers if m in system_prompt]

        # Critério: pelo menos 2 ocorrências de marcadores (indica múltiplos exemplos)
        # OU a palavra "exemplo"/"example" aparecendo pelo menos 2x
        count_exemplo = system_prompt.count("exemplo")
        count_example = system_prompt.count("example")

        has_few_shot = (
            len(markers_found) >= 2
            or count_exemplo >= 2
            or count_example >= 2
        )
        assert has_few_shot, (
            "Prompt não parece conter exemplos few-shot. "
            f"Marcadores encontrados: {markers_found}, "
            f"ocorrências 'exemplo': {count_exemplo}, 'example': {count_example}"
        )

    def test_prompt_no_todos(self, prompt_data):
        """Garante que você não esqueceu nenhum [TODO] no texto."""
        # Verifica todos os campos string do prompt
        for key, value in prompt_data.items():
            if isinstance(value, str):
                assert "[TODO]" not in value, \
                    f"Campo '{key}' ainda contém [TODO]"
                assert "TODO:" not in value, \
                    f"Campo '{key}' ainda contém TODO:"
                # Cobre variações comuns
                assert "<TODO>" not in value, \
                    f"Campo '{key}' ainda contém <TODO>"

    def test_minimum_techniques(self, prompt_data):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = prompt_data.get("techniques_applied")
        assert techniques is not None, (
            "Campo 'techniques_applied' não encontrado nos metadados do YAML. "
            "Adicione uma lista com as técnicas de prompt engineering aplicadas."
        )
        assert isinstance(techniques, list), \
            "'techniques_applied' deve ser uma lista"
        assert len(techniques) >= 2, (
            f"Mínimo de 2 técnicas requeridas, encontradas: {len(techniques)}. "
            f"Lista atual: {techniques}"
        )
        # Garante que cada item é uma string não vazia
        for i, t in enumerate(techniques):
            assert isinstance(t, str) and t.strip() != "", \
                f"Técnica na posição {i} está vazia ou inválida: {t!r}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
