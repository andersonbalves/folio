---
name: git-workflow
description: >
  Orchestrates disciplined Git workflow for all feature work, bug fixes, and maintenance tasks.
  Trigger whenever work is starting on a new task (feature, fix, refactor, chore), whenever
  multiple agents need to work in parallel in the same repo, or whenever a task is finishing
  and needs to be integrated via PR. Covers: syncing from remote main, conventional branch
  naming (feat/, fix/, chore/, etc.), atomic commits, multi-agent worktree coordination,
  and PR creation via gh CLI. Use even if the user just says "start working on X", "fix Y",
  "create a branch for Z", or "I'm done, open a PR" — this skill ties the full lifecycle together.
---

# Git Workflow

Lifecycle: **sync main → branch → [worktree if multi-agent] → atomic commits → PR → cleanup**

Delegates to specialized skills where they exist. Uses bundled scripts for deterministic steps.

**Announce at start:** "Using git-workflow skill."

## Bundled resources

| Resource | Purpose |
|----------|---------|
| `scripts/start-work.sh` | Sync remote main + create conventional branch |
| `scripts/pre-commit.sh` | Detect test runner, run tests, show staged diff |
| `scripts/rebase-update.sh` | Rebase on origin/main + push with --force-with-lease |
| `references/branch-naming.md` | Prefix table, rules, multi-agent naming patterns |
| `references/pr-template.md` | PR body template + full `gh pr create` example |

---

## Phase 1: Start Work

Run the start-work script. It syncs from remote main, stashes if dirty, and creates the branch:

```bash
bash scripts/start-work.sh <type> <description>
# e.g.: bash scripts/start-work.sh feat add-user-authentication
#        bash scripts/start-work.sh fix token-expiry-check
```

Read `references/branch-naming.md` for the full prefix table and naming rules.

**Worktree (multi-agent or parallel work):** invoke `using-git-worktrees` skill. It handles isolation, project setup, and baseline tests. One branch per agent, one worktree per branch — never shared.

---

## Phase 2: Work Atomically

**Rule:** one commit = one logical change. If the subject line needs "and" to describe it, split the commit.

Good: "Add UserProfile model with validation" / "Fix null pointer in auth middleware"
Bad: "Add profile model and fix auth bug" → split into two commits

"Atomic" ≠ tiny. A feature requiring model + migration + tests is one atomic change if they're inseparable.

### Before each commit

Run the pre-commit script — it detects the test runner, runs tests, and shows staged diff:

```bash
bash scripts/pre-commit.sh
```

Then stage exactly what belongs in this commit:

```bash
git add <specific-files>
# or for partial file staging:
git add -p
```

Never `git add .` without reviewing what you're about to stage.

### Commit messages

Invoke `caveman-commit` skill. Conventional Commits format.

---

## Phase 3: Finish Work

Invoke `finishing-a-development-branch` skill. It handles the merge/PR decision, environment detection, and worktree cleanup.

For PR descriptions, read `references/pr-template.md` — it has the template and a full `gh pr create` heredoc example.

Key: PR summary bullets explain **why** something changed, not what — the diff already shows what.

---

## Phase 4: Multi-Agent Coordination

**Isolation rules:**
- Work only in your assigned worktree and branch
- Never modify branches you didn't create
- Never force-push unless you own the branch and it's pre-merge

**Rebasing after others merge:**

```bash
bash scripts/rebase-update.sh
```

Uses `--force-with-lease` (safe: rejects push if remote changed unexpectedly since last fetch).

**Dependency ordering:** if your work depends on another agent's PR, wait for it to merge, then rebase. Signal blocked state explicitly — comment on the blocking PR.

**Avoiding conflicts:** split work at module/file boundaries. Prefer smaller, focused PRs — they merge faster and conflict less.

---

## Red Flags

**Never:**
- Branch from stale local main — `start-work.sh` fetches first
- Commit failing tests — `pre-commit.sh` gates this
- `git add .` without reviewing staged content
- Force-push to `main` or `master`
- Share a worktree between agents
- `--force` instead of `--force-with-lease` on shared remotes

**Always:**
- Run `start-work.sh` to begin any task
- Run `pre-commit.sh` before every commit
- Write the PR body (use template in `references/pr-template.md`)
- Clean up merged branches and worktrees
