export class McpError extends Error {
  constructor(public code: string, message: string) {
    super(message);
    this.name = 'McpError';
  }
}

export const ERR_APEX_PROTECTION_VIOLATION = 'ERR_APEX_PROTECTION_VIOLATION';
export const ERR_INVALID_RECORD_TYPE = 'ERR_INVALID_RECORD_TYPE';
export const ERR_AMBIGUOUS_MULTI_MATCH = 'ERR_AMBIGUOUS_MULTI_MATCH';

const BLOCKED_DOMAINS = new Set(['@', 'www', 'zurielyahav.com', 'www.zurielyahav.com']);
const ALLOWED_TYPES = new Set(['A', 'CNAME', 'TXT']);

export function validateSubdomain(subdomain: string): void {
  if (BLOCKED_DOMAINS.has(subdomain)) {
    throw new McpError(ERR_APEX_PROTECTION_VIOLATION, `Modification of '${subdomain}' is strictly forbidden by safety rules.`);
  }
  // Also block if it ends with the root domain in a way that implies root/www
  if (subdomain.endsWith('zurielyahav.com')) {
      if (subdomain === 'zurielyahav.com' || subdomain === 'www.zurielyahav.com') {
           throw new McpError(ERR_APEX_PROTECTION_VIOLATION, `Modification of '${subdomain}' is strictly forbidden by safety rules.`);
      }
  }
}

export function validateRecordType(type: string): void {
  if (!ALLOWED_TYPES.has(type.toUpperCase())) {
    throw new McpError(ERR_INVALID_RECORD_TYPE, `Record type '${type}' is not allowed. Allowed types: ${Array.from(ALLOWED_TYPES).join(', ')}`);
  }
}

export function enforceProxied(type: string, proxied: boolean): boolean {
  if (type.toUpperCase() === 'TXT') {
    return false; // TXT records cannot be proxied
  }
  return proxied;
}

export function checkMultiMatch(records: any[]): void {
  if (records.length > 1) {
    throw new McpError(ERR_AMBIGUOUS_MULTI_MATCH, `Found ${records.length} matching records. Operation aborted to prevent ambiguous changes.`);
  }
}
