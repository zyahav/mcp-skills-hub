
import { readConfigRaw, extractManagedBlock } from '../config-parser.js';
import { readLedger, findTunnelRecord } from '../ledger.js';
import { getExecutionContext, verifyOwnership, classifyTunnel } from '../ownership.js';
import { runCommand } from '../tool-runner.js';
import { TunnelClass } from '../types.js';
import { verifyDNS } from '../verification.js';
import yaml from 'yaml';

interface ListTunnelsArgs {
    filter?: 'all' | 'owned' | 'ephemeral' | 'persistent';
    verify_dns?: boolean;
}

interface TunnelInfo {
    hostname: string;
    port?: number;
    class: TunnelClass;
    owned_by_current_branch: boolean;
    created_by?: string;
    created_at?: string;
    status: string;
    dns_resolves?: boolean;
    dns_ips?: string[];
}

export async function listTunnelsTool(args: ListTunnelsArgs) {
    const context = getExecutionContext();
    const { filter = 'all', verify_dns = false } = args;
    
    // Parse Full Config
    const rawConfig = await readConfigRaw();
    let configTunnels: { hostname: string, port?: number }[] = [];
    
    try {
        const config = yaml.parse(rawConfig);
        if (config && Array.isArray(config.ingress)) {
            // Extract hostnames and ports
            configTunnels = config.ingress
                .filter((rule: any) => rule.hostname)
                .map((rule: any) => {
                    let port = undefined;
                    if (rule.service && rule.service.startsWith('http://localhost:')) {
                        port = parseInt(rule.service.split(':').pop());
                    }
                    return {
                        hostname: rule.hostname,
                        port
                    };
                });
        }
    } catch (e) {
        // Fallback or error?
        // If we can't parse config, we can't list effectively.
        // But maybe we can list from ledger? 
        // Spec implies merging sources.
        // For now, assume config is parseable or just empty if failed.
    }
    
    // Get Ledger for metadata
    const ledger = await readLedger();
    
    // Process Tunnels
    const results: TunnelInfo[] = [];
    
    for (const t of configTunnels) {
         const classification = await classifyTunnel(t.hostname);
         const ledgerData = ledger.tunnels[t.hostname];
         
         // Verify Ownership
         let owned = false;
         if (classification === TunnelClass.C_EPHEMERAL) {
             owned = await verifyOwnership(t.hostname, context);
         } else if (classification === TunnelClass.B_DEV_INFRA) {
             // Maybe consider owned if branch matches?
             if (ledgerData && ledgerData.feature_branch === context.FEATURE_BRANCH) {
                 owned = true;
             }
         }
         
         const info: TunnelInfo = {
             hostname: t.hostname,
             port: t.port,
             class: classification,
             owned_by_current_branch: owned,
             created_by: ledgerData?.created_by,
             created_at: ledgerData?.created_at,
             status: ledgerData?.status || 'unknown'
         };
         
         results.push(info);
    }


    // Verify DNS if requested
    if (verify_dns) {
        // Parallelize? With Promise.all
        await Promise.all(results.map(async (t) => {
             const res = await verifyDNS(t.hostname);
             if (res.success && res.details?.ips) {
                 t.dns_resolves = true;
                 t.dns_ips = res.details.ips;
             } else {
                 t.dns_resolves = false;
                 t.dns_ips = [];
             }
        }));
    }

    // Filter
    let filtered = results;
    if (filter === 'owned') {
        filtered = filtered.filter(t => t.owned_by_current_branch);
    } else if (filter === 'ephemeral') {
        filtered = filtered.filter(t => t.class === TunnelClass.C_EPHEMERAL);
    } else if (filter === 'persistent') {
        filtered = filtered.filter(t => t.class !== TunnelClass.C_EPHEMERAL);
    }

    return {
        count: filtered.length,
        current_branch: context.FEATURE_BRANCH,
        tunnels: filtered
    };
}
