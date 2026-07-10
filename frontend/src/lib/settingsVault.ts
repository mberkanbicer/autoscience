/**
 * Encrypted storage for API settings using Web Crypto (AES-GCM + PBKDF2).
 */

const VAULT_KEY = 'autoscience_api_settings_vault';
const LEGACY_KEY = 'autoscience_api_settings';
export const VAULT_PASSPHRASE_KEY = 'autoscience_vault_passphrase';

export interface VaultPayload {
  v: number;
  salt: string;
  iv: string;
  ciphertext: string;
}

function toBase64(bytes: Uint8Array): string {
  let binary = '';
  for (let i = 0; i < bytes.length; i += 1) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

function fromBase64(value: string): Uint8Array {
  const binary = atob(value);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

function asBufferSource(bytes: Uint8Array): BufferSource {
  const buffer = new ArrayBuffer(bytes.length);
  new Uint8Array(buffer).set(bytes);
  return buffer;
}

async function deriveKey(passphrase: string, salt: Uint8Array): Promise<CryptoKey> {
  const enc = new TextEncoder();
  const base = await crypto.subtle.importKey(
    'raw',
    enc.encode(passphrase),
    'PBKDF2',
    false,
    ['deriveKey'],
  );
  return crypto.subtle.deriveKey(
    { name: 'PBKDF2', salt: asBufferSource(salt), iterations: 120_000, hash: 'SHA-256' },
    base,
    { name: 'AES-GCM', length: 256 },
    false,
    ['encrypt', 'decrypt'],
  );
}

export function getVaultPassphrase(): string {
  if (typeof window === 'undefined') return '';
  // Passphrase is only ever held in sessionStorage (never persisted to
  // localStorage) so it cannot be exfiltrated via XSS after a page reload.
  return sessionStorage.getItem(VAULT_PASSPHRASE_KEY) || '';
}

export function setVaultPassphrase(passphrase: string) {
  sessionStorage.setItem(VAULT_PASSPHRASE_KEY, passphrase);
  // Never persist the passphrase to localStorage — doing so would let any
  // injected script read it and decrypt the stored API keys.
  localStorage.removeItem(VAULT_PASSPHRASE_KEY);
}

export async function encryptSettings(
  data: Record<string, unknown>,
  passphrase: string,
): Promise<VaultPayload> {
  if (!passphrase) {
    throw new Error('A non-empty passphrase is required to encrypt settings');
  }
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const key = await deriveKey(passphrase, salt);
  const enc = new TextEncoder();
  const ciphertext = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv: asBufferSource(iv) },
    key,
    enc.encode(JSON.stringify(data)),
  );
  return {
    v: 1,
    salt: toBase64(salt),
    iv: toBase64(iv),
    ciphertext: toBase64(new Uint8Array(ciphertext)),
  };
}

export async function decryptSettings(
  vault: VaultPayload,
  passphrase: string,
): Promise<Record<string, unknown>> {
  const key = await deriveKey(passphrase, fromBase64(vault.salt));
  const decrypted = await crypto.subtle.decrypt(
    { name: 'AES-GCM', iv: asBufferSource(fromBase64(vault.iv)) },
    key,
    asBufferSource(fromBase64(vault.ciphertext)),
  );
  return JSON.parse(new TextDecoder().decode(decrypted));
}

export async function loadStoredSettings(): Promise<Record<string, unknown> | null> {
  if (typeof window === 'undefined') return null;

  const legacy = localStorage.getItem(LEGACY_KEY);
  if (legacy) {
    try {
      return JSON.parse(legacy);
    } catch {
      return null;
    }
  }

  const raw = localStorage.getItem(VAULT_KEY);
  if (!raw) return null;

  const passphrase = getVaultPassphrase();
  if (!passphrase) return null;

  try {
    const vault = JSON.parse(raw) as VaultPayload;
    return await decryptSettings(vault, passphrase);
  } catch {
    return null;
  }
}

export async function saveStoredSettings(
  data: Record<string, unknown>,
  passphrase: string,
): Promise<void> {
  const vault = await encryptSettings(data, passphrase);
  localStorage.setItem(VAULT_KEY, JSON.stringify(vault));
  localStorage.removeItem(LEGACY_KEY);
}

export function hasEncryptedVault(): boolean {
  if (typeof window === 'undefined') return false;
  return !!localStorage.getItem(VAULT_KEY) && !localStorage.getItem(LEGACY_KEY);
}

export async function migrateLegacySettings(passphrase: string): Promise<boolean> {
  const legacy = localStorage.getItem(LEGACY_KEY);
  if (!legacy) return false;
  try {
    const data = JSON.parse(legacy);
    await saveStoredSettings(data, passphrase);
    return true;
  } catch {
    return false;
  }
}