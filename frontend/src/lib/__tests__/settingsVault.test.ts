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