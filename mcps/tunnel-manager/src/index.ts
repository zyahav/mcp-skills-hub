#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import { createTunnelTool } from './tools/create-tunnel.js';
import { deleteTunnelTool } from './tools/delete-tunnel.js';
import { listTunnelsTool } from './tools/list-tunnels.js';

const server = new Server(
  {
    name: "tunnel-manager",
    version: "0.1.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "create_tunnel",
        description: "Create a new Cloudflare tunnel for *.zurielyahav.com. This tool adds an ingress rule to the Cloudflare config, routes DNS, and tracks ownership in a ledger. Use 'ephemeral' class for temporary tunnels (default).",
        inputSchema: {
          type: "object",
          properties: {
            subdomain: { 
                type: "string", 
                description: "Subdomain to use (e.g., 'foo' for 'foo.zurielyahav.com'). do NOT include the domain." 
            },
            port: { 
                type: "number", 
                description: "Local port to point the tunnel to (e.g., 3000)." 
            },
            tunnel_class: { 
                type: "string", 
                enum: ["ephemeral", "persistent"], 
                default: "ephemeral",
                description: "Tunnel lifecycle class. 'ephemeral' for temporary use (managed block), 'persistent' requires manual approval (not supported fully yet)."
            }
          },
          required: ["subdomain", "port"],
        },
      },
      {
        name: "delete_tunnel",
        description: "Delete a tunnel. Removes it from the managed config block and marks it deleted in the ledger.",
        inputSchema: {
          type: "object",
          properties: {
            subdomain: { type: "string", description: "Subdomain to delete (e.g. 'foo')." },
            force: { type: "boolean", description: "Force delete even if ownership verification fails (requires sufficient permissions, usually manual override)." }
          },
          required: ["subdomain"]
        }
      },
      {
        name: "list_tunnels",
        description: "List active tunnels. Can filter by ownership or class. Optionally validates DNS resolution.",
        inputSchema: {
          type: "object",
          properties: {
            filter: { 
                type: "string", 
                enum: ["all", "owned", "ephemeral", "persistent"], 
                default: "all",
                description: "Filter results." 
            },
            verify_dns: { 
                type: "boolean", 
                default: false,
                description: "Perform DNS execution to verify tunnel is publicly reachable (slower)." 
            }
          }
        }
      }
    ],
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  try {
    if (request.params.name === "create_tunnel") {
        const args = request.params.arguments as any;
        // Simple manual validation or rely on Zod if we used it for parsing
        if (!args.subdomain || !args.port) {
            throw new Error("Missing required arguments: subdomain, port");
        }
        
        const result = await createTunnelTool({
            subdomain: String(args.subdomain),
            port: Number(args.port),
            tunnel_class: args.tunnel_class as any
        });
        
        return {
            content: [{ type: "text", text: JSON.stringify(result, null, 2) }]
        };
    }

    if (request.params.name === "delete_tunnel") {
        const args = request.params.arguments as any;
        if (!args.subdomain) throw new Error("Missing required argument: subdomain");
        
        const result = await deleteTunnelTool({
            subdomain: String(args.subdomain),
            force: Boolean(args.force)
        });
        return {
            content: [{ type: "text", text: JSON.stringify(result, null, 2) }]
        };
    }

    if (request.params.name === "list_tunnels") {
        const args = request.params.arguments as any;
        const result = await listTunnelsTool({
            filter: args.filter,
            verify_dns: Boolean(args.verify_dns)
        });
        return {
            content: [{ type: "text", text: JSON.stringify(result, null, 2) }]
        };
    }
    
    throw new Error("Tool not found");
  } catch (error: any) {
    return {
        content: [{ type: "text", text: `Error: ${error.message}` }],
        isError: true
    };
  }
});

const transport = new StdioServerTransport();
await server.connect(transport);
