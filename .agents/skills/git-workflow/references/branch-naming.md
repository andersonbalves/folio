# Branch Naming Reference

## Format

```
<prefix>/<short-kebab-description>
```

## Prefix Table

| Prefix | When to use | Example |
|--------|-------------|---------|
| `feat/` | New functionality | `feat/add-user-authentication` |
| `fix/` | Bug fix | `fix/token-expiry-check` |
| `refactor/` | Code restructure, no behavior change | `refactor/extract-auth-middleware` |
| `chore/` | Maintenance — deps, config, tooling | `chore/update-python-deps` |
| `docs/` | Documentation only | `docs/add-api-reference` |
| `test/` | Tests only | `test/add-auth-integration-tests` |
| `perf/` | Performance improvement | `perf/cache-user-profiles` |
| `ci/` | CI/CD pipeline changes | `ci/add-lint-step` |

## Rules

- **Lowercase only** — no uppercase anywhere
- **Hyphens, not underscores** — `feat/add-user-auth` not `feat/add_user_auth`
- **3–5 words after prefix** — descriptive but concise
- **No issue numbers by default** — add only if your project convention requires them (e.g., `fix/GH-123-token-expiry`)
- **Imperative verb to start** — `add-`, `fix-`, `remove-`, `update-`, not `adding-`, `fixed-`

## Multi-agent naming

When multiple agents work in parallel on related work, split by concern:

```
feat/auth-backend
feat/auth-frontend
feat/auth-tests
```

Or by agent index when the split is arbitrary:

```
refactor/cleanup-db-agent-1
refactor/cleanup-db-agent-2
```
