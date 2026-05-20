# Folio

Folio é um sistema de gerenciamento de conhecimento (RAG-ready) que sincroniza documentos Markdown de um bucket S3 para um banco de dados Postgres com busca vetorial/textual, expondo as ferramentas via protocolo MCP (Model Context Protocol).

## Arquitetura

- **`folio-core`**: Lógica pura de domínio (parsing, hashing, categorização).
- **`folio-sync`**: Sincronização event-driven S3 -> Postgres via SQS/SNS.
- **`folio-mcp`**: Servidor MCP que expõe ferramentas de busca e listagem.

## Requisitos

- Python 3.14+
- [uv](https://github.com/astral-sh/uv)
- Docker & Docker Compose
- [LocalStack CLI](https://docs.localstack.cloud/getting-started/installation/) (opcional, `awslocal` recomendado)

## Setup Rápido

```bash
# Sobe infra, aplica migrations, baixa docs K8s, faz seed e deploy das Lambdas
make bootstrap
```

## Comandos Principais

### Infraestrutura

- `make up`: Inicia Postgres e LocalStack, faz seed do S3 e sincroniza com o DB automaticamente.
- `make down`: Para os containers.
- `make clean`: Remove containers, volumes e artefatos de build.

### Desenvolvimento

- `make serve`: Roda o servidor MCP localmente via stdio.
- `make chat`: Abre REPL conversacional com modelo Ollama local + ferramentas MCP (requer `ollama serve` rodando).
- `make seed`: Faz upload dos arquivos `.md` de `seed/` para o bucket S3 local.
- `make sync-full`: Executa uma sincronização manual completa S3 -> DB.
- `make migrate`: Aplica migrations SQL.

### AWS Lambdas (LocalStack)

- `make build`: Empacota as Lambdas em `dist/`.
- `make deploy-local`: Faz o deploy das Lambdas no LocalStack.
- `make invoke-mcp PAYLOAD='...'`: Invoca a Lambda MCP.

**Exemplos por ferramenta:**

```bash
# list_topics — lista todos os tópicos indexados
make invoke-mcp PAYLOAD='{"tool":"list_topics","arguments":{}}'

# list_topics — filtrado por categoria
make invoke-mcp PAYLOAD='{"tool":"list_topics","arguments":{"category":"concept"}}'

# search_docs — busca textual BM25 (suporta websearch syntax)
make invoke-mcp PAYLOAD='{"tool":"search_docs","arguments":{"query":"scheduling pods affinity"}}'

# search_docs — com limite customizado
make invoke-mcp PAYLOAD='{"tool":"search_docs","arguments":{"query":"persistent volume claim","limit":5}}'

# get_document — conteúdo completo de um documento (path vem do list_topics ou search_docs)
make invoke-mcp PAYLOAD='{"tool":"get_document","arguments":{"path":"concepts/workloads/pods.md"}}'
```

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
