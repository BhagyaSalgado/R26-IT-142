import { useEffect, useState } from 'react';
import { MessageSquareText } from 'lucide-react';
import DashboardSectionShell from './DashboardSectionShell';
import { CommentSentimentChart, TopicBarChart } from '../Charts';
import {
  getCachedCommentAnalysis,
  getCommentSentimentHistory
} from '../../services/commentSentimentService';
import type { CommentSentimentSplit, CommentTopic } from '../../types/commentSentiment';
import { formatLocalDateTime } from '../../utils/format';

const legendItems: Array<[string, string]> = [
  ['Positive', '#2563EB'],
  ['Neutral', '#06B6D4'],
  ['Negative', '#E11DFA']
];

export default function SentimentOverviewSection() {
  const [trailerTitle, setTrailerTitle] = useState('');
  const [timestamp, setTimestamp] = useState<string | null>(null);
  const [sentiment, setSentiment] = useState<CommentSentimentSplit | null>(null);
  const [topics, setTopics] = useState<CommentTopic[]>([]);
  const [totalComments, setTotalComments] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;

    const load = async () => {
      setIsLoading(true);
      setError('');
      try {
        const history = await getCommentSentimentHistory(1);
        if (!active) return;

        const latest = history[0];
        if (!latest) {
          setSentiment(null);
          return;
        }

        setTrailerTitle(latest.trailer_title || latest.trailer_id);
        setTimestamp(latest.timestamp || null);
        setSentiment(latest.sentiment || null);
        setTotalComments(latest.totalComments || 0);

        try {
          const detail = await getCachedCommentAnalysis(latest.trailer_id);
          if (!active) return;
          setSentiment(detail.sentiment);
          setTopics(detail.commentTopics || []);
          setTotalComments(detail.totalComments ?? latest.totalComments ?? 0);
        } catch {
          // Summary sentiment split remains available when the detailed cache lookup fails.
        }
      } catch (requestError) {
        if (active) {
          setError(
            requestError instanceof Error
              ? requestError.message
              : 'Unable to load the latest comment sentiment analysis.'
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

  const hasData = Boolean(sentiment);

  return (
    <DashboardSectionShell
      icon={MessageSquareText}
      iconTextClass="text-magentabrand"
      eyebrow="Saved activity · Sentiment engine"
      title="Latest comment sentiment"
      timestamp={timestamp ? formatLocalDateTime(timestamp) : null}
      isLoading={isLoading}
      error={error}
      hasData={hasData}
      emptyText="Run a comment sentiment analysis to show audience reaction on the dashboard."
      trailerTitle={trailerTitle || undefined}
      statusBadge={`${new Intl.NumberFormat('en').format(totalComments)} comments analyzed`}
      statusBadgeClass="bg-magentabrand/10 text-magentabrand ring-1 ring-magentabrand/15"
      tiles={
        sentiment
          ? [
              { label: 'Positive', value: `${sentiment.positive}%`, helper: 'Share of comments', accent: 'bg-electric/10 text-electric' },
              { label: 'Neutral', value: `${sentiment.neutral}%`, helper: 'Share of comments', accent: 'bg-tealbrand/10 text-tealbrand' },
              { label: 'Negative', value: `${sentiment.negative}%`, helper: 'Share of comments', accent: 'bg-magentabrand/10 text-magentabrand' },
              { label: 'Total comments', value: new Intl.NumberFormat('en').format(totalComments), helper: 'Across all languages', accent: 'bg-purplebrand/10 text-purplebrand' }
            ]
          : []
      }
    >
      {sentiment && (
        <div className="grid gap-6 mt-6 lg:grid-cols-2">
          <div className="rounded-3xl border border-slate-200 bg-lightbrand/40 p-5">
            <div className="mb-4">
              <p className="text-xs font-black uppercase tracking-[0.18em] text-electric">Sentiment split</p>
              <h3 className="mt-1 text-lg font-black text-deepnavy">Positive vs. neutral vs. negative</h3>
            </div>
            <CommentSentimentChart sentiment={sentiment} />
            <div className="flex flex-wrap justify-center gap-3 mt-2">
              {legendItems.map(([label, color]) => (
                <div key={label} className="flex items-center gap-2 px-3 py-1 text-xs font-bold rounded-full bg-lightbrand text-slatebrand/70">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} />
                  {label}
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-lightbrand/40 p-5">
            <div className="mb-4">
              <p className="text-xs font-black uppercase tracking-[0.18em] text-magentabrand">Top topics</p>
              <h3 className="mt-1 text-lg font-black text-deepnavy">Most discussed themes</h3>
            </div>
            {topics.length > 0 ? (
              <TopicBarChart commentTopics={topics} />
            ) : (
              <div className="flex items-center justify-center h-72 text-xs font-semibold text-center text-slatebrand/45">
                Topic breakdown unavailable for this saved analysis.
              </div>
            )}
          </div>
        </div>
      )}
    </DashboardSectionShell>
  );
}
