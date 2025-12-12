# MCP Skills Hub - Handoff Document

**Last Updated:** December 11, 2025
**Status:** 🟢 RESTRUCTURE COMPLETE

---

## 🎯 NEXT STEP (Start Here)

**See [WALKTHROUGH.md](WALKTHROUGH.md) for full details on the new architecture.**

The repo has been restructured:
1. `mcps/media-hub/` (formerly `mcp-skills-hub/`)
2. `mcps/disk-manager/` (standalone)
3. `agents/` (capability definitions)

Update your `~/.gemini/settings.json` using the instructions in `WALKTHROUGH.md`.

---

## 📐 Architecture (Target State)

**Philosophy:** Physical Unity, Logical Separation

```
mcp-skills-hub-monorepo/
├── HANDOFF.md                    ← YOU ARE HERE
├── shared/                       ← Common utilities (future)
├── agents/                       ← Agent capability definitions
│   ├── media-agent.json          ← Only sees media-hub
│   ├── disk-agent.json           ← Only sees disk-manager
│   └── admin-agent.json          ← Sees everything
├── mcps/
│   ├── media-hub/                ← Low-risk domain
│   │   ├── hub.py
│   │   ├── wrapper.sh
│   │   └── skills/
│   │       ├── youtube_download/
│   │       ├── mp4_to_mp3/
│   │       ├── transcribe/
│   │       ├── video_snapshot/
│   │       └── tiktok_download/
│   └── disk-manager/             ← High-risk domain (standalone)
│       ├── server.py
│       ├── wrapper.sh
│       └── PROGRESS.md
└── launch/
    └── agent-launcher.sh         ← Enforcement layer
```

**Key Discovery:** Gemini CLI supports `--allowed-mcp-server-names` flag for MCP filtering!

---

## 📊 Current State (Dec 11, 2025)

### Location
```
/Users/zyahav/Documents/dev/mcp-skills-hub-monorepo/mcp-skills-hub/
```

### Working Skills (All Tested ✅)

**Media Skills:**
| Skill | Status |
|-------|--------|
| youtube_download | ✅ Working |
| mp4_to_mp3 | ✅ Working |
| transcribe | ✅ Working (renamed from whisper_local) |
| video_snapshot | ✅ Working |
| tiktok_download | ✅ Working |

**Disk Manager (8 tools, all tested):**
| Tool | Status | Notes |
|------|--------|-------|
| get_disk_status | ✅ PASS | Shows 57% after cleanup |
| scan_junk | ✅ PASS | Found ~14GB cleanable |
| get_procedures | ✅ PASS | Lists 7 procedures |
| get_emergency_workflow | ✅ PASS | Works for normal & critical |
| get_app_status | ✅ PASS | 28 approved, 4 pending |
| approve_app | ✅ PASS | Approved "Antigravity" |
| get_history | ✅ PASS | Shows usage trends |
| execute_cleanup | ✅ PASS | npm_cache freed 11% |

### Git Status
- Repo: `https://github.com/zyahav/mcp-skills-hub.git`
- Last commit: `7e0bd88` - transcribe skill + hub fixes
- **Uncommitted:** disk_manager skill (complete, tested)

---

## 🔧 Key Files

| File | Purpose |
|------|---------|
| `/Users/zyahav/.gemini/settings.json` | Gemini MCP config |
| `mcp-skills-hub/hub.py` | Current hub (has SKILL_LOCKS fix) |
| `mcp-skills-hub/wrapper.sh` | Hub launcher (uses relative paths) |
| `mcp-skills-hub/skills/disk_manager/server.py` | Disk manager (standalone MCP ready) |
| `mcp-skills-hub/skills/disk_manager/PROGRESS.md` | Disk manager task tracking |

---

## 🔑 Key Decisions Made

1. **Separate hubs by domain** - disk is high-risk, media is low-risk
2. **One monorepo** - single git push commits everything
3. **disk_manager is standalone** - doesn't need hub.py, has 8 tools in one server.py
4. **Agent isolation via CLI flag** - `gemini --allowed-mcp-server-names <name>`
5. **Permission protocol** - all disk cleanup requires `confirm=true`

---

## 📝 What Was Discussed

1. Started with fixing wrapper.sh portability and compression thresholds
2. Renamed whisper_local → transcribe skill
3. Fixed race condition in hub.py (added SKILL_LOCKS)
4. Created disk_manager skill from existing ~/.disk_monitor/ scripts
5. Tested all 8 disk_manager tools - ALL PASSED
6. Discussed architecture with ChatGPT - agreed on domain separation
7. Discovered `--allowed-mcp-server-names` flag in Gemini CLI
8. Decided to restructure repo but haven't started yet

---

## 🚀 Commands for Next Session

```bash
# Check current state
cd /Users/zyahav/Documents/dev/mcp-skills-hub-monorepo/mcp-skills-hub
git status

# Test disk_manager directly
cd skills/disk_manager
python3 -c "from server import do_get_disk_status; print(do_get_disk_status())"

# Launch Gemini with specific MCPs
gemini --allowed-mcp-server-names media-hub
gemini --allowed-mcp-server-names disk-manager
```

---

## ⚠️ Don't Forget

- Disk manager is INSIDE mcp-skills-hub/skills/ but should be SEPARATE MCP
- All disk_manager tests passed but skill not yet committed to git
- Gemini settings still point to old structure

---

**To continue:** Read this file, then proceed with "NEXT STEP" at top.
