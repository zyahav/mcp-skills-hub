
# MCP Tunnel Manager

A Model Context Protocol (MCP) server for managing Cloudflare Tunnels safely, with ownership tracking and production protection.

## Features

- **Resource Classification**: Distinguishes between Production (Class A), Dev/Infra (Class B), and Ephemeral (Class C) tunnels.
- **Safety**: Prevents accidental deletion of production tunnels or tunnels owned by other feature branches.
- **Concurrency Control**: Updates config files safely using lock files.
- **Ledger Tracking**: Maintains an audit log of tunnel ownership in `run-state.json`.

## Tools

### `create_tunnel`
Creates a new ephemeral tunnel and routes DNS.
- `subdomain`: (Required) Subdomain (e.g., `test-foo`).
- `port`: (Required) Local port (e.g., `3000`).
- `tunnel_class`: (Optional) `ephemeral` (default).

### `delete_tunnel`
Deletes a tunnel if owned by the current branch.
- `subdomain`: (Required) Subdomain to delete.
- `force`: (Optional) Override ownership check.

### `list_tunnels`
Lists active tunnels with classification and ownership status.
- `filter`: `all`, `owned`, `ephemeral`, `persistent`.
- `verify_dns`: `true` to perform live DNS check.

## Configuration

Set the following environment variables if not using default paths:

- `TUNNEL_CONFIG_PATH`: Path to Cloudflare `config.yml`. Default: `~/tunnel-management/configs/config.yml`.
- `TUNNEL_LEDGER_PATH`: Path to `run-state.json`. Default: `~/tunnel-management/run-state.json`.
- `TUNNEL_LOCK_PATH`: Path to lock file. Default: `~/tunnel-management/.lock`.

## Development

Build:
```bash
npm run build
```

Run Tests:
```bash
node build/test-e2e.js
```

## Usage with Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "tunnel-manager": {
      "command": "node",
      "args": ["/Users/zyahav/Documents/dev/mcp-skills-hub-monorepo/mcp-skills-hub-feature-tunnel-manager/mcps/tunnel-manager/build/index.js"],
      "env": {
        "TUNNEL_CONFIG_PATH": "/Users/zyahav/tunnel-management/configs/config.yml",
        "TUNNEL_LEDGER_PATH": "/Users/zyahav/tunnel-management/run-state.json"
      }
    }
  }
}
```
