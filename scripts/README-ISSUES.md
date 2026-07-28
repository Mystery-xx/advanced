# Day 5 Execution Loop - GitHub Issues Creation Guide

This directory contains tools and documentation for creating 18 GitHub issues for the Day 5 Execution Loop.

## Quick Start

### Option 1: Using Node.js Script (Recommended)

If you have a GitHub token:

```bash
# 1. Create a GitHub token at: https://github.com/settings/tokens
#    - Required scope: repo (for private repos) or public_repo (for public repos)

# 2. Set the token
export GITHUB_TOKEN=ghp_your_token_here

# 3. Run the script
node scripts/create-issues.js
```

This will automatically create all 18 issues with proper labels and descriptions.

### Option 2: Using Bash Script (requires GitHub CLI)

If you have GitHub CLI installed:

```bash
# 1. Install gh CLI (if not installed)
# macOS: brew install gh
# Linux: sudo apt install gh
# Windows: winget install GitHub.cli

# 2. Authenticate
gh auth login

# 3. Run the script
bash scripts/create-day5-issues.sh
```

### Option 3: Manual Creation

If you prefer to create issues manually or don't have API access:

1. Open the file: `DAY5_ISSUES.md`
2. For each issue:
   - Click "New Issue" on GitHub
   - Copy the title and description
   - Add the suggested labels
   - Submit

## Issue Summary

| # | Title | Labels | Effort |
|---|-------|--------|--------|
| 1 | Add @Valid annotation to UserController | bug, backend, user-service | S |
| 2 | Add pagination to GET /api/users | feature, backend, user-service | M |
| 3 | Write unit tests for UserServiceImpl | test, backend, user-service | M |
| 4 | Fix email uniqueness check | bug, backend, user-service | M |
| 5 | Extract password validation to PasswordUtil | refactor, backend, user-service | S |
| 6 | Add JavaDoc to UserController methods | doc, backend, user-service | S |
| 7 | Add order status history tracking | feature, backend, order-service | L |
| 8 | Write integration tests for OrderController | test, backend, order-service | M |
| 9 | Fix order cancellation logic | bug, backend, order-service | S |
| 10 | Add OpenAPI documentation for Order endpoints | doc, backend, order-service | M |
| 11 | Add client-side validation to registration form | bug, frontend, validation | S |
| 12 | Add loading states to all API calls | feature, frontend, ux | M |
| 13 | Write E2E test for registration flow | test, frontend, e2e | M |
| 14 | Extract API base URL to environment config | refactor, frontend, config | S |
| 15 | E2E scenario: login → view users → logout | test, e2e, frontend | M |
| 16 | E2E scenario: creating order and status change | test, e2e, order-service | M |
| 17 | Update README with architecture diagram | doc, infrastructure | M |
| 18 | Add API documentation with examples | doc, api, backend | L |

**Total:** 18 issues (6 Small, 9 Medium, 2 Large)

## Labels Reference

All issues use the following label categories:

- **Type:** `bug`, `feature`, `test`, `refactor`, `doc`
- **Component:** `backend`, `frontend`, `e2e`, `infrastructure`
- **Service:** `user-service`, `order-service`, `api`
- **Other:** `validation`, `security`, `ux`, `database`, `configuration`, `setup`, `business-logic`

## Files Created

- `DAY5_ISSUES.md` - Complete documentation of all 18 issues
- `scripts/create-issues.js` - Node.js script for automated creation
- `scripts/create-day5-issues.sh` - Bash script for GitHub CLI
- `scripts/README-ISSUES.md` - This guide

## Troubleshooting

### GitHub Token Issues

If you get authentication errors:

1. Verify your token is valid: `curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user`
2. Ensure token has correct scope (repo or public_repo)
3. Check token hasn't expired

### Rate Limiting

GitHub API rate limits:
- Unauthenticated: 60 requests/hour
- Authenticated: 5,000 requests/hour

The scripts include delays to avoid hitting rate limits.

### Permission Errors

If you can't create issues:
- Verify you have write access to the repository
- Check if the repository is private (requires repo scope)
- Ensure you're not rate limited

## Next Steps

After creating the issues:

1. Review all issues on GitHub
2. Add issues to project board (if applicable)
3. Assign team members
4. Set milestones
5. Start working on issues!

## Questions?

Refer to `DAY5_ISSUES.md` for complete issue descriptions and acceptance criteria.