import { useEffect, useState } from 'react';
import { Lightbulb } from 'lucide-react';
import DashboardSectionShell from './DashboardSectionShell';
import { RecommendationPriorityChart } from '../Charts';
import {
  getLatestRecommendationGuidance,
  type RecommendationGuidance
} from '../../services/recommendationApi';
import { formatLocalDateTime } from '../../utils/format';

const componentBars: Array<{ key: keyof RecommendationGuidance['componentScores']; label: string; color: string }> = [
  { key: 'audio', label: 'Audio extraction', color: '#2563EB' },
  { key: 'visual', label: 'Visual detection', color: '#06B6D4' },
  { key: 'metadata', label: 'Metadata analysis', color: '#7C3AED' },
  { key: 'fusion', label: 'Emotional fusion', color: '#E11DFA' }
];

export default function RecommendationOverviewSection() {
  const [guidance, setGuidance] = useState<RecommendationGuidance | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;

    const load = async () => {
      setIsLoading(true);
      setError('');
      try {
        const data = await getLatestRecommendationGuidance();
        if (active) setGuidance(data);
      } catch (requestError) {
        if (active) {
          setError(
            requestError instanceof Error
              ? requestError.message
              : 'Unable to load the latest recommendation guidance.'
          );
        }
      } finally {
        if (active) setIsLoading(false);
      }
    };

    void load();
    return () => {
      active = false;
    };
  }, []);

  const hasData = Boolean(guidance && guidance.recommendations.length > 0);

  return (
    <DashboardSectionShell
      icon={Lightbulb}
      iconTextClass="text-electric"
      eyebrow="Saved activity · Recommendation engine"
      title="Latest recommendation guidance"
      timestamp={guidance ? formatLocalDateTime(guidance.generatedAt) : null}
      isLoading={isLoading}
      error={error}
      hasData={hasData}
      emptyText="Complete a trailer analysis to show recommendation guidance on the dashboard."
      trailerTitle={guidance?.trailerTitle}
      statusBadge={guidance ? `Genre: ${guidance.dominantGenre || 'Unclassified'}${guidance.secondaryGenre ? ` / ${guidance.secondaryGenre}` : ''}` : undefined}
      tiles={
        guidance
          ? [
              { label: 'Priority index', value: `${guidance.overallPriorityScore}/100`, helper: 'Overall priority', accent: 'bg-electric/10 text-electric' },
              { label: 'Model confidence', value: `${guidance.modelConfidence}%`, helper: 'Random Forest validation', accent: 'bg-purplebrand/10 text-purplebrand' },
              { label: 'Estimated impact', value: `${guidance.targetAudienceReach}%`, helper: 'Audience retention lift', accent: 'bg-tealbrand/10 text-tealbrand' },
              { label: 'Focus area', value: guidance.focusArea, helper: 'Primary calibration target', accent: 'bg-magentabrand/10 text-magentabrand' }
            ]
          : []
      }
    >
      {guidance && guidance.recommendations.length > 0 && (
        <div className="grid gap-6 mt-6 lg:grid-cols-2">
          <div className="rounded-3xl border border-slate-200 bg-lightbrand/40 p-5">
            <div className="mb-4">
              <p className="text-xs font-black uppercase tracking-[0.18em] text-electric">Priority breakdown</p>
              <h3 className="mt-1 text-lg font-black text-deepnavy">Scene priority &amp; impact</h3>
            </div>
            <RecommendationPriorityChart recommendations={guidance.recommendations} />
          </div>

          <div className="rounded-3xl border border-slate-200 bg-lightbrand/40 p-5">
            <div className="mb-4">
              <p className="text-xs font-black uppercase tracking-[0.18em] text-purplebrand">Component confidence</p>
              <h3 className="mt-1 text-lg font-black text-deepnavy">AI pipeline breakdown</h3>
            </div>
            <div className="flex flex-col justify-center h-64 space-y-4">
              {componentBars.map((bar) => {
                const value = guidance.componentScores[bar.key] ?? 0;
                return (
                  <div key={bar.key}>
                    <div className="flex justify-between text-xs font-bold">
                      <span className="text-slatebrand/70">{bar.label}</span>
                      <span style={{ color: bar.color }}>{value}%</span>
                    </div>
                    <div className="mt-1.5 h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
                      <div className="h-full rounded-full" style={{ width: `${value}%`, backgroundColor: bar.color }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </DashboardSectionShell>
  );
}
