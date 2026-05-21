'use client';

import { usePathname } from 'next/navigation';
import StatusIndicator from '@/components/ui/StatusIndicator';

const routeLabels: Record<string, string> = {
  '/dashboard': 'Command Center',
  '/graph': 'Infrastructure Graph',
  '/assets': 'Asset Inventory',
  '/attack-paths': 'Attack Path Analysis',
};

export default function Header() {
  const pathname = usePathname();
  const currentLabel = routeLabels[pathname || ''] || 'ARES-X';

  return (
    <header className="h-14 border-b border-border-subtle bg-surface/80 backdrop-blur-sm flex items-center justify-between px-6 relative">
      {/* Breadcrumbs */}
      <div className="flex items-center gap-2">
        <span className="text-text-muted text-sm font-mono">ARES-X</span>
        <span className="text-text-muted">/</span>
        <span className="text-text-primary text-sm font-medium">{currentLabel}</span>
      </div>

      {/* Right Section */}
      <div className="flex items-center gap-6">
        {/* Global Search */}
        <div className="relative hidden md:block">
          <input
            type="text"
            placeholder="Search... (Ctrl+K)"
            className="bg-elevated border border-border-subtle rounded-tactical px-3 py-1.5 text-sm text-text-primary placeholder:text-text-muted w-56 focus:outline-none focus:border-accent-cyan transition-colors"
            readOnly
          />
        </div>

        {/* System Status */}
        <div className="flex items-center gap-2">
          <StatusIndicator status="online" size="sm" />
          <StatusIndicator status="online" size="sm" />
          <StatusIndicator status="degraded" size="sm" />
        </div>

        {/* Notifications */}
        <button className="relative text-text-secondary hover:text-text-primary transition-colors">
          <span className="text-lg">{'\u266A'}</span>
          <span className="absolute -top-1 -right-1 w-4 h-4 bg-threat-red rounded-full text-[10px] flex items-center justify-center text-white font-mono">
            3
          </span>
        </button>

        {/* User Avatar */}
        <div className="w-8 h-8 rounded-full bg-elevated border border-border-subtle flex items-center justify-center cursor-pointer hover:border-accent-cyan transition-colors">
          <span className="text-xs font-mono text-accent-cyan">OP</span>
        </div>
      </div>

      {/* Bottom accent line */}
      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-accent-cyan/30 to-transparent" />
    </header>
  );
}
