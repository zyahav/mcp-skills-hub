
import { deleteTunnelTool } from './tools/delete-tunnel.js';
import { CONFIG_PATH, LEDGER_PATH } from './paths.js';
import { readLedger } from './ledger.js';
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
  - hostname: other-tunnel.zurielyahav.com
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
                feature_branch: 'feature/tunnel-manager', // Matches current mock context default
                run_id: 'run-1',
                created_at: new Date().toISOString(),
                status: 'active'
            } as TunnelRecord,
            'other-tunnel.zurielyahav.com': {
                subdomain: 'other-tunnel.zurielyahav.com',
                port: 4000,
                class: 'ephemeral',
                created_by: 'agent',
                feature_branch: 'feature/other', // Different branch
                run_id: 'run-2',
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

async function testDelete() {
    console.log('--- Starting Delete Tunnel Test ---');
    setupMocks();

    try {
        // 1. Delete Owned (Success)
        console.log('\n1. Test Delete Owned (my-tunnel)...');
        // We assume getExecutionContext returns 'feature/tunnel-manager' if we run inside this repo
        // Or we might need to mock getExecutionContext via some way?
        // getExecutionContext calls `git rev-parse`. Assuming we are in the repo.
        // If not, we might fail ownership.
        // Let's assume the test environment is the repo.
        
        await deleteTunnelTool({ subdomain: 'my-tunnel' });
        
        const config1 = fs.readFileSync(CONFIG_PATH, 'utf-8');
        if (config1.includes('my-tunnel.zurielyahav.com')) throw new Error('my-tunnel still in config');
        
        const ledger1 = await readLedger();
        if (ledger1.tunnels['my-tunnel.zurielyahav.com'].status !== 'deleted') throw new Error('my-tunnel not marked deleted');
        
        console.log('✅ Deleted owned tunnel successfully.');

        // 2. Delete Unowned (Fail)
        console.log('\n2. Test Delete Unowned (other-tunnel)...');
        try {
            await deleteTunnelTool({ subdomain: 'other-tunnel' });
            throw new Error('Should have failed ownership check');
        } catch (e: any) {
            if (e.message.includes('Ownership verification failed')) {
                console.log('✅ Correctly blocked unowned deletion.');
            } else {
                throw e;
            }
        }

        // 3. Delete Unowned Force (Success)
        console.log('\n3. Test Delete Force (other-tunnel)...');
        await deleteTunnelTool({ subdomain: 'other-tunnel', force: true });
        
        const config3 = fs.readFileSync(CONFIG_PATH, 'utf-8');
        if (config3.includes('other-tunnel.zurielyahav.com')) throw new Error('other-tunnel still in config');
        console.log('✅ Force delete successful.');

        // 4. Delete Production (Fail)
        console.log('\n4. Test Delete Production (production)...');
        try {
            await deleteTunnelTool({ subdomain: 'production' });
            throw new Error('Should have blocked production deletion');
        } catch (e: any) {
            if (e.message.includes('Cannot delete production')) {
                console.log('✅ Correctly blocked production deletion.');
            } else {
                throw e;
            }
        }

    } finally {
        cleanup();
    }
    console.log('--- Delete Tunnel Test Passed ---');
}

testDelete().catch(e => {
    console.error(e);
    process.exit(1);
});
