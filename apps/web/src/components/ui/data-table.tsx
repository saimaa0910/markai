'use client';

import * as React from 'react';
import { cn } from '@eaimos/shared';
import { ChevronUp, ChevronDown, ChevronLeft, ChevronRight, Search } from 'lucide-react';
import { Input } from './input';
import { Button } from './button';

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────
export interface DataTableColumn<T> {
  key: keyof T | string;
  label: string;
  sortable?: boolean;
  width?: string;
  render?: (row: T) => React.ReactNode;
}

export interface DataTableProps<T extends Record<string, unknown>> {
  columns: DataTableColumn<T>[];
  data: T[];
  isLoading?: boolean;
  searchable?: boolean;
  searchPlaceholder?: string;
  pageSize?: number;
  emptyMessage?: string;
  emptyIcon?: React.ReactNode;
  className?: string;
  onRowClick?: (row: T) => void;
  actions?: (row: T) => React.ReactNode;
}

// ─────────────────────────────────────────────────────────────────────────────
// Skeleton Row
// ─────────────────────────────────────────────────────────────────────────────
function SkeletonRows({ cols, rows = 5 }: { cols: number; rows?: number }) {
  return (
    <>
      {Array.from({ length: rows }).map((_, ri) => (
        <tr key={ri}>
          {Array.from({ length: cols }).map((_, ci) => (
            <td key={ci} className="px-4 py-3">
              <div
                className="h-3.5 rounded bg-neutral-800 animate-pulse"
                style={{ width: `${60 + (ci * 17) % 30}%` }}
              />
            </td>
          ))}
        </tr>
      ))}
    </>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// DataTable Component
// ─────────────────────────────────────────────────────────────────────────────
export function DataTable<T extends Record<string, unknown>>({
  columns,
  data,
  isLoading = false,
  searchable = false,
  searchPlaceholder = 'Search...',
  pageSize = 10,
  emptyMessage = 'No records found.',
  emptyIcon,
  className,
  onRowClick,
  actions,
}: DataTableProps<T>) {
  const [search, setSearch] = React.useState('');
  const [sortKey, setSortKey] = React.useState<string | null>(null);
  const [sortDir, setSortDir] = React.useState<'asc' | 'desc'>('asc');
  const [page, setPage] = React.useState(1);

  // Filter
  const filtered = React.useMemo(() => {
    if (!search.trim()) return data;
    const q = search.toLowerCase();
    return data.filter((row) =>
      Object.values(row).some((v) => String(v ?? '').toLowerCase().includes(q))
    );
  }, [data, search]);

  // Sort
  const sorted = React.useMemo(() => {
    if (!sortKey) return filtered;
    return [...filtered].sort((a, b) => {
      const av = String(a[sortKey] ?? '');
      const bv = String(b[sortKey] ?? '');
      return sortDir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av);
    });
  }, [filtered, sortKey, sortDir]);

  // Paginate
  const totalPages = Math.max(1, Math.ceil(sorted.length / pageSize));
  const paginated = sorted.slice((page - 1) * pageSize, page * pageSize);

  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
    setPage(1);
  };

  React.useEffect(() => setPage(1), [search]);

  const colCount = columns.length + (actions ? 1 : 0);

  return (
    <div className={cn('flex flex-col gap-3', className)}>
      {searchable && (
        <div className="flex items-center gap-2">
          <Input
            placeholder={searchPlaceholder}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            leftIcon={<Search className="w-3.5 h-3.5" />}
            className="max-w-xs h-8 text-xs"
          />
          {search && (
            <span className="text-[11px] text-neutral-500">
              {filtered.length} result{filtered.length !== 1 ? 's' : ''}
            </span>
          )}
        </div>
      )}

      <div className="rounded-xl border border-white/5 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-white/5 bg-neutral-900/60">
                {columns.map((col) => (
                  <th
                    key={String(col.key)}
                    style={{ width: col.width }}
                    className={cn(
                      'px-4 py-2.5 text-left font-semibold text-neutral-400 uppercase tracking-wider text-[10px] select-none',
                      col.sortable && 'cursor-pointer hover:text-white transition-colors'
                    )}
                    onClick={() => col.sortable && handleSort(String(col.key))}
                  >
                    <div className="flex items-center gap-1">
                      {col.label}
                      {col.sortable && (
                        <span className="flex flex-col opacity-40">
                          {sortKey === col.key ? (
                            sortDir === 'asc' ? (
                              <ChevronUp className="w-3 h-3" />
                            ) : (
                              <ChevronDown className="w-3 h-3" />
                            )
                          ) : (
                            <ChevronUp className="w-3 h-3 -mb-1" />
                          )}
                        </span>
                      )}
                    </div>
                  </th>
                ))}
                {actions && (
                  <th className="px-4 py-2.5 text-right text-[10px] font-semibold text-neutral-400 uppercase tracking-wider">
                    Actions
                  </th>
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {isLoading ? (
                <SkeletonRows cols={colCount} />
              ) : paginated.length === 0 ? (
                <tr>
                  <td colSpan={colCount} className="px-4 py-12 text-center">
                    <div className="flex flex-col items-center gap-2 text-neutral-500">
                      {emptyIcon && <div className="opacity-30">{emptyIcon}</div>}
                      <span>{emptyMessage}</span>
                    </div>
                  </td>
                </tr>
              ) : (
                paginated.map((row, ri) => (
                  <tr
                    key={ri}
                    onClick={() => onRowClick?.(row)}
                    className={cn(
                      'transition-colors bg-neutral-950/20',
                      onRowClick && 'cursor-pointer hover:bg-white/3'
                    )}
                  >
                    {columns.map((col) => (
                      <td key={String(col.key)} className="px-4 py-3 text-neutral-300">
                        {col.render
                          ? col.render(row)
                          : String(row[col.key as keyof T] ?? '—')}
                      </td>
                    ))}
                    {actions && (
                      <td className="px-4 py-3 text-right">{actions(row)}</td>
                    )}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {!isLoading && sorted.length > pageSize && (
          <div className="flex items-center justify-between px-4 py-2 border-t border-white/5 bg-neutral-900/40">
            <span className="text-[11px] text-neutral-500">
              {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, sorted.length)} of{' '}
              {sorted.length}
            </span>
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="h-7 w-7 p-0"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
              </Button>
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                const pageNum = Math.max(1, Math.min(totalPages - 4, page - 2)) + i;
                return (
                  <button
                    key={pageNum}
                    onClick={() => setPage(pageNum)}
                    className={cn(
                      'h-7 w-7 rounded text-[11px] font-semibold transition-colors cursor-pointer',
                      page === pageNum
                        ? 'bg-violet-600 text-white'
                        : 'text-neutral-400 hover:text-white hover:bg-white/5'
                    )}
                  >
                    {pageNum}
                  </button>
                );
              })}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="h-7 w-7 p-0"
              >
                <ChevronRight className="w-3.5 h-3.5" />
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
