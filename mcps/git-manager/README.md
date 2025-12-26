# Git Manager MCP

A Model Context Protocol (MCP) server for managing Git workflows.

Supports two modes:
- **Monorepo mode**: Uses worktrees for feature branches (default)
- **Standalone repo mode**: Uses simple branches (with `repo_path` parameter)

## Setup (REQUIRED)

You **must** set `GIT_MANAGER_REPO_ROOT` to point to your monorepo root directory.

### Claude Desktop Configuration

```json
{
  "mcpServers": {
    "git-manager": {
      "command": "/bin/bash",
      "args": ["/path/to/mcp-skills-hub/mcps/git-manager/wrapper.sh"],
      "env": {
        "GIT_MANAGER_REPO_ROOT": "/path/to/your-project-monorepo"
      }
    }
  }
}
```

### Expected Directory Structure (Monorepo Mode)

```
your-project-monorepo/           <- GIT_MANAGER_REPO_ROOT points here
├── your-project-main/           <- main worktree
├── your-project-dev/            <- dev worktree  
├── your-project-feature-X/      <- feature worktrees (temporary)
└── ...
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GIT_MANAGER_REPO_ROOT` | **Yes** | - | Path to monorepo root directory |
| `GIT_MANAGER_TIMEOUT` | No | `60` | Git command timeout in seconds |
| `GIT_MANAGER_LOG_LEVEL` | No | `INFO` | DEBUG, INFO, WARNING, ERROR |

## Tools

### `list_worktrees`
Lists all active worktrees and branches.

### `get_status`
Get git status (modified files, staged changes, branch info) for a worktree.
- **Arguments:**
  - `worktree` (string, optional): Specific worktree path to check (default: dev)

### `create_feature`
Creates a new feature branch. For monorepo: creates worktree. For standalone repos: creates simple branch.
- **Arguments:**
  - `feature` (string, required): Name of the feature (e.g., `add-logging`)
  - `repo_path` (string, optional): Path to standalone repository. If omitted, uses monorepo workflow.

### `delete_feature`
Deletes a feature branch. For monorepo: also removes worktree.
- **Arguments:**
  - `feature` (string, required): Name of the feature to delete
  - `repo_path` (string, optional): Path to standalone repository

### `merge_feature`
Merges a feature branch. For monorepo: merges into `dev`. For standalone repos: merges into `main`.
- **Arguments:**
  - `feature` (string, required): Name of the feature to merge
  - `push` (boolean, default=false): Push after merge
  - `delete_branch` (boolean, default=false): Delete the feature branch after merge
  - `repo_path` (string, optional): Path to standalone repository

### `git_add_commit_push`
Stages changes, commits, and pushes in a specific worktree or repository.
- **Arguments:**
  - `message` (string, optional): Commit message (auto-generated if empty)
  - `worktree` (string, optional): Worktree path or repo path (default: dev)
  - `push` (boolean, default=true): Push to origin

### `sync_env`
Copies `.env` from `dev` to all feature worktrees. (Monorepo only)

### `pull_all`
Pulls the latest changes for all active worktrees. (Monorepo only)

### `release_merge`
Merges `dev` into `main` for release. (Monorepo workflow only)
- **Arguments:**
  - `push` (boolean, default=false): Push main to origin after merge
  - `ff_only` (boolean, default=true): Use fast-forward only merge
  - `repo_path` (string, optional): If provided, returns info message (not applicable)

### `tag_release`
Creates an annotated version tag on main and pushes it.
- **Arguments:**
  - `version` (string, required): Tag name (e.g., `v1.0.0`)
  - `message` (string, optional): Tag message (defaults to "Release {version}")
  - `push` (boolean, default=true): Push tag to origin

### `create_repo`
Creates a new GitHub repository from a local directory. Initializes git if needed, creates the GitHub repo, and pushes.
- **Arguments:**
  - `path` (string, required): Local path to the directory
  - `name` (string, required): Repository name on GitHub (e.g., `my-project`)
  - `public` (boolean, default=true): Make repository public
  - `description` (string, optional): Repository description

### `get_help`
Get usage help for a specific tool or list all tools.
- **Arguments:**
  - `tool_name` (string, optional): Specific tool to get help for

## Workflow Examples

### Monorepo Workflow (dev → main)

```bash
# 1. Create a feature branch (creates worktree)
create_feature(feature="add-login")

# 2. Make changes in the feature worktree...

# 3. Commit and push
git_add_commit_push(message="feat: add login page", worktree="mcp-skills-hub-feature-add-login")

# 4. Merge to dev
merge_feature(feature="add-login", push=true, delete_branch=true)

# 5. Release to main
release_merge(push=true)

# 6. Tag the release
tag_release(version="v1.0.0")
```

### Standalone Repo Workflow (feature → main)

```bash
# 1. Create a feature branch (simple branch, no worktree)
create_feature(feature="fix-bug", repo_path="/path/to/my-project")

# 2. Make changes...

# 3. Commit and push
git_add_commit_push(message="fix: resolve bug", worktree="/path/to/my-project")

# 4. Merge to main and push
merge_feature(feature="fix-bug", repo_path="/path/to/my-project", push=true, delete_branch=true)
```

### Create New Repository

```bash
create_repo(path="/path/to/my-project", name="my-project", public=true, description="My awesome project")
```

## Troubleshooting

### "GIT_MANAGER_REPO_ROOT environment variable is required"

You must set this in your MCP configuration. See Setup section above.

### "path does not exist"

Check that `GIT_MANAGER_REPO_ROOT` points to a valid directory.

### Logs

Check `/tmp/git_manager_wrapper.log` for detailed logs.
