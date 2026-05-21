'use client';

import { useState } from 'react';
import type { ColumnDef } from '@/lib/types';

interface TableProps<T> {
  columns: ColumnDef<T>[];
  data: T[];
  emptyMessage?: string;
}

export default function Table<T extends { id: string }>({
  columns,
  data,
  emptyMessage = 'No data available',
}: TableProps<T>) {
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');

  const handleSort = (accessor: string) => {
    if (sortColumn === accessor) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(accessor);
      setSortDir('asc');
    }
  };

  const sortedData = [...data].sort((a, b) => {
    if (!sortColumn) return 0;
    const aVal = String((a as Record<string, unknown>)[sortColumn] ?? '');
    const bVal = String((b as Record<string, unknown>)[sortColumn] ?? '');
    const cmp = aVal.localeCompare(bVal);
    return sortDir === 'asc' ? cmp : -cmp;
  });

  if (data.length === 0) {
    return (
      <div className="bg-surface border border-border-subtle rounded-tactical p-8 text-center">
        <p className="text-text-muted font-mono">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="bg-surface border border-border-subtle rounded-tactical overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border-subtle bg-elevated/50">
              {columns.map((col) => (
                <th
                  key={col.accessor}
                  onClick={() => handleSort(col.accessor)}
                  className="px-4 py-3 text-left text-xs font-mono font-medium text-text-muted uppercase tracking-wider cursor-pointer hover:text-text-primary transition-colors"
                >
                  <div className="flex items-center gap-1">
                    {col.header}
                    {sortColumn === col.accessor && (
                      <span className="text-accent-cyan">
                        {sortDir === 'asc' ? '\u2191' : '\u2193'}
                      </span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sortedData.map((row, idx) => (
              <tr
                key={row.id}
                className={`
                  border-b border-border-subtle/50 transition-colors
                  hover:bg-elevated/30
                  ${idx % 2 === 0 ? 'bg-transparent' : 'bg-elevated/10'}
                `}
              >
                {columns.map((col) => (
                  <td key={col.accessor} className="px-4 py-3 text-sm">
                    {col.render
                      ? col.render((row as Record<string, unknown>)[col.accessor], row)
                      : String((row as Record<string, unknown>)[col.accessor] ?? '')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
