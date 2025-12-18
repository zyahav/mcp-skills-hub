
export interface TunnelRecord {
  subdomain: string; // Full hostname (e.g. foo.zurielyahav.com)
  port: number;
  class: 'ephemeral' | 'persistent';
  created_by: string;
  feature_branch: string;
  run_id: string;
  created_at: string;
  status: 'active' | 'deleted';
  deleted_at?: string;
}

export interface Ledger {
  tunnels: Record<string, TunnelRecord>;
  metadata: {
    created_at: string;
    schema_version: string;
    last_updated: string;
  };
}

export interface ExecutionContext {
  AGENT_ID: string;
  FEATURE_BRANCH: string;
  RUN_ID?: string; // Optional, specific run identifier
}

export enum TunnelClass {
  A_PRODUCTION = 'production',
  B_DEV_INFRA = 'dev-infra',
  C_EPHEMERAL = 'ephemeral',
  NOT_FOUND = 'not-found'
}

export const PRODUCTION_TUNNELS = [
  // List of protected production subdomains if known, or regex pattern?
  // Spec doesn't list them. But `isProductionTunnel` relies on it.
  // I'll assume standard ones or empty for now.
  // Wait, I should implement `isProductionTunnel` in ownership.ts
];
