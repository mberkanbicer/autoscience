'use client';

import { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { authApi, setAuthSession } from '@/lib/api';
import { Loader2 } from 'lucide-react';

function AuthCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const code = searchParams.get('code');
    const state = searchParams.get('state');
    const provider = localStorage.getItem('oauth_provider');

    if (!code || !provider) {
      setError('Missing OAuth code or provider.');
      return;
    }

    (async () => {
      try {
        const response = await authApi.oauthCallback(provider, code, state || undefined);
        setAuthSession(response.access_token, response.user);
        localStorage.removeItem('oauth_provider');
        localStorage.removeItem('oauth_state');
        const returnTo = localStorage.getItem('oauth_return_to') || '/projects';
        localStorage.removeItem('oauth_return_to');
        router.replace(returnTo);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'OAuth sign-in failed');
      }
    })();
  }, [searchParams, router]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center p-8">
        <div className="text-center space-y-4">
          <h1 className="text-xl font-bold">Sign-in failed</h1>
          <p className="text-muted-foreground">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center">
      <Loader2 className="h-8 w-8 animate-spin text-primary" />
    </div>
  );
}

export default function AuthCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      }
    >
      <AuthCallbackContent />
    </Suspense>
  );
}