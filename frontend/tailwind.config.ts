import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        abyss: '#0a0e17',
        surface: '#0f1623',
        elevated: '#1a2235',
        'border-subtle': '#1e3a5f',
        'border-active': '#2563eb',
        'text-primary': '#e2e8f0',
        'text-secondary': '#94a3b8',
        'text-muted': '#64748b',
        'accent-cyan': {
          DEFAULT: '#06b6d4',
          bright: '#22d3ee',
          dark: '#0891b2',
        },
        'accent-green': {
          DEFAULT: '#10b981',
          bright: '#34d399',
        },
        'threat-red': {
          DEFAULT: '#ef4444',
          bright: '#f87171',
        },
        'warning-amber': {
          DEFAULT: '#f59e0b',
          bright: '#fbbf24',
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
        'scan-line': 'scan-line 4s linear infinite',
        'radar-sweep': 'radar-sweep 3s linear infinite',
        'data-stream': 'data-stream 2s linear infinite',
        'threat-pulse': 'threat-pulse 1.5s ease-in-out infinite',
        'fade-in': 'fade-in 0.3s ease-out',
        'slide-up': 'slide-up 0.4s ease-out',
      },
      keyframes: {
        'pulse-glow': {
          '0%, 100%': { opacity: '1', boxShadow: '0 0 5px currentColor' },
          '50%': { opacity: '0.8', boxShadow: '0 0 20px currentColor, 0 0 40px currentColor' },
        },
        'scan-line': {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' },
        },
        'radar-sweep': {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
        'data-stream': {
          '0%': { backgroundPosition: '0% 0%' },
          '100%': { backgroundPosition: '0% 100%' },
        },
        'threat-pulse': {
          '0%, 100%': { transform: 'scale(1)', opacity: '1' },
          '50%': { transform: 'scale(1.2)', opacity: '0.7' },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'slide-up': {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      boxShadow: {
        'glow-cyan': '0 0 10px #06b6d4, 0 0 20px #06b6d440',
        'glow-green': '0 0 10px #10b981, 0 0 20px #10b98140',
        'glow-red': '0 0 10px #ef4444, 0 0 20px #ef444440',
        'glow-amber': '0 0 10px #f59e0b, 0 0 20px #f59e0b40',
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '100': '25rem',
        '128': '32rem',
      },
      borderRadius: {
        'tactical': '2px',
      },
    },
  },
  plugins: [],
};

export default config;
