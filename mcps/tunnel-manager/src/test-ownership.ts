
import { classifyTunnel, verifyOwnership, getExecutionContext } from './ownership.js';
import { TunnelClass, Ledger } from './types.js';
import { CONFIG_PATH, LEDGER_PATH } from './paths.js';
import fs from 'fs';

// Helper to write mock files
function setupMocks() {
    const configContent = `
tunnel: 1234
ingress:
  - hostname: production.zurielyahav.com
    service: http://localhost:8000
  - hostname: dev-infra.zurielyahav.com
    service: http://localhost:8001
# ZUROT-MANAGED-START
  - hostname: ephemeral-123.zurielyahav.com
    service: http://localhost:9000
# ZUROT-MANAGED-END
  - service: http_status:404
`;
    fs.writeFileSync(CONFIG_PATH, configContent);

    const ledgerContent: Ledger = {
        metadata: {
            created_at: new Date().toISOString(),
            schema_version: '1.0',
            last_updated: new Date().toISOString()
        },
        tunnels: {
            'ephemeral-123.zurielyahav.com': {
                subdomain: 'ephemeral-123.zurielyahav.com',
                port: 9000,
                class: 'ephemeral',
                created_by: 'agent',
                feature_branch: 'feature/tunnel-manager',
                run_id: 'run-123',
                created_at: new Date().toISOString(),
                status: 'active'
            },
            'other-branch.zurielyahav.com': {
                subdomain: 'other-branch.zurielyahav.com',
                port: 9001,
                class: 'ephemeral',
                created_by: 'agent',
                feature_branch: 'feature/other',
                run_id: 'run-456',
                created_at: new Date().toISOString(),
                status: 'active'
            }
        }
    };
    fs.writeFileSync(LEDGER_PATH, JSON.stringify(ledgerContent, null, 2));
}

function cleanupMocks() {
    try { fs.unlinkSync(CONFIG_PATH); } catch (e) {}
    try { fs.unlinkSync(LEDGER_PATH); } catch (e) {}
}

async function testOwnership() {
    console.log('--- Starting Ownership Verification Test ---');
    console.log(`Config: ${CONFIG_PATH}`);
    console.log(`Ledger: ${LEDGER_PATH}`);

    setupMocks();

    try {
        // 1. Test Classification
        console.log('\n1. Testing Classification...');
        const c1 = await classifyTunnel('ephemeral-123.zurielyahav.com');
        console.log('Classified ephemeral:', c1);
        if (c1 !== TunnelClass.C_EPHEMERAL) throw new Error('Failed to classify ephemeral');

        const c2 = await classifyTunnel('production.zurielyahav.com');
        console.log('Classified production:', c2);
        if (c2 !== TunnelClass.A_PRODUCTION) throw new Error('Failed to classify production');

        const c3 = await classifyTunnel('dev-infra.zurielyahav.com');
        console.log('Classified dev-infra:', c3);
        if (c3 !== TunnelClass.B_DEV_INFRA) throw new Error('Failed to classify dev-infra');

        const c4 = await classifyTunnel('missing.zurielyahav.com');
        console.log('Classified missing:', c4);
        if (c4 !== TunnelClass.NOT_FOUND) throw new Error('Failed to classify missing');

        console.log('✅ Classification correct.');

        // 2. Test verifiedOwnership
        console.log('\n2. Testing verifyOwnership...');
        
        // Mock Context: feature/tunnel-manager
        const contextMyBranch = {
            AGENT_ID: 'agent',
            FEATURE_BRANCH: 'feature/tunnel-manager',
            RUN_ID: undefined
        };

        const ownedByBranch = await verifyOwnership('ephemeral-123.zurielyahav.com', contextMyBranch);
        console.log('Verify owned by branch:', ownedByBranch);
        if (!ownedByBranch) throw new Error('Should be owned by branch');

        const notOwned = await verifyOwnership('other-branch.zurielyahav.com', contextMyBranch);
        console.log('Verify not owned:', notOwned);
        if (notOwned) throw new Error('Should NOT be owned by branch');

        // Test RUN_ID ownership
        const contextRunId = {
            AGENT_ID: 'agent',
            FEATURE_BRANCH: 'feature/some-other-branch', // Branch mismatch
            RUN_ID: 'run-custom-id'
        };
        // We pretend the tunnel hostname includes run-custom-id
        const runIdTunnel = 'test-run-custom-id.zurielyahav.com';
        // Note: verifyOwnership Logic 2 checks if hostname includes RUN_ID
        const ownedByRunId = await verifyOwnership(runIdTunnel, contextRunId);
        console.log('Verify owned by RUN_ID:', ownedByRunId);
        if (!ownedByRunId) throw new Error('Should be owned by RUN_ID match');

        console.log('✅ Ownership verification correct.');

    } finally {
        cleanupMocks();
    }
    
    console.log('--- Ownership Tests Passed ---');
}

testOwnership().catch(e => {
    console.error(e);
    process.exit(1);
});
