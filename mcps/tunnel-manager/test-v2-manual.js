
import { createTunnelTool } from './build/tools/create-tunnel.js';

// Setup Mock Env
process.env.TUNNEL_CONFIG_PATH = '/Users/zyahav/tunnel-management/configs/config.yml';
process.env.TUNNEL_LEDGER_PATH = '/Users/zyahav/tunnel-management/run-state.json';
// These mimic the agent context
process.env.AGENT_ID = 'test-agent';
process.env.FEATURE_BRANCH = 'test-v2';
process.env.RUN_ID = 'test-run-123';

async function runTest() {
    console.log("Starting V2 Manual Verification...");
    try {
        const result = await createTunnelTool({
            subdomain: 'v2-verify-test',
            port: 8080,
            tunnel_class: 'ephemeral'
        });
        console.log("Result:", result);
    } catch (e) {
        console.error("Test Failed:", e);
    }
}

runTest();
