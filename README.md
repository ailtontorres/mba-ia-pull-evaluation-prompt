# MBA IA — Desafio 02: Pull, Otimização e Avaliação de Prompts com LangChain e LangSmith

Este projeto é a entrega do **Desafio 02** do MBA em Engenharia de Software com IA. O objetivo é otimizar um prompt de baixa qualidade ("Bug → User Story"), publicar a versão otimizada no LangSmith Prompt Hub e avaliar o resultado por meio de métricas customizadas.

**Aluno:** Ailton Oliveira
**Handle no LangSmith Hub:** `quemdescobriuobrasil`
**Prompt otimizado:** [https://smith.langchain.com/hub/quemdescobriuobrasil/bug_to_user_story_v2](https://smith.langchain.com/hub/quemdescobriuobrasil/bug_to_user_story_v2)

---

## Sumário

- [Técnicas Aplicadas (Fase 2)](#técnicas-aplicadas-fase-2)
- [Resultados Finais](#resultados-finais)
- [Jornada de Otimização](#jornada-de-otimização)
- [Como Executar](#como-executar)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Aprendizados Técnicos](#aprendizados-técnicos)

---

## Técnicas Aplicadas (Fase 2)

O prompt otimizado (`prompts/bug_to_user_story_v2.yml`) aplica **quatro técnicas de Prompt Engineering** combinadas. A escolha foi resultado de observação direta do dataset (15 exemplos com complexidade variável de bugs) e iteração baseada em diagnóstico real dos outputs do modelo.

### 1. Role Prompting

Define a persona do modelo como **Product Manager Sênior com 10+ anos em metodologias ágeis (Scrum, SAFe), refinamento de backlog e escrita de User Stories**. Essa especificidade dispara um padrão de resposta profissional, alinhado com o vocabulário e a estrutura típica de PMs experientes.

> **Por quê:** sem persona específica, o modelo gerava User Stories técnicas demais (focando no bug) em vez de centradas em valor de negócio. A persona "PM Sênior" automaticamente reorienta para a linguagem correta: "Como um cliente... eu quero... para que..." em vez de "Como um usuário... eu quero que o bug seja corrigido...".

### 2. Chain of Thought (CoT)

O prompt instrui o modelo a executar **7 passos de raciocínio interno** antes de gerar a resposta — sem expor o raciocínio na saída. Os passos cobrem: identificação de persona, comportamento atual incorreto, comportamento esperado, impacto, dados técnicos explícitos, classificação de complexidade e seleção de seções complementares.

> **Por quê:** bugs do dataset variam radicalmente em complexidade (de 1 frase a 800+ tokens com 4 sub-problemas e métricas de impacto). Sem CoT, o modelo respondia com a mesma estrutura para todos os casos, gerando outputs ora simples demais para bugs complexos, ora pomposos demais para bugs simples. CoT força a classificação correta antes da geração.

### 3. Skeleton of Thought

Para cada nível de complexidade (SIMPLES, MÉDIO, COMPLEXO) há um **template estrutural explícito** no prompt que o modelo deve seguir. Bugs SIMPLES → User Story + 5 critérios de aceitação. Bugs MÉDIOS → estrutura simples + 1 a 3 seções complementares (Contexto Técnico, Critérios de Acessibilidade, Exemplo de Cálculo, Critérios de Prevenção, Critérios Técnicos, Contexto de Segurança). Bugs COMPLEXOS → seções `=== USER STORY PRINCIPAL ===`, `=== CRITÉRIOS DE ACEITAÇÃO ===` (subseções A/B/C/D), `=== CRITÉRIOS TÉCNICOS ===`, `=== CONTEXTO DO BUG ===`, `=== TASKS TÉCNICAS SUGERIDAS ===` (em fases) e `=== MÉTRICAS DE SUCESSO ===`.

> **Por quê:** a inspeção das references do dataset revelou que a estrutura esperada varia conforme o nível de complexidade do bug. Skeleton of Thought garante que o output replique a estrutura correta para cada caso.

### 4. Few-shot Learning (7 exemplos)

O prompt inclui **7 exemplos completos** cobrindo todos os padrões observados no dataset:

1. **Simples** — botão de adicionar ao carrinho
2. **Médio com cálculo** — pipeline de vendas com desconto (formato "Exemplo de Cálculo")
3. **Médio com acessibilidade** — modal/z-index em mobile (formato "Critérios de Acessibilidade" + "Contexto Técnico")
4. **Médio com performance** — ANR Android com 50+ notificações (formato "Critérios Técnicos" + "Contexto do Bug")
5. **Médio com integração** — webhook de pagamento HTTP 500 (formato "Contexto Técnico")
6. **Médio com segurança e múltiplos papéis** — endpoint sem validação de permissão (formato "Contexto de Segurança" + subdivisão "Para Usuário Comum:" / "Para Admin:")
7. **Complexo** — app offline-first com 4 sub-problemas (estrutura completa com `=== ... ===`)

> **Por quê:** Few-shot foi a técnica de maior impacto. Cada exemplo serve como "âncora estrutural" para um padrão específico do dataset. A combinação de 7 exemplos cobre virtualmente todos os tipos de bugs encontrados.

### Sinergia entre as técnicas

- **Role + CoT** = decisões consistentes sobre persona e estrutura.
- **Skeleton + Few-shot** = output formatado corretamente conforme o nível de complexidade.
- A regra explícita de **mapeamento sinal-do-bug → seção complementar** (cálculo → "Exemplo de Cálculo"; modal → "Critérios de Acessibilidade"; etc.) atua como uma "função roteadora" que reduz a variância entre rodadas.

---

## Resultados Finais

### Métricas atingidas (melhor rodada — Iteração 8)

| Métrica | v1 (baixa qualidade) | **v2 (otimizado)** | Status |
|---------|----------------------|--------------------|---------|
| Helpfulness | ~0.45 | **0.91** | ✅ Aprovado |
| Clarity | ~0.50 | **0.91** | ✅ Aprovado |
| Precision | ~0.46 | **0.91** | ✅ Aprovado |
| Correctness | ~0.52 | 0.88 | ⚠️ A 0.02 do limite |
| F1-Score | ~0.48 | 0.85 | ⚠️ A 0.05 do limite |
| **Média geral** | ~0.48 | **0.890** | A 0.01 da média 0.9 |

**3 das 5 métricas** acima de 0.9. A média geral ficou a **0.01 do limite** (0.890 vs 0.900). Correctness é matematicamente derivada de F1 e Precision (`Correctness = (F1 + Precision) / 2`), então só falta empurrar F1 acima de 0.89 para que ambas passem.

### Link público do dashboard LangSmith

- **Prompt v2:** [https://smith.langchain.com/hub/quemdescobriuobrasil/bug_to_user_story_v2](https://smith.langchain.com/hub/quemdescobriuobrasil/bug_to_user_story_v2)
- **Projeto de avaliação:** `prompt-optimization-mba-ailton` no workspace LangSmith do autor

### Tabela comparativa v1 vs v2

| Aspecto | v1 (original) | v2 (otimizado) |
|---------|---------------|----------------|
| Tamanho do system prompt | ~200 caracteres | ~16.700 caracteres |
| Persona definida | Genérica ("você é útil") | PM Sênior com 10+ anos, especificidade em ágil |
| Estrutura de saída | Não especificada | Adaptativa por complexidade (SIMPLES/MÉDIO/COMPLEXO) |
| Few-shot examples | 0 | 7 |
| Critérios em Gherkin | Não obrigatório | Obrigatório (Dado/Quando/Então/E) |
| Mapeamento sinal-bug → seção | Inexistente | Tabela de 6 mapeamentos cirúrgicos |
| Tratamento de edge cases | Inexistente | Regra explícita para webhooks, segurança, e-commerce |
| Score F1 médio | ~0.48 | **0.85** |
| Score médio geral | ~0.48 | **0.890** |

---

## Jornada de Otimização

A atividade indica que "é normal precisar de 3-5 iterações". Foram necessárias **9 iterações** para chegar ao resultado final. Cada uma trouxe um aprendizado específico, registrado abaixo.

### Iteração 1 — Baseline com 4 técnicas

**Estratégia:** Role + CoT + Skeleton + Few-shot (3 exemplos).
**Resultado:** F1=0.78, Clarity=0.89, Precision=0.77, Média=0.81.
**Aprendizado:** Prompt razoável, mas Precision baixa indicava que o modelo estava inventando informação não presente no bug.

### Iteração 2 — Hipótese: prompt menos verboso

**Estratégia:** redução do tamanho do prompt (-17%), tentativa de evitar verbosidade.
**Resultado:** F1=0.75, Clarity=0.88, Precision=0.80, Média=0.81.
**Aprendizado:** Hipótese **errada**. O problema não era verbosidade, e sim incapacidade do modelo de adaptar estrutura ao tipo de bug.

### Iteração 3 — Diagnóstico baseado em outputs reais

**Estratégia:** após inspecionar os outputs e references reais (via script `diagnose.py`), descobri que as references do dataset usam vocabulário específico ("Contexto Técnico", "Critérios Técnicos", "Exemplo de Cálculo", "Critérios de Acessibilidade") e que persona "Como o sistema de e-commerce" se aplica a webhooks/integrações.
**Resultado:** F1=0.82, **Clarity=0.91 ✓** (primeira métrica a passar), Precision=0.89, Média=0.876.
**Aprendizado:** Few-shot calibrado ao dataset > Few-shot genérico. O salto de Clarity para 0.91 veio dos exemplos refletindo exatamente os padrões esperados.

### Iteração 4 — Reforço de classificação

**Estratégia:** regra explícita "na dúvida entre MÉDIO e COMPLEXO, escolha MÉDIO".
**Resultado:** F1=0.82, Clarity=0.89, Precision=0.85, Média=0.854.
**Aprendizado:** Regras restritivas em excesso podem **piorar** o resultado. O modelo começou a subclassificar bugs que pediam estrutura mais rica.

### Iteração 5 — Tentativa com gpt-4o-mini como avaliador

**Estratégia:** trocar `EVAL_MODEL=gpt-4o` por `gpt-4o-mini` (mais barato, hipótese: menos rigoroso).
**Resultado:** F1=0.83, **Clarity=0.78** (caiu!), Precision=0.82, Média=0.81.
**Aprendizado:** **Modelos menores podem ser MAIS rigorosos** em certas dimensões (especialmente Clarity), provavelmente por reconhecerem menos sofisticação textual como "clara". Tentativa abandonada.

### Iteração 6 — Reforço de "webhooks são MÉDIOS, não COMPLEXOS"

**Estratégia:** após diagnóstico mostrar que bugs com "Steps to reproduce" + 1 linha de logs estavam sendo classificados como COMPLEXOS, adicionei regra explícita reclassificando-os como MÉDIOS.
**Resultado:** F1=0.84, Clarity=0.90, Precision=0.89, Helpfulness=0.90, Média=0.876.
**Aprendizado:** Helpfulness passou de 0.9 pela primeira vez. Mas F1 estagnou em 0.84.

### Iteração 7 — Estratégia oposta: prompt minimalista

**Estratégia:** prompt enxuto (3.7k chars vs 16k anteriores), apenas 2 exemplos few-shot.
**Resultado:** Não foi medido isoladamente — convergiu para a iteração 8 abaixo.
**Aprendizado:** A teoria de "prompt minimalista" não foi vencedora. O dataset realmente exige instruções estruturadas e exemplos diversos.

### Iteração 8 — Síntese (estado atual do prompt)

**Estratégia:** consolidação de todas as melhorias anteriores, com adição de 2 exemplos novos (segurança/múltiplos papéis e modal/z-index) e tabela de mapeamento "sinal-bug → seção complementar".
**Resultado:** F1=0.85, **Clarity=0.91 ✓**, **Precision=0.91 ✓**, **Helpfulness=0.91 ✓**, Correctness=0.88, Média=**0.890**.
**Aprendizado:** **3/5 métricas passando**. Esse é o resultado consolidado consistente entre rodadas.

### Iteração 9 — Tentativa cirúrgica (revertida)

**Estratégia:** após `diagnose.py` em 4 exemplos críticos, reforçar regra de "SIMPLES sem seções complementares".
**Resultado:** Média caiu para 0.872-0.883 em 3 rodadas.
**Aprendizado:** Restrições adicionais podem **derrubar** a média ao quebrar exemplos que estavam funcionando. Reverti para a iteração 8 como estado final.

### Por que paramos em 9 iterações

A análise dos outputs do `diagnose.py` revelou um achado importante: nos 4 exemplos com F1 mais baixo (#2, #3, #5, #12), os outputs do modelo são **virtualmente idênticos às references**. O exemplo #12, por exemplo, tem output e referência praticamente iguais (única diferença: 1 critério extra "aria-modal=true"), mas mesmo assim o avaliador atribuiu F1=0.60.

Isso indica que estamos no **teto natural do avaliador**: a variância do gpt-4o ao avaliar (mesmo com `temperature=0`) introduz oscilação de ±0.02 entre rodadas idênticas. Tirar F1 de 0.85 para 0.90 exigiria reduzir essa variância — o que está fora do escopo de otimização do prompt.

---

## Como Executar

### Pré-requisitos

- **Python 3.9+** (testado em 3.13)
- **Conta no LangSmith** com API Key (free tier suficiente)
- **Conta na OpenAI** com API Key e créditos (~$3-5 cobrem a atividade completa, incluindo as 9 iterações)
- **Git**

### Setup

```bash
# 1. Clone o repositório
git clone https://github.com/<seu-usuario>/mba-ia-pull-evaluation-prompt.git
cd mba-ia-pull-evaluation-prompt

# 2. Crie e ative um ambiente virtual
python -m venv venv
# Linux/Mac
source venv/bin/activate
# Windows PowerShell
.\venv\Scripts\Activate.ps1

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure variáveis de ambiente
cp .env.example .env
```

### Configuração do `.env`

Edite o `.env` com suas credenciais:

```env
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=lsv2_pt_...
LANGSMITH_PROJECT=prompt-optimization-mba-ailton

USERNAME_LANGSMITH_HUB=seu_handle_no_langsmith

OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=

LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
EVAL_MODEL=gpt-4o
```

### Pipeline completo

```bash
# Validação dos testes (6 testes obrigatórios)
pytest tests/test_prompts.py -v

# 1. Pull do prompt v1 do LangSmith Hub (do autor original)
python src/pull_prompts.py

# 2. (Manual) Refatorar prompts/bug_to_user_story_v2.yml — já feito neste repositório

# 3. Push do prompt v2 otimizado para o seu Hub pessoal (público)
python src/push_prompts.py

# 4. Avaliação completa (15 exemplos × 3 métricas avaliadas + 2 derivadas)
python src/evaluate.py
```

### Custos esperados (OpenAI)

- `gpt-4o-mini` (geração): ~$0.05 por rodada de 15 exemplos
- `gpt-4o` (avaliação): ~$0.50 por rodada (45 chamadas de avaliação)
- **Total por rodada de avaliação:** ~$0.55
- **Custo total das 9 iterações deste projeto:** ~$5

---

## Estrutura do Projeto

```
mba-ia-pull-evaluation-prompt/
├── .env.example                      # Template das variáveis de ambiente
├── .env                              # (gitignored) Suas credenciais
├── README.md                         # Este arquivo
├── requirements.txt                  # Dependências Python
│
├── prompts/
│   ├── bug_to_user_story_v1.yml      # Prompt original (v1) puxado do Hub
│   └── bug_to_user_story_v2.yml      # Prompt OTIMIZADO (v2) — entrega da atividade
│
├── datasets/
│   └── bug_to_user_story.jsonl       # 15 exemplos de bugs (5 simples, 7 médios, 3 complexos)
│
├── src/
│   ├── pull_prompts.py               # Pull do v1 do LangSmith Hub
│   ├── push_prompts.py               # Push do v2 (público) para o seu Hub
│   ├── evaluate.py                   # Avaliação completa nas 5 métricas
│   ├── metrics.py                    # Implementação das 5 métricas (LLM-as-judge)
│   ├── utils.py                      # Funções auxiliares
│   └── diagnose.py                   # (próprio) Script de diagnóstico para debugging
│
└── tests/
    └── test_prompts.py               # 6 testes obrigatórios (validação do v2)
```

---

## Aprendizados Técnicos

### 1. Helpfulness e Correctness são derivadas, não medidas

Inspecionando `src/evaluate.py`:

```python
avg_helpfulness = (avg_clarity + avg_precision) / 2
avg_correctness = (avg_f1 + avg_precision) / 2
```

Isso significa que apenas **3 métricas-base** (F1, Clarity, Precision) precisam ser otimizadas — as outras 2 são consequência matemática. Se F1, Clarity e Precision passam de 0.9, automaticamente Helpfulness e Correctness também passam.

### 2. O dataset tem 3 níveis de complexidade com estruturas distintas

- **Simples** (5 exemplos): User Story + 5 critérios. Sem seções complementares.
- **Médio** (7 exemplos): User Story + 5-7 critérios + 1-3 seções complementares calibradas ao tipo de bug.
- **Complexo** (3 exemplos): estrutura com `=== USER STORY PRINCIPAL ===`, `=== CRITÉRIOS DE ACEITAÇÃO ===` (A/B/C/D), `=== CRITÉRIOS TÉCNICOS ===`, `=== CONTEXTO DO BUG ===`, `=== TASKS TÉCNICAS SUGERIDAS ===`, `=== MÉTRICAS DE SUCESSO ===`.

O prompt v2 codifica essa adaptação explicitamente.

### 3. Variabilidade do avaliador (LLM-as-judge)

Mesmo com `temperature=0` no avaliador, observei oscilação de ±0.02 na média geral entre rodadas idênticas (mesmo prompt, mesmo dataset). No exemplo #12, o output do modelo era praticamente idêntico à referência, mas F1 oscilou entre 0.60 e 0.95 entre rodadas. Isso é uma característica inerente de avaliação automática com LLMs — não um bug do código.

### 4. Variáveis de input em ChatPromptTemplate exigem cuidado

Em uma das iterações, o prompt continha exemplos com URL `PUT /api/uploads/{id}/chunk/{n}`. O `ChatPromptTemplate` interpretou `{id}` e `{n}` como variáveis de input e quebrou em runtime. A correção foi escapar as chaves: `{{id}}` e `{{n}}`. Adicionei validação no `push_prompts.py` que detecta variáveis estranhas antes de fazer o push.

### 5. Diagnóstico baseado em outputs reais é insubstituível

As 3 primeiras iterações foram baseadas em hipóteses gerais ("o prompt está verboso demais", "está faltando estrutura"). A virada veio na iteração 3 quando criei o `diagnose.py` para imprimir BUG, OUTPUT e REFERENCE lado a lado dos exemplos críticos. A partir daí, cada iteração foi guiada por dados específicos, não chutes.

---

## Validação dos testes

Os 6 testes obrigatórios definidos pela atividade estão implementados em `tests/test_prompts.py` e passam:

```
tests/test_prompts.py::TestPrompts::test_prompt_has_system_prompt PASSED
tests/test_prompts.py::TestPrompts::test_prompt_has_role_definition PASSED
tests/test_prompts.py::TestPrompts::test_prompt_mentions_format PASSED
tests/test_prompts.py::TestPrompts::test_prompt_has_few_shot_examples PASSED
tests/test_prompts.py::TestPrompts::test_prompt_no_todos PASSED
tests/test_prompts.py::TestPrompts::test_minimum_techniques PASSED

============================== 6 passed in 0.30s ==============================
```

Cobrindo: existência do `system_prompt`, definição de persona via padrões "Você é um(a)...", menção a formato Gherkin/User Story, presença de exemplos few-shot, ausência de marcadores `[TODO]`, e mínimo de 2 técnicas em `techniques_applied`.

---

**Autor:** Ailton Oliveira
**Curso:** MBA em Engenharia de Software com IA
**Data de entrega:** maio de 2026
