# CLAUDE.md - Project Rules for AI Assistants

> **This file defines how AI assistants should work on this project.**
> Read this FIRST before taking any action.

---

## 🚨 CRITICAL RULES

### Rule 1: No Direct Git Commands
```
❌ NEVER: git commit, git push, git merge, git checkout (via terminal)
✅ ALWAYS: Use git-manager MCP tools
```
**Why:** Git-manager has safety checks, proper workflow, and prevents mistakes.

**Available tools:**
- `list_worktrees` - See current state
- `get_status` - Check for changes
- `create_feature` - Start new work
- `git_add_commit_push` - Commit and push
- `merge_feature` - Merge feature → dev
- `release_merge` - Merge dev → main
- `tag_release` - Create version tag

### Rule 2: Feature Branch Workflow
```
create_feature → work → git_add_commit_push → merge_feature → release_merge
```
Never commit directly to `main` or `dev`.

### Rule 3: Clean Up After Merge
Feature worktrees are temporary. Delete them after merging.
GitHub is the source of truth, not local folders.

---

## 📁 Repository Structure

```
mcp-skills-hub/
├── mcps/                    # All MCP servers
│   ├── git-manager/         # Git operations (worktree-aware)
│   ├── media-hub/           # YouTube, transcription, video tools
│   ├── disk-manager/        # Disk monitoring and cleanup
│   ├── tunnel-manager/      # Cloudflare tunnels
│   ├── cloudflare-dns/      # DNS management
│   ├── bitwarden/           # Password manager
│   └── mcp-scaffolder/      # Create new MCPs
├── dashboard/               # Web UI for config generation
└── README.md                # Installation guide
```

---

## 🔧 Git-Manager Configuration

Environment variables (optional):
- `GIT_MANAGER_REPO_ROOT` - Override auto-detected repo root
- `GIT_MANAGER_TIMEOUT` - Command timeout in seconds (default: 60)
- `GIT_MANAGER_LOG_LEVEL` - DEBUG, INFO, WARNING, ERROR

---

## ✅ Before Committing

- [ ] No `node_modules/` in git
- [ ] No `.env` files (use `.env.example`)
- [ ] No debug logs or temp files
- [ ] README.md is up to date

---

## 🔗 Related Resources

- GitHub: https://github.com/zyahav/mcp-skills-hub
- Issues: Use GitHub Issues for bug reports

---

*This project follows a main/dev/feature branch strategy with git worktrees.*
