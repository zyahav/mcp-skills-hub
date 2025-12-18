#!/usr/bin/env node
/**
 * Bitwarden MCP CLI
 * 
 * Usage:
 *   bitwarden-mcp get-secret <item> <field>
 *   bitwarden-mcp get-notes <item>
 * 
 * This CLI uses the same core as the MCP server.
 * All safety rules (R1-R8) are enforced.
 */

import { BitwardenClient, BitwardenError } from "./bitwarden_client.js";

async function main() {
  const [,, command, ...args] = process.argv;

  if (!command) {
    console.error("Usage:");
    console.error("  bitwarden-mcp get-secret <item> <field>");
    console.error("  bitwarden-mcp get-notes <item>");
    process.exit(1);
  }

  const client = new BitwardenClient();

  try {
    switch (command) {
      case "get-secret": {
        const [item, field] = args;
        if (!item || !field) {
          console.error("Usage: bitwarden-mcp get-secret <item> <field>");
          process.exit(1);
        }
        const secret = await client.getSecret(item, field);
        // Output ONLY the value, nothing else (for shell capture)
        process.stdout.write(secret);
        break;
      }

      case "get-notes": {
        const [item] = args;
        if (!item) {
          console.error("Usage: bitwarden-mcp get-notes <item>");
          process.exit(1);
        }
        const notes = await client.getNotes(item);
        process.stdout.write(notes);
        break;
      }

      default:
        console.error(`Unknown command: ${command}`);
        console.error("Available commands: get-secret, get-notes");
        process.exit(1);
    }
  } catch (error) {
    if (error instanceof BitwardenError) {
      console.error(`Error: ${error.message}`);
      process.exit(1);
    }
    throw error;
  }
}

main();
