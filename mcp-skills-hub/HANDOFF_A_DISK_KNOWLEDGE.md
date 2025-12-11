# HANDOFF A: Disk Knowledge Service

**Version:** 1.0  
**Date:** December 10, 2025  
**Status:** Ready for Implementation  
**Owner:** Development Team  
**Reviewer:** Board Approval Required  

---

## 📋 Executive Summary

Build a read-only MCP skill that exposes our battle-tested disk management knowledge as a structured, queryable API for LLM agents. This service consolidates scattered instruction files into a single source of truth, enabling safe reasoning before any destructive operations.

**Key Metrics:**
- **Risk Level:** ZERO (read-only, no system modification)
- **Dependencies:** None (foundation layer)
- **Priority:** HIGHEST (all other skills depend on this)
- **Estimated Effort:** 2-3 days

---

## 🎯 Problem Statement

### Current State (Problems)

1. **Knowledge Fragmentation**
   - Instructions scattered across 5+ markdown files
   - Located in multiple directories (`~/.disk_monitor/`, `/agent/mac-disk-monitor/`)
   - No single source of truth
   - Duplication and inconsistency risk

2. **LLM Reasoning Risk**
   - Agents must read multiple files to understand context
   - Risk of hallucinating cleanup procedures
   - No structured way to query "what should I do at 92% disk usage?"
   - Cannot validate actions against proven procedures

3. **Operational Intelligence Loss**
   - Rich historical data (96GB freed on Sept 28, 2025) not accessible
   - Proven procedures with results not queryable
   - Baseline metrics scattered
   - No way to learn from past successes

### Desired State (Solution)

A single MCP skill that:
- ✅ Consolidates all disk knowledge into one canonical source
- ✅ Exposes structured queries for safe reasoning
- ✅ Returns proven procedures with historical results
- ✅ Provides emergency workflows based on current disk state
- ✅ Zero side effects - pure knowledge retrieval
- ✅ Version-controlled for audit trail

---

## 📦 Scope Definition

### ✅ IN SCOPE

1. **Knowledge Consolidation**
   - Merge all existing MD files into single canonical source
   - Preserve all operational intelligence and history
   - Maintain proven procedures with timestamps
   - Include baseline metrics and thresholds

2. **MCP Skill Implementation**
   - Create `disk_knowledge` skill following hub standards
   - Implement 5 core tools (defined below)
   - Pure Python markdown parser (no shell access)
   - Structured JSON responses

3. **Query Interface**
   - Natural language query support
   - Category-based lookup
   - Historical trend access
   - Emergency workflow generation

4. **Testing & Validation**
   - Unit tests for all tools
   - Snapshot tests for output stability
   - Invalid input handling
   - Missing data fallback behavior

### ❌ OUT OF SCOPE

1. **NO System Interaction**
   - No `df`, `du`, or any shell commands
   - No file system scanning
   - No real-time disk metrics
   - No file operations (those belong to `disk_monitor`)

2. **NO Action Execution**
   - No cleanup operations
   - No file deletion
   - No system modification
   - (Those belong to `disk_operator`)

3. **NO Live Data**
   - Does not report current disk usage
   - Does not scan for junk files
   - Does not monitor processes
   - (Those belong to `disk_monitor`)

---

## 📁 Data Model & Structure

### Knowledge Repository Structure

```
skills/disk_knowledge/
├── skill.json                    # MCP skill manifest
├── server.py                     # MCP server implementation
├── INSTRUCTIONS.md               # Consolidated knowledge base
├── README.md                     # Developer documentation
└── lib/
    ├── __init__.py
    ├── knowledge.py              # Markdown parser
    └── query.py                  # Query engine
```

### INSTRUCTIONS.md Schema

The consolidated knowledge base follows this structure:

```markdown
# Disk Management Knowledge Base
Version: 1.0 | Last Updated: 2025-09-28

## Current Baseline
- Total Disk: 228GB
- Current Usage: 123GB (62%)
- Available: 77GB
- Status: EXCELLENT
- Last Major Cleanup: September 28, 2025 (96GB freed)

## Thresholds
- Normal Operation: < 75%
- Warning Level: 75-85%
- Emergency Level: 85-90%
- Critical Level: > 90%

## Proven Cleanup Procedures

### NPM Cache Cleanup
- **Command:** `npm cache clean --force`
- **Location:** `~/.npm`
- **Typical Space Freed:** 6GB+
- **Safety Level:** HIGH (regenerates automatically)
- **Last Success:** 2025-09-28 (freed 6GB)
- **Prerequisites:** None
- **Risk:** None - npm automatically rebuilds cache

### Development Caches Cleanup
- **Locations:** 
  - `~/.cache/puppeteer` (typically 1-2GB)
  - `~/.cache/uv` (typically 500MB+)
  - `~/.cache/whisper` (typically 100-200MB)
  - `~/.cache/lm-studio` (typically 100-200MB)
- **Total Space Freed:** 2.7GB
- **Safety Level:** HIGH
- **Last Success:** 2025-09-28
- **Risk:** None - tools regenerate as needed

### Homebrew Cleanup
- **Command:** `brew cleanup`
- **Typical Space Freed:** 500MB-1GB
- **Safety Level:** HIGH
- **Last Success:** 2025-09-28 (freed 800MB)
- **Risk:** None - keeps current versions

### System Caches
- **Locations:** `~/Library/Caches/*`
- **Typical Space Freed:** 3-5GB
- **Safety Level:** MEDIUM (review contents first)
- **Components:**
  - Google caches: 2.4GB
  - Telegram: 425MB
  - node-gyp: 277MB
  - Browser caches: varies

### Library Application Support Cleanup
- **Locations:** `~/Library/Application Support/*`
- **Potential Space:** 40GB+
- **Safety Level:** MEDIUM-HIGH (requires careful selection)
- **Last Success:** 2025-09-28 (freed 47GB)
- **Safe Targets:**
  - VS Code caches (WebStorage, Service Worker, CachedExtensionVSIXs)
  - Google Drive caches
  - Application GPUCache directories
- **NEVER Touch:** User folders, extensions, settings databases

## Emergency Workflows

### At 85-90% Capacity (Warning)
1. NPM cache cleanup (6GB expected)
2. Development caches (2.7GB expected)
3. Homebrew cleanup (800MB expected)
**Expected Recovery:** ~10GB

### At 90-95% Capacity (Emergency)
1. All above procedures
2. System caches cleanup (3-5GB expected)
3. Review Library/Caches manually
**Expected Recovery:** ~15GB

### At 95%+ Capacity (Critical)
1. All above procedures
2. Library Application Support targeted cleanup
3. Manual review of large directories
**Expected Recovery:** ~20-50GB

## Development Environment Context
- Heavy npm/pnpm usage (caches grow 6GB+ monthly)
- AI development tools (Whisper, LM-Studio, Puppeteer)
- Node.js development environment
- VS Code (cache-heavy)
- Homebrew package manager

## Historical Performance Data

### September 28, 2025 - Major Cleanup Session
- **Starting:** 181GB (74% - danger zone)
- **Ending:** 123GB (62% - excellent)
- **Total Freed:** 96GB (58GB net improvement)
- **Procedures Used:**
  - Session 1: NPM, dev caches, Homebrew, pnpm (49GB)
  - Session 2: Library cleanup (47GB)
- **Outcome:** Crisis completely resolved

## Maintenance Schedule
- **Monthly:** npm cache clean, dev cache cleanup
- **Quarterly:** Homebrew cleanup, pnpm store prune
- **As Needed:** AI tool cache cleanup, Library review

## Safety Protocols

### Permission Requirements
- **CRITICAL:** NEVER execute ANY cleanup without explicit user permission
- **ALWAYS** ask "Permission to run [specific command]?"
- **WAIT** for explicit YES/NO response
- **NEVER** assume permission, even for "safe" operations

### Safe vs Unsafe Operations
**ALWAYS SAFE:**
- Reading disk usage
- Scanning for junk files
- Querying this knowledge base

**REQUIRES PERMISSION:**
- Any rm, cleanup, brew, npm command
- File deletion or modification
- System cache clearing

**NEVER SAFE WITHOUT REVIEW:**
- Deleting from ~/Documents, ~/Desktop, ~/Projects
- Removing user data or settings
- Touching application databases
```

---

## 🔧 Tool Interface Specification

### Tool 1: `get_baseline()`

**Purpose:** Return current baseline metrics and system status

**Input Schema:**
```json
{}
```

**Output Schema:**
```json
{
  "disk_size_gb": 228,
  "baseline_used_gb": 123,
  "baseline_percent": 62,
  "baseline_date": "2025-09-28",
  "available_gb": 77,
  "status": "excellent",
  "thresholds": {
    "warning": 75,
    "emergency": 85,
    "critical": 90
  },
  "last_major_cleanup": {
    "date": "2025-09-28",
    "freed_gb": 96
  }
}
```

**Error Behavior:**
- If baseline data missing: Return error with instructions to update INSTRUCTIONS.md
- Never return fabricated data

---

### Tool 2: `get_procedures(category?)`

**Purpose:** Return proven cleanup procedures with historical results

**Input Schema:**
```json
{
  "category": "string | null"  // Optional: "npm", "dev_caches", "system", "all"
}
```

**Output Schema:**
```json
{
  "procedures": [
    {
      "name": "npm_cache_cleanup",
      "category": "npm",
      "command": "npm cache clean --force",
      "location": "~/.npm",
      "typical_space_freed_gb": 6.0,
      "safety_level": "high",
      "last_success": "2025-09-28",
      "prerequisites": [],
      "risk": "none",
      "notes": "npm automatically rebuilds cache as needed"
    },
    {
      "name": "dev_caches_cleanup",
      "category": "dev_caches",
      "locations": [
        "~/.cache/puppeteer",
        "~/.cache/uv",
        "~/.cache/whisper",
        "~/.cache/lm-studio"
      ],
      "typical_space_freed_gb": 2.7,
      "safety_level": "high",
      "last_success": "2025-09-28",
      "risk": "none",
      "notes": "Tools regenerate caches automatically"
    }
  ],
  "total_expected_gb": 8.7,
  "version": "1.0"
}
```

**Error Behavior:**
- Unknown category: Return all procedures with warning
- No procedures found: Return empty array with explanation

---

### Tool 3: `get_emergency_workflow(current_percent)`

**Purpose:** Generate recommended cleanup sequence based on current disk state

**Input Schema:**
```json
{
  "current_percent": 92  // Required: current disk usage percentage
}
```

**Output Schema:**
```json
{
  "current_percent": 92,
  "status": "emergency",
  "severity": "high",
  "recommended_sequence": [
    {
      "step": 1,
      "procedure": "npm_cache_cleanup",
      "expected_recovery_gb": 6.0,
      "priority": "critical"
    },
    {
      "step": 2,
      "procedure": "dev_caches_cleanup",
      "expected_recovery_gb": 2.7,
      "priority": "high"
    },
    {
      "step": 3,
      "procedure": "homebrew_cleanup",
      "expected_recovery_gb": 0.8,
      "priority": "high"
    },
    {
      "step": 4,
      "procedure": "system_caches_cleanup",
      "expected_recovery_gb": 3.5,
      "priority": "medium"
    }
  ],
  "total_expected_recovery_gb": 13.0,
  "estimated_final_percent": 86,
  "message": "EMERGENCY: Disk at 92%. Execute recommended sequence to recover ~13GB.",
  "next_steps": [
    "User must approve each cleanup operation",
    "Use disk_operator skill with explicit permission",
    "Monitor results after each step"
  ]
}
```

**Status Mapping:**
- < 75%: "normal"
- 75-85%: "warning"  
- 85-90%: "emergency"
- 90%+: "critical"

**Error Behavior:**
- Invalid percentage (< 0 or > 100): Return error
- Missing current_percent: Return error with usage example

---

### Tool 4: `query_instructions(question)`

**Purpose:** Natural language query interface to knowledge base

**Input Schema:**
```json
{
  "question": "string"  // Required: natural language question
}
```

**Output Schema:**
```json
{
  "question": "What should I do at 92% disk usage?",
  "answer": "EMERGENCY: At 92% disk usage, you are in the emergency zone. Recommended immediate actions:\n\n1. NPM Cache Cleanup - Expected to free 6GB\n2. Development Caches - Expected to free 2.7GB\n3. Homebrew Cleanup - Expected to free 800MB\n4. System Caches - Expected to free 3.5GB\n\nTotal expected recovery: ~13GB, bringing you to approximately 86%.\n\nIMPORTANT: Each cleanup requires explicit user permission. Use the disk_operator skill to execute with proper approval.\n\nSee proven procedures from September 28, 2025 session where similar procedures freed 96GB total.",
  "relevant_sections": [
    "Emergency Workflows - At 85-90% Capacity",
    "Proven Cleanup Procedures",
    "Historical Performance Data"
  ],
  "confidence": "high"
}
```

**Query Processing:**
- Keywords extraction (e.g., "92%", "emergency", "cleanup")
- Section matching in INSTRUCTIONS.md
- Contextual answer generation
- Include relevant historical data

**Error Behavior:**
- Empty question: Return error
- No relevant information: Return "No information found" with suggestion to update knowledge base

---

### Tool 5: `get_history(limit?)`

**Purpose:** Return historical cleanup sessions and trends

**Input Schema:**
```json
{
  "limit": 10  // Optional: number of sessions to return (default: 10)
}
```

**Output Schema:**
```json
{
  "sessions": [
    {
      "date": "2025-09-28",
      "type": "major_cleanup",
      "starting_gb": 181,
      "ending_gb": 123,
      "freed_gb": 58,
      "procedures_used": [
        "npm_cache_cleanup",
        "dev_caches_cleanup",
        "library_cleanup"
      ],
      "outcome": "Crisis resolved - moved from danger zone (74%) to excellent (62%)"
    }
  ],
  "trends": {
    "average_monthly_growth_gb": 10,
    "largest_cleanup_gb": 96,
    "most_effective_procedure": "library_cleanup",
    "maintenance_frequency_days": 30
  },
  "version": "1.0"
}
```

**Error Behavior:**
- No history available: Return empty array with note
- Invalid limit: Use default value

---

## 🔒 Safety & Security

### Read-Only Guarantees

**MUST NOT:**
- Execute any shell commands
- Use subprocess for system calls
- Modify files on disk
- Access network resources
- Write to any files except its own logs

**MUST:**
- Only read from INSTRUCTIONS.md
- Parse markdown in-memory
- Return pure JSON
- Fail closed on errors
- Version all responses

### Input Validation

All tool inputs must be validated:
- Type checking (strings, numbers, nulls)
- Range checking (percentages 0-100)
- Length limits (questions < 500 chars)
- Sanitization (no path traversal attempts)

### Error Handling

**Principle:** Fail safe, fail visible

```python
# Good error response
{
  "error": "baseline_data_missing",
  "message": "Baseline data not found in INSTRUCTIONS.md",
  "remedy": "Update INSTRUCTIONS.md with current baseline",
  "severity": "high"
}

# Bad error response (NEVER)
{
  "error": "unknown",
  "message": "Something went wrong"
}
```

---

## 🧪 Testing Requirements

### Unit Tests (Required)

**File:** `tests/test_disk_knowledge.py`

```python
import unittest
from skills.disk_knowledge.lib.knowledge import KnowledgeParser
from skills.disk_knowledge.lib.query import QueryEngine

class TestDiskKnowledge(unittest.TestCase):
    
    def test_get_baseline_success(self):
        """Test baseline retrieval with valid data"""
        result = get_baseline()
        self.assertEqual(result["disk_size_gb"], 228)
        self.assertEqual(result["status"], "excellent")
        
    def test_get_baseline_missing_data(self):
        """Test baseline retrieval with missing file"""
        # Mock missing INSTRUCTIONS.md
        result = get_baseline()
        self.assertIn("error", result)
        
    def test_get_procedures_all(self):
        """Test retrieving all procedures"""
        result = get_procedures()
        self.assertGreater(len(result["procedures"]), 0)
        self.assertIn("npm_cache_cleanup", [p["name"] for p in result["procedures"]])
        
    def test_get_procedures_category_filter(self):
        """Test category filtering"""
        result = get_procedures(category="npm")
        self.assertEqual(len(result["procedures"]), 1)
        self.assertEqual(result["procedures"][0]["category"], "npm")
        
    def test_get_emergency_workflow_critical(self):
        """Test emergency workflow at critical level"""
        result = get_emergency_workflow(current_percent=92)
        self.assertEqual(result["status"], "emergency")
        self.assertGreater(result["total_expected_recovery_gb"], 10)
        
    def test_get_emergency_workflow_normal(self):
        """Test workflow at normal level"""
        result = get_emergency_workflow(current_percent=60)
        self.assertEqual(result["status"], "normal")
        
    def test_query_instructions_relevant(self):
        """Test natural language query"""
        result = query_instructions("What should I do at 92%?")
        self.assertIn("emergency", result["answer"].lower())
        self.assertEqual(result["confidence"], "high")
        
    def test_query_instructions_empty(self):
        """Test empty query"""
        result = query_instructions("")
        self.assertIn("error", result)
        
    def test_get_history_success(self):
        """Test history retrieval"""
        result = get_history(limit=5)
        self.assertIn("sessions", result)
        self.assertIn("trends", result)
        
    def test_input_validation_percentage(self):
        """Test percentage validation"""
        with self.assertRaises(ValueError):
            get_emergency_workflow(current_percent=150)
        with self.assertRaises(ValueError):
            get_emergency_workflow(current_percent=-10)
```

### Integration Tests

```python
class TestDiskKnowledgeIntegration(unittest.TestCase):
    
    def test_full_workflow(self):
        """Test complete reasoning workflow"""
        # 1. Get baseline
        baseline = get_baseline()
        
        # 2. Check if emergency
        if baseline["baseline_percent"] > 85:
            # 3. Get emergency workflow
            workflow = get_emergency_workflow(baseline["baseline_percent"])
            
            # 4. Verify procedures exist
            for step in workflow["recommended_sequence"]:
                procedures = get_procedures(category=step["procedure"])
                self.assertGreater(len(procedures["procedures"]), 0)
```

### Snapshot Tests

**Purpose:** Ensure output structure stability

```python
def test_output_schema_stability(self):
    """Verify JSON schemas don't change unexpectedly"""
    result = get_baseline()
    expected_keys = [
        "disk_size_gb", "baseline_used_gb", "baseline_percent",
        "status", "thresholds", "last_major_cleanup"
    ]
    self.assertEqual(set(result.keys()), set(expected_keys))
```

---

## 📊 Success Criteria (Definition of Done)

### Functional Requirements

- [ ] All 5 tools implemented and working
- [ ] INSTRUCTIONS.md consolidated from all existing MD files
- [ ] All historical data preserved
- [ ] JSON schemas match specification exactly
- [ ] Natural language query works with 90%+ accuracy

### Safety Requirements

- [ ] Zero shell command execution
- [ ] No file system modification capability
- [ ] All inputs validated
- [ ] All errors handled gracefully
- [ ] Fail-closed behavior verified

### Testing Requirements

- [ ] All unit tests pass (100% pass rate)
- [ ] Integration tests pass
- [ ] Snapshot tests stable
- [ ] Edge cases covered (missing data, invalid input, corrupted files)
- [ ] Manual testing completed

### Documentation Requirements

- [ ] README.md written for developers
- [ ] INSTRUCTIONS.md complete and accurate
- [ ] Tool descriptions clear for LLM
- [ ] Example queries documented
- [ ] Error messages documented

### Integration Requirements

- [ ] skill.json manifest correct
- [ ] server.py follows MCP protocol
- [ ] Loads successfully in hub.py
- [ ] Shows up in Claude Desktop tool list
- [ ] Can be called from Claude successfully

---

## 🎯 Implementation Checklist

### Phase 1: Foundation (Day 1)

- [ ] Create `skills/disk_knowledge/` directory structure
- [ ] Write skill.json manifest
- [ ] Create INSTRUCTIONS.md (consolidate existing MDs)
- [ ] Set up lib/knowledge.py markdown parser
- [ ] Implement basic error handling framework

### Phase 2: Core Tools (Day 2)

- [ ] Implement `get_baseline()`
- [ ] Implement `get_procedures()`
- [ ] Implement `get_emergency_workflow()`
- [ ] Implement `get_history()`
- [ ] Write unit tests for all tools

### Phase 3: Query Interface (Day 2-3)

- [ ] Implement `query_instructions()` with NLP
- [ ] Add keyword extraction
- [ ] Add context matching
- [ ] Test with various question formats

### Phase 4: Testing & Polish (Day 3)

- [ ] Complete test suite
- [ ] Manual testing with Claude Desktop
- [ ] Performance optimization
- [ ] Documentation review
- [ ] Security audit

---

## 🚀 Deployment & Validation

### Pre-Deployment Checklist

- [ ] All tests green
- [ ] Code review completed
- [ ] INSTRUCTIONS.md validated for accuracy
- [ ] No breaking changes to hub.py
- [ ] Git commit with proper message

### Validation Steps

1. **Load test in hub:**
   ```bash
   cd mcp-skills-hub
   python3 hub.py
   # Verify disk_knowledge appears in logs
   ```

2. **Test each tool manually:**
   ```bash
   # Use MCP inspector or Claude Desktop
   # Call each tool with sample inputs
   # Verify outputs match spec
   ```

3. **Integration test with Claude:**
   - Ask Claude about disk procedures
   - Verify it uses disk_knowledge tools
   - Check response quality
   - Ensure no hallucinations

---

## 📞 Support & Maintenance

### Known Limitations

1. **Static Knowledge:** Does not update automatically with new cleanups
   - **Mitigation:** Manual update process documented
   
2. **Natural Language Queries:** May not understand all question formats
   - **Mitigation:** Example queries documented

3. **Historical Data:** Limited to what's in INSTRUCTIONS.md
   - **Mitigation:** Clear process for adding new sessions

### Update Process

To update knowledge base:

1. Edit `INSTRUCTIONS.md`
2. Add new procedures with all required fields
3. Update baseline if changed
4. Add historical session if major cleanup occurred
5. Increment version number
6. Restart hub to reload

### Troubleshooting

**Problem:** Tool returns "baseline_data_missing"
- **Solution:** Verify INSTRUCTIONS.md exists and has baseline section

**Problem:** Query returns low confidence
- **Solution:** Check question keywords match instruction sections

**Problem:** Emergency workflow unexpected
- **Solution:** Verify current_percent input is correct

---

## 🔗 Dependencies

### Technical Dependencies

- Python 3.10+
- MCP Python SDK (`mcp` package)
- Pydantic for validation
- No external APIs
- No shell dependencies

### Knowledge Dependencies

- Existing MD files in:
  - `~/.disk_monitor/disk_management_knowledge.md`
  - `~/.disk_monitor/session_summary.md`
  - `~/.disk_monitor/README.md`
  - `/Users/zyahav/agent/mac-disk-monitor/SYSTEM_GUIDE.md`
  - `/Users/zyahav/agent/mac-disk-monitor/scripts/INTERNAL_README.md`

### Process Dependencies

- None (this is the foundation - nothing depends on having this first)

---

## 📋 Board Approval Checklist

### Risk Assessment

- **Technical Risk:** ⬜ LOW - Read-only, well-defined scope
- **Security Risk:** ⬜ ZERO - No system access, no side effects
- **Business Risk:** ⬜ ZERO - Foundation for all other work
- **Resource Risk:** ⬜ LOW - 2-3 day effort, clear requirements

### Expected Benefits

1. **Eliminates LLM hallucinations** on disk procedures
2. **Centralizes operational knowledge** in one place
3. **Enables safe reasoning** before destructive operations
4. **Preserves institutional knowledge** with version control
5. **Foundation for Monitor & Operator** skills

### Cost-Benefit

- **Cost:** 2-3 developer days
- **Benefit:** Prevents catastrophic errors, enables entire platform
- **ROI:** Infinite (prevents disaster scenarios)

---

## ✅ Approval Sign-off

**Technical Lead Approval:**

- [ ] Architecture reviewed and approved
- [ ] Safety guarantees verified
- [ ] Testing requirements adequate
- [ ] Implementation plan reasonable

**Product Owner Approval:**

- [ ] Scope appropriate
- [ ] Success criteria clear
- [ ] Timeline acceptable
- [ ] Dependencies understood

**Security Review:**

- [ ] No security concerns
- [ ] Read-only verified
- [ ] Input validation adequate
- [ ] Error handling safe

**Board Approval:**

- [ ] Strategic value confirmed
- [ ] Resource allocation approved
- [ ] Risk acceptable
- [ ] Ready to implement

---

**Signatures:**

Technical Lead: _________________ Date: _______

Product Owner: _________________ Date: _______

Security: _________________ Date: _______

Board: _________________ Date: _______

---

## 📎 Appendix

### Appendix A: Example Queries

```python
# Example 1: Check baseline
result = get_baseline()
# Returns: {"disk_size_gb": 228, "baseline_percent": 62, ...}

# Example 2: Get all procedures
result = get_procedures()
# Returns: {"procedures": [...], "total_expected_gb": 15.2}

# Example 3: Emergency at 92%
result = get_emergency_workflow(current_percent=92)
# Returns: {"status": "emergency", "recommended_sequence": [...]}

# Example 4: Natural language query
result = query_instructions("How do I clean npm cache?")
# Returns: {"answer": "Run 'npm cache clean --force'...", ...}

# Example 5: Get cleanup history
result = get_history(limit=3)
# Returns: {"sessions": [...], "trends": {...}}
```

### Appendix B: INSTRUCTIONS.md Template

See [Data Model & Structure](#data-model--structure) section above for complete template.

### Appendix C: Migration Path

**From current scattered MDs to consolidated knowledge:**

1. Create backup of all existing MD files
2. Extract content from each file:
   - Baseline data from session_summary.md
   - Procedures from disk_management_knowledge.md
   - Safety protocols from SYSTEM_GUIDE.md
3. Organize into INSTRUCTIONS.md template
4. Validate no information loss
5. Keep originals as backup for 30 days

---

**END OF HANDOFF A**

*This document serves as the complete specification for implementing the Disk Knowledge Service. All implementation decisions should reference this document. Any changes to scope, tools, or behavior require board approval and document update.*
