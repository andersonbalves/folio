# PR Description Template

## Template

```markdown
## Summary
- <why this changed — not what; the diff already shows what>
- <bullet 2 if needed>
- <bullet 3 if needed>

## Motivation
<The problem this solves and why it matters now. Link to issue if one exists.>

## Test plan
- [ ] <specific behavior to verify manually>
- [ ] <edge case covered by new tests>
- [ ] <regression area to check>

## Breaking changes
<What callers must update. Omit this section entirely if there are none.>
```

## gh CLI invocation

```bash
gh pr create \
  --title "feat(auth): add JWT-based user authentication" \
  --body "$(cat <<'EOF'
## Summary
- Replace session-cookie auth with JWT to support load-balanced deployments
- Add `/login` and `/refresh` endpoints in `auth/handlers.go`
- Wire `AuthMiddleware` into all `/api/*` routes

## Motivation
Session cookies broke under load balancing because sessions weren't shared
across instances. JWT tokens are stateless and work without shared storage.
Closes #42.

## Test plan
- [ ] Login with valid credentials returns 200 + token
- [ ] Protected route with expired token returns 401
- [ ] Refresh endpoint issues new token without re-login
- [ ] Existing `/api/users` routes still respond correctly

## Breaking changes
`Authorization: Bearer <token>` header now required on all `/api/*` routes.
Clients using cookie auth will receive 401 until updated.
EOF
)"
```

## Tips

- **Summary bullets say WHY, not what.** "Replace session-cookie auth with JWT to support load balancing" is a why. "Add JWT middleware" is a what.
- **Motivation is one paragraph** — don't repeat the summary bullets.
- **Test plan uses checkboxes** — reviewers can tick them off.
- **Omit Breaking changes entirely** if there are none — don't write "None."
- **PR title** follows Conventional Commits: `<type>(<scope>): <imperative summary>`
