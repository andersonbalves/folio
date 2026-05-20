.PHONY: up down clean ps logs migrate k8s-docs seed sync-full \
        build deploy-local invoke-mcp serve chat worker \
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
	@bash docker/localstack-init/01-bootstrap-aws.sh
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
	uv run python scripts/apply_migrations.py

# === Seed ===
k8s-docs:
	@echo "Clonando docs Kubernetes..."
	git clone --filter=blob:none --sparse \
	  https://github.com/kubernetes/website.git _k8s-clone
	cd _k8s-clone && git sparse-checkout set \
	  content/en/docs/concepts content/en/docs/tasks
	mkdir -p seed/kubernetes-docs
	cp -r _k8s-clone/content/en/docs/concepts seed/kubernetes-docs/
	cp -r _k8s-clone/content/en/docs/tasks seed/kubernetes-docs/
	rm -rf _k8s-clone
	@echo "Docs: $$(find seed/kubernetes-docs -name '*.md' | wc -l) arquivos"

seed:
	uv run python scripts/seed_localstack.py
	@echo "S3: $$(uv run awslocal s3 ls s3://$(NAME)-docs --recursive | wc -l) objetos"

# === Sync ===
sync-full:
	uv run python scripts/run_full_sync.py

# === Lambda ===
build:
	bash scripts/build_lambdas.sh

deploy-local:
	bash scripts/deploy_lambdas.sh

invoke-mcp:
	@uv run awslocal lambda invoke \
	  --function-name $(NAME)-mcp \
	  --payload '$(PAYLOAD)' \
	  /tmp/mcp-response.json > /dev/null && cat /tmp/mcp-response.json | uv run python -m json.tool
	# Uso: make invoke-mcp PAYLOAD='{"tool":"list_topics","arguments":{}}'

# === Dev local (sem Lambda) ===
serve:
	uv run $(NAME)-mcp

chat:
	uv run scripts/chat.py $(ARGS)

chat-web:
	uv run chainlit run scripts/web_chat.py -w

start-localstack:
	uv run localstack start -d
	uv run localstack wait -t 60

deploy-mcp:
	bash scripts/deploy_mcp_lwa.sh

# === Quality ===
test:
	uv run pytest -v

lint:
	uv run ruff check .

typecheck:
	uv run pyright packages/

format:
	uv run ruff format .

check: lint typecheck test
	@echo "Tudo verde."

# === Bootstrap completo ===
bootstrap: up migrate k8s-docs seed sync-full build deploy-local deploy-mcp
	@echo ""
	@echo "Ambiente pronto."
	@echo "  Modo stdio   : make serve"
	@echo "  Invoke Lambda: make invoke-mcp PAYLOAD='{...}'"
	@echo "  Testes       : make check"
