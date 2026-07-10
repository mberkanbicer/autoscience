import { loadStoredSettings } from './settingsVault';

export interface ApiSettings {
  openrouter_api_key: string;
  openrouter_model: string;
  openai_api_key: string;
  openai_model: string;
  anthropic_api_key: string;
  anthropic_model: string;
  local_base_url: string;
  local_model: string;
  llamacpp_base_url: string;
  llamacpp_model: string;
  default_provider: string;
}

export const defaultApiSettings: ApiSettings = {
  openrouter_api_key: '',
  openrouter_model: 'openai/gpt-4o',
  openai_api_key: '',
  openai_model: 'gpt-4o',
  anthropic_api_key: '',
  anthropic_model: 'claude-sonnet-4-20250514',
  local_base_url: 'http://localhost:11434',
  local_model: 'llama3',
  llamacpp_base_url: 'http://localhost:8080',
  llamacpp_model: 'local-model',
  default_provider: 'openrouter',
};

let cachedSettings: ApiSettings | null = null;

export function getApiSettings(): ApiSettings {
  if (cachedSettings) return cachedSettings;
  if (typeof window === 'undefined') return defaultApiSettings;

  const legacy = localStorage.getItem('autoscience_api_settings');
  if (legacy) {
    try {
      const parsed = { ...defaultApiSettings, ...JSON.parse(legacy) } as ApiSettings;
      cachedSettings = parsed;
      return parsed;
    } catch {
      return defaultApiSettings;
    }
  }
  return defaultApiSettings;
}

export async function refreshApiSettings(): Promise<ApiSettings> {
  const stored = await loadStoredSettings();
  cachedSettings = stored
    ? { ...defaultApiSettings, ...(stored as Partial<ApiSettings>) }
    : getApiSettings();
  return cachedSettings;
}

export function getLlmHeaders(): Record<string, string> {
  const s = getApiSettings();
  return {
    'X-OpenRouter-API-Key': s.openrouter_api_key || '',
    'X-OpenRouter-Model': s.openrouter_model || 'openai/gpt-4o',
    'X-OpenAI-API-Key': s.openai_api_key || '',
    'X-OpenAI-Model': s.openai_model || 'gpt-4o',
    'X-Anthropic-API-Key': s.anthropic_api_key || '',
    'X-Anthropic-Model': s.anthropic_model || 'claude-sonnet-4-20250514',
    'X-Default-Provider': s.default_provider || 'openrouter',
  };
}

export function isLlmConfigured(): boolean {
  const s = getApiSettings();
  return !!(s.openrouter_api_key || s.openai_api_key || s.anthropic_api_key);
}