import { FormEvent, useEffect, useState } from 'react';
import {
  AlertCircle,
  Clock3,
  Languages,
  Link2,
  Loader2,
  MessageSquareText,
  RefreshCcw,
  Smile,
  Tags,
  WandSparkles
} from 'lucide-react';

import {
  CommentSentimentChart,
  EmotionRadarChart,
  RegionalBarChart,
  TopicBarChart
} from '../components/Charts';
import SectionTitle from '../components/SectionTitle';
import {
  analyzeCommentsFromUrl,
  getCachedCommentAnalysis,
  getCommentSentimentHistory
} from '../services/commentSentimentService';
import type { CommentSentimentData, CommentSentimentHistoryRecord } from '../types/commentSentiment';

export default function CommentSentimentAnalysis({
  initialResult,
  onAnalysisComplete
}: {
  initialResult?: CommentSentimentData | null;
  onAnalysisComplete?: (result: CommentSentimentData) => void;
}) {
  const [trailerUrl, setTrailerUrl] = useState('');
  const [trailerTitle, setTrailerTitle] = useState('');
  const [result, setResult] = useState<CommentSentimentData | null>(initialResult ?? null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState('');

  const [history, setHistory] = useState<CommentSentimentHistoryRecord[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [historyError, setHistoryError] = useState('');
  const [selectedTrailerId, setSelectedTrailerId] = useState<string | null>(null);
  const [selectedTrailerTitle, setSelectedTrailerTitle] = useState('');
  const [isLoadingSelected, setIsLoadingSelected] = useState(false);

  const loadHistory = async () => {
    setIsLoadingHistory(true);
    setHistoryError('');

    try {
      const records = await getCommentSentimentHistory(5);
      setHistory(records);
    } catch (err) {
      setHistoryError(
        err instanceof Error ? err.message : 'Could not load recent trailer history.'
      );
    } finally {
      setIsLoadingHistory(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const handleSelectHistoryItem = async (item: CommentSentimentHistoryRecord) => {
    if (!item.trailer_id) return;

    setError('');
    setSelectedTrailerId(item.trailer_id);
    setSelectedTrailerTitle(item.trailer_title || item.trailer_id);
    setIsLoadingSelected(true);

    try {
      const data = await getCachedCommentAnalysis(item.trailer_id);
      setResult(data);
      onAnalysisComplete?.(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Could not load the saved analysis for this trailer.'
      );
    } finally {
      setIsLoadingSelected(false);
    }
  };

  const handleAnalyze = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');

    if (!trailerUrl.trim()) {
      setError('Please enter a YouTube trailer URL.');
      return;
    }

    setIsAnalyzing(true);

    try {
      const data = await analyzeCommentsFromUrl(trailerUrl.trim(), trailerTitle.trim() || undefined);
      setResult(data);
      setSelectedTrailerId(null);
      if (!trailerTitle.trim() && data.trailerTitle) {
        setTrailerTitle(data.trailerTitle);
      }
      onAnalysisComplete?.(data);
      loadHistory();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Something went wrong while analyzing comments.'
      );
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="space-y-8">
      <section className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
        <form
          onSubmit={handleAnalyze}
          className="flex h-full flex-col rounded-[2rem] bg-white p-6 shadow-card ring-1 ring-slate-200/80"
        >
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0">
              <p className="text-[11px] font-black uppercase tracking-[0.18em] text-electric">
                Comment analysis
              </p>
              <h2 className="mt-2 text-[2rem] font-black leading-[1.1] text-deepnavy">
                Comment Sentiment Analysis Input
              </h2>
              <p className="mt-3 max-w-xl text-sm leading-6 text-slatebrand/60">
                Paste a YouTube trailer URL. Comments are fetched and run through
                language detection, sentiment, emotion and topic extraction models.
              </p>
            </div>

            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-lightbrand text-electric ring-1 ring-blue-100">
              <MessageSquareText className="h-6 w-6" />
            </div>
          </div>

          <label className="mt-6 block">
            <span className="text-sm font-black text-deepnavy">YouTube trailer URL</span>
            <div className="mt-2 flex items-center gap-3 rounded-2xl border border-slate-200 bg-lightbrand px-4 py-3 shadow-inner shadow-slate-200/40 focus-within:border-electric focus-within:ring-4 focus-within:ring-electric/10">
              <Link2 className="h-5 w-5 text-slatebrand/40" />
              <input
                value={trailerUrl}
                onChange={(event) => setTrailerUrl(event.target.value)}
                placeholder="https://www.youtube.com/watch?v=KrLj6nc516A"
                className="w-full bg-transparent text-sm font-semibold text-deepnavy outline-none placeholder:text-slatebrand/35"
              />
            </div>
          </label>

          <label className="mt-5 block">
            <span className="text-sm font-black text-deepnavy">Trailer title (auto-fetched)</span>
            <input
              value={trailerTitle}
              readOnly
              placeholder="Fetched automatically from YouTube after analysis"
              className="mt-2 w-full cursor-not-allowed rounded-2xl border border-slate-200 bg-lightbrand px-4 py-3 text-sm font-semibold text-deepnavy/70 outline-none"
            />
          </label>

          {error && (
            <div className="mt-5 flex items-start gap-3 rounded-2xl bg-rose-50 p-4 text-sm font-semibold text-rose-700 ring-1 ring-rose-100">
              <AlertCircle className="mt-0.5 h-5 w-5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <button
            type="submit"
            disabled={isAnalyzing}
            className="mt-6 inline-flex w-full min-h-[58px] items-center justify-center gap-2 whitespace-nowrap rounded-[1.1rem] bg-electric px-5 py-4 text-base font-black leading-none text-white shadow-[0_12px_30px_rgba(59,130,246,0.20)] transition hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {isAnalyzing ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <WandSparkles className="h-5 w-5" />
            )}
            <span className="translate-y-[0.5px]">{isAnalyzing ? 'Analyzing comments...' : 'Run Comment Analysis'}</span>
          </button>
        </form>

        <SentimentHistoryPanel
          history={history}
          isLoading={isLoadingHistory}
          error={historyError}
          onRefresh={loadHistory}
          selectedTrailerId={selectedTrailerId}
          isLoadingSelected={isLoadingSelected}
          onSelect={handleSelectHistoryItem}
        />
      </section>

      {!result && !isLoadingSelected && (
        <p className="rounded-2xl bg-lightbrand p-4 text-center text-sm font-semibold text-slatebrand/60">
          Run a new analysis or click a trailer above to view its charts.
        </p>
      )}

      {result && (
        <>
          {selectedTrailerId && (
            <div className="flex items-center gap-2 rounded-2xl bg-electric/10 p-4 text-sm font-bold text-electric">
              <Clock3 className="h-4 w-4" />
              Viewing saved analysis: {selectedTrailerTitle}
            </div>
          )}

          <section className="grid gap-6 lg:grid-cols-2">
            <div className="rounded-[2rem] bg-white p-6 shadow-card ring-1 ring-slate-200/80">
              <SectionTitle
                eyebrow="Sentiment chart"
                title="Positive vs neutral vs negative"
                description="Aggregated per-comment sentiment predictions."
              />
              <CommentSentimentChart sentiment={result.sentiment} />
            </div>

            <div className="rounded-[2rem] bg-white p-6 shadow-card ring-1 ring-slate-200/80">
              <SectionTitle
                eyebrow="Emotion chart"
                title="Deeper emotion distribution"
                description="Joy, excitement, anger, sadness, fear and surprise."
              />
              <EmotionRadarChart deeperEmotions={result.deeperEmotions} />
            </div>
          </section>

          <section className="grid gap-6 lg:grid-cols-2">
            <div className="rounded-[2rem] bg-white p-6 shadow-card ring-1 ring-slate-200/80">
              <SectionTitle
                eyebrow="Topic extraction"
                title="Most discussed topics"
                description="Frequency of topics mentioned across all comments."
              />
              <TopicBarChart commentTopics={result.commentTopics} />
            </div>

            <div className="rounded-[2rem] bg-white p-6 shadow-card ring-1 ring-slate-200/80">
              <SectionTitle
                eyebrow="Language & audience"
                title="Estimated audience by country"
                description="Estimated from detected comment language, not a direct signal."
              />
              <RegionalBarChart regionalInterest={result.regionalInterest} />
            </div>
          </section>

          <DetailedResultsTable result={result} />
          <AnalysisSummary result={result} />
        </>
      )}
    </div>
  );
}

const sentimentBadgeStyles: Record<string, string> = {
  Positive: 'bg-emerald-50 text-emerald-700 ring-emerald-100',
  Neutral: 'bg-amber-50 text-amber-700 ring-amber-100',
  Negative: 'bg-rose-50 text-rose-700 ring-rose-100'
};

function dominantHistorySentiment(sentiment?: { positive: number; neutral: number; negative: number }) {
  if (!sentiment) return 'Neutral';
  const entries = Object.entries(sentiment) as Array<[string, number]>;
  const [dominant] = entries.sort((a, b) => b[1] - a[1])[0] || ['neutral', 0];
  return dominant.charAt(0).toUpperCase() + dominant.slice(1);
}

function formatHistoryDate(value?: string) {
  if (!value) return 'N/A';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'N/A';
  return new Intl.DateTimeFormat('en', {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date);
}

function SentimentHistoryPanel({
  history,
  isLoading,
  error,
  onRefresh,
  selectedTrailerId,
  isLoadingSelected,
  onSelect
}: {
  history: CommentSentimentHistoryRecord[];
  isLoading: boolean;
  error: string;
  onRefresh: () => void;
  selectedTrailerId: string | null;
  isLoadingSelected: boolean;
  onSelect: (item: CommentSentimentHistoryRecord) => void;
}) {
  return (
    <section className="rounded-[2rem] bg-white p-6 shadow-card ring-1 ring-slate-200/80">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <SectionTitle
          eyebrow="Upload history"
          title="Recent 5 trailer analyses"
          description="Click a trailer to view its saved charts and results."
        />
        <button
          type="button"
          onClick={onRefresh}
          disabled={isLoading}
          className="inline-flex items-center gap-2 rounded-2xl bg-lightbrand px-4 py-3 text-sm font-black text-deepnavy ring-1 ring-slate-200 disabled:opacity-70"
        >
          {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCcw className="h-4 w-4" />}
          Refresh
        </button>
      </div>

      {error && (
        <div className="mt-5 flex items-start gap-3 rounded-2xl bg-rose-50 p-4 text-sm font-semibold text-rose-700 ring-1 ring-rose-100">
          <AlertCircle className="mt-0.5 h-5 w-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {!isLoading && !error && history.length === 0 && (
        <p className="mt-5 rounded-2xl bg-lightbrand p-4 text-sm font-semibold text-slatebrand/60">
          No trailers analyzed yet. Run an analysis above to see it here.
        </p>
      )}

      <div className="mt-5 space-y-3">
        {history.slice(0, 5).map((item, index) => {
          const dominant = dominantHistorySentiment(item.sentiment);
          const isSelected = Boolean(item.trailer_id) && item.trailer_id === selectedTrailerId;

          return (
            <button
              key={`${item.trailer_id}-${index}`}
              type="button"
              onClick={() => onSelect(item)}
              disabled={isLoadingSelected}
              className={`flex w-full flex-wrap items-center justify-between gap-3 rounded-2xl bg-lightbrand p-4 text-left transition hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-70 ${
                isSelected ? 'ring-2 ring-electric' : 'ring-1 ring-transparent'
              }`}
            >
              <div>
                <p className="font-black text-deepnavy">
                  {item.trailer_title || item.trailer_id || 'Untitled trailer'}
                </p>
                <p className="mt-1 flex items-center gap-1 text-xs font-semibold text-slatebrand/50">
                  <Clock3 className="h-3.5 w-3.5" />
                  {formatHistoryDate(item.timestamp)} • {item.totalComments ?? 0} comments
                </p>
              </div>
              <span className="flex items-center gap-2">
                {isSelected && isLoadingSelected && (
                  <Loader2 className="h-4 w-4 animate-spin text-electric" />
                )}
                <span
                  className={`w-fit rounded-full px-3 py-1 text-xs font-black ring-1 ${
                    sentimentBadgeStyles[dominant] || sentimentBadgeStyles.Neutral
                  }`}
                >
                  {dominant}
                </span>
              </span>
            </button>
          );
        })}
      </div>
    </section>
  );
}

function DetailedResultsTable({ result }: { result: CommentSentimentData }) {
  return (
    <section className="rounded-[2rem] bg-white p-6 shadow-card ring-1 ring-slate-200/80">
      <SectionTitle
        eyebrow="Per-comment output"
        title="Detailed comment predictions"
        description="Preview of individual comment predictions (up to 20 shown)."
      />

      <div className="mt-5 overflow-x-auto">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead>
            <tr className="text-xs font-black uppercase tracking-wider text-slatebrand/45">
              <th className="pb-3 pr-4">Comment</th>
              <th className="pb-3 pr-4">
                <span className="inline-flex items-center gap-1">
                  <Languages className="h-3.5 w-3.5" /> Language / Country
                </span>
              </th>
              <th className="pb-3 pr-4">Sentiment</th>
              <th className="pb-3 pr-4">
                <span className="inline-flex items-center gap-1">
                  <Smile className="h-3.5 w-3.5" /> Emotion
                </span>
              </th>
              <th className="pb-3">
                <span className="inline-flex items-center gap-1">
                  <Tags className="h-3.5 w-3.5" /> Topic
                </span>
              </th>
            </tr>
          </thead>
          <tbody>
            {result.detailedResults.map((item, index) => (
              <tr key={index} className="border-t border-slate-100">
                <td className="max-w-xs truncate py-3 pr-4 font-semibold text-deepnavy" title={item.text}>
                  {item.text}
                </td>
                <td className="py-3 pr-4 text-slatebrand/70">
                  {item.language || 'N/A'} / {item.country || 'N/A'}
                </td>
                <td className="py-3 pr-4">
                  <span className="rounded-full bg-lightbrand px-3 py-1 text-xs font-black text-deepnavy">
                    {item.sentiment}
                  </span>
                </td>
                <td className="py-3 pr-4 text-slatebrand/70">{item.emotion}</td>
                <td className="py-3 text-slatebrand/70">{item.topic}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function AnalysisSummary({ result }: { result: CommentSentimentData }) {
  const dominantSentiment = getDominantSentiment(result.sentiment);
  const topTopic = result.commentTopics[0];
  const topEmotion = getDominantEmotion(result.deeperEmotions);
  const positiveMinusNegative = result.sentiment.positive - result.sentiment.negative;

  return (
    <section className="rounded-[2rem] bg-white p-6 shadow-card ring-1 ring-slate-200/80">
      <SectionTitle
        eyebrow="Final summary"
        title="Comment sentiment summary"
        description="A concise recap of the uploaded trailer analysis."
      />

      <div className="mt-5 grid gap-4 lg:grid-cols-2">
        <div className="rounded-[1.5rem] bg-lightbrand p-5 ring-1 ring-slate-200/80">
          <div className="grid gap-3 sm:grid-cols-2">
            <SummaryStat label="Total comments" value={result.totalComments.toLocaleString()} />
            <SummaryStat label="Dominant sentiment" value={dominantSentiment} />
            <SummaryStat label="Top emotion" value={topEmotion} />
            <SummaryStat label="Top topic" value={topTopic ? topTopic.topic : 'N/A'} />
          </div>
        </div>

        <div className="rounded-[1.5rem] bg-deepnavy p-5 text-white ring-1 ring-slate-200/80">
          <p className="text-xs font-black uppercase tracking-widest text-tealbrand">Summary insight</p>
          <p className="mt-3 text-lg font-black">
            {dominantSentiment === 'Positive'
              ? 'Audience reaction is strongly positive and engagement looks healthy.'
              : dominantSentiment === 'Neutral'
                ? 'Audience reaction is balanced, with sentiment spread more evenly across comments.'
                : 'Audience reaction is leaning negative, so the trailer may need stronger positioning.'}
          </p>
          <ul className="mt-4 space-y-2 text-sm leading-6 text-white/80">
            <li>• Positive vs negative gap: {positiveMinusNegative}%</li>
            <li>• Most discussed topic: {topTopic ? `${topTopic.topic} (${topTopic.mentions})` : 'N/A'}</li>
            <li>• Strongest emotion signal: {topEmotion}</li>
          </ul>
        </div>
      </div>

      <div className="mt-5 grid gap-4 md:grid-cols-3">
        <SummaryInsight
          title="Key read"
          detail={`The trailer received ${dominantSentiment.toLowerCase()} response from the analyzed comments.`}
        />
        <SummaryInsight
          title="Discussion focus"
          detail={topTopic ? `Most comments mentioned ${topTopic.topic.toLowerCase()}.` : 'No topic data available.'}
        />
        <SummaryInsight
          title="Action hint"
          detail="Use this summary to compare audience reaction before publishing or promoting the trailer again."
        />
      </div>
    </section>
  );
}

function SummaryStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-white p-4 shadow-sm ring-1 ring-slate-200/80">
      <p className="text-xs font-black uppercase tracking-widest text-slatebrand/45">{label}</p>
      <p className="mt-2 text-xl font-black text-deepnavy">{value}</p>
    </div>
  );
}

function SummaryInsight({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="rounded-[1.5rem] bg-lightbrand p-4 ring-1 ring-slate-200/80">
      <p className="text-sm font-black text-deepnavy">{title}</p>
      <p className="mt-2 text-sm leading-6 text-slatebrand/65">{detail}</p>
    </div>
  );
}

function getDominantSentiment(sentiment: CommentSentimentData['sentiment']) {
  const entries = Object.entries(sentiment) as Array<[keyof CommentSentimentData['sentiment'], number]>;
  const [dominant] = entries.sort((a, b) => b[1] - a[1])[0] || ['neutral', 0];

  return dominant.charAt(0).toUpperCase() + dominant.slice(1);
}

function getDominantEmotion(deeperEmotions: CommentSentimentData['deeperEmotions']) {
  const entries = Object.entries(deeperEmotions) as Array<[keyof CommentSentimentData['deeperEmotions'], number]>;
  const [dominant] = entries.sort((a, b) => b[1] - a[1])[0] || ['excitement', 0];

  return dominant.charAt(0).toUpperCase() + dominant.slice(1);
}
