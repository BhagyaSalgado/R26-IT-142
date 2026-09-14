interface DashboardMetricTileProps {
  label: string;
  value: string;
  helper: string;
  accent: string;
}

export default function DashboardMetricTile({ label, value, helper, accent }: DashboardMetricTileProps) {
  return (
    <div className="p-4 rounded-2xl bg-lightbrand/70 ring-1 ring-slate-200/70">
      <p className="text-[10px] font-black uppercase tracking-[0.15em] text-slatebrand/40">
        {label}
      </p>
      <div className={`mt-3 inline-flex max-w-full rounded-xl px-3 py-2 ${accent}`}>
        <span className="text-lg font-black truncate">{value}</span>
      </div>
      <p className="mt-2 text-xs font-semibold text-slatebrand/45">{helper}</p>
    </div>
  );
}
