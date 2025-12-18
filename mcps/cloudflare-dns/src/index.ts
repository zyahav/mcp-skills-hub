import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { CloudflareClient } from "./cloudflare.js";
import { 
  validateSubdomain, 
  validateRecordType, 
  enforceProxied, 
  checkMultiMatch,
  McpError 
} from "./safety.js";

const CLOUDFLARE_API_TOKEN = process.env.CLOUDFLARE_API_TOKEN;
const CLOUDFLARE_ZONE_ID = process.env.CLOUDFLARE_ZONE_ID;

if (!CLOUDFLARE_API_TOKEN || !CLOUDFLARE_ZONE_ID) {
  console.error("Error: CLOUDFLARE_API_TOKEN and CLOUDFLARE_ZONE_ID environment variables are required.");
  process.exit(1);
}

const client = new CloudflareClient(CLOUDFLARE_API_TOKEN, CLOUDFLARE_ZONE_ID);
const server = new McpServer({
  name: "cloudflare-dns",
  version: "1.0.0",
});

server.tool(
  "upsert_dns_record",
  "Create or update a DNS record. Idempotent: updates if exists, creates if missing.",
  {
    subdomain: z.string().describe("The subdomain to configure (e.g., 'test', 'app'). Root (@) and www are blocked."),
    type: z.enum(["A", "CNAME", "TXT"]).describe("DNS record type (A, CNAME, TXT only)."),
    content: z.string().describe("Target IP, alias, or text content."),
    proxied: z.boolean().describe("Whether to proxy traffic through Cloudflare (ignored/false for TXT)."),
  },
  async ({ subdomain, type, content, proxied }) => {
    try {
      // 1. Safety Validations
      validateSubdomain(subdomain);
      validateRecordType(type);
      const startProxied = enforceProxied(type, proxied);

      // 2. Idempotency Check (Get existing)
      const existingRecords = await client.listRecords(subdomain, type);
      
      // 3. Logic based on count
      if (existingRecords.length === 0) {
        // Create
        const created = await client.createRecord({
          type,
          name: subdomain,
          content,
          proxied: startProxied,
          ttl: 1 // Automatic
        });
        return {
          content: [{ type: "text", text: `Successfully created ${type} record for ${subdomain} (ID: ${created.id})` }]
        };

      } else if (existingRecords.length === 1) {
        // Update
        const record = existingRecords[0];
        // Check if update is needed? (Optional optimization, but we'll always update for simplicity/ensure state)
        const updated = await client.updateRecord(record.id, {
          type,
          name: subdomain,
          content,
          proxied: startProxied,
          ttl: 1
        });
         return {
          content: [{ type: "text", text: `Successfully updated ${type} record for ${subdomain} (ID: ${updated.id})` }]
        };

      } else {
        // Ambiguous > 1
        checkMultiMatch(existingRecords); // Should throw
        // Fallback if checkMultiMatch doesn't throw (it should)
        throw new McpError("ERR_AMBIGUOUS_MULTI_MATCH", `Found ${existingRecords.length} matching records.`);
      }

    } catch (error: any) {
      if (error instanceof McpError) {
         return {
             isError: true,
             content: [{ type: "text", text: `[${error.code}] ${error.message}` }]
         };
      }
      return {
        isError: true,
        content: [{ type: "text", text: `Error: ${error.message}` }]
      };
    }
  }
);

server.tool(
  "delete_dns_record",
  "Delete a DNS record. Fails if multiple records match.",
  {
    subdomain: z.string().describe("The subdomain to delete."),
    type: z.enum(["A", "CNAME", "TXT"]).optional().describe("Optional type filter to ensure we delete the correct record."),
  },
  async ({ subdomain, type }) => {
     try {
       // 1. Safety Validations
       validateSubdomain(subdomain);
       if (type) validateRecordType(type);

       // 2. Get existing
       const existingRecords = await client.listRecords(subdomain, type);

       // 3. Logic
       if (existingRecords.length === 1) {
         const record = existingRecords[0];
         await client.deleteRecord(record.id);
         return {
           content: [{ type: "text", text: `Successfully deleted record for ${subdomain} (ID: ${record.id})` }]
         };
       } else if (existingRecords.length === 0) {
          return {
            isError: true,
             content: [{ type: "text", text: `Error: No matching records found for ${subdomain}` }]
          };
       } else {
          // > 1
          checkMultiMatch(existingRecords); // Throws
          throw new McpError("ERR_AMBIGUOUS_MULTI_MATCH", `Found ${existingRecords.length} matching records.`);
       }

     } catch (error: any) {
       if (error instanceof McpError) {
         return {
             isError: true,
             content: [{ type: "text", text: `[${error.code}] ${error.message}` }]
         };
      }
      return {
        isError: true,
        content: [{ type: "text", text: `Error: ${error.message}` }]
      };
    }
  }
);

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Cloudflare DNS MCP Server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error in main:", error);
  process.exit(1);
});
