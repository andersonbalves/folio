#!/usr/bin/env bash
set -euo pipefail

REGION="us-east-1"
ACCOUNT="000000000000"
ROLE="arn:aws:iam::${ACCOUNT}:role/lambda-role"
HOST_GATEWAY="172.17.0.1"
DATABASE_HOST="$HOST_GATEWAY"
S3_URL="http://$HOST_GATEWAY:4566"
SQS_URL="http://$HOST_GATEWAY:4566"

# Build the docker image
echo "Building folio-mcp-lwa docker image..."
docker build -t folio-mcp-lwa:latest -f Dockerfile.lambda .

COMMON_ENV="Variables={\
FOLIO_MCP_DATABASE__HOST=$DATABASE_HOST,\
FOLIO_MCP_S3__ENDPOINT_URL=$S3_URL,\
FOLIO_MCP_S3__REGION=$REGION,\
FOLIO_MCP_S3__ACCESS_KEY=test,\
FOLIO_MCP_S3__SECRET_KEY=test,\
ROOT_PATH_FOR_DYNACONF=.\
}"

echo "Deploying folio-mcp-http Lambda..."
uv run awslocal lambda create-function \
  --function-name folio-mcp-http \
  --package-type Image \
  --code ImageUri=folio-mcp-lwa:latest \
  --role $ROLE \
  --timeout 60 \
  --environment "$COMMON_ENV" \
  2>/dev/null || \
uv run awslocal lambda update-function-code \
  --function-name folio-mcp-http \
  --image-uri folio-mcp-lwa:latest

# Wait for function to be active
echo "Waiting for function to be active..."
uv run awslocal lambda wait function-updated-v2 --function-name folio-mcp-http

echo "Creating Function URL..."
uv run awslocal lambda create-function-url-config \
  --function-name folio-mcp-http \
  --auth-type NONE \
  2>/dev/null || true

URL=$(uv run awslocal lambda get-function-url-config --function-name folio-mcp-http | grep FunctionUrl | cut -d'"' -f4)

echo "Lambda deployada. URL: $URL"
echo "Atualize o seu .env com: MCP_LAMBDA_URL=$URL"
