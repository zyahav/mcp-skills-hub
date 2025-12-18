
import express from 'express';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT_DIR = path.resolve(__dirname, '..'); // Monorepo root
const MCPS_DIR = path.join(ROOT_DIR, 'mcps');

const app = express();
const PORT = 3000;

app.use(express.static(__dirname));

function detectMCPs() {
    const mcps = [];
    if (!fs.existsSync(MCPS_DIR)) return mcps;

    const dirs = fs.readdirSync(MCPS_DIR);
    for (const dir of dirs) {
        if (dir.startsWith('.')) continue;
        const mcpPath = path.join(MCPS_DIR, dir);
        if (!fs.statSync(mcpPath).isDirectory()) continue;

        let config = null;

        // Detection Priority:
        // 1. wrapper.sh (highest priority for complex setups)
        // 2. build/index.js (compiled TS)
        // 3. index.js (simple JS)
        // 4. server.py (Python)

        if (fs.existsSync(path.join(mcpPath, 'wrapper.sh'))) {
            config = {
                command: '/bin/bash',
                args: [path.join(mcpPath, 'wrapper.sh')],
                type: 'wrapper'
            };
        } else if (fs.existsSync(path.join(mcpPath, 'package.json'))) {
            // Node.js project
            // Try to find entry point or assume standard build/index.js
            const pkg = JSON.parse(fs.readFileSync(path.join(mcpPath, 'package.json'), 'utf-8'));
            
            let entry = 'index.js';
            if (fs.existsSync(path.join(mcpPath, 'build', 'index.js'))) {
                entry = 'build/index.js';
            } else if (fs.existsSync(path.join(mcpPath, 'dist', 'index.js'))) {
                entry = 'dist/index.js';
            } else if (pkg.main) {
                entry = pkg.main;
            } else {
                 // Default fallback for TS projects not yet built
                 entry = 'build/index.js';
            }
            
            config = {
                command: 'node',
                args: [path.join(mcpPath, entry)],
                type: 'node'
            };
        } else if (fs.existsSync(path.join(mcpPath, 'server.py'))) {

            config = {
                command: 'python3', // or uv run
                args: [path.join(mcpPath, 'server.py')],
                type: 'python'
            };
        }

        if (config) {
            // Check for specific env formatting needs
            const env = {};
            // Example: Tunnel Manager needs envs
            if (dir === 'tunnel-manager') {
                env['TUNNEL_CONFIG_PATH'] = path.join(os.homedir(), 'tunnel-management', 'configs', 'config.yml');
                env['TUNNEL_LEDGER_PATH'] = path.join(os.homedir(), 'tunnel-management', 'run-state.json');
            }
            
            mcps.push({
                name: dir,
                ...config,
                env
            });
        }
    }
    return mcps;
}

import os from 'os';

app.get('/api/config', (req, res) => {
    const mcps = detectMCPs();
    
    // Generate configs for different platforms
    
    // 1. Claude Desktop (mcpServers object)
    const claude = { mcpServers: {} };
    mcps.forEach(m => {
        claude.mcpServers[m.name] = {
            command: m.command,
            args: m.args,
            env: Object.keys(m.env).length > 0 ? m.env : undefined
        };
    });

    // 2. Gemini / VSCode (often array or map)
    // Gemini often uses "mcpServers" too in settings.json
    const gemini = { mcpServers: {} };
    mcps.forEach(m => {
        gemini.mcpServers[m.name] = {
            command: m.command,
            args: m.args,
            env: Object.keys(m.env).length > 0 ? m.env : undefined
        };
    });

    res.json({
        mcps,
        claude: JSON.stringify(claude, null, 2),
        gemini: JSON.stringify(gemini, null, 2)
    });
});

app.listen(PORT, () => {
    console.log(`MCP Dashboard running at http://localhost:${PORT}`);
});
