# Quick Task 260323-ljx: Protect default branch

## What was done

Applied branch protection rules to `main` branch of `hdwhdw/sonic-buildcop` via GitHub API:

- **Require PR reviews:** 1 approval required
- **Require status checks:** Must be up-to-date before merging
- **No force pushes:** Disabled
- **No deletions:** Disabled
- **Enforce admins:** Not enforced (owner can bypass for emergencies)

## Command used

```bash
gh api repos/hdwhdw/sonic-buildcop/branches/main/protection --method PUT --input - << 'EOF'
{
  "required_status_checks": {"strict": true, "contexts": []},
  "enforce_admins": false,
  "required_pull_request_reviews": {"required_approving_review_count": 1},
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF
```

## Verification

```json
{
  "required_pr_reviews": 1,
  "require_status_checks": true,
  "enforce_admins": false,
  "allow_force_pushes": false,
  "allow_deletions": false
}
```
