# Alterações aplicadas

## Estrutura e previsibilidade
- `core/task_router.py`
  - trocado o retorno simples por `TaskIntent`, com objetivo, confiança, escopo sugerido e motivo.
  - reduzido o risco de roteamento cego e de reinterpretação escondida.

- `core/models.py`
  - adicionado `TaskIntent`.
  - expandido `ResourceInspection` com:
    - `objective`
    - `confirmed_facts`
    - `inferred_facts`
    - `not_confirmed`
    - `scope_validation`
    - `task_intent`

## Honestidade operacional com o Aider
- `core/aider_manager.py`
  - `AiderRunResult` agora informa:
    - `asked_for_input`
    - `detected_prompts`
    - `command`
    - `scope_dir`
  - removida a ilusão de automação inexistente.
  - implementada detecção de prompts interativos do Aider na saída.

## Inspeção de escopo mais profissional
- `core/resource_manager.py`
  - objetivo agora pode ser travado com `lock_objective=True`.
  - separação entre fatos confirmados, inferências e pontos não confirmados.
  - validação de suficiência do escopo.
  - observações mais claras para debug parcial e revisão NUI incompleta.

## Prompt mais confiável
- `core/prompt_builder.py`
  - contexto inclui leitura da intenção da tarefa.
  - inclui fatos confirmados, inferências e itens não confirmados.
  - inclui validação do escopo.
  - reforça no prompt a separação entre confirmado e inferido.

## UX do menu
- `menus/main_menu.py`
  - ao trocar de projeto, o modelo ativo agora acompanha o projeto selecionado.
  - tela de roteamento automático mostra escopo sugerido.
  - se o Aider exibir prompt interativo, o sistema avisa de forma explícita.

## Documentação e qualidade
- `README.md`
  - removida a promessa de auto-resposta ao loop do Aider.
  - documentadas as melhorias reais.
- `tests/test_smoke.py`
  - adicionado teste básico de fumaça.
- limpeza de `__pycache__` do pacote entregue.
