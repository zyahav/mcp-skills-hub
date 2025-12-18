
import { extractManagedBlock, updateManagedBlock, readConfigRaw } from './config-parser.js';
import fs from 'fs';
import path from 'path';
import { CONFIG_PATH } from './paths.js';

// Mock config path for testing
const TEST_CONFIG_PATH = path.join(process.cwd(), 'test-config.yml');

// We need to mock the CONFIG_PATH. 
// Since CONFIG_PATH is a constant imported from paths.js, we can't easily change it 
// unless we change the file on disk OR use a different way to inject it.
// However, checking paths.ts, it uses process.env.TUNNEL_CONFIG_PATH.
// BUT paths.ts module is already evaluated.
// So we probably need to ensure we set the ENV var BEFORE importing paths.js?
// Too late for this script if imports happen first.
// Just for this test, let's write to the actual CONFIG_PATH location or assume we can override it by creating a dummy paths.js mock? No.
// Let's look at paths.ts again.
// It exports CONFIG_PATH.
// I will just create a "test-paths.ts" or I will manually overwrite the file at CONFIG_PATH if acceptable, OR
// I will just verify the logic by passing strings to `extractManagedBlock` which is pure.
// But `updateManagedBlock` uses `CONFIG_PATH`.
// I should probably modify `config-parser.ts` to accept an optional path, or allow dependency injection.
// For now, I'll modify `config-parser.ts` to export `setConfigPath` or similar? No, standard is env vars.
// I'll make the test script write a `test-config-runner.js` that sets env var THEN imports the main test logic.
// OR simpler: `export TUNNEL_CONFIG_PATH=...` in the command line.

// Let's rely on the Pure Function testing for extraction, 
// and for `updateManagedBlock`, I'll use the CLI env var approach when running the test.

const TEST_CONTENT = `
tunnel: 1234
credentials-file: /etc/cloudflared/cert.json
ingress:
  - hostname: production.zurielyahav.com
    service: http://localhost:8000
# ZUROT-MANAGED-START
  - hostname: test.zurielyahav.com
    service: http://localhost:9000
# ZUROT-MANAGED-END
  - service: http_status:404
`;

async function testParser() {
    console.log('--- Starting Config Parser Test ---');
    
    // 1. Test Extraction (Pure)
    console.log('\n1. Testing Extraction...');
    const result = extractManagedBlock(TEST_CONTENT);
    
    console.log('Before:', result.before.trim());
    console.log('Managed:', result.managedContent.trim());
    console.log('After:', result.after.trim());

    if (!result.managedContent.includes('hostname: test.zurielyahav.com')) {
        throw new Error('Failed to extract managed content properly');
    }
    if (!result.before.includes('tunnel: 1234')) {
         throw new Error('Before content missing');
    }
    console.log('✅ Extraction correct.');

    // 2. Test Update (Integration)
    console.log('\n2. Testing Update...');
    // We expect CONFIG_PATH to be set to our test file
    console.log('Target Config:', CONFIG_PATH);
    
    // Write initial file
    fs.writeFileSync(CONFIG_PATH, TEST_CONTENT);
    
    const NEW_BLOCK = `
  - hostname: updated.zurielyahav.com
    service: http://localhost:9999
`;
    await updateManagedBlock(NEW_BLOCK);
    
    const newContent = fs.readFileSync(CONFIG_PATH, 'utf-8');
    console.log('New File Content:\n', newContent);
    
    if (!newContent.includes('updated.zurielyahav.com')) {
        throw new Error('New content not found');
    }
    if (newContent.includes('test.zurielyahav.com')) {
        throw new Error('Old content should be gone');
    }
    if (!newContent.includes('tunnel: 1234')) {
        throw new Error('Header preserved failed');
    }
    console.log('✅ Update successful.');

    // Cleanup
    fs.unlinkSync(CONFIG_PATH);
    console.log('--- Config Parser Tests Passed ---');
}

testParser().catch(e => {
    console.error(e);
    process.exit(1);
});
