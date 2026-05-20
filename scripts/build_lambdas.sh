#!/usr/bin/env bash
set -euo pipefail

mkdir -p dist

# doc-sync
echo "Building folio-sync..."
rm -rf dist/sync && mkdir -p dist/sync
uv export --package folio-sync --no-dev --no-hashes --no-emit-workspace -o /tmp/sync-req.txt
uv pip install -r /tmp/sync-req.txt --target dist/sync/ --quiet
cp -r packages/doc-sync/src/folio_sync dist/sync/
cp -r packages/core/src/folio_core dist/sync/
(cd dist/sync && zip -qr ../folio-sync.zip .)

# mcp-server
echo "Building folio-mcp..."
rm -rf dist/mcp && mkdir -p dist/mcp
uv export --package folio-mcp --no-dev --no-hashes --no-emit-workspace -o /tmp/mcp-req.txt
uv pip install -r /tmp/mcp-req.txt --target dist/mcp/ --quiet
cp -r packages/mcp-server/src/folio_mcp dist/mcp/
cp -r packages/core/src/folio_core dist/mcp/
cp settings.yaml dist/mcp/
(cd dist/mcp && zip -qr ../folio-mcp.zip .)

echo "Artifacts: dist/folio-sync.zip, dist/folio-mcp.zip"
