#!/usr/bin/env bash
set -euo pipefail

REGION="us-east-1"
ACCOUNT="000000000000"
ROLE="arn:aws:iam::${ACCOUNT}:role/lambda-role"
PG_HOST="172.17.0.1"  # acesso ao Postgres do host no Linux bridge gateway

COMMON_ENV="Variables={PGHOST=$PG_HOST,PGPORT=5432,PGDATABASE=folio,PGUSER=folio,PGPASSWORD=dev,ROOT_PATH_FOR_DYNACONF=.}"

# Overrides for Lambda environment
# We use the bridge gateway IP to reach the host's mapped ports (Postgres, LocalStack)
HOST_GATEWAY="172.17.0.1"
DATABASE_HOST="$HOST_GATEWAY"
S3_URL="http://$HOST_GATEWAY:4566"
SQS_URL="http://$HOST_GATEWAY:4566"

# Dynaconf overrides via environment variables
COMMON_ENV="Variables={\
FOLIO_SYNC_DATABASE__HOST=$DATABASE_HOST,\
FOLIO_SYNC_S3__ENDPOINT_URL=$S3_URL,\
FOLIO_SYNC_S3__REGION=$REGION,\
FOLIO_SYNC_S3__ACCESS_KEY=test,\
FOLIO_SYNC_S3__SECRET_KEY=test,\
FOLIO_SYNC_SQS__ENDPOINT_URL=$SQS_URL,\
FOLIO_MCP_DATABASE__HOST=$DATABASE_HOST,\
FOLIO_MCP_S3__ENDPOINT_URL=$S3_URL,\
FOLIO_MCP_S3__REGION=$REGION,\
FOLIO_MCP_S3__ACCESS_KEY=test,\
FOLIO_MCP_S3__SECRET_KEY=test,\
ROOT_PATH_FOR_DYNACONF=.\
}"

# doc-sync Lambda
echo "Deploying folio-sync..."
uv run awslocal lambda create-function \
  --function-name folio-sync \
  --runtime python3.14 \
  --handler folio_sync.handler.lambda_handler \
  --zip-file fileb://dist/folio-sync.zip \
  --role $ROLE \
  --timeout 60 \
  --environment "$COMMON_ENV" \
  2>/dev/null || \
uv run awslocal lambda update-function-code \
  --function-name folio-sync \
  --zip-file fileb://dist/folio-sync.zip

# Event source mapping: SQS → doc-sync
uv run awslocal lambda create-event-source-mapping \
  --function-name folio-sync \
  --event-source-arn arn:aws:sqs:${REGION}:${ACCOUNT}:folio-sync \
  --batch-size 10 \
  2>/dev/null || true

# mcp-server Lambda
echo "Deploying folio-mcp..."
uv run awslocal lambda create-function \
  --function-name folio-mcp \
  --runtime python3.14 \
  --handler folio_mcp.handler.lambda_handler \
  --zip-file fileb://dist/folio-mcp.zip \
  --role $ROLE \
  --timeout 30 \
  --environment "$COMMON_ENV" \
  2>/dev/null || \
uv run awslocal lambda update-function-code \
  --function-name folio-mcp \
  --zip-file fileb://dist/folio-mcp.zip

echo "Lambdas deployadas."
