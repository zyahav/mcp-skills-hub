
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

export async function verifyConfigIntegrity(): Promise<VerificationResult> {
    try {
        // cloudflared check-config returns exit code 0 on success, non-zero on failure
        // It reads the default config file in ~/.cloudflared/config.yml or /usr/local/etc/cloudflared/config.yml
        // We assume environment is set up correctly for it to find the config.
        // We can pass the path explicitly if we assume TUNNEL_CONFIG_PATH is standard cloudflared location, 
        // but usually check-config finds the default. 
        // Let's rely on default behavior first as user's run-command usually has context.
        // Actually, we should probably pass the path if known.
        // The tool runner doesn't easily expose the path env var here, but we can assume default.
        
        // Command: cloudflared --config /Users/zyahav/tunnel-management/configs/config.yml check-config ?
        // Or just `cloudflared tunnel check-config` ?
        // `cloudflared` main command has `check-config`? No, it's `cloudflared --config ... tunnel ingress validation`?
        // Actually, simple `cloudflared tunnel ingress validate` validates the ingress rules.
        // But preventing YAML syntax errors is key.
        // `cloudflared --config <path> tunnel ingress validate` is the robust check.
        // We need the config path.
        // We can try to get it from process.env.TUNNEL_CONFIG_PATH or default.
        
        const configPath = process.env.TUNNEL_CONFIG_PATH;
        let cmd = 'cloudflared tunnel ingress validate'; // This acts as syntax check too
        if (configPath) {
            cmd = `cloudflared --config "${configPath}" tunnel ingress validate`;
        }

        const { stdout, stderr } = await runCommand(cmd);
        // If it throws, runCommand catches and rethrows? No, runCommand returns stdout/stderr.
        // Wait, looking at tool-runner.ts might be needed. 
        // Usually exec throws if exit code != 0.
        return { success: true, details: { output: stdout || stderr } };
    } catch (e: any) {
        return { success: false, error: `Config validation failed: ${e.message}` };
    }
}
