import type { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string;
  helper: string;
  icon: LucideIcon;
  accent?: string;
}

export default function MetricCard({ title, value, helper, icon: Icon, accent = '#2563EB' }: MetricCardProps) {
  return (
    <div className="group rounded-[1.7rem] bg-white p-5 shadow-card ring-1 ring-slate-200/80 transition hover:-translate-y-1 hover:shadow-glow">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-slatebrand/60">{title}</p>
          <p className="mt-3 text-3xl font-black tracking-tight text-deepnavy">{value}</p>
        </div>
        <div className="rounded-2xl p-3 text-white shadow-lg" style={{ backgroundColor: accent }}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
      <p className="mt-4 text-sm leading-6 text-slatebrand/65">{helper}</p>
    </div>
  );
}
