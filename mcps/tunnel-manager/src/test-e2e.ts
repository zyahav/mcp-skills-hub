
import { createTunnelTool } from './tools/create-tunnel.js';
import { listTunnelsTool } from './tools/list-tunnels.js';
import { deleteTunnelTool } from './tools/delete-tunnel.js';
import { CONFIG_PATH, LEDGER_PATH } from './paths.js';
import { readLedger } from './ledger.js';
import fs from 'fs';

function setupMocks() {
    const configContent = `
tunnel: 1234
ingress:
  - service: http_status:404
# ZUROT-MANAGED-START
# ZUROT-MANAGED-END
  - service: http_status:404
`;
    fs.writeFileSync(CONFIG_PATH, configContent);

    const ledgerContent = {
        metadata: {
            created_at: new Date().toISOString(),
            schema_version: '1.0',
            last_updated: new Date().toISOString()
        },
        tunnels: {}
    };
    fs.writeFileSync(LEDGER_PATH, JSON.stringify(ledgerContent, null, 2));
}

function cleanup() {
    try { fs.unlinkSync(CONFIG_PATH); } catch (e) {}
    try { fs.unlinkSync(LEDGER_PATH); } catch (e) {}
}

async function testE2E() {
    console.log('--- Starting E2E Test ---');
    setupMocks();

    try {
        const TUNNEL_NAME = 'e2e-test';
        const FULL_DOMAIN = 'e2e-test.zurielyahav.com';

        // 1. Create
        console.log('\n[1] Create Tunnel...');
        try {
            await createTunnelTool({ subdomain: TUNNEL_NAME, port: 8080 });
        } catch (e: any) {
            console.log('ignored cloudflared error during create');
        }
        
        // Verify Config
        const config1 = fs.readFileSync(CONFIG_PATH, 'utf-8');
        if (!config1.includes(FULL_DOMAIN)) throw new Error('Create failed: Config missing tunnel');
        console.log('✅ Created.');

        // 2. List
        console.log('\n[2] List Tunnels...');
        const listRes = await listTunnelsTool({ filter: 'owned' });
        if (listRes.count !== 1) throw new Error(`List failed: Expected 1 tunnel, got ${listRes.count}`);
        if (listRes.tunnels[0].hostname !== FULL_DOMAIN) throw new Error('List failed: Wrong hostname');
        console.log('✅ Listed.');

        // 3. Delete
        console.log('\n[3] Delete Tunnel...');
        await deleteTunnelTool({ subdomain: TUNNEL_NAME });
        
        // Verify Delete
        const config2 = fs.readFileSync(CONFIG_PATH, 'utf-8');
        if (config2.includes(FULL_DOMAIN)) throw new Error('Delete failed: Config still has tunnel');
        
        const ledger2 = await readLedger();
        if (ledger2.tunnels[FULL_DOMAIN].status !== 'deleted') throw new Error('Delete failed: Ledger status not deleted');
        
        console.log('✅ Deleted.');

    } finally {
        cleanup();
    }
    console.log('--- E2E Test Passed ---');
}

testE2E().catch(e => {
    console.error(e);
    process.exit(1);
});
