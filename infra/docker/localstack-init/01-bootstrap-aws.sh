#!/usr/bin/env bash
set -euo pipefail

BUCKET="folio-docs"
TOPIC_NAME="folio-events"
QUEUE_NAME="folio-sync"
DLQ_NAME="folio-sync-dlq"

echo "Criando recursos AWS no LocalStack..."

# S3
uv run awslocal s3 mb s3://$BUCKET

# SNS
TOPIC_ARN=$(uv run awslocal sns create-topic --name $TOPIC_NAME \
  --query TopicArn --output text)

# SQS — DLQ primeiro
DLQ_URL=$(uv run awslocal sqs create-queue --queue-name $DLQ_NAME \
  --query QueueUrl --output text)
DLQ_ARN=$(uv run awslocal sqs get-queue-attributes \
  --queue-url $DLQ_URL \
  --attribute-names QueueArn \
  --query Attributes.QueueArn --output text)

# SQS — fila principal com redrive pra DLQ
QUEUE_URL=$(uv run awslocal sqs create-queue \
  --queue-name $QUEUE_NAME \
  --attributes "{\"RedrivePolicy\":\"{\\\"deadLetterTargetArn\\\":\\\"$DLQ_ARN\\\",\\\"maxReceiveCount\\\":\\\"3\\\"}\"}" \
  --query QueueUrl --output text)
QUEUE_ARN=$(uv run awslocal sqs get-queue-attributes \
  --queue-url $QUEUE_URL \
  --attribute-names QueueArn \
  --query Attributes.QueueArn --output text)

# SNS → SQS subscription
uv run awslocal sns subscribe \
  --topic-arn $TOPIC_ARN \
  --protocol sqs \
  --notification-endpoint $QUEUE_ARN

# S3 → SNS notification (apenas .md)
uv run awslocal s3api put-bucket-notification-configuration \
  --bucket $BUCKET \
  --notification-configuration "{
    \"TopicConfigurations\": [{
      \"TopicArn\": \"$TOPIC_ARN\",
      \"Events\": [\"s3:ObjectCreated:*\"],
      \"Filter\": {
        \"Key\": {\"FilterRules\": [{\"Name\": \"suffix\", \"Value\": \".md\"}]}
      }
    }]
  }"

echo "LocalStack pronto."
echo "  Bucket : s3://$BUCKET"
echo "  SNS    : $TOPIC_ARN"
echo "  SQS    : $QUEUE_URL"
echo "  DLQ    : $DLQ_URL"
