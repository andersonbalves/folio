#!/usr/bin/env bash
# Rebase current feature branch on top of latest origin/main, then push.
# Safe: uses --force-with-lease (rejects push if remote changed unexpectedly).
# Usage: rebase-update.sh [remote] [base-branch]
set -euo pipefail

REMOTE=${1:-origin}
BASE=${2:-main}
BRANCH=$(git branch --show-current)

if [[ -z "$BRANCH" ]]; then
  echo "Error: detached HEAD — checkout a branch first"
  exit 1
fi

if [[ "$BRANCH" == "main" || "$BRANCH" == "master" ]]; then
  echo "Error: do not rebase main/master — checkout your feature branch"
  exit 1
fi

# Abort if dirty
if ! git diff --quiet || ! git diff --staged --quiet; then
  echo "Error: uncommitted changes — stash or commit before rebasing"
  exit 1
fi

echo "Fetching $REMOTE..."
git fetch "$REMOTE"

echo "Rebasing $BRANCH onto $REMOTE/$BASE..."
git rebase "$REMOTE/$BASE"

echo "Pushing with --force-with-lease..."
git push --force-with-lease "$REMOTE" "$BRANCH"

echo ""
echo "Done: $BRANCH rebased on $REMOTE/$BASE and pushed."
