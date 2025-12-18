
import fs from 'fs';
import { LEDGER_PATH } from './paths.js';
import { Ledger, TunnelRecord } from './types.js';

export async function readLedger(): Promise<Ledger> {
  try {
    const content = await fs.promises.readFile(LEDGER_PATH, 'utf-8');
    return JSON.parse(content) as Ledger;
  } catch (e: any) {
    if (e.code === 'ENOENT') {
      return {
          metadata: { 
              created_at: new Date().toISOString(), 
              schema_version: '1.0', 
              last_updated: new Date().toISOString() 
          },
          tunnels: {}
      };
    }
    throw e;
  }
}

export async function writeLedger(ledger: Ledger): Promise<void> {
    ledger.metadata.last_updated = new Date().toISOString();
    await fs.promises.writeFile(LEDGER_PATH, JSON.stringify(ledger, null, 2), 'utf-8');
}

export async function findTunnelRecord(hostname: string): Promise<TunnelRecord | undefined> {
    const ledger = await readLedger();
    return ledger.tunnels[hostname];
}

export async function updateTunnelRecord(hostname: string, record: TunnelRecord): Promise<void> {
    const ledger = await readLedger();
    ledger.tunnels[hostname] = record;
    await writeLedger(ledger);
}
