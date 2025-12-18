
import { createTunnelTool } from './build/tools/create-tunnel.js';

console.log("Starting manual tunnel creation for 'ark-on'...");

try {
    const result = await createTunnelTool({ 
        subdomain: "ark-on", 
        port: 3737, 
        tunnel_class: "ephemeral" 
    });
    console.log("Success:", JSON.stringify(result, null, 2));
} catch (error) {
    console.error("Error:", error);
}
