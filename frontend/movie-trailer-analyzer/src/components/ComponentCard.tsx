import { ArrowRight, CheckCircle2 } from 'lucide-react';
import type { ComponentSummary } from '../types';

interface ComponentCardProps {
  component: ComponentSummary;
}

export default function ComponentCard({ component }: ComponentCardProps) {
  return (
    <article className="rounded-[1.8rem] bg-white p-6 shadow-card ring-1 ring-slate-200/80 transition hover:-translate-y-1 hover:shadow-glow">
      <div className="flex gap-4 justify-between items-start">
        <div>
          <p
            className="text-xs font-black uppercase tracking-[0.22em]"
            style={{ color: component.accent }}
          >
            {component.owner}
          </p>

          <h3 className="mt-2 text-xl font-black text-deepnavy">
            {component.name}
          </h3>
        </div>

        <div
          className="p-3 text-white rounded-2xl"
          style={{ backgroundColor: component.accent }}
        >
          <CheckCircle2 className="w-5 h-5" />
        </div>
      </div>

      <p className="mt-4 text-sm leading-6 min-h-20 text-slatebrand/70">
        {component.purpose}
      </p>

      <div className="p-4 mt-5 rounded-2xl bg-lightbrand">
        <div className="flex justify-between mb-2 text-xs font-bold tracking-wider uppercase text-slatebrand/60">
          <span>Frontend simulation</span>
          <span>{component.progress}%</span>
        </div>

        <div className="overflow-hidden h-2 bg-white rounded-full">
          <div
            className="h-full rounded-full"
            style={{
              width: `${component.progress}%`,
              backgroundColor: component.accent
            }}
          />
        </div>
      </div>

      <div className="mt-5 space-y-2">
        {component.outputs.map((output) => (
          <div
            key={output}
            className="flex gap-2 items-center text-sm font-semibold text-slatebrand/70"
          >
            <span
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: component.accent }}
            />
            {output}
          </div>
        ))}
      </div>

      <div className="flex justify-between items-center px-4 py-3 mt-5 rounded-2xl border border-slate-200">
        <span className="text-xs font-semibold text-slatebrand/60">
          {component.endpoint}
        </span>

        <ArrowRight className="w-4 h-4 text-electric" />
      </div>
    </article>
  );
}