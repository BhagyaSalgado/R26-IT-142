import { useEffect, useState } from 'react';
import { TrendingUp } from 'lucide-react';
import DashboardSectionShell from './DashboardSectionShell';
import { PopularityGrowthChart, PopularityGrowthPercentChart } from '../Charts';
import {
  getFutureMetricsHistory,
  getPopularityHistory,
  type FutureMetricsHistoryRecord,
  type PopularityHistoryRecord
} from '../../services/popularityService';
import { formatCompactNumber, formatLocalDateTime } from '../../utils/format';

type AnyRecord = Record<string, unknown>;

function pick(record: AnyRecord | null | undefined, keys: string[], fallback = 0): number {
  if (!record) return fallback;
  for (const key of keys) {
    const value = record[key];
    if (typeof value === 'number' && Number.isFinite(value)) return value;
  }
  return fallback;
}

function toReactionLabel(value: string | undefined) {
  const normalized = (value || '').toUpperCase();
  if (normalized.includes('HIGH')) return 'High Reaction';
  if (normalized.includes('LOW')) return 'Low Reaction';
  if (normalized.includes('MEDIUM') || normalized.includes('MODERATE')) return 'Medium Reaction';
  return 'Reaction Pending';
}

export default function PopularityOverviewSection() {
  const [record, setRecord] = useState<(FutureMetricsHistoryRecord & AnyRecord) | (PopularityHistoryRecord & AnyRecord) | null>(null);
  const [hasFutureMetrics, setHasFutureMetrics] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;

    const load = async () => {
      setIsLoading(true);
      setError('');
      try {
        const future = await getFutureMetricsHistory(1);
        if (!active) return;

        if (future.length > 0) {
          setRecord(future[0]);
          setHasFutureMetrics(true);
          return;
        }

        const basic = await getPopularityHistory(1);
        if (!active) return;
        setRecord(basic[0] || null);
        setHasFutureMetrics(false);
      } catch (requestError) {
        if (active) {
          setError(
            requestError instanceof Error
              ? requestError.message
              : 'Unable to load the latest popularity analysis.'
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

  const hasData = Boolean(record);

  const confidenceRaw = pick(record, ['confidence_score']);
  const confidence = confidenceRaw > 1 ? confidenceRaw : confidenceRaw * 100;
  const engagementRateRaw = pick(record, ['predicted_engagement_rate', 'engagement_rate']);
  const engagementRate = engagementRateRaw > 1 ? engagementRateRaw : engagementRateRaw * 100;
  const popularityScore = pick(record, ['popularity_score']);
  const currentViews = pick(record, ['current_views', 'views', 'view_count']);

  const growthData = [
    {
      name: 'Views',
      current: pick(record, ['current_views', 'views', 'view_count']),
      predicted: pick(record, ['predicted_views'])
    },
    {
      name: 'Likes',
      current: pick(record, ['current_likes', 'likes', 'like_count']),
      predicted: pick(record, ['predicted_likes'])
    },
    {
      name: 'Comments',
      current: pick(record, ['current_comment_count', 'comment_count']),
      predicted: pick(record, ['predicted_comment_count'])
    }
  ];

  const growthPercentData = [
    { name: 'Views', value: pick(record, ['expected_view_growth_percent']) },
    { name: 'Likes', value: pick(record, ['expected_like_growth_percent']) },
    { name: 'Comments', value: pick(record, ['expected_comment_growth_percent']) }
  ];

  return (
    <DashboardSectionShell
      icon={TrendingUp}
      iconTextClass="text-purplebrand"
      eyebrow="Saved activity · Popularity engine"
      title="Latest popularity analysis"
      timestamp={record ? formatLocalDateTime((record as AnyRecord).created_at as string) : null}
      isLoading={isLoading}
      error={error}
      hasData={hasData}
      emptyText="Run a popularity analysis to show audience reaction forecasts on the dashboard."
      trailerTitle={record ? String((record as AnyRecord).title || (record as AnyRecord).video_id || 'Untitled trailer') : undefined}
      statusBadge={record ? `${toReactionLabel((record as AnyRecord).predicted_reaction as string)} · ${confidence.toFixed(0)}% confidence` : undefined}
      statusBadgeClass="bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200"
      tiles={
        record
          ? [
              { label: 'Views', value: formatCompactNumber(currentViews), helper: 'Current view count', accent: 'bg-electric/10 text-electric' },
              { label: 'Engagement rate', value: `${engagementRate.toFixed(1)}%`, helper: 'Likes + comments / views', accent: 'bg-purplebrand/10 text-purplebrand' },
              { label: 'Model confidence', value: `${confidence.toFixed(0)}%`, helper: 'Prediction certainty', accent: 'bg-tealbrand/10 text-tealbrand' },
              { label: 'Popularity score', value: popularityScore.toFixed(2), helper: 'Composite model score', accent: 'bg-magentabrand/10 text-magentabrand' }
            ]
          : []
      }
    >
      {record && (
        <div className="grid gap-6 mt-6 lg:grid-cols-2">
          <div className="rounded-3xl border border-slate-200 bg-lightbrand/40 p-5">
            <div className="mb-4">
              <p className="text-xs font-black uppercase tracking-[0.18em] text-purplebrand">Growth forecast</p>
              <h3 className="mt-1 text-lg font-black text-deepnavy">Current vs. predicted</h3>
            </div>
            {hasFutureMetrics ? (
              <PopularityGrowthChart data={growthData} />
            ) : (
              <div className="flex items-center justify-center h-64 text-xs font-semibold text-center text-slatebrand/45">
                No future-metrics prediction saved for this trailer yet.
              </div>
            )}
          </div>

          <div className="rounded-3xl border border-slate-200 bg-lightbrand/40 p-5">
            <div className="mb-4">
              <p className="text-xs font-black uppercase tracking-[0.18em] text-magentabrand">Predicted growth</p>
              <h3 className="mt-1 text-lg font-black text-deepnavy">Expected change by horizon</h3>
            </div>
            {hasFutureMetrics ? (
              <PopularityGrowthPercentChart data={growthPercentData} />
            ) : (
              <div className="flex items-center justify-center h-64 text-xs font-semibold text-center text-slatebrand/45">
                No future-metrics prediction saved for this trailer yet.
              </div>
            )}
          </div>
        </div>
      )}
    </DashboardSectionShell>
  );
}
