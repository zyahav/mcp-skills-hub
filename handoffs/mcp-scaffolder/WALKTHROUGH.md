# Walkthrough: MCP Scaffolder

## 🎯 Goal
Implement `mcp-scaffolder`, a tool to standardize the creation of new MCP skills in the monorepo, ensuring consistent structure and proper git history.

## 🛠️ Changes

### 1. Specification
- Created `standard_skill_spec.md` defining the "Golden Set" of files (`feature_list.json`, `progress.txt`, `RESUME.md`, etc.).

### 2. Implementation (`mcps/mcp-scaffolder/`)
- **`server.py`**: Python-based MCP server containing the `scaffold_skill` tool.
    - **Templates**: Embedded templates for all standard files with correctly escaped formatting.
    - **Logic**: 
        - Validates input (skill name format).
        - Creates `handoffs/<skill>` and `mcps/<skill>` directories.
        - Populates files from templates.
        - Adds files to git index and commits them.
- **`wrapper.sh`**: Launch script for the server.
- **`skill.json`**: MCP manifest.

### 3. Verification
- Created a verification script `verify_scaffolder.py`.
- Successfully generated a `test-skill-verification` skill.
- Verified file creation and git commit history.
- Cleaned up test artifacts (reset git history, removed files).
- **Registration**: Added `mcp-scaffolder` to `~/.gemini/settings.json` so it is available for future agents.

## 🚀 Usage

```bash
# Run the tool (via MCP client or wrapper)
./mcps/mcp-scaffolder/wrapper.sh
```

**Tool Arguments:**
- `skill_name`: e.g., `new-skill`
- `description`: "Description of skill"
- `archon_project_id`: "p-123" (Optional)
