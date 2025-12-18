
import fs from 'fs';
import path from 'path';
import os from 'os';

const CONFIG_PATH = path.join(os.homedir(), 'tunnel-management', 'configs', 'config.yml');

console.log('Fixing config.yml lines...');
let content = fs.readFileSync(CONFIG_PATH, 'utf-8');

// Fix the smashed line issue
if (content.includes('# ZUROT-MANAGED-START- hostname')) {
    console.log('Found smashed marker...');
    content = content.replace('# ZUROT-MANAGED-START- hostname', '# ZUROT-MANAGED-START\n  - hostname');
}

fs.writeFileSync(CONFIG_PATH, content);
console.log('Fixed.');
