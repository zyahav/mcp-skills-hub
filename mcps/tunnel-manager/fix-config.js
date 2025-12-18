
import fs from 'fs';
import path from 'path';
import os from 'os';

const CONFIG_PATH = path.join(os.homedir(), 'tunnel-management', 'configs', 'config.yml');

console.log('Fixing config.yml...');
let content = fs.readFileSync(CONFIG_PATH, 'utf-8');

// Remove [] line if present inside our block area (simple string replace for this specific corruption)
if (content.includes('[]')) {
    console.log('Found [], removing...');
    content = content.replace('[]', '');
}

// Also check if ark-on entry is there but maybe messy newlines
// Clean up double newlines or weird indentation
// Actually, cloudflared YAML parser is strict.
// Let's ensure ZUROT-MANAGED-START is followed by newline then - hostname

// Just doing the [] removal is likely enough if the rest is valid block YAML.
// But let's verify indentation of the ark-on block.
// Current bad state:
//   # ZUROT-MANAGED-START
// []
//   - hostname: ...

// If we remove [], we get
//   # ZUROT-MANAGED-START
// 
//   - hostname: ...
// That is valid.

fs.writeFileSync(CONFIG_PATH, content);
console.log('Fixed.');
