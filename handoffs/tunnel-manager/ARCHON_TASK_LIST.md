# Tunnel Manager MCP - Archon Task List
## Project Information

**Project Name:** Tunnel Manager MCP  
**Description:** Cloudflare Tunnel management MCP for *.zurielyahav.com with three-class tunnel system  
**Status:** Active  

---

## Tasks (Ordered by Priority)

### Milestone 0: Environment Verification (task_order: 100)
**Title:** Environment Verification & Health Check  
**Description:** Verify all prerequisites from prerequisites.xml are met. Run "Zurot Ready" check before starting implementation.  
**Estimated Hours:** 0.5  
**Status:** todo  

**Verification:**
```bash
git rev-parse --abbrev-ref HEAD  # Should NOT be "main"
cloudflared version              # Should show version
test -f ~/tunnel-management/configs/config.yml && echo "exists"
pgrep -f cloudflared            # Should return PID
ping -c 3 google.com            # Should succeed
grep "ZUROT-MANAGED" ~/tunnel-management/configs/config.yml | wc -l  # Should be 2
```

---

### Milestone 1: Initialize Managed Block (task_order: 90)
**Title:** Initialize Managed Block in Config  
**Description:** Add ZUROT-MANAGED markers to config.yml if they don't exist. Creates boundary between persistent and managed tunnels.  
**Estimated Hours:** 1  
**Status:** todo  
**Depends On:** Milestone 0  

**Verification:**
```bash
grep -A 2 "ZUROT-MANAGED-START" ~/tunnel-management/configs/config.yml
```

---

### Milestone 2: Initialize Run State Ledger (task_order: 80)
**Title:** Create Run State Ledger (run-state.json)  
**Description:** Initialize the ownership tracking ledger. Authoritative record of tunnel ownership.  
**Estimated Hours:** 1  
**Status:** todo  
**Depends On:** Milestone 1  

**Verification:**
```bash
cat ~/tunnel-management/run-state.json | jq '.metadata.schema_version'  # Should output "1.0"
```

---

### Milestone 3: Scaffold MCP Project (task_order: 70)
**Title:** Scaffold MCP Project via mcp-scaffolder  
**Description:** Use mcp-scaffolder to generate standard project structure in handoffs/ and mcps/ directories. Link to Archon project.  
**Estimated Hours:** 2  
**Status:** todo  
**Depends On:** Milestone 2, Archon project created  

**Actions:**
```bash
# Get Archon project ID first
# Then run:
scaffold_skill(
  skill_name="tunnel-manager",
  description="Cloudflare Tunnel management for *.zurielyahav.com",
  archon_project_id="[PROJECT_ID]"
)
```

**Verification:**
```bash
ls -R ~/mcp-skills-hub-monorepo/mcp-skills-hub-dev/mcps/tunnel-manager/
cat ~/mcp-skills-hub-monorepo/mcp-skills-hub-dev/mcps/tunnel-manager/skill.json
```

---

### Milestone 4: Implement Lock Mechanism (task_order: 60)
**Title:** Implement Concurrency Lock System  
**Description:** Create lock acquisition/release functions to prevent concurrent writes to config.yml and run-state.json.  
**Estimated Hours:** 2  
**Status:** todo  
**Depends On:** Milestone 3  

**Deliverable:** src/lock.ts with acquireLock() and releaseLock() functions  

**Verification:**
```bash
# Manual test with stale lock detection
touch ~/tunnel-management/.lock
node build/test-lock.js
```

---

### Milestone 5: Implement Config Parser (task_order: 50)
**Title:** Build Managed-Block YAML Parser  
**Description:** Create functions to read/write ONLY within ZUROT-managed block, preserving all content outside byte-for-byte.  
**Estimated Hours:** 3  
**Status:** todo  
**Depends On:** Milestone 4  

**Deliverable:** src/config-parser.ts with extractManagedBlock(), updateManagedBlock(), parseManagedTunnels()  

**Verification:**
```bash
node build/test-parser.js read
```

---

### Milestone 6: Implement Ownership Verification (task_order: 40)
**Title:** Build Ownership Verification Logic  
**Description:** Implement functions to verify tunnel ownership using run-state.json, RUN_ID in subdomain, and FEATURE_BRANCH context.  
**Estimated Hours:** 2  
**Status:** todo  
**Depends On:** Milestone 5  

**Deliverable:** src/ownership.ts with getExecutionContext(), verifyOwnership(), classifyTunnel()  

**Verification:**
```bash
node build/test-ownership.js verify "test-tunnel" "feature/test"
```

---

### Milestone 7: Implement create_tunnel Tool (task_order: 30)
**Title:** Implement create_tunnel MCP Tool  
**Description:** Build primary tool for creating new tunnels with idempotent behavior, DNS routing, and ledger tracking.  
**Estimated Hours:** 3  
**Status:** todo  
**Depends On:** Milestones 4, 5, 6  

**Deliverable:** create_tunnel(subdomain, port, tunnel_class) MCP tool  

**Tool Signature:**
- subdomain: string (without .zurielyahav.com)
- port: number
- tunnel_class: 'ephemeral' | 'persistent' (default: 'ephemeral')

---

### Milestone 8: Implement delete_tunnel Tool (task_order: 20)
**Title:** Implement delete_tunnel MCP Tool  
**Description:** Build tool for safely deleting tunnels with ownership verification and lifecycle rules.  
**Estimated Hours:** 2  
**Status:** todo  
**Depends On:** Milestone 7  

**Deliverable:** delete_tunnel(subdomain, force) MCP tool  

**Tool Signature:**
- subdomain: string
- force: boolean (default: false)

---

### Milestone 9: Implement list_tunnels Tool (task_order: 10)
**Title:** Implement list_tunnels MCP Tool  
**Description:** Build tool to query active tunnels with classification, ownership, and status information.  
**Estimated Hours:** 2  
**Status:** todo  
**Depends On:** Milestone 8  

**Deliverable:** list_tunnels(filter, verify_dns) MCP tool  

**Tool Signature:**
- filter: 'all' | 'owned' | 'ephemeral' | 'persistent' (default: 'all')
- verify_dns: boolean (default: false)

---

### Milestone 10: Implement Verification Protocol (task_order: 5)
**Title:** Add Tunnel Verification Functions  
**Description:** Implement DNS and HTTP verification to confirm tunnels are working.  
**Estimated Hours:** 2  
**Status:** todo  
**Depends On:** Milestone 9  

**Deliverable:** verifyDNS() and verifyHTTP() functions integrated into create_tunnel  

**Verification:**
```bash
curl -I https://vibetunnel.zurielyahav.com
dig +short vibetunnel.zurielyahav.com
```

---

### Milestone 11: End-to-End Testing (task_order: 3)
**Title:** End-to-End Testing  
**Description:** Test complete workflow: create → verify → list → delete. Verify all safety checks.  
**Estimated Hours:** 3  
**Status:** todo  
**Depends On:** Milestones 7-10  

**Test Cases:**
1. Create ephemeral tunnel
2. Test idempotency (create same tunnel twice)
3. List tunnels (filter by owned)
4. Restart cloudflared and verify DNS/HTTP
5. Delete tunnel
6. Test ownership protection (different branch)
7. Test production protection (Class A)

---

### Milestone 12: Documentation & Deployment (task_order: 1)
**Title:** Documentation & Claude Desktop Integration  
**Description:** Complete README, update feature_list.json, and add to Claude config.  
**Estimated Hours:** 2  
**Status:** todo  
**Depends On:** Milestone 11  

**Deliverables:**
- Updated README.md with usage examples
- feature_list.json marked as passing
- Claude Desktop config entry
- Working MCP in Claude Desktop

**Verification:**
```bash
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | jq '.mcpServers."tunnel-manager"'
```

---

## Total Estimated Hours: 22.5

## Project Links
- Prerequisites Spec: `/Users/zyahav/Documents/dev/mcp-skills-hub-monorepo/mcp-skills-hub-dev/handoffs/tunnel-manager/tunnel_manager_prerequisites.xml`
- Execution Spec: `/Users/zyahav/Documents/dev/mcp-skills-hub-monorepo/mcp-skills-hub-dev/handoffs/tunnel-manager/tunnel_manager_execution.xml`
- Lessons Learned: `/Users/zyahav/Documents/dev/mcp-skills-hub-monorepo/mcp-skills-hub-dev/handoffs/tunnel-manager/LESSONS_LEARNED.md`
