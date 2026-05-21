'use client';

import { useState } from 'react';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import { login, verifyMfa } from '@/lib/auth';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [mfaCode, setMfaCode] = useState('');
  const [showMfa, setShowMfa] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    if (!showMfa) {
      // Call the auth API for credential validation
      if (email && password) {
        try {
          const result = await login(email, password);
          if (result.success) {
            window.location.href = '/dashboard';
          } else if (result.mfaRequired) {
            setShowMfa(true);
          } else {
            setError('Invalid credentials. Access denied.');
          }
        } catch {
          setError('Authentication service unavailable.');
        }
      } else {
        setError('All fields are required');
      }
      setIsLoading(false);
    } else {
      // MFA verification via API
      if (mfaCode.length === 6) {
        try {
          const success = await verifyMfa(mfaCode);
          if (success) {
            window.location.href = '/dashboard';
          } else {
            setError('Invalid MFA code. Verification failed.');
            setIsLoading(false);
          }
        } catch {
          setError('MFA verification service unavailable.');
          setIsLoading(false);
        }
      } else {
        setError('Invalid MFA code. Enter 6 digits.');
        setIsLoading(false);
      }
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-xl font-mono text-text-primary tracking-wider">
          CLASSIFIED ACCESS
        </h2>
        <div className="mt-2 h-px bg-gradient-to-r from-transparent via-accent-cyan to-transparent" />
      </div>

      {/* Login Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="bg-surface border border-border-subtle rounded-tactical p-6 space-y-4 hud-border">
          {!showMfa ? (
            <>
              <Input
                label="OPERATOR ID"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="operator@ares-x.mil"
                autoComplete="email"
              />
              <Input
                label="ACCESS KEY"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter secure passphrase"
                autoComplete="current-password"
              />
            </>
          ) : (
            <Input
              label="MFA VERIFICATION CODE"
              type="text"
              value={mfaCode}
              onChange={(e) => setMfaCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
              placeholder="000000"
              maxLength={6}
              className="text-center text-2xl tracking-[0.5em] font-mono"
            />
          )}

          {error && (
            <p className="text-threat-red text-sm font-mono">{error}</p>
          )}

          <Button
            type="submit"
            variant="primary"
            size="lg"
            isLoading={isLoading}
            className="w-full mt-4"
          >
            {showMfa ? 'VERIFY ACCESS' : 'ACCESS SYSTEM'}
          </Button>
        </div>
      </form>

      {/* Security Footer */}
      <div className="text-center space-y-2">
        <div className="h-px bg-gradient-to-r from-transparent via-border-subtle to-transparent" />
        <p className="text-text-muted text-xs font-mono tracking-wider">
          SECURITY LEVEL: MAXIMUM
        </p>
        <p className="text-text-muted text-xs opacity-50">
          Unauthorized access will be logged and reported
        </p>
      </div>
    </div>
  );
}
