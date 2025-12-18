# MCP Scaffolder

A standardized tool for generating new MCP skills in the monorepo. This tool ensures all new skills adhere to the "Golden Set" of files and directory structure.

## Tools

### `scaffold_skill`

Creates a new skill with the following structure:
- `handoffs/<skill-name>/`: Project management and handoff files
- `mcps/<skill-name>/`: Source code and MCP configuration

**Arguments:**
- `skill_name`: Name of the skill (lowercase, hyphens only, e.g. `weather-api`)
- `description`: Short description of the skill
- `archon_project_id`: (Optional) UUID of the Archon Project tracking this skill

## Usage

This tool is intended to be used by Agents (e.g. via Archon) to initialize new work.

```bash
# Manual execution via wrapper
./mcps/mcp-scaffolder/wrapper.sh
```
