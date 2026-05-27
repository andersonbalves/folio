.PHONY: up down clean ps logs migrate seed sync-full k8s-docs \
        serve serve-http chat chat-web \
        test lint typecheck format check bootstrap

NAME := folio

# === Infra ===
up:
	docker compose up -d
	@echo "Aguardando Postgres..."
	@until docker compose exec -T postgres pg_isready -U $(NAME) > /dev/null 2>&1; do sleep 1; done
	@echo "Iniciando LocalStack via CLI..."
	uv run localstack start -d
	@echo "Aguardando LocalStack..."
	uv run localstack wait -t 60
	@bash infra/docker/localstack-init/01-bootstrap-aws.sh
	$(MAKE) seed sync-full
	@echo "Stack pronta."

down:
	docker compose down
	uv run localstack stop

clean:
	docker compose down -v
	uv run localstack stop
	rm -rf dist/ _k8s-clone/

ps:
	docker compose ps
	uv run localstack status

logs:
	docker compose logs -f

# === Banco ===
migrate:
	uv run python infra/scripts/apply_migrations.py

# === Seed ===
k8s-docs:
	@echo "Clonando docs Kubernetes..."
	git clone --filter=blob:none --sparse \
	  https://github.com/kubernetes/website.git _k8s-clone
	cd _k8s-clone && git sparse-checkout set \
	  content/en/docs/concepts content/en/docs/tasks
	mkdir -p infra/seed/kubernetes-docs
	cp -r _k8s-clone/content/en/docs/concepts infra/seed/kubernetes-docs/
	cp -r _k8s-clone/content/en/docs/tasks infra/seed/kubernetes-docs/
	rm -rf _k8s-clone
	@echo "Docs: $$(find infra/seed/kubernetes-docs -name '*.md' | wc -l) arquivos"

seed:
	uv run python infra/scripts/seed_localstack.py
	@echo "S3: $$(uv run awslocal s3 ls s3://$(NAME)-docs --recursive | wc -l) objetos"

# === Sync ===
sync-full:
	uv run python infra/scripts/run_full_sync.py

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

start-localstack:
	uv run localstack start -d
	uv run localstack wait -t 60

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

# === Bootstrap completo ===
bootstrap: up migrate k8s-docs seed sync-full
	@echo ""
	@echo "Ambiente pronto."
	@echo "  Modo stdio   : make serve"
	@echo "  HTTP SSE     : make serve-http"
	@echo "  Chat CLI     : make chat"
	@echo "  Chat Web     : make chat-web"
	@echo "  Testes       : make check"
