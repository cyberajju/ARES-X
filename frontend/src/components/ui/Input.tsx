'use client';

import { InputHTMLAttributes } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: React.ReactNode;
}

export default function Input({
  label,
  error,
  icon,
  className = '',
  ...props
}: InputProps) {
  return (
    <div className="w-full">
      {label && (
        <label className="block text-xs text-text-secondary uppercase tracking-wider mb-1.5 font-mono">
          {label}
        </label>
      )}
      <div className="relative">
        {icon && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted">
            {icon}
          </div>
        )}
        <input
          className={`
            w-full bg-elevated border rounded-tactical px-3 py-2
            text-sm text-text-primary font-mono
            placeholder:text-text-muted
            focus:outline-none focus:border-accent-cyan focus:shadow-glow-cyan
            transition-all duration-200
            ${icon ? 'pl-10' : ''}
            ${error ? 'border-threat-red' : 'border-border-subtle'}
            ${className}
          `}
          {...props}
        />
      </div>
      {error && (
        <p className="mt-1 text-xs text-threat-red font-mono">{error}</p>
      )}
    </div>
  );
}
