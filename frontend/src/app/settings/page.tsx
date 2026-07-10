'use client';

import { useState, useEffect } from 'react';
import { Layout } from '@/components/layout/Layout';
import { Header } from '@/components/layout/Header';
import { Card, CardContent, CardHeader } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input, Textarea } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { Settings, Key, Cpu, Save, ExternalLink, AlertTriangle, Shield } from 'lucide-react';
import {
  defaultApiSettings,
  refreshApiSettings,
  type ApiSettings,
} from '@/lib/apiSettings';
import {
  hasEncryptedVault,
  loadStoredSettings,
  migrateLegacySettings,
  saveStoredSettings,
  setVaultPassphrase,
} from '@/lib/settingsVault';

export default function SettingsPage() {
  const [settings, setSettings] = useState<ApiSettings>(defaultApiSettings);
  const [vaultPassphrase, setVaultPassphraseState] = useState('');
  const [persistPassphrase, setPersistPassphrase] = useState(false);
  const [vaultLocked, setVaultLocked] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      const stored = await loadStoredSettings();
      if (stored) {
        setSettings({ ...defaultApiSettings, ...(stored as Partial<ApiSettings>) });
        setVaultLocked(false);
      } else if (hasEncryptedVault()) {
        setVaultLocked(true);
      } else {
        const legacy = localStorage.getItem('autoscience_api_settings');
        if (legacy) {
          setSettings({ ...defaultApiSettings, ...JSON.parse(legacy) });
        }
      }
    })();
  }, []);

  const handleUnlock = async () => {
    if (!vaultPassphrase.trim()) return;
    setVaultPassphrase(vaultPassphrase.trim());
    const stored = await loadStoredSettings();
    if (stored) {
      setSettings({ ...defaultApiSettings, ...(stored as Partial<ApiSettings>) });
      setVaultLocked(false);
    }
  };

  const handleSave = async () => {
    if (!vaultPassphrase.trim()) {
      setError('A vault passphrase is required to save API settings');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      setVaultPassphrase(vaultPassphrase.trim());
      await migrateLegacySettings(vaultPassphrase.trim());
      await saveStoredSettings(settings as unknown as Record<string, unknown>, vaultPassphrase.trim());
      await refreshApiSettings();
      setSaved(true);
      setVaultLocked(false);
      setTimeout(() => setSaved(false), 2000);
    } finally {
      setSaving(false);
    }
  };

  const providers = [
    { id: 'openrouter', name: 'OpenRouter', description: 'Access 100+ models via single API' },
    { id: 'openai', name: 'OpenAI', description: 'GPT-4o, GPT-4o-mini, o3' },
    { id: 'anthropic', name: 'Anthropic', description: 'Claude 3.5 Sonnet, Claude 3 Opus' },
    { id: 'local', name: 'Ollama / Local', description: 'Run models locally via Ollama' },
    { id: 'llamacpp', name: 'Llama.cpp', description: 'Local models via llama-server' },
  ];

  return (
    <Layout>
      <Header
        title="API Settings"
        subtitle="Configure LLM providers and API keys"
        actions={
          <Button onClick={handleSave} loading={saving}>
            <Save size={18} className="mr-2" />
            {saved ? 'Saved!' : 'Save Settings'}
          </Button>
        }
      />

      {error && <p className="text-sm text-error">{error}</p>}

      <div className="p-4 lg:p-6 space-y-6 max-w-4xl">
        <Card className="glass overflow-hidden border-border/20">
          <CardHeader className="bg-white/40 backdrop-blur-md border-b border-border/10">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-primary/10 rounded-2xl flex items-center justify-center">
                <Shield className="text-primary" size={24} />
              </div>
              <div>
                <h3 className="text-lg font-bold">Encrypted Vault</h3>
                <p className="text-xs text-muted-foreground">
                  API keys are encrypted with AES-GCM before storage in your browser.
                </p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-6 space-y-4">
            {vaultLocked && (
              <div className="flex items-start gap-2 p-3 rounded-xl bg-amber-500/10 text-sm">
                <AlertTriangle size={16} className="mt-0.5 shrink-0" />
                <span>Enter your vault passphrase to unlock saved API keys.</span>
              </div>
            )}
            <Input
              label="Vault passphrase"
              type="password"
              value={vaultPassphrase}
              onChange={(e) => setVaultPassphraseState(e.target.value)}
              placeholder="Choose a passphrase to encrypt keys"
            />
            <label className="flex items-center gap-2 text-sm text-muted-foreground">
              <input
                type="checkbox"
                checked={persistPassphrase}
                onChange={(e) => setPersistPassphrase(e.target.checked)}
              />
              Remember passphrase on this device
            </label>
            {vaultLocked && (
              <Button variant="secondary" onClick={handleUnlock}>
                Unlock Vault
              </Button>
            )}
          </CardContent>
        </Card>

        {/* Default Provider */}
        <Card className="glass overflow-hidden border-border/20">
          <CardHeader className="bg-white/40 backdrop-blur-md border-b border-border/10">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-primary/10 rounded-2xl flex items-center justify-center shadow-inner">
                <Cpu className="text-primary" size={24} />
              </div>
              <div>
                <h3 className="text-lg font-bold text-foreground tracking-tight">Default Laboratory Provider</h3>
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-widest mt-0.5">Primary Cognitive Engine</p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-8">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {providers.map((provider) => (
                <button
                  key={provider.id}
                  onClick={() => setSettings({ ...settings, default_provider: provider.id })}
                  className={`p-5 rounded-2xl border-2 text-left transition-all duration-500 hover:scale-[1.02] ${
                    settings.default_provider === provider.id
                      ? 'border-primary bg-primary/5 shadow-lg shadow-primary/10'
                      : 'border-border/40 bg-white/20 hover:border-border hover:bg-white/40'
                  }`}
                >
                  <div className="font-bold text-foreground tracking-tight">{provider.name}</div>
                  <div className="text-xs font-medium text-muted-foreground mt-2 leading-relaxed">{provider.description}</div>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* OpenRouter */}
        <Card className="glass overflow-hidden border-border/10 shadow-lg">
          <CardHeader className="bg-white/40 backdrop-blur-md border-b border-border/10">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-tertiary/10 rounded-2xl flex items-center justify-center shadow-inner">
                  <Key className="text-tertiary" size={24} />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-foreground tracking-tight">OpenRouter Access</h3>
                  <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-[0.2em] mt-0.5">Multi-Model Gateway</p>
                </div>
              </div>
              <a
                href="https://openrouter.ai/keys"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:text-primary/70 flex items-center gap-2 text-xs font-bold uppercase tracking-wider transition-all duration-300 hover:translate-x-1"
              >
                Provision Key <ExternalLink size={14} />
              </a>
            </div>
          </CardHeader>
          <CardContent className="space-y-6 p-8">
            <Input
              label="API Key"
              type="password"
              placeholder="sk-or-..."
              value={settings.openrouter_api_key}
              onChange={(e) => setSettings({ ...settings, openrouter_api_key: e.target.value })}
            />
            <Input
              label="Default Research Model"
              placeholder="openai/gpt-4o"
              value={settings.openrouter_model}
              onChange={(e) => setSettings({ ...settings, openrouter_model: e.target.value })}
              helperText="Examples: openai/gpt-4o, anthropic/claude-3-sonnet, meta-llama/llama-3-70b"
            />
          </CardContent>
        </Card>

        {/* OpenAI */}
        <Card className="glass overflow-hidden border-border/10 shadow-lg">
          <CardHeader className="bg-white/40 backdrop-blur-md border-b border-border/10">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-success/10 rounded-2xl flex items-center justify-center shadow-inner">
                  <Key className="text-success" size={24} />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-foreground tracking-tight">OpenAI Direct</h3>
                  <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-[0.2em] mt-0.5">GPT-4o & Reasoning Models</p>
                </div>
              </div>
              <a
                href="https://platform.openai.com/api-keys"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:text-primary/70 flex items-center gap-2 text-xs font-bold uppercase tracking-wider transition-all duration-300 hover:translate-x-1"
              >
                Provision Key <ExternalLink size={14} />
              </a>
            </div>
          </CardHeader>
          <CardContent className="space-y-6 p-8">
            <Input
              label="API Key"
              type="password"
              placeholder="sk-..."
              value={settings.openai_api_key}
              onChange={(e) => setSettings({ ...settings, openai_api_key: e.target.value })}
            />
            <Input
              label="Default Research Model"
              placeholder="gpt-4o"
              value={settings.openai_model}
              onChange={(e) => setSettings({ ...settings, openai_model: e.target.value })}
            />
          </CardContent>
        </Card>

        {/* Anthropic */}
        <Card className="glass overflow-hidden border-border/10 shadow-lg">
          <CardHeader className="bg-white/40 backdrop-blur-md border-b border-border/10">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-warning/10 rounded-2xl flex items-center justify-center shadow-inner">
                  <Key className="text-warning" size={24} />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-foreground tracking-tight">Anthropic Laboratory</h3>
                  <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-[0.2em] mt-0.5">Claude Research Engine</p>
                </div>
              </div>
              <a
                href="https://console.anthropic.com/settings/keys"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:text-primary/70 flex items-center gap-2 text-xs font-bold uppercase tracking-wider transition-all duration-300 hover:translate-x-1"
              >
                Provision Key <ExternalLink size={14} />
              </a>
            </div>
          </CardHeader>
          <CardContent className="space-y-6 p-8">
            <Input
              label="API Key"
              type="password"
              placeholder="sk-ant-..."
              value={settings.anthropic_api_key}
              onChange={(e) => setSettings({ ...settings, anthropic_api_key: e.target.value })}
            />
            <Input
              label="Default Research Model"
              placeholder="claude-sonnet-4-20250514"
              value={settings.anthropic_model}
              onChange={(e) => setSettings({ ...settings, anthropic_model: e.target.value })}
            />
          </CardContent>
        </Card>

        {/* Local (Ollama) */}
        <Card className="glass overflow-hidden border-border/10 shadow-lg">
          <CardHeader className="bg-white/40 backdrop-blur-md border-b border-border/10">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-stone-100 dark:bg-stone-800 rounded-2xl flex items-center justify-center shadow-inner">
                <Cpu className="text-foreground" size={24} />
              </div>
              <div>
                <h3 className="text-lg font-bold text-foreground tracking-tight">Ollama / Local</h3>
                <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-[0.2em] mt-0.5">Run models locally via Ollama</p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-6 p-8">
            <Input
              label="Base URL"
              placeholder="http://localhost:11434"
              value={settings.local_base_url}
              onChange={(e) => setSettings({ ...settings, local_base_url: e.target.value })}
            />
            <Input
              label="Model"
              placeholder="llama3"
              value={settings.local_model}
              onChange={(e) => setSettings({ ...settings, local_model: e.target.value })}
            />
          </CardContent>
        </Card>

        {/* Llama.cpp */}
        <Card className="glass overflow-hidden border-border/10 shadow-lg">
          <CardHeader className="bg-white/40 backdrop-blur-md border-b border-border/10">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-tertiary/10 rounded-2xl flex items-center justify-center shadow-inner">
                <Cpu className="text-tertiary" size={24} />
              </div>
              <div>
                <h3 className="text-lg font-bold text-foreground tracking-tight">Llama.cpp (llama-server)</h3>
                <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-[0.2em] mt-0.5">Local models via llama-server HTTP API</p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-6 p-8">
            <Input
              label="Base URL"
              placeholder="http://localhost:8080"
              value={settings.llamacpp_base_url}
              onChange={(e) => setSettings({ ...settings, llamacpp_base_url: e.target.value })}
            />
            <Input
              label="Model Name"
              placeholder="local-model"
              value={settings.llamacpp_model}
              onChange={(e) => setSettings({ ...settings, llamacpp_model: e.target.value })}
            />
          </CardContent>
        </Card>

        {/* Note */}
        <Card className="bg-warning/5 border-warning/20">
          <CardContent>
            <div className="flex items-start gap-3">
              <AlertTriangle className="text-warning mt-0.5" size={20} />
              <div>
                <h4 className="font-medium text-warning/90">Important</h4>
                <p className="text-sm text-warning/80 mt-1">
                  API keys are stored in your browser's localStorage. For production use,
                  configure them as environment variables in the backend.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
