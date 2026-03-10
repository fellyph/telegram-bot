# Guia de Uso e Deploy — Telegram Bot

## Visão Geral

Este projeto é um **bot para o Telegram** construído como um **Cloudflare Worker em Python** (via Pyodide). Ele recebe mensagens via webhook, gera respostas utilizando **Cloudflare Workers AI** (modelo Llama 3) e armazena o histórico de conversas no **Cloudflare D1** (SQLite distribuído no edge).

## Pré-requisitos

- **Node.js** (v18+) e **npm** — [nodejs.org](https://nodejs.org/)
- **uv** (gerenciador de pacotes Python) — [docs.astral.sh/uv](https://docs.astral.sh/uv/getting-started/installation/)
- **Python 3.12+**
- Conta na **Cloudflare** com Workers habilitado — [dash.cloudflare.com](https://dash.cloudflare.com/)
- Bot criado no Telegram via **@BotFather** — salve o token gerado

## Configuração Inicial

### 1. Instalar dependências

```bash
npm install
uv venv && uv sync
```

### 2. Criar o banco de dados D1

```bash
npx wrangler d1 create bot-database
```

O comando acima retornará um `database_id`. Atualize o campo `database_id` dentro de `d1_databases` no arquivo `wrangler.jsonc`:

```jsonc
"d1_databases": [
    {
        "binding": "DB",
        "database_name": "bot-database",
        "database_id": "<SEU_DATABASE_ID>"
    }
]
```

### 3. Configurar o token do bot

```bash
npx wrangler secret put TELEGRAM_BOT_TOKEN
```

Digite o token fornecido pelo @BotFather quando solicitado.

### 4. Aplicar o schema no banco de dados

**Localmente (para desenvolvimento):**

```bash
npx wrangler d1 execute bot-database --local --file=./schema.sql
```

**Remotamente (produção):**

```bash
npx wrangler d1 execute bot-database --remote --file=./schema.sql
```

## Desenvolvimento Local

Inicie o servidor de desenvolvimento:

```bash
npm run dev
```

### Testando com curl

Simule um payload do Telegram enviando um POST para o servidor local:

```bash
curl -X POST http://localhost:8787 \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "message_id": 1,
      "chat": { "id": 123456 },
      "text": "Olá, bot!"
    }
  }'
```

> **Nota:** Certifique-se de que o schema foi aplicado localmente antes de testar (veja passo 4 acima).

## Testes

Rodar todos os testes:

```bash
uv run pytest
```

Rodar um teste específico:

```bash
uv run pytest tests/test_entry.py::nome_do_teste
```

## Deploy

### 1. Fazer o deploy do Worker

```bash
npm run deploy
```

O comando retornará a URL pública do Worker, no formato:
`https://telegram-bot.<seu-subdomain>.workers.dev`

### 2. Aplicar o schema no D1 remoto

Se ainda não fez, aplique o schema em produção:

```bash
npx wrangler d1 execute bot-database --remote --file=./schema.sql
```

### 3. Configurar o webhook do Telegram

Substitua `<SEU_TOKEN>` e `<URL_DO_WORKER>` pelos valores reais:

```bash
curl "https://api.telegram.org/bot<SEU_TOKEN>/setWebhook?url=<URL_DO_WORKER>"
```

Exemplo:

```bash
curl "https://api.telegram.org/bot123456:ABC-DEF/setWebhook?url=https://telegram-bot.meu-subdomain.workers.dev"
```

A resposta esperada é `{"ok": true, "result": true, "description": "Webhook was set"}`.

## Monitoramento

Acompanhe os logs do Worker em tempo real:

```bash
npx wrangler tail
```

## Arquitetura

```
Telegram → Webhook POST → Cloudflare Worker (Python)
                              │
                              ├── Salva mensagem do usuário no D1
                              ├── Envia texto para Workers AI (Llama 3)
                              ├── Envia resposta via API do Telegram (sendMessage)
                              └── Salva resposta da IA no D1
```

### Arquivos principais

| Arquivo | Descrição |
|---------|-----------|
| `src/entry.py` | Entrypoint do Worker — lógica principal do bot |
| `schema.sql` | Schema do banco D1 (tabela `messages`) |
| `wrangler.jsonc` | Configuração do Cloudflare Workers (bindings AI e D1) |
| `pyproject.toml` | Dependências Python |
| `package.json` | Scripts npm (`dev`, `deploy`) |

## Referência de Comandos

| Tarefa | Comando |
|--------|---------|
| Instalar dependências Node | `npm install` |
| Instalar dependências Python | `uv venv && uv sync` |
| Servidor de desenvolvimento | `npm run dev` |
| Deploy em produção | `npm run deploy` |
| Rodar todos os testes | `uv run pytest` |
| Rodar teste específico | `uv run pytest tests/test_entry.py::nome_do_teste` |
| Aplicar schema (local) | `npx wrangler d1 execute bot-database --local --file=./schema.sql` |
| Aplicar schema (remoto) | `npx wrangler d1 execute bot-database --remote --file=./schema.sql` |
| Configurar secret | `npx wrangler secret put TELEGRAM_BOT_TOKEN` |
| Logs em tempo real | `npx wrangler tail` |
| Gerar types | `npx wrangler types` |
