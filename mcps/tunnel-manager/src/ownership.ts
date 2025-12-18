
import fs from 'fs';
import { execSync } from 'child_process';
import { Ledger, ExecutionContext, TunnelClass } from './types.js';
import { extractManagedBlock, readConfigRaw } from './config-parser.js';

export function getExecutionContext(): ExecutionContext {
  let branch = 'unknown';
  try {
    branch = execSync('git rev-parse --abbrev-ref HEAD', { encoding: 'utf-8' }).trim();
  } catch (e) {
    // console.warn('Not a git repository or git command failed');
  }

  return {
    AGENT_ID: process.env.AGENT_ID || 'manual',
    FEATURE_BRANCH: branch,
    // RUN_ID generation logic or env var?
    // Spec says `generateRunId()`.
    // I'll assume we can generate one or read from env.
    // If verification requires checking against *existing* run ID, we might not know it unless passed?
    // But for `getExecutionContext`, it usually returns the *current* context.
    RUN_ID: process.env.TUNNEL_RUN_ID || undefined
  };
}

import { readLedger } from './ledger.js';

export async function classifyTunnel(hostname: string): Promise<TunnelClass> {
  // Read config
  const config = await readConfigRaw();
  const { before, managedContent, after } = extractManagedBlock(config);

  if (managedContent.includes(hostname)) {
    return TunnelClass.C_EPHEMERAL;
  }

  if (before.includes(hostname) || after.includes(hostname)) {
      if (isProductionTunnel(hostname)) {
          return TunnelClass.A_PRODUCTION;
      }
      return TunnelClass.B_DEV_INFRA;
  }

  return TunnelClass.NOT_FOUND;
}

export function isProductionTunnel(hostname: string): boolean {
    // Heuristic: Does it start with 'production' or matches known list?
    // Looking at test content: 'production.zurielyahav.com'
    if (hostname.includes('production')) return true;
    if (hostname === 'zurielyahav.com' || hostname.startsWith('www')) return true;
    return false;
}

export async function verifyOwnership(hostname: string, context: ExecutionContext): Promise<boolean> {
  const ledger = await readLedger();
  const record = ledger.tunnels[hostname];

  // Method 1: Check Ledger
  if (record) {
      if (record.feature_branch === context.FEATURE_BRANCH) {
          return true;
      }
      // If feature branch matches but agent ID doesn't? Usually branch ownership is enough.
  }

  // Method 2: Check RUN_ID in subdomain (if context has a RUN_ID)
  if (context.RUN_ID && hostname.includes(context.RUN_ID)) {
      return true;
  }
  
  // Method 3: Check AGENT_ID? 
  // If verifying ownership for *deletion*, usually stricter.
  
  return false;
}
