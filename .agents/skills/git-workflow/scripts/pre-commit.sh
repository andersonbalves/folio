#!/usr/bin/env bash
# Pre-commit gate: detect test runner, run tests, show staged diff.
# Run before every commit. Exit non-zero if tests fail.
set -euo pipefail

# Detect and run tests
run_tests() {
  if [ -f package.json ] && grep -q '"test"' package.json 2>/dev/null; then
    echo "Running: npm test"
    npm test
  elif [ -f pyproject.toml ] || [ -f setup.py ] || [ -f pytest.ini ] || [ -f setup.cfg ]; then
    echo "Running: pytest"
    pytest
  elif [ -f Cargo.toml ]; then
    echo "Running: cargo test"
    cargo test
  elif [ -f go.mod ]; then
    echo "Running: go test ./..."
    go test ./...
  elif [ -f mix.exs ]; then
    echo "Running: mix test"
    mix test
  elif [ -f Gemfile ]; then
    echo "Running: bundle exec rspec"
    bundle exec rspec
  else
    echo "Warning: no test runner detected — skipping tests"
    return 0
  fi
}

run_tests

# Show what's staged
STAGED=$(git diff --staged --name-only)
if [ -z "$STAGED" ]; then
  echo ""
  echo "Warning: nothing staged — did you forget 'git add'?"
  exit 1
fi

echo ""
echo "=== Staged files ==="
git diff --staged --stat

echo ""
echo "=== Staged diff ==="
git diff --staged

echo ""
echo "Tests passed. Review diff above, then commit."
