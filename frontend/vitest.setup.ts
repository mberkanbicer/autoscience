import { webcrypto } from 'node:crypto';

// Replace jsdom's incomplete crypto.subtle with Node's native WebCrypto
// implementation, which properly supports PBKDF2 and other modern algorithms.
Object.defineProperty(globalThis, 'crypto', {
  value: webcrypto,
  writable: true,
  configurable: true,
});
