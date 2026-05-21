'use client';

import { ButtonHTMLAttributes } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

const variantStyles = {
  primary: 'bg-accent-cyan/10 border-accent-cyan text-accent-cyan hover:bg-accent-cyan/20 hover:shadow-glow-cyan',
  secondary: 'bg-elevated border-border-subtle text-text-primary hover:border-border-active hover:bg-surface',
  danger: 'bg-threat-red/10 border-threat-red text-threat-red hover:bg-threat-red/20 hover:shadow-glow-red',
  ghost: 'bg-transparent border-transparent text-text-secondary hover:text-text-primary hover:bg-elevated',
};

const sizeStyles = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base',
};

export default function Button({
  variant = 'primary',
  size = 'md',
  isLoading = false,
  disabled,
  className = '',
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={`
        inline-flex items-center justify-center gap-2
        border rounded-tactical font-mono font-medium
        tracking-wider uppercase
        transition-all duration-200
        disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:shadow-none
        ${variantStyles[variant]}
        ${sizeStyles[size]}
        ${className}
      `}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && (
        <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      )}
      {children}
    </button>
  );
}
