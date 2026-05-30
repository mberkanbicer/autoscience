'use client';

import { useState, useEffect } from 'react';
import { Layout } from '@/components/layout/Layout';
import { Header } from '@/components/layout/Header';
import { Card, CardContent, CardHeader } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input, Textarea } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { Settings, Key, Cpu, Save, ExternalLink, AlertTriangle } from 'lucide-react';

interface ApiSettings {
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

const defaultSettings: ApiSettings = {
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

export default function SettingsPage() {
  const [settings, setSettings] = useState<ApiSettings>(defaultSettings);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    // Load from localStorage
    const saved = localStorage.getItem('autoscience_api_settings');
    if (saved) {
      setSettings({ ...defaultSettings, ...JSON.parse(saved) });
    }
  }, []);

  const handleSave = () => {
    setSaving(true);
    try {
      localStorage.setItem('autoscience_api_settings', JSON.stringify(settings));
      setSaved(true);
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

      <div className="p-6 space-y-6 max-w-4xl">
        {/* Default Provider */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
                <Cpu className="text-blue-600" size={20} />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Default Provider</h3>
                <p className="text-sm text-gray-500">Select which provider to use by default</p>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {providers.map((provider) => (
                <button
                  key={provider.id}
                  onClick={() => setSettings({ ...settings, default_provider: provider.id })}
                  className={`p-4 rounded-xl border-2 text-left transition-all ${
                    settings.default_provider === provider.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="font-medium text-gray-900">{provider.name}</div>
                  <div className="text-sm text-gray-500 mt-1">{provider.description}</div>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* OpenRouter */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center">
                  <Key className="text-purple-600" size={20} />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">OpenRouter</h3>
                  <p className="text-sm text-gray-500">Access Claude, GPT-4o, Gemini, Llama, and more</p>
                </div>
              </div>
              <a
                href="https://openrouter.ai/keys"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-700 flex items-center gap-1 text-sm"
              >
                Get API Key <ExternalLink size={14} />
              </a>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input
              label="API Key"
              type="password"
              placeholder="sk-or-..."
              value={settings.openrouter_api_key}
              onChange={(e) => setSettings({ ...settings, openrouter_api_key: e.target.value })}
            />
            <Input
              label="Default Model"
              placeholder="openai/gpt-4o"
              value={settings.openrouter_model}
              onChange={(e) => setSettings({ ...settings, openrouter_model: e.target.value })}
              helperText="Examples: openai/gpt-4o, anthropic/claude-3-sonnet, meta-llama/llama-3-70b"
            />
          </CardContent>
        </Card>

        {/* OpenAI */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-green-100 rounded-xl flex items-center justify-center">
                  <Key className="text-green-600" size={20} />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">OpenAI</h3>
                  <p className="text-sm text-gray-500">GPT-4o, GPT-4o-mini, o3</p>
                </div>
              </div>
              <a
                href="https://platform.openai.com/api-keys"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-700 flex items-center gap-1 text-sm"
              >
                Get API Key <ExternalLink size={14} />
              </a>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input
              label="API Key"
              type="password"
              placeholder="sk-..."
              value={settings.openai_api_key}
              onChange={(e) => setSettings({ ...settings, openai_api_key: e.target.value })}
            />
            <Input
              label="Default Model"
              placeholder="gpt-4o"
              value={settings.openai_model}
              onChange={(e) => setSettings({ ...settings, openai_model: e.target.value })}
            />
          </CardContent>
        </Card>

        {/* Anthropic */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-orange-100 rounded-xl flex items-center justify-center">
                  <Key className="text-orange-600" size={20} />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Anthropic</h3>
                  <p className="text-sm text-gray-500">Claude 3.5 Sonnet, Claude 3 Opus</p>
                </div>
              </div>
              <a
                href="https://console.anthropic.com/settings/keys"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-700 flex items-center gap-1 text-sm"
              >
                Get API Key <ExternalLink size={14} />
              </a>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input
              label="API Key"
              type="password"
              placeholder="sk-ant-..."
              value={settings.anthropic_api_key}
              onChange={(e) => setSettings({ ...settings, anthropic_api_key: e.target.value })}
            />
            <Input
              label="Default Model"
              placeholder="claude-sonnet-4-20250514"
              value={settings.anthropic_model}
              onChange={(e) => setSettings({ ...settings, anthropic_model: e.target.value })}
            />
          </CardContent>
        </Card>

        {/* Local (Ollama) */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gray-100 rounded-xl flex items-center justify-center">
                <Cpu className="text-gray-600" size={20} />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Ollama / Local</h3>
                <p className="text-sm text-gray-500">Run models locally via Ollama</p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
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
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-indigo-100 rounded-xl flex items-center justify-center">
                <Cpu className="text-indigo-600" size={20} />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Llama.cpp (llama-server)</h3>
                <p className="text-sm text-gray-500">Local models via llama-server HTTP API</p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
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
        <Card className="bg-yellow-50 border-yellow-200">
          <CardContent>
            <div className="flex items-start gap-3">
              <AlertTriangle className="text-yellow-600 mt-0.5" size={20} />
              <div>
                <h4 className="font-medium text-yellow-800">Important</h4>
                <p className="text-sm text-yellow-700 mt-1">
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
