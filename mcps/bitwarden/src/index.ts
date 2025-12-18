#!/usr/bin/env node
/**
 * Bitwarden MCP Server
 * 
 * Exposes secure, read-only access to Bitwarden secrets.
 * All safety rules (R1-R8) enforced via BitwardenClient.
 * 
 * Tools:
 *   - bitwarden_get_secret(item, field) → Custom field value
 *   - bitwarden_get_notes(item)         → Notes (gated by PUBLIC_NOTES)
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { BitwardenClient, BitwardenError } from "./bitwarden_client.js";

const server = new Server(
  {
    name: "bitwarden",
    version: "0.1.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

const client = new BitwardenClient();

// Tool definitions
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "bitwarden_get_secret",
        description: "Retrieve a secret value from a Bitwarden item's custom field. Requires BW_SESSION to be set and vault unlocked.",
        inputSchema: {
          type: "object",
          properties: {
            item: {
              type: "string",
              description: "Exact name of the Bitwarden item"
            },
            field: {
              type: "string", 
              description: "Name of the custom field containing the secret"
            }
          },
          required: ["item", "field"]
        }
      },
      {
        name: "bitwarden_get_notes",
        description: "Retrieve notes from a Bitwarden item. Only works if item has PUBLIC_NOTES=\"true\" custom field.",
        inputSchema: {
          type: "object",
          properties: {
            item: {
              type: "string",
              description: "Exact name of the Bitwarden item"
            }
          },
          required: ["item"]
        }
      }
    ]
  };
});


// Tool handlers
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "bitwarden_get_secret": {
        const item = String(args?.item);
        const field = String(args?.field);
        
        if (!item || !field) {
          return {
            isError: true,
            content: [{ type: "text", text: "Error: Both 'item' and 'field' are required" }]
          };
        }

        const secret = await client.getSecret(item, field);
        
        // R3: Return only the value, no logging
        return {
          content: [{ type: "text", text: secret }]
        };
      }

      case "bitwarden_get_notes": {
        const item = String(args?.item);
        
        if (!item) {
          return {
            isError: true,
            content: [{ type: "text", text: "Error: 'item' is required" }]
          };
        }

        const notes = await client.getNotes(item);
        
        return {
          content: [{ type: "text", text: notes }]
        };
      }

      default:
        return {
          isError: true,
          content: [{ type: "text", text: `Unknown tool: ${name}` }]
        };
    }
  } catch (error) {
    // R3b: Errors are already value-redacted by BitwardenClient
    if (error instanceof BitwardenError) {
      return {
        isError: true,
        content: [{ type: "text", text: error.message }]
      };
    }
    
    // Unexpected error - keep it generic
    return {
      isError: true,
      content: [{ type: "text", text: "An unexpected error occurred" }]
    };
  }
});

// Start server
const transport = new StdioServerTransport();
await server.connect(transport);
