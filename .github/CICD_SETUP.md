# CI/CD Setup Guide

## GitHub Actions Workflows

### 1. CI Workflow (`ci.yml`)
**Triggers:** Push to `dev`, PR to `main`

**Jobs:**
- `validate` - Checks JSON, Python syntax, shell scripts, agent definitions
- `test-mcps` - Tests MCP server imports
- `test-launcher` - Tests agent-launcher.sh

### 2. Release Workflow (`release.yml`)
**Triggers:** Push to `main`, Manual dispatch

**Actions:**
- Creates GitHub Release with auto-generated version tag
- Manual trigger allows custom version (e.g., `v1.0.0`)

---

## Branch Protection Rules (Required Setup)

Go to: **GitHub → Settings → Branches → Add rule**

### Protect `main` branch:

| Setting | Value |
|---------|-------|
| Branch name pattern | `main` |
| ✅ Require a pull request before merging | Enabled |
| ✅ Require approvals | 1 (or as needed) |
| ✅ Require status checks to pass | Enabled |
| Required checks | `validate`, `test-mcps`, `test-launcher` |
| ✅ Require branches to be up to date | Enabled |
| ✅ Do not allow bypassing | Recommended |

### Protect `dev` branch (optional):

| Setting | Value |
|---------|-------|
| Branch name pattern | `dev` |
| ✅ Require status checks to pass | Enabled |
| Required checks | `validate` |

---

## Workflow: Feature Development

```
1. Create feature branch from dev
   git checkout dev
   git pull origin dev
   git checkout -b feature/my-feature

2. Make changes, commit, push
   git add .
   git commit -m "feat: Add new feature"
   git push origin feature/my-feature

3. Create PR: feature/my-feature → dev
   - CI runs automatically
   - Merge when green

4. Create PR: dev → main (Release)
   - CI runs automatically
   - Requires approval
   - Auto-creates release on merge
```

---

## Using git-manager MCP

Instead of manual git commands, use the git-manager tools:

```
# Create feature worktree
git_manager.create_feature(feature="my-feature")

# Work on feature...

# Merge to dev
git_manager.merge_feature(feature="my-feature", push=true, delete_branch=true)

# Release to main
git_manager.release_merge(push=true)
git_manager.tag_release(version="v1.0.0")
```

---

## Secrets Required

None required for basic CI. The `GITHUB_TOKEN` is automatically provided.

For additional integrations (notifications, deployments), add secrets in:
**GitHub → Settings → Secrets and variables → Actions**
