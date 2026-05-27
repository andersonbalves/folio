# Folio

Folio é um sistema de gerenciamento de conhecimento (RAG-ready) que indexa documentos Markdown locais para um banco de dados SQLite com busca textual (BM25 via FTS5), expondo as ferramentas de busca e recuperação de documentos via protocolo MCP (Model Context Protocol). O projeto é distribuído como uma imagem Docker multi-stage completamente standalone.

## Arquitetura

- **`folio-core`** (`packages/core/`): Tipos de domínio compartilhados e helper SQL. `models.py`, `sql.py` e `splitter.py` (chunking de documentos Markdown).
- **`folio-embeddings`** (`packages/embeddings/`): Protocolo de embedding compartilhado com providers: `none`, `ollama`, `fastembed`, `openai`.
- **`folio-sync`** (`packages/doc-sync/`): Indexador local. Possui `core/` próprio (parser, hasher, categorizer, indexer) e `shell/` (db, cli). Lê arquivos Markdown de `data/`, divide em chunks e popula SQLite com FTS5 e vetores (se configurado).
- **`folio-mcp`** (`packages/mcp-server/`): Servidor MCP que expõe `list_topics`, `lexical_search`, `semantic_search`, `hybrid_search`, `get_document`. Possui `core/` (ranking RRF) e `shell/` (db, tools, handler) com conexão direta em SQLite.
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

## Busca Semântica (opcional)

Por padrão, apenas busca lexical (BM25) está disponível. Para habilitar busca semântica e híbrida, configure um provider de embeddings:

### Variáveis de ambiente (indexação — prefixo `FOLIO_SYNC_`)

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `FOLIO_SYNC_EMBEDDER` | `none` | Provider: `none`, `ollama`, `fastembed`, `openai` |
| `FOLIO_SYNC_EMBEDDER_MODEL` | `""` | Modelo do provider (ex: `BAAI/bge-small-en-v1.5`) |
| `FOLIO_SYNC_CHUNK_SIZE` | `512` | Tamanho preferencial de chunk em tokens |
| `FOLIO_SYNC_CHUNK_MAX_SIZE` | `1024` | Tamanho máximo de chunk em tokens |

### Variáveis de ambiente (servidor MCP — prefixo `FOLIO_MCP_`)

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `FOLIO_MCP_DB_PATH` | `folio.sqlite` | Caminho para o banco SQLite |
| `FOLIO_MCP_EMBEDDER` | `none` | Mesmo provider usado na indexação |
| `FOLIO_MCP_EMBEDDER_MODEL` | `""` | Mesmo modelo usado na indexação |

O modelo configurado no MCP deve ser idêntico ao usado na indexação — caso contrário o servidor recusa inicializar.

### Exemplo com fastembed

```bash
# .env
FOLIO_SYNC_EMBEDDER=fastembed
FOLIO_SYNC_EMBEDDER_MODEL=BAAI/bge-small-en-v1.5
FOLIO_MCP_EMBEDDER=fastembed
FOLIO_MCP_EMBEDDER_MODEL=BAAI/bge-small-en-v1.5
```

### Qualidade

- `make test`: Executa os testes com pytest.
- `make lint`: Verifica estilo com ruff.
- `make typecheck`: Verifica tipos com pyright.
- `make check`: Roda lint, typecheck e testes.

## Uso com Claude Desktop

### Via imagem Docker (recomendado)

1. Popule `data/` com seus documentos Markdown e construa a imagem:

```bash
make build-image
```

2. Adicione ao seu `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "folio": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "folio-mcp"]
    }
  }
}
```

O banco SQLite fica embutido na imagem — nenhum volume externo necessário. Para atualizar os documentos, reindexe e rebuilde a imagem.

### Via uv (desenvolvimento local)

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
