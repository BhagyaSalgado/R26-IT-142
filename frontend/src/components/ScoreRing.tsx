interface ScoreRingProps {
  value: number;
  label: string;
  subLabel?: string;
}

export default function ScoreRing({ value, label, subLabel }: ScoreRingProps) {
  const radius = 52;
  const circumference = 2 * Math.PI * radius;
  const progress = circumference - (value / 100) * circumference;

  return (
    <div className="relative flex flex-col items-center justify-center rounded-[2rem] bg-deepnavy p-8 text-white shadow-glow overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(37,99,235,0.42),transparent_28%),radial-gradient(circle_at_80%_30%,rgba(225,29,250,0.28),transparent_30%)]" />
      <svg className="relative h-36 w-36 -rotate-90" viewBox="0 0 140 140" aria-label={`${label} score ${value}`}>
        <circle cx="70" cy="70" r={radius} fill="none" stroke="rgba(255,255,255,0.15)" strokeWidth="12" />
        <circle
          cx="70"
          cy="70"
          r={radius}
          fill="none"
          stroke="url(#ringGradient)"
          strokeLinecap="round"
          strokeWidth="12"
          strokeDasharray={circumference}
          strokeDashoffset={progress}
        />
        <defs>
          <linearGradient id="ringGradient" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#06B6D4" />
            <stop offset="52%" stopColor="#2563EB" />
            <stop offset="100%" stopColor="#E11DFA" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute top-[4.8rem] text-center">
        <p className="text-4xl font-black tracking-tight">{value}</p>
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-white/60">score</p>
      </div>
      <div className="relative mt-3 text-center">
        <p className="text-lg font-bold">{label}</p>
        {subLabel && <p className="mt-1 text-sm text-white/70">{subLabel}</p>}
      </div>
    </div>
  );
}
