import type { ReactNode } from 'react';
import type { LucideIcon } from 'lucide-react';
import DashboardMetricTile from './DashboardMetricTile';

export interface DashboardSectionTile {
  label: string;
  value: string;
  helper: string;
  accent: string;
}

interface DashboardSectionShellProps {
  icon: LucideIcon;
  iconTextClass: string;
  eyebrow: string;
  title: string;
  timestamp?: string | null;
  isLoading: boolean;
  error: string;
  hasData: boolean;
  emptyText: string;
  trailerLabel?: string;
  trailerTitle?: string;
  statusBadge?: string;
  statusBadgeClass?: string;
  tiles?: DashboardSectionTile[];
  children?: ReactNode;
}

export default function DashboardSectionShell({
  icon: Icon,
  iconTextClass,
  eyebrow,
  title,
  timestamp,
  isLoading,
  error,
  hasData,
  emptyText,
  trailerLabel = 'Most recent trailer',
  trailerTitle,
  statusBadge,
  statusBadgeClass = 'bg-electric/10 text-electric ring-1 ring-electric/15',
  tiles = [],
  children
}: DashboardSectionShellProps) {
  return (
    <section className="overflow-hidden rounded-[2rem] border border-slate-200 bg-white shadow-card">
      <div className="flex flex-col gap-4 px-6 py-5 text-white bg-deepnavy sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4">
          <div className={`flex items-center justify-center w-12 h-12 rounded-2xl bg-white/10 ring-1 ring-white/10 ${iconTextClass}`}>
            <Icon className="w-6 h-6" />
          </div>
          <div>
            <p className={`text-[10px] font-black uppercase tracking-[0.2em] ${iconTextClass}`}>{eyebrow}</p>
            <h2 className="mt-1 text-xl font-black sm:text-2xl">{title}</h2>
          </div>
        </div>
        {!isLoading && timestamp && <p className="text-xs font-semibold text-white/45">{timestamp}</p>}
      </div>

      <div className="p-6">
        {isLoading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[1, 2, 3, 4].map((item) => <div key={item} className="h-28 animate-pulse rounded-2xl bg-slate-100" />)}
          </div>
        ) : error ? (
          <div className="px-5 py-4 text-sm font-bold rounded-2xl bg-rose-50 text-rose-700 ring-1 ring-rose-200">{error}</div>
        ) : !hasData ? (
          <div className="px-5 py-8 text-sm font-semibold text-center border border-dashed rounded-2xl border-slate-200 bg-lightbrand/50 text-slatebrand/50">
            {emptyText}
          </div>
        ) : (
          <div>
            {trailerTitle && (
              <div className="flex flex-col gap-3 pb-5 border-b border-slate-100 sm:flex-row sm:items-center sm:justify-between">
                <div className="min-w-0">
                  <p className="text-xs font-black uppercase tracking-[0.16em] text-electric">{trailerLabel}</p>
                  <h3 className="mt-1 text-xl font-black truncate text-deepnavy" title={trailerTitle}>{trailerTitle}</h3>
                </div>
                {statusBadge && (
                  <span className={`px-4 py-2 text-xs font-black rounded-full w-fit ${statusBadgeClass}`}>{statusBadge}</span>
                )}
              </div>
            )}

            {tiles.length > 0 && (
              <div className="grid gap-4 mt-5 sm:grid-cols-2 lg:grid-cols-4">
                {tiles.map((tile) => (
                  <DashboardMetricTile key={tile.label} label={tile.label} value={tile.value} helper={tile.helper} accent={tile.accent} />
                ))}
              </div>
            )}

            {children}
          </div>
        )}
      </div>
    </section>
  );
}
