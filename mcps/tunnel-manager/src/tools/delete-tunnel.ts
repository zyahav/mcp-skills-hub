
import { updateManagedBlock as updateBlockInConfig, readConfigRaw, extractManagedBlock } from '../config-parser.js';
import { acquireLock, releaseLock, withLock } from '../lock.js';
import { updateTunnelRecord, findTunnelRecord } from '../ledger.js';
import { getExecutionContext, isProductionTunnel, verifyOwnership, classifyTunnel } from '../ownership.js';
import { runCommand } from '../tool-runner.js';
import { TunnelClass, TunnelRecord } from '../types.js';

interface DeleteTunnelArgs {
    subdomain: string;
    force?: boolean;
}

export async function deleteTunnelTool(args: DeleteTunnelArgs) {
    const context = getExecutionContext();
    const { subdomain, force = false } = args;
    const fullDomain = `${subdomain}.zurielyahav.com`;

    // Check classification
    // We need config path, but classifyTunnel handles reading it.
    const classification = await classifyTunnel(fullDomain);
    
    if (classification === TunnelClass.A_PRODUCTION) {
        throw new Error('ERR_TUNNEL_002: Cannot delete production tunnel via MCP');
    }

    if (classification === TunnelClass.NOT_FOUND) {
        // Idempotency: "Delete: missing = NO-OP"
        // But we should verify if it's in ledger?
        // If not in config AND not in ledger, it's gone.
        // If in ledger but not config, we should mark ledger deleted.
        const record = await findTunnelRecord(fullDomain);
        if (record && record.status === 'active') {
             // Inconsistent state. Update ledger to deleted.
             await updateTunnelRecord(fullDomain, { ...record, status: 'deleted', deleted_at: new Date().toISOString() });
             return { status: 'deleted', message: 'Tunnel was missing from config, marked deleted in ledger.' };
        }
        return { status: 'no-op', message: 'Tunnel not found (already deleted)' };
    }

    // Verify Ownership
    // Only enforced for managed/ephemeral tunnels usually, or strict for all.
    // Spec: "Verify ownership (for Class C)... Class B requires user approval".
    if (classification === TunnelClass.C_EPHEMERAL) {
        const isOwned = await verifyOwnership(fullDomain, context);
        if (!isOwned && !force) {
            throw new Error(`ERR_TUNNEL_001: Ownership verification failed for ${fullDomain}. Use force=true to override.`);
        }
    } else if (classification === TunnelClass.B_DEV_INFRA && !force) {
        // "Class B requires user approval"
        // If force is false, we assume no approval given.
        throw new Error(`Deletion of persistent dev tunnel ${fullDomain} requires force=true (user approval).`);
    }

    // Perform Deletion
    await withLock(async () => {
        // 1. Update Config (if needed)
        if (classification === TunnelClass.C_EPHEMERAL) {
            const config = await readConfigRaw();
            const { managedContent } = extractManagedBlock(config);
            
            // Remove lines containing the hostname
            const lines = managedContent.split('\n');
            const newLines = lines.filter(line => !line.includes(`hostname: ${fullDomain}`) && !line.includes(`hostname: "${fullDomain}"`));
            
            // We lose the 'service' line if it's separate?
            // YAML structure:
            // - hostname: foo
            //   service: bar
            // If we only remove the hostname line, we leave a dangling service line?
            // OR if it's on same line (not standard yaml usually).
            // Usually:
            // - hostname: ...
            //   service: ...
            // We need to parse correctly.
            // My `createTunnel` appended: `  - hostname: ...\n    service: ...`
            // So they are adjacent.
            
            // Parsing Logic:
            // We need to remove the hostname line AND the following service line(s) associated with it.
            // THIS is why a YAML parser is better.
            // But preserving comments/byte-for-byte outside is hard with parser.
            // Inside the block we can re-generate?
            // "MCP may ONLY edit within ZUROT-managed block"
            // So we can rewrite the whole block using parsed data?
            // Yes! `managedContent` is ours to define.
            // Let's use `yaml` lib to parse `managedContent`, filter, then `yaml.stringify`?
            // But `yaml.stringify` might change formatting.
            // If "byte-preservation" is strictly for OUTSIDE block, we are fine reformatting INSIDE block.
            // The Spec says "preserving all content OUTSIDE". 
            // So rewriting inside is fine.
            
            const yaml = await import('yaml');
            // managedContent might be a list of objects or just specific lines.
            // Depending on how `extractManagedBlock` slices it, it might include comments.
            // If we parse the string, we might lose comments inside the block.
            // BUT, usually ephemeral tunnels don't have important comments.
            // Let's try parsing.
            try {
                let data = yaml.parse(managedContent);
                if (!Array.isArray(data)) {
                    // Try to fix common issues or maybe it's empty?
                    if (!data) data = [];
                    else if (typeof data === 'object') {
                         // Maybe it didnt parse as list?
                    }
                }
                
                if (Array.isArray(data)) {
                    // Filter
                    const newData = data.filter((t: any) => t.hostname !== fullDomain);
                    const newString = yaml.stringify(newData);
                    await updateBlockInConfig('\n' + newString);
                } else {
                    // Fallback to line based if parse fails or structure unknown
                    throw new Error("Managed block is not a list");
                }
            } catch (e) {
                // Fallback: Line filtering (removing 2 lines)
                // Assuming standard format created by us.
                const kept: string[] = [];
                let skipNext = false;
                for (let i = 0; i < lines.length; i++) {
                    if (lines[i].includes(`hostname: ${fullDomain}`)) {
                         skipNext = true; // Remove this line
                         // Check if next line is 'service'
                         if (i+1 < lines.length && lines[i+1].trim().startsWith('service:')) {
                             i++; // Skip next too
                         }
                    } else {
                        kept.push(lines[i]);
                    }
                }
                await updateBlockInConfig(kept.join('\n'));
            }

        } else if (classification === TunnelClass.B_DEV_INFRA) {
            // Cannot delete from persistent block safely with `updateManagedBlock`.
            // We should error or warn. 
            // "Class B requires user approval" - handled above.
            // But we can't implement the write easily.
            // We'll throw NOT_IMPLEMENTED for modifying persistent config.
            throw new Error("Automated deletion for persistent tunnels is not supported (cannot edit config outside managed block). Please delete manually.");
        }

        // 2. Update Ledger
        const record = await findTunnelRecord(fullDomain);
        if (record) {
            await updateTunnelRecord(fullDomain, { ...record, status: 'deleted', deleted_at: new Date().toISOString() });
        }
    });

    return {
        status: 'deleted',
        message: 'Tunnel deleted from config and ledger. Restart cloudflared to apply changes.'
    };
}
