---
name: pr-review-response
description: >
  Guides Claude to close the loop on PR review comments after addressing them — replying to each
  thread to explain what was done (fixed, ignored, deferred) and resolving the thread on GitHub
  when the issue is fully addressed. Always use this skill when the user says things like "respond
  to review comments", "address PR feedback", "I fixed the review", "mark comments as resolved",
  "ignorei o comentário do X", "corrigi o que foi apontado", or after completing implementation
  work prompted by a code review. Even if the user doesn't explicitly mention the skill, if they're
  done working on a PR and reviewers left comments, this skill should trigger.
---

## Why this matters

Reviewers shouldn't have to re-read your diff to figure out what happened to their feedback.
For every review thread — fixed, ignored, or deferred — add a reply explaining the decision.
This creates a paper trail, respects the reviewer's time, and keeps the PR discussion clean.

## Step 1: Fetch all review threads

You need GraphQL to get the thread IDs required for resolving. Comment `databaseId` alone isn't
enough.

```bash
# First, get the repo owner and name
gh repo view --json owner,name -q '"\(.owner.login)/\(.name)"'

# Then fetch threads — replace OWNER, REPO, PR_NUMBER
gh api graphql -f query='
query($owner: String!, $repo: String!, $number: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      reviewThreads(first: 100) {
        nodes {
          id
          isResolved
          comments(first: 5) {
            nodes {
              databaseId
              body
              path
              line
              author { login }
            }
          }
        }
      }
    }
  }
}' -f owner=OWNER -f repo=REPO -F number=PR_NUMBER
```

Each thread has:
- `id` — GraphQL ID, needed to resolve the thread
- `isResolved` — skip threads already resolved
- `comments.nodes[0].databaseId` — REST ID, needed to reply
- `comments.nodes[0].body` — the reviewer's original comment

## Step 2: Reply to each unresolved thread

Reply to the **first comment** in each thread using its `databaseId`:

```bash
gh api repos/{owner}/{repo}/pulls/comments/{databaseId}/replies \
  -f body="your response"
```

**What to write in the reply:**

| Situation | Reply style |
|-----------|-------------|
| Fixed | What changed and where. "Extracted to `parse_date()` in `utils.py:42`." |
| Intentionally ignored | The reasoning. "Keeping as-is — this runs only at startup, allocation cost is negligible." |
| Deferred to another issue | Why + issue link. "Agreed, but out of scope here — tracking in #456." |
| Disagree, want discussion | State your position. Don't resolve — leave open for further review. |

Keep replies short. One or two sentences is almost always enough.

## Step 3: Resolve the thread (when appropriate)

Use the thread's GraphQL `id` (not the comment `databaseId`):

```bash
gh api graphql -f query='
mutation($threadId: ID!) {
  resolveReviewThread(input: { threadId: $threadId }) {
    thread { isResolved }
  }
}' -f threadId="THREAD_GRAPHQL_ID"
```

**Resolve when:** the change is made, an intentional decision was made and explained, or the
issue is deferred to a tracked issue/PR (the issue is the right place to follow up — not this thread).

**Don't resolve when:** actively disagreeing and want continued discussion. Leave open so
the reviewer can push back before the PR merges.

## Step 4: Verify

Re-run the GraphQL query from Step 1 and confirm addressed threads show `isResolved: true`.

## Full workflow

1. `gh pr view --json number` — confirm current PR number
2. Fetch all threads (Step 1)
3. For each `isResolved: false` thread:
   a. Compose reply based on what was done
   b. Post reply (Step 2)
   c. If addressed: resolve thread (Step 3)
4. Verify (Step 4)

## Example session

```
User: "Corrigi tudo que o João pediu no PR, vai lá e responde"

→ fetch threads for current PR
→ thread 1 (extract method): reply "Extracted to `validate_payload()` in core/parser.py:88." → resolve
→ thread 2 (add type hints): reply "Added type hints throughout the module." → resolve
→ thread 3 (rename var): reply "Renamed `d` to `document` across the file." → resolve
→ verify all isResolved: true
```
