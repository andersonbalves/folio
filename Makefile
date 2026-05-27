.PHONY: clean k8s-docs index build-image export-image serve serve-http chat chat-web test lint typecheck format check

NAME := folio

# === Build e Infra ===
clean:
	rm -rf dist/ _k8s-clone/ folio.sqlite

k8s-docs:
	@echo "Clonando docs Kubernetes para massa de dados..."
	git clone --filter=blob:none --sparse \
	  https://github.com/kubernetes/website.git _k8s-clone
	cd _k8s-clone && git sparse-checkout set \
	  content/en/docs/concepts content/en/docs/tasks
	mkdir -p data/kubernetes-docs
	cp -r _k8s-clone/content/en/docs/concepts data/kubernetes-docs/
	cp -r _k8s-clone/content/en/docs/tasks data/kubernetes-docs/
	rm -rf _k8s-clone
	@echo "Docs baixados: $$(find data/kubernetes-docs -name '*.md' | wc -l) arquivos"

index:
	uv run python packages/doc-sync/src/folio_sync/shell/cli.py data/ folio.sqlite

build-image:
	docker build -t $(NAME)-mcp .

export-image: build-image
	docker save -o $(NAME)-mcp.tar $(NAME)-mcp
	@echo "Imagem exportada para $(NAME)-mcp.tar. Pronta para compartilhamento."

# === Dev local ===
serve:
	uv run $(NAME)-mcp

serve-http:
	uv run fastmcp run packages/mcp-server/src/folio_mcp/shell/handler.py:mcp \
	  --transport sse --port 8001

chat:
	uv run packages/chat/src/folio_chat/shell/chat.py $(ARGS)

chat-web:
	@echo "Requer MCP server rodando: make serve-http (em outro terminal)"
	uv run chainlit run packages/chat/src/folio_chat/shell/app.py -w

# === Quality ===
test:
	uv run pytest -m "not integration" -v

coverage:
	uv run pytest -m "not integration" --cov --cov-report=term-missing

lint:
	uv run ruff check .

typecheck:
	uv run pyright packages/

format:
	uv run ruff format .

check: lint typecheck test
	@echo "Tudo verde."
