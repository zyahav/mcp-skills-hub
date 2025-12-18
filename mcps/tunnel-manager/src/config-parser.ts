
import fs from 'fs';
import yaml from 'yaml'; // We need a yaml parser. I assume it's available or I should use 'js-yaml' or assume simple parsing if structure is simple. 
// Actually, `package.json` didn't list a yaml parser. I should check if I can install one or use simple string manipulation if the managed block is just a list of ingress rules.
// But wait, Cloudflare config is YAML. I really should use a YAML parser for safety inside the block.
// `LESSONS_LEARNED` says: "The managed block ... solved the coexistence problem".
// I'll check package.json again. I saw `zod` and `@modelcontextprotocol/sdk`. No yaml parser.
// I should probably add one. `yaml` is a good library.
// For now, I'll rely on string manipulation for the *block extraction* and maybe simple parsing or assume I can add the dependency.
// Given I'm in a "skill" and user might have specific preferences, I'll check if I can genericize it.
// The managed block likely contains specific ingress rules.
// Let's assume I should install `yaml`.

import { CONFIG_PATH } from './paths.js';

const START_MARKER = '# ZUROT-MANAGED-START';
const END_MARKER = '# ZUROT-MANAGED-END';

export class ConfigError extends Error {
  constructor(message: string, public code: string) {
    super(message);
    this.name = 'ConfigError';
  }
}

export interface ManagedBlockResult {
    before: string;
    managedContent: string;
    after: string;
}

export async function readConfigRaw(): Promise<string> {
    try {
        return await fs.promises.readFile(CONFIG_PATH, 'utf-8');
    } catch (e: any) {
        if (e.code === 'ENOENT') {
             throw new ConfigError('Config file not found', 'ERR_TUNNEL_005');
        }
        throw e;
    }
}

export function extractManagedBlock(fullContent: string): ManagedBlockResult {
    const startIndex = fullContent.indexOf(START_MARKER);
    const endIndex = fullContent.indexOf(END_MARKER);

    if (startIndex === -1 || endIndex === -1) {
        throw new ConfigError('Managed block markers not found in config', 'ERR_TUNNEL_003');
    }

    if (startIndex >= endIndex) {
        throw new ConfigError('Managed start marker appears after end marker', 'ERR_TUNNEL_006');
    }

    const before = fullContent.substring(0, startIndex + START_MARKER.length);
    // Content between markers (trimming handled by parser potentially, but we keep whitespace for update)
    // Actually, usually we want the lines *between* the markers.
    const managedContent = fullContent.substring(startIndex + START_MARKER.length, endIndex);
    const after = fullContent.substring(endIndex);

    return { before, managedContent, after };
}

// Simple YAML parser wrapper since we might not have a heavy lib yet.
// If the content is simple ingress rules, maybe we can parse manually or use a regex?
// "ingress:" list.
// If I assume I can run `npm install yaml`, I should do that.
// Steps:
// 1. Install yaml
// 2. Parse `managedContent` as YAML.
// 3. Modifying it: 
//    We need to reconstruct the YAML string for the managed block.

// For now, let's just export the extractor and updater helpers.
// The actual parsing logic will depend on `yaml` package.

export async function updateManagedBlock(newContent: string): Promise<void> {
    const full = await readConfigRaw();
    const { before, after } = extractManagedBlock(full);
    
    // Ensure newContent ends with newline if needed or format it nicely
    // This is raw string replacement.
    const newFull = before + newContent + after;
    await fs.promises.writeFile(CONFIG_PATH, newFull, 'utf-8');
}
