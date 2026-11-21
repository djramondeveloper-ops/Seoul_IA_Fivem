# Seoul IA FiveM — IA local e na nuvem

A seleção de IA fica em **Trocar modelo ativo (local / nuvem)**. O programa continua rodando no seu Windows, acessando a pasta local da base FiveM. Apenas as chamadas ao modelo são enviadas ao provedor escolhido.

## Modelos

- Ollama local: modelos instalados no computador.
- Gemini: `gemini/gemini-2.5-flash`.
- OpenAI: `openai/gpt-4.1-mini`.
- Automático: escolhe Gemini se houver chave; senão OpenAI; senão Ollama. **A seleção ocorre ao escolher a opção, não há retentativa automática depois de falha.**
- Personalizado: use prefixo `ollama/`, `gemini/` ou `openai/`. A disponibilidade depende do provedor e da versão do Aider/LiteLLM.

## Credenciais no Windows

No PowerShell, execute **somente para o provedor desejado**, substituindo `SUA_CHAVE` por sua chave real:

```powershell
[Environment]::SetEnvironmentVariable("GEMINI_API_KEY", "SUA_CHAVE", "User")
[Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "SUA_CHAVE", "User")
```

**Feche e reabra o terminal** depois de configurar. Não coloque chaves no GitHub, screenshots ou prompts. As variáveis de ambiente de usuário são persistentes no Windows e podem ser acessadas por processos sob a mesma conta; proteja seu perfil de usuário.

## Verificação

1. Instale e atualize Aider: `python -m pip install --upgrade aider-chat`.
2. Abra o Seoul IA e escolha a opção **Trocar modelo ativo (local / nuvem)**.
3. Selecione o provedor e confirme que sua chave está configurada.
4. Abra **Testar provedor de IA** para verificar a configuração e, se desejar, executar um teste real. Testes na nuvem podem gerar cobrança.
5. Selecione **Modo avançado** para conversar ou uma tarefa específica para analisar resources.

**Importante:** o modo avançado usa Aider e pode modificar arquivos. Use cópias ou controle de versão e recuse alterações não desejadas. A opção de teste é uma solicitação de não alterar, não uma barreira técnica de escrita. O aviso de Git não significa falha da IA.

## Limitações conhecidas

- Seleção automática não é fallback em tempo real.
- Os modelos de nuvem precisam de conexão e chaves válidas, e podem custar por uso.
- Aider/LiteLLM e APIs dos provedores podem mudar: se o modelo falhar, confira o erro e atualize Aider.
- Não houve teste real contra contas Gemini/OpenAI neste commit; a integração precisa ser validada no Windows com credenciais do usuário.
