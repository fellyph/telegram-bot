# Planejamento de Implementação: Telegram Bot com Python, Cloudflare Workers e Cloudflare AI

O objetivo é criar um bot para o Telegram capaz de interagir com os usuários utilizando LLMs (Cloudflare Workers AI), servido diretamente no _edge_ global através do Cloudflare Workers, utilizando o suporte nativo a **Python** (via Pyodide).

> [!NOTE]
> Os links da documentação da Cloudflare fornecidos inicialmente apontavam para o serviço de "Bot Management" (proteção e bloqueio contra bots maliciosos). Para o desenvolvimento e hospedagem de um bot interativo de IA, a ferramenta correta da Cloudflare é o **Cloudflare Workers** acoplado ao **Cloudflare Workers AI**. O plano abaixo utiliza as documentações corretas para esta tecnologia.

## Arquitetura Proposta

1.  **Telegram Bot API (Webhook)**: O bot não usará _long polling_. Em vez disso, o Telegram enviará as mensagens dos usuários diretamente para a URL do nosso Cloudflare Worker via Webhook (`setWebhook`).
2.  **Cloudflare Workers (Python)**: Atuará como o servidor _serverless_. Receberá o POST do Telegram, extrairá a mensagem, enviará o contexto para a IA e devolverá a resposta para o usuário chamando a API do Telegram.
3.  **Cloudflare Workers AI**: Modelo instanciado pelo Worker (ex: Llama 3) para gerar a resposta com base em uma documentação específica.
4.  **Cloudflare D1 (SQLite)**: Banco de dados relacional distribuído no Edge. Será utilizado para registrar todas as interações (mensagens dos usuários e respostas da IA), permitindo a auditoria das conversas, extração de logs para um dashboard e identificação de melhorias para os prompts do bot.
5.  **Vector Database / Contexto (Opcional Futuro/RAG)**: Para "consultar uma documentação específica", o contexto da documentação pode ser injetado diretamente no prompt (se for pequeno) ou podemos usar o **Cloudflare Vectorize** (banco de dados vetorial) para implementar RAG (Retrieval-Augmented Generation) caso a documentação seja extensa.

## Mudanças Propostas e Estrutura de Arquivos

Criaremos um novo projeto usando o Wrangler CLI configurado para Python.

### Componentes Principais

#### [MODIFY] `wrangler.toml` (Configuração)
Será o arquivo que declara o projeto na Cloudflare, definindo o nome, a compatibilidade de datas e os _bindings_ para a Inteligência Artificial e para o banco de dados.
Ele permitirá o uso de `env.AI` (para acessar o LLM) e `env.DB` (para acesso via SQL ao banco Cloudflare D1) dentro do código Python. Também definirá os "Secrets" (Tokens) criptografados (`TELEGRAM_BOT_TOKEN`).

#### [NEW] `schema.sql` (Estrutura do BD)
Um arquivo SQL simples que ditará as tabelas do D1. Provavelmente teremos uma tabela `messages` contendo colunas como `id`, `chat_id`, `role` (user/assistant), `content` e `timestamp`.

#### [MODIFY] `src/index.py` (Lógica do Bot)
O script Python do Cloudflare Worker. Ele conterá a lógica principal:
*   `on_fetch(request, env)`: O manipulador principal requisitado pelo webhook do Telegram.
*   Extração segura do chat_id e do texto recebido em tempo real.
*   Chamadas assíncronas assombrosas a `env.AI.run()` passando a instrução de sistema (onde inseriremos o link/texto da documentação específica) e a mensagem do utilizador.
*   Conexão via API assíncrona com o _binding_ do D1 (`env.DB.prepare(...)`) para inserir e registrar as mensagens.
*   Requisição de saída via `httpx` (ou utilitário compatível com Pyodide em CF) de volta para o endpoint `sendMessage` da API do Telegram.

#### [NEW] `requirements.txt`
Para que o Pyodide saiba quais dependências Python públicas o script necessita, caso necessário (por exemplo `httpx` para fazer POST no Telegram de maneira simplificada, se escolhermos não usar o utilitário embutido JS via `fetch`).

## Passos de Inicialização

1.  **Criar o Bot no Telegram**
    *   No Telegram, iniciar uma conversa com o `@BotFather`.
    *   Enviar o comando `/newbot`, definir um nome e username.
    *   Salvar o **Bot Token** gerado.
2.  **Inicializar o Projeto Cloudflare e Banco D1**
    *   Executar `npm create cloudflare@latest telegram-ai-bot -- --type=hello-world-python` localmente.
    *   Criar instâncias de DB: `npx wrangler d1 create bot-database`.
    *   Ajustar o `wrangler.toml` para atrelar as funcionalidades de AI e registrar os _bindings_ em tela exibidos pós-criação do D1 (`[[d1_databases]]`).
    *   Aplicar o schema: `npx wrangler d1 execute bot-database --local --file=./schema.sql` (local) e `--remote` (produção).
3.  **Configurar Segredos (Secrets)**
    *   Definir o Token de forma secreta: `npx wrangler secret put TELEGRAM_BOT_TOKEN`.
4.  **Codificar o Roteamento e Interação (Python)**
    *   Substituir/adaptar o boilerplate `src/index.py` com a interação `request -> Telegram Update -> CF AI -> Telegram API`.
5.  **Deploy e Set Webhook**
    *   `npx wrangler deploy` para obter o endereço público (`https://seu-worker.seu-subdomain.workers.dev`).
    *   Configurar o Webhook fazendo uma chamada para: `https://api.telegram.org/bot<SEU_TOKEN>/setWebhook?url=https://seu-worker.seu-subdomain.workers.dev`.

## Plano de Verificação

### 1. Testes Locais e Verificação Estática
*   **Inspeção de Código:** Revisar o `index.py` para conferir se o parsing do objeto JSON do Telegram está extraindo `message.text` e `message.chat.id` corretamente.
*   **Wrangler Dev (Opcional):** É possível inicializar o worker localmente com `npx wrangler dev` para debug, enviando requisições REST locais emulando o payload do Telegram (via `curl` ou Postman) para validar o comportamento e retorno da IA sem precisar do bot ativo no app.

### 2. Verificação de Integração Manual (Via Telegram)
*   Após o **Deploy e setWebhook**, enviar a mensagem "/start" para o bot no aplicativo ou no Telegram Web.
*   **Resultado esperado:** O bot invoca a *Cloudflare AI*, obtém a resposta (baseada no prompt pré-configurado contendo instruções sobre sua documentação base) e retorna uma mensagem inteligível no chat devolvendo a informação requerida.
*   Adicionar um comando customizado tipo `/doc <pergunta>` para testar especificamente a resposta amarrada à documentação.
*   O log da execução poderá ser monitorado via `npx wrangler tail` para debugar qualquer problema nos requests ou nas chamadas da Inteligência Artificial.
