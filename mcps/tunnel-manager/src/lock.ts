
import fs from 'fs';
import { LOCK_PATH, LOCK_STALE_MS, LOCK_RETRY_DELAY_MS, LOCK_MAX_RETRIES } from './paths.js';

class LockError extends Error {
  constructor(message: string, public code: string) {
    super(message);
    this.name = 'LockError';
  }
}

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export async function isLockStale(): Promise<boolean> {
  try {
    const stats = await fs.promises.stat(LOCK_PATH);
    const now = Date.now();
    const mtime = stats.mtimeMs;
    return (now - mtime) > LOCK_STALE_MS;
  } catch (error: any) {
    if (error.code === 'ENOENT') {
      return false; // No lock, so not stale (but also not held)
    }
    throw error;
  }
}

export async function acquireLock(retries = LOCK_MAX_RETRIES): Promise<void> {
  for (let i = 0; i < retries; i++) {
    try {
      // exclusive flag 'x' fails if file exists
      await fs.promises.writeFile(LOCK_PATH, process.pid.toString(), { flag: 'wx' });
      return; // Acquired!
    } catch (error: any) {
      if (error.code === 'EEXIST') {
        // Lock exists. Check if stale.
        if (await isLockStale()) {
          try {
             // Try to remove stale lock and retry immediately
             await fs.promises.unlink(LOCK_PATH);
             continue; 
          } catch (unlinkError: any) {
             // Someone else might have removed it or acquired it. Just retry loop.
          }
        }
        
        // Wait and retry
        await sleep(LOCK_RETRY_DELAY_MS);
        continue;
      }
      throw error; // Unexpected error
    }
  }
  throw new LockError(`Failed to acquire lock after ${retries} attempts`, 'ERR_TUNNEL_004');
}

export async function releaseLock(): Promise<void> {
    try {
        await fs.promises.unlink(LOCK_PATH);
    } catch (error: any) {
        if (error.code === 'ENOENT') {
            // Already gone, ignore
            return;
        }
        throw error;
    }
}

export async function withLock<T>(operation: () => Promise<T>): Promise<T> {
  await acquireLock();
  try {
    return await operation();
  } finally {
    await releaseLock();
  }
}
