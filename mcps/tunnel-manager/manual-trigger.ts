
import { createTunnelTool } from './src/tools/create-tunnel.js';

console.log("Starting manual tunnel creation...");
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
