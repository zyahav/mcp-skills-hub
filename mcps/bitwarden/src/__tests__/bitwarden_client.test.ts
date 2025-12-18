/**
 * Bitwarden Client Tests
 * 
 * All tests use mocks - NO live vault access
 * Tests verify rules R1-R8
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { BitwardenClient, BitwardenError } from "../bitwarden_client.js";
import * as child_process from "child_process";

// Mock child_process.execFile
vi.mock("child_process", () => ({
  execFile: vi.fn(),
}));

const mockExecFile = child_process.execFile as unknown as ReturnType<typeof vi.fn>;

// Helper to create mock execFile response
function mockBwResponse(response: any) {
  mockExecFile.mockImplementation((_cmd: string, _args: string[], _opts: any, callback?: Function) => {
    if (callback) {
      callback(null, { stdout: JSON.stringify(response) });
    }
    return { stdout: JSON.stringify(response) };
  });
}

function mockBwError(message: string) {
  mockExecFile.mockImplementation((_cmd: string, _args: string[], _opts: any, callback?: Function) => {
    const error = new Error(message);
    if (callback) {
      callback(error, null);
    }
    throw error;
  });
}

describe("BitwardenClient", () => {
  let client: BitwardenClient;
  const originalEnv = process.env;

  beforeEach(() => {
    client = new BitwardenClient();
    process.env = { ...originalEnv, BW_SESSION: "test-session-token" };
    vi.clearAllMocks();
  });

  afterEach(() => {
    process.env = originalEnv;
  });


  // =========================================================================
  // R1: Session validation
  // =========================================================================
  
  describe("R1: Session validation", () => {
    it("should fail if BW_SESSION is not set", async () => {
      delete process.env.BW_SESSION;
      
      await expect(client.checkSession()).rejects.toThrow(BitwardenError);
      await expect(client.checkSession()).rejects.toMatchObject({
        code: "ERR_NO_SESSION"
      });
    });

    it("should fail if vault is locked", async () => {
      mockBwResponse({ status: "locked" });
      
      await expect(client.checkSession()).rejects.toMatchObject({
        code: "ERR_VAULT_LOCKED"
      });
    });

    it("should succeed if vault is unlocked", async () => {
      mockBwResponse({ status: "unlocked" });
      
      await expect(client.checkSession()).resolves.toBeUndefined();
    });
  });

  // =========================================================================
  // R6 & R7: Deterministic item resolution
  // =========================================================================
  
  describe("R6 & R7: Item resolution", () => {
    beforeEach(() => {
      // First call is always status check
      mockExecFile.mockImplementationOnce((_cmd: string, _args: string[], _opts: any, callback?: Function) => {
        if (callback) callback(null, { stdout: JSON.stringify({ status: "unlocked" }) });
        return { stdout: JSON.stringify({ status: "unlocked" }) };
      });
    });

    it("should fail if no items match (0 matches)", async () => {
      mockExecFile.mockImplementationOnce((_cmd: string, _args: string[], _opts: any, callback?: Function) => {
        if (callback) callback(null, { stdout: JSON.stringify([]) });
        return { stdout: JSON.stringify([]) };
      });

      await expect(client.resolveItem("NonExistent")).rejects.toMatchObject({
        code: "ERR_ITEM_NOT_FOUND",
        metadata: { itemName: "NonExistent" }
      });
    });

    it("should fail if multiple items match (R7: duplicates)", async () => {
      const items = [
        { id: "id-1", name: "Duplicate Item" },
        { id: "id-2", name: "Duplicate Item" }
      ];
      mockExecFile.mockImplementationOnce((_cmd: string, _args: string[], _opts: any, callback?: Function) => {
        if (callback) callback(null, { stdout: JSON.stringify(items) });
        return { stdout: JSON.stringify(items) };
      });

      await expect(client.resolveItem("Duplicate Item")).rejects.toMatchObject({
        code: "ERR_AMBIGUOUS_MATCH"
      });
    });

    it("should succeed with exactly 1 match", async () => {
      const items = [{ id: "unique-id", name: "Unique Item" }];
      mockExecFile.mockImplementationOnce((_cmd: string, _args: string[], _opts: any, callback?: Function) => {
        if (callback) callback(null, { stdout: JSON.stringify(items) });
        return { stdout: JSON.stringify(items) };
      });

      const id = await client.resolveItem("Unique Item");
      expect(id).toBe("unique-id");
    });

    it("should filter by exact name match only", async () => {
      const items = [
        { id: "id-1", name: "Test Item" },
        { id: "id-2", name: "Test Item Extended" }
      ];
      mockExecFile.mockImplementationOnce((_cmd: string, _args: string[], _opts: any, callback?: Function) => {
        if (callback) callback(null, { stdout: JSON.stringify(items) });
        return { stdout: JSON.stringify(items) };
      });

      const id = await client.resolveItem("Test Item");
      expect(id).toBe("id-1");
    });
  });


  // =========================================================================
  // getSecret tests
  // =========================================================================
  
  describe("getSecret", () => {
    const mockSetup = () => {
      // Status check
      mockExecFile.mockImplementationOnce((_cmd: string, _args: string[], _opts: any, callback?: Function) => {
        if (callback) callback(null, { stdout: JSON.stringify({ status: "unlocked" }) });
      });
      // List items
      mockExecFile.mockImplementationOnce((_cmd: string, _args: string[], _opts: any, callback?: Function) => {
        if (callback) callback(null, { stdout: JSON.stringify([{ id: "item-123", name: "My Item" }]) });
      });
    };

    it("should return custom field value", async () => {
      mockSetup();
      // Get item
      mockExecFile.mockImplementationOnce((_cmd: string, _args: string[], _opts: any, callback?: Function) => {
        const item = {
          id: "item-123",
          name: "My Item",
          fields: [{ name: "API_KEY", value: "secret-value-123", type: 0 }]
        };
        if (callback) callback(null, { stdout: JSON.stringify(item) });
      });

      const secret = await client.getSecret("My Item", "API_KEY");
      expect(secret).toBe("secret-value-123");
    });

    it("should fail if field not found", async () => {
      mockSetup();
      mockExecFile.mockImplementationOnce((_cmd: string, _args: string[], _opts: any, callback?: Function) => {
        const item = { id: "item-123", name: "My Item", fields: [] };
        if (callback) callback(null, { stdout: JSON.stringify(item) });
      });

      await expect(client.getSecret("My Item", "MISSING_FIELD")).rejects.toMatchObject({
        code: "ERR_FIELD_NOT_FOUND",
        metadata: { itemName: "My Item", fieldName: "MISSING_FIELD" }
      });
    });

    it("should fail if field is empty", async () => {
      mockSetup();
      mockExecFile.mockImplementationOnce((_cmd: string, _args: string[], _opts: any, callback?: Function) => {
        const item = {
          id: "item-123",
          name: "My Item",
          fields: [{ name: "EMPTY_FIELD", value: "", type: 0 }]
        };
        if (callback) callback(null, { stdout: JSON.stringify(item) });
      });

      await expect(client.getSecret("My Item", "EMPTY_FIELD")).rejects.toMatchObject({
        code: "ERR_FIELD_EMPTY"
      });
    });
  });

  // =========================================================================
  // R8: getNotes gating
  // =========================================================================
  
  describe("R8: getNotes gating", () => {
    const mockSetup = () => {
      mockExecFile.mockImplementationOnce((_cmd: string, _args: string[], _opts: any, callback?: Function) => {
        if (callback) callback(null, { stdout: JSON.stringify({ status: "unlocked" }) });
      });
      mockExecFile.mockImplementationOnce((_cmd: string, _args: string[], _opts: any, callback?: Function) => {
        if (callback) callback(null, { stdout: JSON.stringify([{ id: "item-123", name: "My Item" }]) });
      });
    };

    it("should fail if PUBLIC_NOTES field is missing", async () => {
      mockSetup();
      mockExecFile.mockImplementationOnce((_cmd: string, _args: string[], _opts: any, callback?: Function) => {
        const item = { id: "item-123", name: "My Item", notes: "Secret notes", fields: [] };
        if (callback) callback(null, { stdout: JSON.stringify(item) });
      });

      await expect(client.getNotes("My Item")).rejects.toMatchObject({
        code: "ERR_NOTES_NOT_PUBLIC"
      });
    });

    it("should fail if PUBLIC_NOTES is not 'true'", async () => {
      mockSetup();
      mockExecFile.mockImplementationOnce((_cmd: string, _args: string[], _opts: any, callback?: Function) => {
        const item = {
          id: "item-123",
          name: "My Item",
          notes: "Secret notes",
          fields: [{ name: "PUBLIC_NOTES", value: "false", type: 0 }]
        };
        if (callback) callback(null, { stdout: JSON.stringify(item) });
      });

      await expect(client.getNotes("My Item")).rejects.toMatchObject({
        code: "ERR_NOTES_NOT_PUBLIC"
      });
    });

    it("should return notes when PUBLIC_NOTES='true'", async () => {
      mockSetup();
      mockExecFile.mockImplementationOnce((_cmd: string, _args: string[], _opts: any, callback?: Function) => {
        const item = {
          id: "item-123",
          name: "My Item",
          notes: "These are public notes",
          fields: [{ name: "PUBLIC_NOTES", value: "true", type: 0 }]
        };
        if (callback) callback(null, { stdout: JSON.stringify(item) });
      });

      const notes = await client.getNotes("My Item");
      expect(notes).toBe("These are public notes");
    });
  });
});
