
import { updateManagedBlock, updateManagedBlock as updateBlockInConfig, readConfigRaw } from '../config-parser.js';
import { acquireLock, releaseLock, withLock } from '../lock.js';
import { updateTunnelRecord, findTunnelRecord } from '../ledger.js';
import { getExecutionContext, isProductionTunnel } from '../ownership.js';
import { runCommand } from '../tool-runner.js';
import { TunnelClass, TunnelRecord } from '../types.js';
import { verifyConfigIntegrity, verifyDNS, verifyHTTP } from '../verification.js';
import fs from 'fs';
import path from 'path';

interface CreateTunnelArgs {
    subdomain: string;
    port: number;
    tunnel_class?: 'ephemeral' | 'persistent';
}

export async function createTunnelTool(args: CreateTunnelArgs) {
    const context = getExecutionContext();
    const { subdomain, port, tunnel_class = 'ephemeral' } = args;

    // Validation
    if (subdomain.endsWith('.zurielyahav.com')) {
        throw new Error("Only provide subdomain, not full domain (e.g., 'foo', not 'foo.zurielyahav.com')");
    }

    const fullDomain = `${subdomain}.zurielyahav.com`;
    const tunnelUrl = `https://${fullDomain}`;

    // === Idempotency Check (The "Self-Healing" V2 Logic) ===
    // Check 1: Is it in the ledger?
    const existingLedger = await findTunnelRecord(fullDomain);
    
    // Check 2: Does DNS resolve? (Zombie Check)
    const dnsStatus = await verifyDNS(fullDomain);
    
    // Check 3: Is it reachable?
    // const httpStatus = await verifyHTTP(tunnelUrl);

    if (existingLedger) {
        if (existingLedger.port === port) {
             // It exists in ledger. 
             // If DNS is missing, should we heal it?
             if (!dnsStatus.success) {
                  // HEALING: "Tunnel exists locally but not publicly."
                  console.error(`Status: Tunnel ${fullDomain} found in ledger but missing DNS. Healing...`);
                  await runCommand(`cloudflared tunnel route dns mobile-logs-tunnel ${fullDomain}`);
                  return { status: 'healed', message: 'Tunnel existed but DNS was missing. DNS route recreated.', url: tunnelUrl };
             }
             return { status: 'no-op', message: 'Tunnel already exists with same config', url: tunnelUrl };
        } else {
             throw new Error(`Tunnel conflict: ${fullDomain} already exists on port ${existingLedger.port}`);
        }
    }

    if (tunnel_class === 'persistent') {
        if (isProductionTunnel(fullDomain)) {
            throw new Error('ERR_TUNNEL_002: Cannot create production tunnel via MCP');
        }
        throw new Error("Creation of persistent tunnels is not yet supported by automation. Please add manually to config.yml outside the managed block.");
    }

    // === Phase 1: Config Update with Rollback Protection ===
    await withLock(async () => {
        // 1. Backup Current Config
        // We read raw content to memory
        const currentConfig = await readConfigRaw();
        const configPath = process.env.TUNNEL_CONFIG_PATH; // Should be set by wrapper
        
        // 2. Prepare Update
        const { extractManagedBlock } = await import('../config-parser.js');
        const { managedContent } = extractManagedBlock(currentConfig);
        
        // Helper to clean '[]' artifact but preserve structure
        let newBlock = managedContent;
        if (newBlock.trim() === '[]') {
            newBlock = '';
        }

        // If blockText is empty, we must start with a newline to separate from START marker.
        if (!newBlock) {
            newBlock = '\n';
        } 
        // If it's not empty but doesn't start with newline, prepend one (rare/smashed case).
        else if (!newBlock.startsWith('\n')) {
            newBlock = '\n' + newBlock;
        }

        // Ensure it ends with newline before appending next item
        if (!newBlock.endsWith('\n')) {
            newBlock += '\n';
        }

        const newEntry = `  - hostname: ${fullDomain}\n    service: http://localhost:${port}\n    originRequest:\n      httpHostHeader: "localhost"\n`;
        newBlock += newEntry;
        
        // 3. Apply Update
        try {
            await updateBlockInConfig(newBlock);
            
            // 4. Verify Integrity (The "Syntax" Check)
            const integrity = await verifyConfigIntegrity();
            if (!integrity.success) {
                // FAIL! Rollback!
                throw new Error(`Config integrity check failed: ${integrity.error}`);
            }
        } catch (e: any) {
            console.error('Config update failed. Rolling back...');
            if (configPath) {
                fs.writeFileSync(configPath, currentConfig); // Restore original bytes
            }
            throw new Error(`ERR_CONFIG_INVALID: Failed to update config safely. Rolled back. Details: ${e.message}`);
        }
        
        // === Phase 2: DNS Routing ===
        try {
            await runCommand(`cloudflared tunnel route dns mobile-logs-tunnel ${fullDomain}`);
            
            // Verify DNS (Wait a moment?)
            // DNS propagation takes time, but cloudflare is fast.
            // We'll trust the command success for now, or do a loose check.
        } catch (e: any) {
            if (!e.message.includes('already exists')) {
                 // If DNS fails, we have a Zombie Tunnel (Local config yes, DNS no).
                 // We should probably rollback config too? 
                 // Or leave it and let next idempotent run Heal it?
                 // V2 Philosophy: Let "Self-Healing" handle it next time.
                 // Returing user error but leaving partial state IS the zombie cause.
                 // But cleaning up config is complex.
                 // We'll throw detailed error advising retry.
                 throw new Error(`ERR_DNS_FAILED: Tunnel configured locally but DNS failed. Retry to heal. Details: ${e.message}`);
            }
        }

        // === Phase 3: Ledger Record ===
        const record: TunnelRecord = {
            subdomain: fullDomain,
            port,
            class: TunnelClass.C_EPHEMERAL,
            created_by: context.AGENT_ID,
            feature_branch: context.FEATURE_BRANCH,
            run_id: context.RUN_ID || 'unknown',
            created_at: new Date().toISOString(),
            status: 'active'
        };
        await updateTunnelRecord(fullDomain, record);
    });
    
    // === Final Reachability Check ===
    // We do this OUTSIDE the lock to be fast and non-blocking
    // Wait 1s for propagation
    await new Promise(r => setTimeout(r, 1000));
    const reachability = await verifyHTTP(tunnelUrl);
    let message = 'Tunnel created successfully.';
    if (!reachability.success) {
        message += ` WARNING: Reachability check failed (${reachability.error}). Ensure local server is running on port ${port}.`;
    }

    return {
        status: 'created',
        message,
        url: tunnelUrl
    };
}
