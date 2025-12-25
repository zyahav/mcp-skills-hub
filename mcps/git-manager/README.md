# Git Manager MCP

A Model Context Protocol (MCP) server for managing Git workflows in a monorepo with nested worktrees.

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GIT_MANAGER_REPO_ROOT` | (auto-detected) | Override the repository root path |
| `GIT_MANAGER_TIMEOUT` | `60` | Git command timeout in seconds |
| `GIT_MANAGER_LOG_LEVEL` | `INFO` | Logging level: DEBUG, INFO, WARNING, ERROR |

### Example with custom config

```json
{
  "git-manager": {
    "command": "/bin/bash",
    "args": ["/path/to/mcps/git-manager/wrapper.sh"],
    "env": {
      "GIT_MANAGER_TIMEOUT": "120",
      "GIT_MANAGER_LOG_LEVEL": "DEBUG"
    }
  }
}
```

## Tools

### `list_worktrees`
Lists all active worktrees and branches.

### `get_status`
Get git status (modified files, staged changes, branch info) for a worktree.
- **Arguments:**
  - `worktree` (string, optional): Specific worktree to check (default: dev)

### `create_feature`
Creates a new feature branch and a sibling worktree.
- **Arguments:**
  - `feature` (string, required): Name of the feature (e.g., `add-logging`)

### `delete_feature`
Deletes a feature worktree and its branch.
- **Arguments:**
  - `feature` (string, required): Name of the feature to delete

### `merge_feature`
Merges a feature branch into `dev`.
- **Arguments:**
  - `feature` (string, required): Name of the feature to merge
  - `push` (boolean, default=false): Push `dev` to origin after merge
  - `delete_branch` (boolean, default=false): Delete the feature branch after merge

### `git_add_commit_push`
Stages changes, commits, and pushes in a specific worktree.
- **Arguments:**
  - `message` (string, optional): Commit message (auto-generated if empty)
  - `worktree` (string, optional): Worktree name (default: dev)
  - `push` (boolean, default=true): Push to origin


### `sync_env`
Copies `.env` from `dev` to all feature worktrees.

### `pull_all`
Pulls the latest changes for all active worktrees.

### `release_merge`
Merges `dev` into `main` for release.
- **Arguments:**
  - `push` (boolean, default=false): Push main to origin after merge
  - `ff_only` (boolean, default=true): Use fast-forward only merge

### `tag_release`
Creates an annotated version tag on main and pushes it.
- **Arguments:**
  - `version` (string, required): Tag name (e.g., `v1.0.0`)
  - `message` (string, optional): Tag message (defaults to "Release {version}")
  - `push` (boolean, default=true): Push tag to origin

### `get_help`
Get usage help for a specific tool or list all tools.
- **Arguments:**
  - `tool_name` (string, optional): Specific tool to get help for

## Workflow Example

```bash
# 1. Create a feature branch
git-manager create_feature feature="add-login"

# 2. Make changes in the feature worktree...

# 3. Commit and push
git-manager git_add_commit_push message="feat: add login page" worktree="feature-add-login"

# 4. Merge to dev
git-manager merge_feature feature="add-login" push=true delete_branch=true

# 5. Release to main
git-manager release_merge push=true

# 6. Tag the release
git-manager tag_release version="v1.0.0"
```
