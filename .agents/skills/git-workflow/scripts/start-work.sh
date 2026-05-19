#!/usr/bin/env bash
# Start a new task: sync from remote main, then create a conventional branch.
# Usage: start-work.sh <type> <description>
# Example: start-work.sh feat add-user-authentication
set -euo pipefail

VALID_TYPES="feat fix refactor chore docs test perf ci"
TYPE=${1:-}
DESC=${2:-}

if [[ -z "$TYPE" || -z "$DESC" ]]; then
  echo "Usage: start-work.sh <type> <description>"
  echo "Types: $VALID_TYPES"
  exit 1
fi

if ! echo "$VALID_TYPES" | grep -qw "$TYPE"; then
  echo "Error: invalid type '$TYPE'. Valid types: $VALID_TYPES"
  exit 1
fi

BRANCH="$TYPE/$DESC"

# Check for conflicts with existing branch
if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
  echo "Error: branch '$BRANCH' already exists locally"
  exit 1
fi

# Stash if dirty working tree
STASHED=0
if ! git diff --quiet || ! git diff --staged --quiet; then
  echo "Stashing uncommitted changes..."
  git stash push -m "start-work: stash before syncing main"
  STASHED=1
fi

PREV_BRANCH=$(git branch --show-current)

# Sync remote main
echo "Fetching origin..."
git fetch origin

echo "Switching to main and pulling..."
git checkout main
git pull origin main

# Restore stash to original branch if we stashed
if [[ $STASHED -eq 1 ]]; then
  echo "Returning to $PREV_BRANCH and restoring stash..."
  git checkout "$PREV_BRANCH"
  git stash pop
  # Branch from main, not from current branch
  git checkout main
fi

# Create branch
git checkout -b "$BRANCH"
echo ""
echo "Ready: $BRANCH (branched from $(git rev-parse --short HEAD) on main)"
