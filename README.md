# Folio

Folio é um sistema de gerenciamento de conhecimento (RAG-ready) que sincroniza documentos Markdown de um bucket S3 para um banco de dados Postgres com busca vetorial/textual, expondo as ferramentas via protocolo MCP (Model Context Protocol).

## Arquitetura

- **`folio-core`** (`packages/core/`): Tipos de domínio compartilhados e helper SQL. Apenas `models.py` e `sql.py`.
- **`folio-sync`** (`packages/doc-sync/`): Sincronização S3 → Postgres. Possui `core/` próprio (parser, hasher, categorizer, indexer) e `shell/` (db, s3_client, indexer, handler).
- **`folio-mcp`** (`packages/mcp-server/`): Servidor MCP que expõe `list_topics`, `search_docs`, `get_document`. Possui `core/` (queries, mappers) e `shell/` (db, tools, handler).
- **`folio-chat`** (`packages/chat/`): Interface web Chainlit e REPL CLI para testes locais.

## Requisitos

- Python 3.14+
- [uv](https://github.com/astral-sh/uv)
- Docker & Docker Compose
- [LocalStack CLI](https://docs.localstack.cloud/getting-started/installation/) (`awslocal` recomendado)

## Setup Rápido

```bash
# Sobe infra, aplica migrations, baixa docs K8s, faz seed e sincroniza
make bootstrap
```

## Comandos Principais

### Infraestrutura

- `make up`: Inicia Postgres e LocalStack, faz seed do S3 e sincroniza com o DB.
- `make down`: Para os containers e LocalStack.
- `make clean`: Remove containers, volumes e artefatos de build.
- `make migrate`: Aplica migrations SQL de `infra/migrations/`.
- `make seed`: Faz upload dos arquivos `.md` de `infra/seed/` para o bucket S3 local.
- `make sync-full`: Executa sincronização manual completa S3 → DB.

### Desenvolvimento

- `make serve`: Roda o servidor MCP localmente via stdio.
- `make serve-http`: Roda o servidor MCP via SSE na porta 8001.
- `make chat`: Abre REPL conversacional no terminal com Ollama + MCP.
- `make chat-web`: Abre a interface Web Chainlit (requer `make serve-http` em outro terminal).

### Qualidade

- `make test`: Executa os testes com pytest.
- `make lint`: Verifica estilo com ruff.
- `make typecheck`: Verifica tipos com pyright.
- `make check`: Roda lint, typecheck e testes.

## Uso com Claude Desktop

Adicione ao seu `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "folio": {
      "command": "uv",
      "args": ["--directory", "/caminho/para/folio", "run", "folio-mcp"]
    }
  }
}
```
