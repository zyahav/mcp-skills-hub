
import { acquireLock, releaseLock, isLockStale, withLock } from './lock.js';
import { LOCK_PATH } from './paths.js';
import fs from 'fs';

async function testLock() {
    console.log('--- Starting Lock Mechanism Test ---');
    console.log(`Lock path: ${LOCK_PATH}`);

    // Cleanup any existing lock
    try { fs.unlinkSync(LOCK_PATH); } catch (e) {}

    // 1. Basic Acquisition
    console.log('\n1. Testing Basic Acquisition...');
    await acquireLock();
    console.log('✅ Lock acquired.');
    
    if (!fs.existsSync(LOCK_PATH)) {
        console.error('❌ Lock file missing!');
        process.exit(1);
    }

    // 2. Contention (Self-contention for simulation)
    console.log('\n2. Testing Contention (Should fail if immediate)...');
    try {
        // Try to acquire again immediately with 1 retry to fail fast
        await acquireLock(1);
        console.error('❌ Second lock acquisition should have failed!');
    } catch (e: any) {
        if (e.code === 'ERR_TUNNEL_004') {
            console.log('✅ Correctly failed to acquire held lock.');
        } else {
            console.error('❌ Unexpected error:', e);
        }
    }

    // 3. Release
    console.log('\n3. Testing Release...');
    await releaseLock();
    if (fs.existsSync(LOCK_PATH)) {
        console.error('❌ Lock file should be gone!');
        process.exit(1);
    }
    console.log('✅ Lock released.');

    // 4. Stale Lock Recovery
    console.log('\n4. Testing Stale Lock Recovery...');
    // Create a "stale" lock (older than 10s)
    const oldTime = new Date(Date.now() - 15000);
    fs.writeFileSync(LOCK_PATH, 'STALE_PID');
    fs.utimesSync(LOCK_PATH, oldTime, oldTime);
    
    console.log('Created stale lock file.');

    // Should break the lock and acquire
    await acquireLock();
    console.log('✅ Stale lock broken and acquired.');
    
    await releaseLock();

    // 5. withLock helper
    console.log('\n5. Testing withLock helper...');
    await withLock(async () => {
        console.log('Inside protected block.');
        if (!fs.existsSync(LOCK_PATH)) throw new Error('Lock should exist inside block');
    });
    if (fs.existsSync(LOCK_PATH)) throw new Error('Lock should be gone after block');
    console.log('✅ withLock wrapper working.');

    console.log('\n--- All Lock Tests Passed ---');
}

testLock().catch(e => {
    console.error('Test failed:', e);
    process.exit(1);
});
