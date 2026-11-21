# SEOUL IA FIVEM

Desenvolvimento e identidade Seoul Developer. Informações de procedência e atribuição do código de terceiros em `THIRD_PARTY_NOTICES.md`.

## Detector automático de frameworks

O módulo `core/auto_framework_detector.py` identifica evidências de Qbox, QBCore, ESX e vRP, além de integrações instaladas. O resultado é heurístico e deve ser confirmado antes de alterações.



CLI local para trabalhar com projetos FiveM usando Ollama, Gemini ou OpenAI + Aider, com foco em segurança para usuário comum e escopo real para dev.

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
- Ollama (opcional para o painel online)
- Aider (necessário para edição assistida pela CLI)

## Uso

No Windows, execute `INSTALAR_SEOUL.bat` e depois `ABRIR_PAINEL_SEOUL.bat` para o painel web ou `INICIAR_SEOUL.bat` para o menu original.

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

## Guia do cliente: IA local e na nuvem

O Seoul IA FiveM permite usar um modelo local (Ollama) ou um provedor de IA na nuvem (Gemini ou OpenAI). **Nao e necessario informar e-mail ou senha do Google ou ChatGPT no Seoul.** Para nuvem, use uma **chave de API propria**.

> Importante: ChatGPT Plus/Pro e Google AI Pro/Ultra nao significam acesso ilimitado as APIs. O uso das APIs pode ter cobranca, cotas e limites independentes.

### 1. Instale o programa

1. No Windows, instale Python 3.11+, Git e Aider (`python -m pip install --upgrade aider-chat`).
2. Execute `INSTALAR_SEOUL.bat`, depois `INICIAR_SEOUL.bat` para abrir o menu.
3. Cadastre sua base FiveM informando o nome e a pasta. O Seoul tenta detectar QBX/Qbox, QBCore, ESX ou vRP e as integracoes automaticamente.
4. Para usar Ollama, instale-o, inicie o servico e baixe um modelo. Para usar apenas nuvem, nao precisa baixar modelos Ollama, mas o Aider continua necessario na CLI.

### 2. Obtenha sua chave de API

**Gemini:** acesse https://aistudio.google.com/apikey, entre na sua conta Google, crie uma chave de API no Google AI Studio e consulte cotas e precos.

**OpenAI:** acesse https://platform.openai.com/api-keys, entre na plataforma de API da OpenAI, configure faturamento/limites conforme necessario e crie uma chave secreta.

**Nao compartilhe chaves** em chats, prints, tickets, repositórios ou arquivos da base. Nunca forneca sua senha Google ou ChatGPT ao Seoul.

### 3. Configure a chave no Windows

Abra o **PowerShell** e execute apenas o comando correspondente ao seu provedor, substituindo `SUA_CHAVE` pela chave verdadeira:

```powershell
[Environment]::SetEnvironmentVariable("GEMINI_API_KEY", "SUA_CHAVE", "User")
[Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "SUA_CHAVE", "User")
```

**Feche e abra novamente** o terminal e o Seoul para carregar a nova variavel. A chave e armazenada no ambiente de usuario do Windows, nao no cadastro do projeto Seoul. Proteja sua conta do Windows e revogue a chave no site do provedor caso ela seja exposta.

### 4. Escolha o modelo

No menu principal, entre em **Trocar modelo ativo (local / nuvem)**. Escolha:

- **Ollama rapido ou forte:** usa o modelo local do projeto.
- **Google Gemini:** modelo padrao `gemini/gemini-2.5-flash`.
- **OpenAI:** modelo padrao `openai/gpt-4.1-mini`.
- **Automatico:** seleciona Gemini se houver chave, senao OpenAI se houver chave, senao Ollama.
- **Escolher Ollama instalado:** lista modelos locais.
- **Modelo personalizado:** informe o identificador completo com `ollama/`, `gemini/` ou `openai/`.

A escolha **Automatico** e feita no momento da selecao: **nao** e fallback dinamico durante erros de rede, saldo ou limite de API.

### 5. Teste antes de analisar sua base

Entre em **Testar provedor de IA** no menu. O programa mostra se a chave de nuvem esta presente (isso **nao comprova** que ela e valida). Se desejar, autorize um teste real pelo Aider. Esse teste pode consumir creditos da API.

Para tarefas reais, use **Revisar resource / pasta / arquivo** ou **Modo avancado (prompt livre)**. O Aider pode propor ou executar edicoes: use Git/backups e revise qualquer mudanca. Um pedido no prompt para nao alterar arquivos nao substitui protecoes tecnicas.

### 6. Problemas comuns

| Sintoma | O que conferir |
|---|---|
| Chave ausente | Variavel `GEMINI_API_KEY` ou `OPENAI_API_KEY`; reinicie o terminal |
| Erro 401 / autenticacao | Chave correta, ativa e associada ao provedor certo |
| Erro 429 / limite | Cotas, saldo, limites e politica de uso da API |
| Modelo nao encontrado | Nome de modelo suportado pelo provedor e pela versao do Aider/LiteLLM |
| Ollama lento | Capacidade do computador; considere um modelo menor ou API |
| Git alterado | Verifique arquivos nao rastreados e modificacoes antes de autorizar o Aider |
| Volta ao menu | Execute o teste novamente e examine a saida do Aider; nao presuma que houve resposta da IA |

### 7. Licenca Seoul x chave da IA

Sao coisas diferentes:

- **Licenca Seoul IA:** no futuro, permitira ativar o software conforme o plano contratado. **O sistema de licenciamento ainda nao esta implementado nesta versao.**
- **Chave de API:** pertence ao cliente e e utilizada diretamente com Gemini/OpenAI; custos e limites sao do provedor e da conta do cliente.

Para detalhes tecnicos, veja [Guia de provedores](docs/PROVEDORES_IA.md).

