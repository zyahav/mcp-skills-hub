# CLAUDE.md - Project Contract & Rules

> **This file is a contract between Zuriel and any AI assistant working on this project.**
> Read this FIRST before taking any action. Remind Zuriel if he tries to break these rules.

---

## 🚨 CRITICAL RULES (Never Break These)

### Rule 1: No Direct Git Commands
```
❌ NEVER: git commit, git push, git merge, git checkout (via terminal)
✅ ALWAYS: Use git-manager MCP tools
```
**Why:** Git-manager has safety checks, proper workflow, and prevents mistakes.

### Rule 2: Two Personas - Never Mix Them
| Persona | Location | Purpose |
|---------|----------|---------|
| **User Zuriel** | `/Users/Shared/tools/mcp-skills-hub` | Uses the tool, never edits |
| **Developer Zuriel** | Clone fresh to `/tmp/` or feature worktree | Makes changes, then deletes |

**Why:** Mixing dev and usage causes confusion and breaks things.

### Rule 3: No Permanent Dev Folders
```
❌ NEVER: Keep development code after merging
✅ ALWAYS: Clone → Branch → PR → Delete
```
**Why:** Stale code causes confusion. GitHub is the source of truth.

---

## 📋 Development Workflow (The Only Way)

### Starting New Work
1. **Clone fresh** (or use git-manager to create feature worktree)
2. **Create feature branch** via git-manager
3. **Make changes**
4. **Commit & push** via `git-manager:git_add_commit_push`
5. **Merge to dev** via `git-manager:merge_feature`
6. **Test in dev**
7. **Release to main** via `git-manager:release_merge`
8. **Delete local copy**
9. **Update tools folder:** `cd /Users/Shared/tools/mcp-skills-hub && git pull`

### If Zuriel Says...
| Zuriel Says | AI Response |
|-------------|-------------|
| "Just run git commit..." | "🚨 Rule 1: We use git-manager, not direct git. Let me use the proper tool." |
| "Edit the file in my tools folder" | "🚨 Rule 2: Tools folder is for USER mode only. Let's clone for development." |
| "I'll keep this dev folder for later" | "🚨 Rule 3: We delete after merging. GitHub is the source of truth." |
| "Let me quickly fix this..." | "Let's follow the workflow: create feature branch first?" |

---

## 🏗️ Repository Structure

### On GitHub (Source of Truth)
```
github.com/zyahav/mcp-skills-hub
├── main          ← Stable, public, what users clone
└── dev           ← Integration branch, testing
```

### On Zuriel's Computer
```
/Users/Shared/tools/
└── mcp-skills-hub/        ← USER MODE (clone of main, read-only mindset)

/tmp/ or /Users/Shared/dev/
└── mcp-skills-hub-*/      ← DEVELOPER MODE (temporary, delete after merge)
```

---

## 🔧 Git-Manager Commands (The Only Git Tools)

| Task | Command |
|------|---------|
| See status | `git-manager:get_status` |
| List worktrees | `git-manager:list_worktrees` |
| Start new feature | `git-manager:create_feature` |
| Commit & push | `git-manager:git_add_commit_push` |
| Merge feature to dev | `git-manager:merge_feature` |
| Release dev to main | `git-manager:release_merge` |
| Tag a release | `git-manager:tag_release` |
| Delete feature | `git-manager:delete_feature` |

---

## 🎯 Project Goals

1. **mcp-skills-hub** is a public, professional MCP toolkit
2. Others can clone and use it easily
3. Clean git history with proper commits
4. No mess, no confusion, no "where is the latest version?"

---

## 📅 Session Start Checklist

When starting a new session, AI should:
1. ✅ Read this CLAUDE.md file
2. ✅ Check current state: `git-manager:list_worktrees`
3. ✅ Confirm which mode Zuriel is in (User or Developer)
4. ✅ Remind rules if needed

---

## 🤝 The Contract

**Zuriel agrees to:**
- Follow the workflow
- Not bypass git-manager
- Delete dev folders after merging
- Keep User and Developer modes separate

**AI agrees to:**
- Always read CLAUDE.md first
- Refuse direct git commands (politely)
- Remind Zuriel of rules when he strays
- Use git-manager for all git operations
- Help maintain clean, professional workflow

---

*Last updated: December 25, 2024*
*Created by: Claude (Dev Organizer)*
