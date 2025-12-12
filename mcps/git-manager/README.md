# Git Manager MCP

A Model Context Protocol (MCP) server for managing Git workflows in a monorepo with nested worktrees.

## Tools

### `create_feature`
Creates a new feature branch and a sibling worktree.
- **Arguments:**
  - `feature` (string, required): Name of the feature (e.g., `add-logging`). Warning: Do NOT use arguments like `--help`.

### `delete_feature`
Deletes a feature worktree and its branch.
- **Arguments:**
  - `feature` (string, required): Name of the feature to delete.

### `merge_feature`
Merges a feature branch into `dev`.
- **Arguments:**
  - `feature` (string, required): Name of the feature to merge.
  - `push` (boolean, default=False): Whether to push `dev` to origin after merge.
  - `delete_branch` (boolean, default=False): Whether to delete the feature branch after merge.

### `git_add_commit_push`
Stages changes, commits, and pushes in a specific worktree.
- **Arguments:**
  - `message` (string, required): Commit message.
  - `worktree` (string, optional): Name of the worktree (e.g. `feature-add-logging`). Defaults to `dev` if omitted.
  - `push` (boolean, default=True): Whether to push to origin.

### `list_worktrees`
Lists all active worktrees and branches.
- **Arguments:** None.

### `sync_env`
Copies `.env` from `dev` to all feature worktrees.
- **Arguments:** None.

### `pull_all`
Pulls the latest changes for all active worktrees.
- **Arguments:** None.

### `release_merge`
Merges `dev` into `main` for release.
- **Arguments:**
  - `push` (boolean): Push main after merge.
  - `ff_only` (boolean): Enforce fast-forward merge.

### `tag_release`
Tags the current `main` branch.
- **Arguments:**
  - `version` (string): Tag name (e.g. `v1.0.0`).
  - `message` (string): Tag message.
  - `push` (boolean): Push tag to origin.
