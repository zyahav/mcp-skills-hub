
import { listTunnelsTool } from './tools/list-tunnels.js';
import { CONFIG_PATH, LEDGER_PATH } from './paths.js';
import { TunnelRecord } from './types.js';
import fs from 'fs';

function setupMocks() {
    const configContent = `
tunnel: 1234
ingress:
  - hostname: production.zurielyahav.com
    service: http://localhost:8000
# ZUROT-MANAGED-START
  - hostname: my-tunnel.zurielyahav.com
    service: http://localhost:3000
  - hostname: unowned-tunnel.zurielyahav.com
    service: http://localhost:4000
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
        tunnels: {
            'my-tunnel.zurielyahav.com': {
                subdomain: 'my-tunnel.zurielyahav.com',
                port: 3000,
                class: 'ephemeral',
                created_by: 'agent',
                feature_branch: 'feature/tunnel-manager',
                run_id: 'run-1',
                created_at: new Date().toISOString(),
                status: 'active'
            } as TunnelRecord
        }
    };
    fs.writeFileSync(LEDGER_PATH, JSON.stringify(ledgerContent, null, 2));
}

function cleanup() {
    try { fs.unlinkSync(CONFIG_PATH); } catch (e) {}
    try { fs.unlinkSync(LEDGER_PATH); } catch (e) {}
}

async function testList() {
    console.log('--- Starting List Tunnels Test ---');
    setupMocks();

    try {
        // 1. List All
        console.log('\n1. Testing Filter: ALL...');
        const resAll = await listTunnelsTool({ filter: 'all' });
        console.log(`Count: ${resAll.count}`);
        
        // Expected: production, my-tunnel, unowned-tunnel = 3
        if (resAll.count !== 3) throw new Error(`Expected 3 tunnels, got ${resAll.count}`);
        
        const myTunnel = resAll.tunnels.find(t => t.hostname === 'my-tunnel.zurielyahav.com');
        if (!myTunnel || !myTunnel.owned_by_current_branch) throw new Error('my-tunnel ownership check failed');

        const unowned = resAll.tunnels.find(t => t.hostname === 'unowned-tunnel.zurielyahav.com');
        if (!unowned || unowned.owned_by_current_branch) throw new Error('unowned-tunnel ownership check failed');
        
        // 2. List Owned
        console.log('\n2. Testing Filter: OWNED...');
        const resOwned = await listTunnelsTool({ filter: 'owned' });
        console.log(`Count: ${resOwned.count}`);
        if (resOwned.count !== 1) throw new Error(`Expected 1 owned tunnel, got ${resOwned.count}`);
        if (resOwned.tunnels[0].hostname !== 'my-tunnel.zurielyahav.com') throw new Error('Wrong owned tunnel');

        // 3. List Persistent
        console.log('\n3. Testing Filter: PERSISTENT...');
        const resPers = await listTunnelsTool({ filter: 'persistent' });
        console.log(`Count: ${resPers.count}`);
        // production is persistent (Class A).
        // unowned-tunnel in managed block? Yes. So ephemeral.
        // my-tunnel in managed block? Yes. So ephemeral.
        // So expected production only.
        if (resPers.count !== 1) throw new Error(`Expected 1 persistent tunnel, got ${resPers.count}`);
        if (resPers.tunnels[0].hostname !== 'production.zurielyahav.com') throw new Error('Wrong persistent tunnel');

        console.log('✅ List filtering verified.');

    } finally {
        cleanup();
    }
    console.log('--- List Tunnels Test Passed ---');
}

testList().catch(e => {
    console.error(e);
    process.exit(1);
});
