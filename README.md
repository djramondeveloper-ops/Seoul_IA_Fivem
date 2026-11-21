# MZ AI FIVEM Community v2

CLI local para trabalhar com projetos FiveM usando Ollama + Aider, com foco em segurança para usuário comum e escopo real para dev.

## O que melhorou nesta versão
- revisão de **resource / pasta / arquivo específico**
- inspeção real da estrutura antes de chamar a IA
- prompt mais rígido para evitar inventar `client.lua`, `server.lua` etc.
- separação entre confirmado, inferido e não confirmado na inspeção de escopo
- validação de suficiência do escopo antes da análise profunda
- histórico local de tarefas com opção de **continuar a última tarefa**
- detecção explícita de prompts interativos do Aider, sem fingir automação que não existe
- uso opcional do **modelo forte** em análises estruturais
- `.aiderignore` automático
- referência de framework continua como **apoio**, nunca como verdade principal

## Requisitos
- Python 3.11+
- Git
- Ollama
- Aider

## Uso
```bash
python app.py
```

## Fluxo recomendado
1. Primeira configuração / verificar ambiente
2. Cadastrar projeto
3. Selecionar projeto ativo
4. Revisar um resource / pasta / arquivo
5. Se precisar, abrir histórico e continuar a tarefa

## Regras internas importantes
- projeto do usuário sempre vence a referência de framework
- scripts com prefixo custom do projeto são prioridade
- sem Git, o modo seguro bloqueia por padrão
- o app tenta trabalhar com **escopo real**, não com achismo de framework


## Criação de resource com scaffolding

Agora a opção **Criar resource novo** primeiro gera a estrutura base no disco e depois oferece abrir a IA para completar a lógica.

Tipos cobertos nesta V1:
- básico
- com banco
- com NUI

Os tipos **com banco + NUI**, **admin/staff** e **phone app** usam a base mais próxima disponível e a IA completa a especialização depois.
