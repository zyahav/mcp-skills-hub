
import { createTunnelTool } from './build/tools/create-tunnel.js';
import { updateTunnelRecord } from './build/ledger.js';

console.log("Force Re-provisioning 'ark-on'...");

async function run() {
    try {
        console.log("1. Clearing ledger for ark-on...");
        await updateTunnelRecord('ark-on.zurielyahav.com', {
            subdomain: 'ark-on.zurielyahav.com',
            port: 0,
            class: 'ephemeral',
            created_by: 'manual',
            feature_branch: 'manual',
            run_id: 'manual',
            created_at: new Date().toISOString(),
            status: 'deleted'
        });
        
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
}

run();
