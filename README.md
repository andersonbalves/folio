# Folio

Folio é um sistema de gerenciamento de conhecimento (RAG-ready) que indexa documentos Markdown locais para um banco de dados SQLite com busca textual (BM25 via FTS5), expondo as ferramentas de busca e recuperação de documentos via protocolo MCP (Model Context Protocol). O projeto é distribuído como uma imagem Docker multi-stage completamente standalone.

## Arquitetura

- **`folio-core`** (`packages/core/`): Tipos de domínio compartilhados e helper SQL. Apenas `models.py` e `sql.py`.
- **`folio-sync`** (`packages/doc-sync/`): Indexador local. Possui `core/` próprio (parser, hasher, categorizer, indexer) e `shell/` (db, cli). Lê arquivos Markdown de `data/` e processa os dados populando a base local SQLite.
- **`folio-mcp`** (`packages/mcp-server/`): Servidor MCP que expõe `list_topics`, `search_docs`, `get_document`. Possui `core/` (queries, mappers) e `shell/` (db, tools, handler) com conexão direta em SQLite.
- **`folio-chat`** (`packages/chat/`): Interface web Chainlit e REPL CLI para testes locais.

## Requisitos

- Python 3.14+
- [uv](https://github.com/astral-sh/uv)
- Docker

## Setup Rápido

```bash
# Baixa base de dados de exemplo (kubernetes-docs) e indexa para o SQLite
make k8s-docs
make index
```

## Comandos Principais

### Build e Infra

- `make k8s-docs`: Clona a documentação do Kubernetes em `/data` como massa de teste.
- `make index`: Varre o diretório `data/` e cria/atualiza o banco de dados embutido `folio.sqlite`.
- `make build-image`: Executa o build multi-stage Docker para gerar a imagem imutável `folio-mcp` autônoma (binário + SQLite).
- `make clean`: Remove pastas temporárias e banco sqlite gerado.

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
