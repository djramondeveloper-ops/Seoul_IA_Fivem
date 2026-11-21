# Seoul IA FiveM — Painel Web

Acesse pelo Windows com `ABRIR_PAINEL_SEOUL.bat` (após `INSTALAR_SEOUL.bat`). O painel abre somente em `http://127.0.0.1:8765`.

## Modos de IA

- **Local**: Ollama em `127.0.0.1:11434`. Requer `ollama pull qwen2.5-coder:7b` antes do primeiro uso.
- **Online**: OpenAI, Gemini, Anthropic ou OpenRouter. Escolha o provedor, informe o identificador do modelo e aplique a chave.
- **Automático**: usa o provedor principal e, se a chamada falhar, tenta cada fallback configurado em ordem, no formato `provedor|modelo`. Para fallbacks online, aplique a chave de cada provedor separadamente. A troca não acontece por qualidade de resposta, apenas por erro de requisição.

As chaves digitadas no painel ficam apenas na memória do processo; não são gravadas em disco. Para persistência, configure as variáveis de ambiente `OPENAI_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY` e `OPENROUTER_API_KEY` no Windows. **Não envie chaves para o GitHub.** O painel é local e não deve ser exposto à internet.

## Detector de framework

Informe o caminho absoluto de uma base FiveM existente no computador e clique em **Analisar framework e integrações**. O detector é somente leitura. Ele procura manifests, nomes de resources e referências de código para inferir QBX/Qbox, QBCore, ESX e vRP, com evidências e níveis heurísticos de confiança.

## Escopo e limitações

O chat web envia mensagens a modelos reais, mas **não modifica arquivos**. Para edição assistida, utilize o menu CLI original via `INICIAR_SEOUL.bat`, que usa Aider. A seleção de provedor do painel web ainda não é compartilhada com o fluxo Aider da CLI. O modo online pode gerar custos no provedor. Não foi feito teste de integração em um servidor FiveM real.

## Como funciona o Ollama

1. Instale Ollama e execute `ollama pull qwen2.5-coder:7b`.
2. Confirme com `ollama list`.
3. Abra o painel, selecione **IA Local** e informe o mesmo nome do modelo.
4. Envie uma pergunta no chat. A primeira resposta pode demorar enquanto o modelo carrega.
5. Se aparecer erro de conexão, confirme que o aplicativo Ollama está em execução.

Projeto Seoul Developer baseado no MZ AI FIVEM Community v2 de Mazus-Ofc. Preserve os avisos de autoria e licença aplicáveis ao código original.
