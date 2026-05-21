'use client';

import { usePathname } from 'next/navigation';
import Link from 'next/link';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

interface NavItem {
  label: string;
  href: string;
  icon: string;
  disabled?: boolean;
}

const navItems: NavItem[] = [
  { label: 'Dashboard', href: '/dashboard', icon: '\u2593' },
  { label: 'Infrastructure Graph', href: '/graph', icon: '\u2726' },
  { label: 'Asset Inventory', href: '/assets', icon: '\u2750' },
  { label: 'Attack Paths', href: '/attack-paths', icon: '\u2192' },
  { label: 'Threat Intel', href: '/threat-intel', icon: '\u2620', disabled: true },
  { label: 'Reports', href: '/reports', icon: '\u2630', disabled: true },
];

export default function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const pathname = usePathname();

  return (
    <aside
      className={`
        flex flex-col h-full bg-surface border-r border-border-subtle
        transition-all duration-300
        ${collapsed ? 'w-16' : 'w-64'}
      `}
    >
      {/* Logo */}
      <div className="p-4 border-b border-border-subtle">
        <Link href="/dashboard" className="flex items-center gap-2">
          <span className="text-xl font-mono font-bold text-accent-cyan text-glow-cyan">
            {collapsed ? 'AX' : 'ARES-X'}
          </span>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-2 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = pathname === item.href || pathname?.startsWith(item.href + '/');
          return (
            <Link
              key={item.href}
              href={item.disabled ? '#' : item.href}
              className={`
                flex items-center gap-3 px-3 py-2.5 rounded-tactical
                text-sm font-medium transition-all duration-200
                ${item.disabled
                  ? 'opacity-40 cursor-not-allowed'
                  : isActive
                    ? 'bg-elevated text-accent-cyan border-l-2 border-accent-cyan'
                    : 'text-text-secondary hover:bg-elevated hover:text-text-primary'
                }
              `}
              onClick={item.disabled ? (e) => e.preventDefault() : undefined}
            >
              <span className="text-lg w-5 text-center">{item.icon}</span>
              {!collapsed && (
                <span className="truncate">{item.label}</span>
              )}
              {!collapsed && item.disabled && (
                <span className="ml-auto text-xs text-text-muted">Soon</span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* User Info */}
      {!collapsed && (
        <div className="p-3 border-t border-border-subtle">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-elevated border border-border-subtle flex items-center justify-center">
              <span className="text-xs font-mono text-accent-cyan">OP</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs text-text-primary truncate">Operator Alpha</p>
              <p className="text-xs text-text-muted">LEVEL 5 CLEARANCE</p>
            </div>
          </div>
        </div>
      )}

      {/* Classified Watermark */}
      {!collapsed && (
        <div className="px-4 py-2 text-center">
          <span className="text-xs font-mono text-text-muted/30 tracking-widest">
            CLASSIFIED
          </span>
        </div>
      )}

      {/* Collapse Toggle */}
      <button
        onClick={onToggle}
        className="p-3 border-t border-border-subtle text-text-muted hover:text-text-primary hover:bg-elevated transition-colors"
      >
        <span className="text-lg">{collapsed ? '\u00BB' : '\u00AB'}</span>
      </button>
    </aside>
  );
}
