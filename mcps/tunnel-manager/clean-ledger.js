
import fs from 'fs';
import path from 'path';
import os from 'os';

const LEDGER_PATH = path.join(os.homedir(), 'tunnel-management', 'run-state.json');

console.log('Cleaning ledger...');
try {
    const content = fs.readFileSync(LEDGER_PATH, 'utf-8');
    const ledger = JSON.parse(content);
    
    if (ledger.tunnels['ark-on.zurielyahav.com']) {
        console.log('Found corrupt record, deleting...');
        delete ledger.tunnels['ark-on.zurielyahav.com'];
        fs.writeFileSync(LEDGER_PATH, JSON.stringify(ledger, null, 2));
        console.log('Ledger cleaned.');
    } else {
        console.log('Record not found in ledger.');
    }
} catch (e) {
    console.error('Failed:', e);
}
