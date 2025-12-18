
import path from 'path';
import os from 'os';

export const USER_HOME = os.homedir();
export const TUNNEL_MANAGEMENT_DIR = process.env.TUNNEL_MANAGEMENT_DIR || path.join(USER_HOME, 'tunnel-management');

export const CONFIG_PATH = process.env.TUNNEL_CONFIG_PATH || path.join(TUNNEL_MANAGEMENT_DIR, 'configs', 'config.yml');
export const LEDGER_PATH = process.env.TUNNEL_LEDGER_PATH || path.join(TUNNEL_MANAGEMENT_DIR, 'run-state.json');
export const LOCK_PATH = process.env.TUNNEL_LOCK_PATH || path.join(TUNNEL_MANAGEMENT_DIR, '.lock');

// Lock configuration
export const LOCK_STALE_MS = 10000; // 10 seconds
export const LOCK_RETRY_DELAY_MS = 500;
export const LOCK_MAX_RETRIES = 10;
