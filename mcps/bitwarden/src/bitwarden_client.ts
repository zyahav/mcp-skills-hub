/**
 * Bitwarden Client - THE SACRED CORE
 * 
 * All Bitwarden access goes through this file.
 * All safety rules (R1-R8) are enforced here.
 * 
 * DO NOT:
 * - Log secret values
 * - Return full item JSON
 * - Call bw unlock/login
 * - Parse human-readable output
 */

import { execFile } from "child_process";
import { promisify } from "util";

const execFileAsync = promisify(execFile);

// ============================================================================
// Types
// ============================================================================

interface BitwardenStatus {
  status: "locked" | "unlocked" | "unauthenticated";
  userEmail?: string;
}

interface BitwardenItem {
  id: string;
  name: string;
  notes?: string;
  fields?: BitwardenField[];
}

interface BitwardenField {
  name: string;
  value: string;
  type: number;
}

// ============================================================================
// Errors (value-redacted per R3b)
// ============================================================================

export class BitwardenError extends Error {
  constructor(
    public code: string,
    message: string,
    public metadata?: { itemName?: string; fieldName?: string }
  ) {
    // R3b: Only metadata in error, never values
    super(`[${code}] ${message}`);
    this.name = "BitwardenError";
  }
}

// ============================================================================
// Core Client
// ============================================================================

export class BitwardenClient {
  /**
   * R1: Verify BW_SESSION exists and vault is unlocked
   */
  async checkSession(): Promise<void> {
    // Check env var exists
    if (!process.env.BW_SESSION) {
      throw new BitwardenError(
        "ERR_NO_SESSION",
        "BW_SESSION environment variable is not set"
      );
    }

    // R2: Use JSON output only
    const status = await this.execBw<BitwardenStatus>(["status"]);

    if (status.status !== "unlocked") {
      throw new BitwardenError(
        "ERR_VAULT_LOCKED",
        `Vault is ${status.status}, must be unlocked`
      );
    }
  }

  /**
   * R6: Deterministic item resolution
   * - Search by name
   * - Exact match only
   * - 0 matches = fail
   * - >1 matches = fail (R7)
   * - Exactly 1 = success
   */
  async resolveItem(itemName: string): Promise<string> {
    await this.checkSession();

    // R2a: bw list items --format json
    const items = await this.execBw<BitwardenItem[]>([
      "list", "items", "--search", itemName
    ]);

    // Filter for exact name match
    const exactMatches = items.filter(item => item.name === itemName);

    if (exactMatches.length === 0) {
      throw new BitwardenError(
        "ERR_ITEM_NOT_FOUND",
        `No item found with exact name`,
        { itemName }
      );
    }

    // R7: Duplicate names = hard failure
    if (exactMatches.length > 1) {
      throw new BitwardenError(
        "ERR_AMBIGUOUS_MATCH",
        `Found ${exactMatches.length} items with same name - cannot resolve`,
        { itemName }
      );
    }

    return exactMatches[0].id;
  }

  /**
   * Get a secret value from a custom field
   * R3: Never log the value
   * R3a: Never return full item JSON
   */
  async getSecret(itemName: string, fieldName: string): Promise<string> {
    const itemId = await this.resolveItem(itemName);

    // R2a: bw get item --format json
    const item = await this.execBw<BitwardenItem>(["get", "item", itemId]);

    // Find the custom field
    const field = item.fields?.find(f => f.name === fieldName);

    if (!field) {
      throw new BitwardenError(
        "ERR_FIELD_NOT_FOUND",
        `Custom field not found`,
        { itemName, fieldName }
      );
    }

    if (!field.value) {
      throw new BitwardenError(
        "ERR_FIELD_EMPTY",
        `Custom field is empty`,
        { itemName, fieldName }
      );
    }

    // R3: Return only the value, nothing else
    return field.value;
  }

  /**
   * Get notes from an item
   * R8: Gated by PUBLIC_NOTES="true" custom field
   */
  async getNotes(itemName: string): Promise<string> {
    const itemId = await this.resolveItem(itemName);

    const item = await this.execBw<BitwardenItem>(["get", "item", itemId]);

    // R8: Check for PUBLIC_NOTES gate
    const publicNotesField = item.fields?.find(f => f.name === "PUBLIC_NOTES");
    
    if (!publicNotesField || publicNotesField.value !== "true") {
      throw new BitwardenError(
        "ERR_NOTES_NOT_PUBLIC",
        `Notes access denied - item must have PUBLIC_NOTES="true" custom field`,
        { itemName }
      );
    }

    if (!item.notes) {
      throw new BitwardenError(
        "ERR_NO_NOTES",
        `Item has no notes`,
        { itemName }
      );
    }

    return item.notes;
  }

  /**
   * Execute bw CLI with JSON output
   * R2: All access uses structured JSON (never human text)
   * R4: Never call unlock/login
   */
  private async execBw<T>(args: string[]): Promise<T> {
    // R4: Block forbidden commands
    const forbiddenCommands = ["unlock", "login", "logout", "lock"];
    if (forbiddenCommands.includes(args[0])) {
      throw new BitwardenError(
        "ERR_FORBIDDEN_COMMAND",
        `Command '${args[0]}' is not allowed`
      );
    }

    try {
      const { stdout } = await execFileAsync("bw", [...args, "--format", "json"], {
        env: {
          ...process.env,
          BW_SESSION: process.env.BW_SESSION,
        },
        // R3: Don't let secrets leak via error messages
        maxBuffer: 10 * 1024 * 1024, // 10MB
      });

      return JSON.parse(stdout) as T;
    } catch (error: any) {
      // R3b: Redact any potential secret content from errors
      const safeMessage = error.message?.replace(/BW_SESSION=\S+/g, "BW_SESSION=[REDACTED]");
      throw new BitwardenError(
        "ERR_BW_COMMAND_FAILED",
        `Bitwarden CLI error: ${safeMessage?.substring(0, 200)}`
      );
    }
  }
}
