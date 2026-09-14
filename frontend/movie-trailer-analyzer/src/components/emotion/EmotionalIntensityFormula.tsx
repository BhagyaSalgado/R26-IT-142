import { Activity, Box, Music2, ScanFace, Sigma } from 'lucide-react';

const signals = [
  {
    symbol: 'M',
    weight: '35%',
    title: 'Motion intensity',
    description: 'How fast and strongly things move in the scene.',
    icon: Activity,
    color: 'bg-electric/10 text-electric'
  },
  {
    symbol: 'A',
    weight: '30%',
    title: 'Audio energy',
    description: 'How loud, energetic and intense the soundtrack is.',
    icon: Music2,
    color: 'bg-tealbrand/10 text-tealbrand'
  },
  {
    symbol: 'O',
    weight: '20%',
    title: 'Object action score',
    description: 'Action-related objects such as explosions, vehicles or weapons.',
    icon: Box,
    color: 'bg-purplebrand/10 text-purplebrand'
  },
  {
    symbol: 'F',
    weight: '15%',
    title: 'Face emotion score',
    description: 'Detected actor emotions such as happiness, sadness or anger.',
    icon: ScanFace,
    color: 'bg-magentabrand/10 text-magentabrand'
  }
] as const;

export function EmotionalIntensityFormula() {
  return (
    <section className="overflow-hidden rounded-[2rem] border border-slate-200 bg-white shadow-card">
      <div className="flex flex-col gap-5 bg-deepnavy px-6 py-6 text-white sm:px-8 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-start gap-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-white/10 text-tealbrand ring-1 ring-white/10">
            <Sigma className="h-6 w-6" />
          </div>
          <div>
            <p className="text-xs font-black uppercase tracking-[0.22em] text-tealbrand">Fusion formula</p>
            <h2 className="mt-1 text-xl font-black sm:text-2xl">Emotional Intensity Score</h2>
          </div>
        </div>

        <div className="overflow-x-auto rounded-2xl border border-white/10 bg-white/10 px-5 py-4">
          <p className="min-w-max font-mono text-sm font-black text-white sm:text-base">
            EI = (0.35 × M) + (0.30 × A) + (0.20 × O) + (0.15 × F)
          </p>
        </div>
      </div>

      <div className="grid gap-4 p-6 sm:grid-cols-2 xl:grid-cols-4 sm:p-8">
        {signals.map(({ symbol, weight, title, description, icon: Icon, color }) => (
          <article key={symbol} className="rounded-3xl bg-lightbrand/70 p-5 ring-1 ring-slate-200/70">
            <div className="flex items-center justify-between gap-3">
              <div className={`flex h-11 w-11 items-center justify-center rounded-2xl ${color}`}>
                <Icon className="h-5 w-5" />
              </div>
              <span className="rounded-full bg-white px-3 py-1 text-xs font-black text-deepnavy shadow-sm">
                {weight} weight
              </span>
            </div>
            <h3 className="mt-4 font-black text-deepnavy">{symbol} · {title}</h3>
            <p className="mt-2 text-sm font-semibold leading-6 text-slatebrand/55">{description}</p>
          </article>
        ))}
      </div>
    </section>
  );
}