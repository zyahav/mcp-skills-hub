
import { runCommand } from './tool-runner.js';

export interface VerificationResult {
    success: boolean;
    error?: string;
    details?: any;
}

export async function verifyDNS(hostname: string): Promise<VerificationResult> {
    try {
        const { stdout } = await runCommand(`dig +short ${hostname}`);
        const ips = stdout.split('\n').filter(Boolean);
        if (ips.length > 0) {
            return { success: true, details: { ips } };
        }
        return { success: false, error: 'DNS not resolving (empty result)' };
    } catch (e: any) {
        return { success: false, error: `DNS check failed: ${e.message}` };
    }
}

export async function verifyHTTP(url: string): Promise<VerificationResult> {
    try {
        // -I for HEAD request, -m 5 for 5 second timeout
        const { stdout } = await runCommand(`curl -I -m 5 ${url}`);
        // Check for 200, 301, 302
        if (stdout.match(/HTTP\/\d(\.\d)? (200|301|302)/)) {
            return { success: true, details: { headers: stdout } };
        }
        return { success: false, error: 'HTTP check failed (status not 2xx/3xx)', details: { output: stdout } };
    } catch (e: any) {
        return { success: false, error: `HTTP check failed: ${e.message}` };
    }
}
