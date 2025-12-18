
import fs from 'fs';
import path from 'path';
import os from 'os';

const CONFIG_PATH = path.join(os.homedir(), 'tunnel-management', 'configs', 'config.yml');

console.log('Patching config.yml...');
let content = fs.readFileSync(CONFIG_PATH, 'utf-8');

// Find the ark-on entry
//   - hostname: ark-on.zurielyahav.com
//     service: http://localhost:3737

if (content.includes('originRequest')) {
    console.log('Already patched?');
} else {
    // Regex replace to insert originRequest block
    const target = 'service: http://localhost:3737';
    const replacement = 'service: http://localhost:3737\n    originRequest:\n      httpHostHeader: "localhost"';
    
    if (content.includes(target)) {
        content = content.replace(target, replacement);
        fs.writeFileSync(CONFIG_PATH, content);
        console.log('Patched!');
    } else {
        console.log('Target not found.');
    }
}
