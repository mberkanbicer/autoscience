/**
 * @vitest-environment node
 * Node 24 provides native WebCrypto with full PBKDF2 support.
 * jsdom's polyfill rejects the salt ArrayBuffer with ERR_INVALID_ARG_TYPE.
 */
import { describe, it, expect } from 'vitest';
import { encryptSettings, decryptSettings } from '../settingsVault';

describe('settingsVault', () => {
  it('round-trips encrypted settings', async () => {
    const data = { openai_api_key: 'sk-test', default_provider: 'openai' };
    const vault = await encryptSettings(data, 'test-passphrase');
    const restored = await decryptSettings(vault, 'test-passphrase');
    expect(restored).toEqual(data);
  });
});