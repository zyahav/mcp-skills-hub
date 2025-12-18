
import { exec } from 'child_process';
import util from 'util';

const execAsync = util.promisify(exec);

export async function runCommand(command: string): Promise<{ stdout: string; stderr: string; }> {
    try {
        const { stdout, stderr } = await execAsync(command);
        return { stdout, stderr };
    } catch (error: any) {
        throw new Error(`Command failed: ${command}\nError: ${error.message}\nStderr: ${error.stderr}`);
    }
}
