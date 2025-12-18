# Session Retrospective & Lessons Learned

## Session: 2025-12-18 (Tunnel Manager MCP Design)

### 1. The "Three Classes" Discovery Process
**Observation:** Initial handoff (v1.0) defined only two tunnel types: Persistent (read-only) and Managed (ephemeral). During review, we discovered a critical third class: editable persistent development tunnels (e.g., `vibetunnel.zurielyahav.com`, `agent-hub.zurielyahav.com`).

**Reality:** Real-world development needs flexible infrastructure that isn't tied to feature branches but still needs to be editable on-the-fly.

**Lesson:** **When designing infrastructure MCPs, always classify resources into three categories:**
1. **Production (Read-Only)** - Never touched by automation
2. **Development Infrastructure (Editable)** - Long-lived but flexible
3. **Ephemeral (Managed)** - Tied to branches/runs, auto-cleanup

**Impact:** Updated handoff to v2.0 with explicit three-class model. This pattern should be applied to ALL future infrastructure MCPs.

---

### 2. The Managed-Block Pattern (Universal Solution)
**Observation:** The "managed block" strategy (`ZUROT-MANAGED-START/END`) solved the coexistence problem elegantly - allowing automation to manage part of a config while preserving human-managed sections.

**Lesson:** **This isn't tunnel-specific - it's a GENERAL pattern for any config-editing MCP:**
- DNS records
- Environment variables
- Deployment configs
- Database connections

**Recommendation:** Create a "Config Coexistence Standard" document that ALL MCPs reference. Define:
- Standard markers for different formats (YAML, JSON, TOML)
- Byte-preservation rules
- Conflict resolution strategies

---

### 3. The XML → Archon Conversion Gap
**Observation:** Current workflow requires manual conversion:
1. Write `execution.xml` with `<milestone>` tags
2. Manually read and understand structure
3. Manually create Archon project
4. Manually create tasks from milestones

**Lesson:** **This is error-prone and time-consuming.** The execution spec should be structured to AUTO-GENERATE Archon tasks.

**Recommendation:** Enhance execution.xml format:
```xml
<milestone index="1" archon_task_order="10" estimated_hours="2">
  <title>Setup Environment</title>
  <verification>cat .env.local | grep DATABASE_URI</verification>
</milestone>
```

Build a parser script that reads execution.xml and calls Archon MCP to create tasks automatically.

---

### 4. Missing: Standard Verification Library
**Observation:** Every execution spec reinvents verification commands:
- DNS checks
- HTTP status verification
- File existence
- Process checks
- Secret validation

**Lesson:** **Create a reusable verification pattern library:**
```yaml
verification_patterns:
  dns_resolution: "dig +short {subdomain}.zurielyahav.com"
  http_status_ok: "curl -I https://{url} | grep -E '(200|301|302)'"
  file_exists: "test -f {path} && echo 'exists' || echo 'missing'"
  process_running: "pgrep -f {process_name} || echo 'not running'"
  secret_loaded: "env | grep {VAR_NAME} | wc -l"
  config_valid: "yq eval . {config_file} > /dev/null"
```

**Impact:** Speeds up spec writing, ensures consistency, reduces errors.

---

### 5. The Lock File Pattern (When to Use)
**Observation:** Tunnel manager needs concurrent write protection via lock files.

**Question Raised:** Which MCPs need locks?
- ✅ Tunnel Manager (config writes)
- ✅ DNS Manager (record mutations)
- ❓ Bitwarden MCP (secret writes)
- ❓ Any config-writing MCP

**Lesson:** **Add to Zurot Standard: "Lock File Decision Tree"**
- Single writer? → No lock needed
- Multiple potential writers? → Lock required
- Read-only operations? → No lock needed

---

### 6. Error Message Standards (Missing)
**Observation:** Handoff uses phrases like "hard abort", "fail with error" without standardization.

**Lesson:** **Every MCP needs standard error codes:**
```
ERR_TUNNEL_001: Ownership ambiguous - cannot prove RUN_ID ownership
ERR_TUNNEL_002: Apex protection violation - attempted to modify production
ERR_TUNNEL_003: Managed block not found in config.yml
ERR_TUNNEL_004: Lock acquisition timeout (stale lock?)
```

**Format:** `ERR_{MCP}_{NUMBER}: {message}`

**Recommendation:** Create error code registry per MCP in prerequisites.xml.

---

### 7. The Bitwarden Discovery Pattern (Reusable)
**Observation:** Every MCP that needs secrets uses the same pattern:
1. List folders
2. Find folder ID
3. Search items within folder
4. Get specific field

**Lesson:** **This should be a standard template in prerequisites.xml:**
```yaml
secret_map:
  CLOUDFLARE_API_TOKEN:
    folder: "Infrastructure"
    item: "Cloudflare DNS Manager"
    field: "CLOUDFLARE_API_TOKEN"
  DATABASE_URI:
    folder: "Zurot-CMS"
    item: "Neon - Dev"
    field: "DATABASE_URI"
```

**Recommendation:** Create "Bitwarden Secret Map Standard" that all MCPs follow.

---

### 8. Idempotency Decision Tree (Universal)
**Observation:** Tunnel manager defined clear idempotency rules:
- Create: exists + same = NO-OP
- Create: exists + different = FAIL
- Delete: missing = NO-OP
- Delete: not owned = FAIL

**Lesson:** **This logic applies to ALL resource-managing MCPs.** Create a reusable decision tree template:

```
CREATE OPERATION:
├─ Resource exists?
│  ├─ Yes → Properties match?
│  │  ├─ Yes → NO-OP (success)
│  │  └─ No → FAIL (conflict)
│  └─ No → CREATE (new)

DELETE OPERATION:
├─ Resource exists?
│  ├─ Yes → Owned by caller?
│  │  ├─ Yes → DELETE (success)
│  │  └─ No → FAIL (unauthorized)
│  └─ No → NO-OP (already gone)
```

**Recommendation:** Add this as "Idempotency Standard" to Zurot guidelines.

---

### 9. The "Zurot Ready" Health Check (Standardize)
**Observation:** Every MCP needs environment validation before execution.

**Current:** Different checks for each project (inconsistent).

**Lesson:** **Build a generic MCP health check framework:**
```bash
# Standard MCP Health Check
mcp-health-check tunnel-manager
# Returns:
# ✓ Auth (Bitwarden)
# ✓ Config exists
# ✓ Lock available
# ✓ Process running
# ✓ Network reachable
```

**Recommendation:** Create `scripts/mcp-health-check.sh` that accepts MCP name and runs standardized checks.

---

## Priority Recommendations (Before Next MCP)

### **Priority 1: Config Coexistence Standard** 📄
**Why:** Multiple MCPs will need this pattern (DNS, tunnels, deployments)
**Action:** Create `STANDARDS/config-coexistence.md` with:
- Managed block syntax for YAML/JSON/TOML
- Byte-preservation rules
- Conflict resolution strategies

### **Priority 2: Verification Library** ✅
**Why:** Every execution spec needs verification commands
**Action:** Create `STANDARDS/verification-patterns.md` with reusable command templates

### **Priority 3: Execution → Archon Auto-Parser** 🤖
**Why:** Manual conversion is error-prone and time-consuming
**Action:** Build script that parses execution.xml and creates Archon tasks automatically

---

## Meta-Lesson: Architecture Before Implementation

**Key Insight:** Taking time to iterate on the handoff document (v1.0 → v1.2 → v2.0) saved massive downstream complexity. The three-class discovery would have been painful if found during implementation.

**Lesson:** **Always validate handoff with real-world scenarios before scaffolding.** Ask:
- "What edge cases exist?"
- "What don't we know yet?"
- "What assumptions are we making?"

The Zurot Standard's two-document approach (prerequisites + execution) forces this thinking.

---

## Session Conclusion

This session produced a **production-ready, three-class tunnel management architecture** that balances safety, flexibility, and automation. The lessons learned apply broadly to all infrastructure MCPs in the Zurot ecosystem.

**Next Steps:**
1. Create prerequisites.xml
2. Create execution.xml
3. Convert to Archon tasks
4. Scaffold via mcp-scaffolder
5. Implement following Agent Loop

**Status:** Ready for implementation ✅

---

### 10. The Scaffolding "Blind Spots" (Git & Tests)
**Observation:** We verified the completeness of the `mcp-scaffolder` loop:
1.  **Git:** ✅ Created and committed successfully.
2.  **Tests:** ❌ No test harness (`tests/` folder or `vitest` config) was generated.
3.  **Completeness:** ❌ The loop halted due to `Archon` connectivity (timeout) and `mcp-scaffolder` dependency issues.

**Lesson:** **The "Harness Loop" is incomplete without a Test Harness.**
We cannot practice TDD if the scaffolder doesn't give us a test environment.

**Recommendation:** Update `mcp-scaffolder` template to include:
- `tests/` directory
- `vitest` dependency
- `basic.test.ts` to verify the "health check"

### 11. The "Archon-First" Friction (Connectivity)
**Observation:** The strict "Archon-First" rule halted work because the Agent couldn't connect to `localhost:8051`, even though the tunnel was up.
- **Cause:** `mcp_config.json` default timeout was too short for tunnel latency.
- **Fix:** Added `"timeout": 60` to config.

**Lesson:** **Resilience is required for the Task Manager.**
If the Task Manager (Archon) is unreachable, the Agent is paralyzed.
1.  **Config:** Always set high timeouts for tunneled MCPs.
2.  **Strategy:** Use public URLs (Cloudflare Access) instead of raw tunnels for critical infrastructure.

### 12. "Bootstrapping" Paradox
**Observation:** We needed `mcp-scaffolder` to create the project, but `mcp-scaffolder` crashed because it lacked the `mcp` dependency (which we hadn't installed yet).

**Lesson:** **Tools must be runnable in "CLI Mode" without heavy dependencies.**

### Session 2025-12-18: Tunnel Manager Implementation

#### 13. "Mock-First" Testing for Infrastructure Tools
**Observation:** When building MCPs that modify system state (like editing config files or running shell commands), "Unit Tests" often aren't enough, but "E2E Tests" are too dangerous.
**Solution:** We created `src/test-e2e.ts` which uses the *real* tool logic but points to *temporary* mock config/ledger paths via environment variables (`TUNNEL_CONFIG_PATH=./test.yml`).
**Benefit:** verified the full toolchain (parsing, locking, logic, file I/O) without risking the user's actual production setup. This should be a standard pattern for all "Infrastructure" MCPs.

#### 14. The "Managed Block" Pattern Confirmed
**Observation:** We needed to manage a Cloudflare config file that the user also manually edits.
**Solution:** The strategy of using `ZUROT-MANAGED-START` and `END` config/ledger markers proved highly effective.
**Detail:** We used string splitting to find the block, but a YAML parser *inside* the block. This preserved comments and structure *outside* the block perfectly, which a full Load -> Edit -> Dump cycle would have destroyed.

#### 15. The "Dual-Ledger" Drift Problem
**Observation:** We maintain two sources of truth: `config.yml` (Cloudflare Routing) and `run-state.json` (Ownership Metadata).
**Risk:** If `cloudflared` fails or the process crashes between updating Config and updating Ledger, they drift.
**Mitigation:** `create_tunnel` uses "Config First" (action) then "Ledger Second" (record). `list_tunnels` reads *both* and attempts to correlate.
**Lesson:** Infrastructure tools must assume drift can happen and handle it gracefully (e.g., listing a tunnel as "active" in config but "unknown" in ledger if missing metadata).

#### 16. Concurrency Locking is Mandatory
**Observation:** Even for a single-user agent, file locking (`.lock`) was critical.
**Detail:** We verified this with `src/test-lock.ts`. rapid-fire tool calls would race to read/write the config file. The `retry` + `stale check` logic is a reusable component for all future file-based MCPs.

#### 17. The "Vite Host Header" Trap
**Context:** Modern dev servers (Vite, Webpack) reject requests where the `Host` header doesn't match `localhost` (DNS Rebinding protection).
**Issue:** Cloudflare Tunnels forward the public hostname (e.g., `ark-on.zurielyahav.com`) as the `Host` header by default. This causes the local server to reject the connection with "Host not allowed".
**Fix:** We must explicitly configure `originRequest: httpHostHeader: "localhost"` in the Cloudflare ingress rule.
**Action:** The `create_tunnel` tool was patched to include this automatically for all new tunnels.

#### 18. The "Zombie Ledger" & Desync
**Context:** If a tunnel is deleted from `config.yml` manually (or via a failed script) but remains in `run-state.json`, the tool thinks it exists ("no-op").
**Issue:** `create_tunnel` checks the ledger first for idempotency. If the ledger is stale, you cannot recreate the tunnel.
**Fix:** We need a "Force Reconcile" or "Janitor" tool. For now, manual remediation involves deleting the specific key from `run-state.json`.

#### 19. YAML Artifacts ("The Empty Array")
**Context:** When using simple string manipulation or regex to append to YAML, beware of flow-style artifacts like empty arrays `[]` left behind by parsers or previous edits.
**Issue:** Cloudflare's YAML parser is strict. An errant `[]` line caused the service to fail to restart (`could not find expected ':'`).
**Fix:** Always sanitize input strings (trim, remove artifacts) before appending to the managed block.
