
import { createTunnelTool } from './build/tools/create-tunnel.js';
import { deleteTunnelTool } from './build/tools/delete-tunnel.js';

console.log("Re-provisioning 'ark-on'...");

try {
    console.log("1. Deleting old tunnel...");
    // Try delete, ignore if missing
    try {
        await deleteTunnelTool({ subdomain: "ark-on", force: true });
        console.log("Deleted.");
    } catch (e) {
        console.log("Delete skipped/failed:", e.message);
    }

    console.log("2. Creating new tunnel...");
    const result = await createTunnelTool({ 
        subdomain: "ark-on", 
        port: 3737, 
        tunnel_class: "ephemeral" 
    });
    console.log("Success:", JSON.stringify(result, null, 2));
} catch (error) {
    console.error("Error:", error);
}
