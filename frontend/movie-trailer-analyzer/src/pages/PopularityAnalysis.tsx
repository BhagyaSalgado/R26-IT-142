import { FormEvent, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import type { LucideIcon } from 'lucide-react';
import {
  Activity,
  AlertCircle,
  BarChart3,
  CheckCircle2,
  Clock3,
  Copy,
  Film,
  Gauge,
  Link2,
  Loader2,
  MessageSquareText,
  PlayCircle,
  RefreshCcw,
  Search,
  Sparkles,
  ThumbsUp,
  TrendingUp,
  WandSparkles
} from 'lucide-react';

import {
  analyzePopularityWithFuture,
  getApiBaseUrl,
  getFutureMetricsHistory,
  getPopularityHistory,
  type FutureMetricsHistoryRecord,
  type PopularityHistoryRecord
} from '../services/popularityService';

import type {
  FutureMetricsData,
  PopularityAnalysisData,
  PopularityCombinedResult,
  ReactionClass
} from '../types/popularity';

const horizonOptions = [7, 30];

function formatNumber(value?: number) {
  if (value === undefined || value === null || Number.isNaN(value)) return '0';
  return new Intl.NumberFormat('en', {
    notation: 'compact',
    maximumFractionDigits: 1
  }).format(value);
}

function formatFullNumber(value?: number) {
  if (value === undefined || value === null || Number.isNaN(value)) return '0';
  return new Intl.NumberFormat('en').format(value);
}

function formatPercent(value?: number, multiply = false) {
  if (value === undefined || value === null || Number.isNaN(value)) return '0%';
  const finalValue = multiply ? value * 100 : value;
  return `${finalValue.toFixed(finalValue >= 10 ? 1 : 2)}%`;
}

function formatDate(value?: string) {
  if (!value) return 'N/A';

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return value;

  return new Intl.DateTimeFormat('en', {
    year: 'numeric',
    month: 'short',
    day: '2-digit'
  }).format(date);
}

function reactionUi(reaction?: ReactionClass | string) {
  const key = String(reaction || '').toUpperCase();

  if (key.includes('HIGH')) {
    return {
      label: 'High Reaction',
      short: 'High',
      badge: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
      progress: 'from-emerald-500 to-teal-500',
      helper:
        'Strong audience response. The trailer shows strong popularity and engagement signals.'
    };
  }

  if (key.includes('LOW')) {
    return {
      label: 'Low Reaction',
      short: 'Low',
      badge: 'bg-rose-50 text-rose-700 ring-rose-200',
      progress: 'from-rose-500 to-pink-500',
      helper:
        'Weak audience response. The trailer may need better promotion, title, thumbnail, or timing.'
    };
  }

  return {
    label: 'Medium Reaction',
    short: 'Medium',
    badge: 'bg-amber-50 text-amber-700 ring-amber-200',
    progress: 'from-amber-500 to-orange-500',
    helper:
      'Moderate audience response. The trailer performs reasonably but can still be improved.'
  };
}

function safeJson(data: unknown) {
  try {
    return JSON.stringify(data, null, 2);
  } catch {
    return '';
  }
}

export default function PopularityAnalysis() {
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [horizonDays, setHorizonDays] = useState(7);
  const [customHorizon, setCustomHorizon] = useState('');
  const [includeFuturePrediction, setIncludeFuturePrediction] = useState(true);

  const [result, setResult] = useState<PopularityCombinedResult | null>(null);
  const [popularityHistory, setPopularityHistory] = useState<PopularityHistoryRecord[]>([]);
  const [futureHistory, setFutureHistory] = useState<FutureMetricsHistoryRecord[]>([]);

  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [error, setError] = useState('');
  const [showRawJson, setShowRawJson] = useState(false);
  const [copied, setCopied] = useState(false);

  const selectedHorizon = useMemo(() => {
    const customValue = Number(customHorizon);

    if (customHorizon && Number.isFinite(customValue) && customValue > 0) {
      return customValue;
    }

    return horizonDays;
  }, [customHorizon, horizonDays]);

  const handleAnalyze = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');
    setCopied(false);

    if (!youtubeUrl.trim()) {
      setError('Please enter a YouTube trailer URL or video ID.');
      return;
    }

    setIsAnalyzing(true);

    try {
      const response = await analyzePopularityWithFuture({
        youtubeUrl: youtubeUrl.trim(),
        horizonDays: selectedHorizon,
        includeFuturePrediction
      });

      setResult(response);
      setShowRawJson(false);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Something went wrong while analyzing the trailer.'
      );
    } finally {
      setIsAnalyzing(false);
    }
  };

  const loadHistory = async () => {
    setIsLoadingHistory(true);
    setError('');

    try {
      const [analysisRecords, futureRecords] = await Promise.all([
        getPopularityHistory(10),
        getFutureMetricsHistory(10)
      ]);

      setPopularityHistory(analysisRecords);
      setFutureHistory(futureRecords);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Could not load analysis history.'
      );
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const copyResult = async () => {
    if (!result) return;

    await navigator.clipboard.writeText(safeJson(result));
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2200);
  };

  return (
    <div className="space-y-8">
      {/* <HeroSection /> */}

      <section className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
        <form
          onSubmit={handleAnalyze}
          className="rounded-[2rem] bg-white p-6 shadow-card ring-1 ring-slate-200/80"
        >
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs font-black uppercase tracking-widest text-electric">
                Analyze trailer
              </p>
              <h2 className="mt-2 text-2xl font-black text-deepnavy">
                Popularity Analysis Input
              </h2>
              <p className="mt-2 text-sm leading-6 text-slatebrand/60">
                Paste a YouTube trailer URL. The page calls your FastAPI backend
                and returns audience reaction, popularity features and optional
                future metric prediction.
              </p>
            </div>

            <div className="rounded-2xl bg-lightbrand p-3 text-electric">
              <Link2 className="h-6 w-6" />
            </div>
          </div>

          <label className="mt-6 block">
            <span className="text-sm font-black text-deepnavy">
              YouTube URL or video ID
            </span>

            <div className="mt-2 flex items-center gap-3 rounded-2xl border border-slate-200 bg-lightbrand px-4 py-3 focus-within:border-electric focus-within:ring-4 focus-within:ring-electric/10">
              <Search className="h-5 w-5 text-slatebrand/40" />
              <input
                value={youtubeUrl}
                onChange={(event) => setYoutubeUrl(event.target.value)}
                placeholder="https://www.youtube.com/watch?v=KrLj6nc516A"
                className="w-full bg-transparent text-sm font-semibold text-deepnavy outline-none placeholder:text-slatebrand/35"
              />
            </div>
          </label>

          <div className="mt-6">
            <div className="mb-3 flex items-center justify-between gap-3">
              <span className="text-sm font-black text-deepnavy">
                Future prediction option
              </span>

              <label className="flex cursor-pointer items-center gap-2 text-xs font-bold text-slatebrand/60">
                <input
                  type="checkbox"
                  checked={includeFuturePrediction}
                  onChange={(event) =>
                    setIncludeFuturePrediction(event.target.checked)
                  }
                  className="h-4 w-4 rounded border-slate-300 text-electric"
                />
                Include forecast
              </label>
            </div>

            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {horizonOptions.map((days) => (
                <button
                  key={days}
                  type="button"
                  onClick={() => {
                    setHorizonDays(days);
                    setCustomHorizon('');
                  }}
                  className={`rounded-2xl px-4 py-3 text-sm font-black ring-1 transition ${
                    !customHorizon && horizonDays === days
                      ? 'bg-deepnavy text-white ring-deepnavy'
                      : 'bg-lightbrand text-slatebrand/70 ring-slate-200 hover:bg-slate-100'
                  }`}
                >
                  Next {days} days
                </button>
              ))}

              <input
                value={customHorizon}
                onChange={(event) =>
                  setCustomHorizon(event.target.value.replace(/[^\d]/g, ''))
                }
                placeholder="More days"
                className="col-span-2 rounded-2xl border border-slate-200 bg-lightbrand px-4 py-3 text-sm font-black text-deepnavy outline-none focus:border-electric focus:ring-4 focus:ring-electric/10"
              />
            </div>

            <p className="mt-2 text-xs font-semibold text-slatebrand/45">
              Use 7 or 30 days if those are the only trained model files in the
              backend.
            </p>
          </div>

          {error && (
            <div className="mt-5 flex items-start gap-3 rounded-2xl bg-rose-50 p-4 text-sm font-semibold text-rose-700 ring-1 ring-rose-100">
              <AlertCircle className="mt-0.5 h-5 w-5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="mt-6 grid gap-3 sm:grid-cols-[1fr_auto]">
            <button
              type="submit"
              disabled={isAnalyzing}
              className="inline-flex items-center justify-center gap-2 rounded-2xl bg-electric px-5 py-4 text-sm font-black text-white shadow-lg shadow-blue-600/20 transition hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-70"
            >
              {isAnalyzing ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <WandSparkles className="h-5 w-5" />
              )}
              {isAnalyzing ? 'Analyzing...' : 'Run Analysis'}
            </button>

            <button
              type="button"
              onClick={loadHistory}
              disabled={isLoadingHistory}
              className="inline-flex items-center justify-center gap-2 rounded-2xl bg-lightbrand px-5 py-4 text-sm font-black text-deepnavy ring-1 ring-slate-200 transition hover:bg-slate-100 disabled:opacity-70"
            >
              {isLoadingHistory ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <RefreshCcw className="h-5 w-5" />
              )}
              Load history
            </button>
          </div>
        </form>

        <ConnectionPanel result={result} />
      </section>

      {result && (
        <>
          <ResultSummary analysis={result.analysis} future={result.future} />

          <section className="grid gap-6 lg:grid-cols-2">
            <ReactionPanel analysis={result.analysis} />
            {result.future && <FuturePanel future={result.future} />}
          </section>

          <TrailerDetailsPanel analysis={result.analysis} />

          <section className="rounded-[2rem] bg-white p-6 shadow-card ring-1 ring-slate-200/80">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-xs font-black uppercase tracking-widest text-electric">
                  Developer output
                </p>
                <h2 className="mt-2 text-2xl font-black text-deepnavy">
                  Raw backend response
                </h2>
              </div>

              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => setShowRawJson((value) => !value)}
                  className="rounded-2xl bg-lightbrand px-4 py-2 text-sm font-black text-deepnavy ring-1 ring-slate-200"
                >
                  {showRawJson ? 'Hide JSON' : 'Show JSON'}
                </button>

                <button
                  type="button"
                  onClick={copyResult}
                  className="inline-flex items-center gap-2 rounded-2xl bg-deepnavy px-4 py-2 text-sm font-black text-white"
                >
                  <Copy className="h-4 w-4" />
                  {copied ? 'Copied' : 'Copy'}
                </button>
              </div>
            </div>

            {showRawJson && (
              <pre className="mt-5 max-h-[520px] overflow-auto rounded-2xl bg-slate-950 p-5 text-xs leading-6 text-slate-100">
                {safeJson(result)}
              </pre>
            )}
          </section>
        </>
      )}

      {(popularityHistory.length > 0 || futureHistory.length > 0) && (
        <HistoryPanel
          popularityHistory={popularityHistory}
          futureHistory={futureHistory}
        />
      )}
    </div>
  );
}

function HeroSection() {
  return (
    <section className="relative overflow-hidden rounded-[2.5rem] bg-deepnavy p-6 text-white shadow-glow sm:p-8 lg:p-10">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_15%_10%,rgba(37,99,235,0.38),transparent_30%),radial-gradient(circle_at_85%_18%,rgba(225,29,250,0.24),transparent_28%),linear-gradient(135deg,rgba(255,255,255,0.08),transparent)]" />

      <div className="relative grid gap-8 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45 }}
        >
          <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/10 px-4 py-2 text-sm font-black text-white/85">
            <Sparkles className="h-4 w-4 text-tealbrand" />
            POPULARITY METRICS ANALYSIS
          </div>

          <h1 className="max-w-4xl text-4xl font-black tracking-tight sm:text-5xl lg:text-6xl">
            Predict trailer reaction and future engagement.
          </h1>

          <p className="mt-5 max-w-2xl text-base leading-8 text-white/72">
            Analyze YouTube trailer metrics, classify audience reaction and
            forecast future views, likes and comments using your FastAPI ML
            backend.
          </p>

          <div className="mt-7 flex flex-wrap gap-3 text-sm font-bold">
            <span className="inline-flex items-center gap-2 rounded-2xl bg-white/10 px-4 py-3 ring-1 ring-white/10">
              <Gauge className="h-4 w-4 text-tealbrand" />
              Reaction model
            </span>

            <span className="inline-flex items-center gap-2 rounded-2xl bg-white/10 px-4 py-3 ring-1 ring-white/10">
              <TrendingUp className="h-4 w-4 text-tealbrand" />
              Future forecast
            </span>

            <span className="inline-flex items-center gap-2 rounded-2xl bg-white/10 px-4 py-3 ring-1 ring-white/10">
              <Film className="h-4 w-4 text-tealbrand" />
              Trailer insights
            </span>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.45 }}
          className="rounded-[2rem] bg-white/95 p-5 text-deepnavy shadow-2xl"
        >
          <div className="flex items-center gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50 text-electric">
              <PlayCircle className="h-7 w-7" />
            </div>

            <div>
              <p className="text-xs font-black uppercase tracking-widest text-slatebrand/50">
                Connected API
              </p>
              <p className="mt-1 break-all text-sm font-black">
                {getApiBaseUrl()}
              </p>
            </div>
          </div>

          <div className="mt-5 grid gap-3 sm:grid-cols-3">
            <HeroMini label="Input" value="YouTube URL" />
            <HeroMini label="Reaction" value="Low / Med / High" />
            <HeroMini label="Forecast" value="7D / 30D" />
          </div>
        </motion.div>
      </div>
    </section>
  );
}

function HeroMini({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-lightbrand p-3">
      <p className="text-xs font-bold text-slatebrand/45">{label}</p>
      <p className="mt-1 text-sm font-black text-deepnavy">{value}</p>
    </div>
  );
}

function ConnectionPanel({ result }: { result: PopularityCombinedResult | null }) {
  return (
    <div className="rounded-[2rem] bg-white p-6 shadow-card ring-1 ring-slate-200/80">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-black uppercase tracking-widest text-electric">
            Backend status
          </p>
          <h2 className="mt-2 text-2xl font-black text-deepnavy">
            End-user API flow
          </h2>
          <p className="mt-2 text-sm leading-6 text-slatebrand/60">
            This page only calls user-facing APIs: analysis, future prediction
            and history.
          </p>
        </div>

        <div className="rounded-2xl bg-emerald-50 p-3 text-emerald-600">
          <Activity className="h-6 w-6" />
        </div>
      </div>

      <div className="mt-6 grid gap-3">
        <StatusRow
          label="Reaction analysis"
          value={result ? 'Completed' : 'Waiting'}
          ok={Boolean(result)}
        />

        <StatusRow
          label="Future forecast"
          value={result?.future ? 'Completed' : 'Optional'}
          ok={Boolean(result?.future)}
        />

        <StatusRow
          label="Latest metrics source"
          value={result?.analysis.metrics.source || 'No result yet'}
          ok={Boolean(result)}
        />
      </div>

      {/* <div className="mt-5 rounded-2xl bg-lightbrand p-4">
        <p className="text-xs font-black uppercase tracking-widest text-slatebrand/45">
          Used endpoints
        </p>
        <div className="mt-3 space-y-2 text-xs font-bold text-slatebrand/70">
          <p>POST /api/v1/analyze</p>
          <p>POST /api/v1/future-metrics/predict</p>
          <p>GET /api/v1/history</p>
          <p>GET /api/v1/future-metrics/history</p>
        </div>
      </div> */}
    </div>
  );
}

function StatusRow({
  label,
  value,
  ok
}: {
  label: string;
  value: string;
  ok: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-2xl bg-lightbrand px-4 py-3">
      <span className="text-sm font-bold text-slatebrand/60">{label}</span>

      <span
        className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-black ring-1 ${
          ok
            ? 'bg-emerald-50 text-emerald-700 ring-emerald-200'
            : 'bg-slate-100 text-slate-500 ring-slate-200'
        }`}
      >
        {ok ? (
          <CheckCircle2 className="h-3.5 w-3.5" />
        ) : (
          <Clock3 className="h-3.5 w-3.5" />
        )}
        {value}
      </span>
    </div>
  );
}

function ResultSummary({
  analysis,
  future
}: {
  analysis: PopularityAnalysisData;
  future?: FutureMetricsData;
}) {
  const reaction = reactionUi(analysis.prediction.predicted_reaction);

  return (
    <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <MetricTile
        title="Predicted reaction"
        value={reaction.short}
        helper={`${formatPercent(
          analysis.prediction.confidence_score,
          true
        )} confidence`}
        icon={Gauge}
      />

      <MetricTile
        title="Current views"
        value={formatNumber(analysis.metrics.view_count)}
        helper={`${formatNumber(analysis.metrics.like_count)} likes • ${formatNumber(
          analysis.metrics.comment_count
        )} comments`}
        icon={BarChart3}
      />

      <MetricTile
        title="Popularity score"
        value={analysis.features.popularity_score.toFixed(1)}
        helper={`${formatPercent(
          analysis.features.engagement_rate,
          true
        )} engagement rate`}
        icon={Activity}
      />

      <MetricTile
        title={`Future views${
          future ? ` (${future.future_prediction.horizon_days}D)` : ''
        }`}
        value={
          future
            ? formatNumber(future.future_prediction.predicted_views)
            : 'Disabled'
        }
        helper={
          future
            ? `${future.future_prediction.expected_view_growth_percent.toFixed(
                1
              )}% expected growth`
            : 'Enable future forecast'
        }
        icon={TrendingUp}
      />
    </section>
  );
}

function MetricTile({
  title,
  value,
  helper,
  icon: Icon
}: {
  title: string;
  value: string;
  helper: string;
  icon: LucideIcon;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-[2rem] bg-white p-5 shadow-card ring-1 ring-slate-200/80"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-black text-slatebrand/50">{title}</p>
          <p className="mt-3 text-3xl font-black text-deepnavy">{value}</p>
          <p className="mt-2 text-sm font-semibold text-slatebrand/55">
            {helper}
          </p>
        </div>

        <div className="rounded-2xl bg-blue-50 p-3 text-electric">
          <Icon className="h-6 w-6" />
        </div>
      </div>
    </motion.div>
  );
}

function ReactionPanel({ analysis }: { analysis: PopularityAnalysisData }) {
  const reaction = reactionUi(analysis.prediction.predicted_reaction);
  const probabilities = Object.entries(analysis.prediction.probabilities || {});

  return (
    <div className="rounded-[2rem] bg-white p-6 shadow-card ring-1 ring-slate-200/80">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-black uppercase tracking-widest text-electric">
            Audience reaction model
          </p>

          <h2 className="mt-2 text-2xl font-black text-deepnavy">
            {reaction.label}
          </h2>

          <p className="mt-2 text-sm leading-6 text-slatebrand/60">
            {reaction.helper}
          </p>
        </div>

        <span
          className={`rounded-full px-4 py-2 text-sm font-black ring-1 ${reaction.badge}`}
        >
          {formatPercent(analysis.prediction.confidence_score, true)} confidence
        </span>
      </div>

      <div className="mt-6 space-y-4">
        {probabilities.map(([label, value]) => (
          <div key={label}>
            <div className="mb-2 flex items-center justify-between text-sm font-black">
              <span className="text-slatebrand/60">
                {label.replace(/_/g, ' ')}
              </span>
              <span className="text-deepnavy">
                {formatPercent(value, true)}
              </span>
            </div>

            <div className="h-3 overflow-hidden rounded-full bg-lightbrand">
              <div
                className={`h-full rounded-full bg-gradient-to-r ${
                  reactionUi(label).progress
                }`}
                style={{
                  width: `${Math.min(100, Math.max(0, value * 100))}%`
                }}
              />
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 rounded-2xl bg-lightbrand p-4">
        <p className="text-xs font-black uppercase tracking-widest text-slatebrand/45">
          Recommendation
        </p>

        <p className="mt-2 text-sm font-semibold leading-6 text-slatebrand/70">
          {analysis.prediction.recommendation ||
            'No recommendation returned by backend.'}
        </p>
      </div>
    </div>
  );
}

function FuturePanel({ future }: { future: FutureMetricsData }) {
  const prediction = future.future_prediction;

  return (
    <div className="rounded-[2rem] bg-white p-6 shadow-card ring-1 ring-slate-200/80">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-black uppercase tracking-widest text-electric">
            Future metrics model
          </p>

          <h2 className="mt-2 text-2xl font-black text-deepnavy">
            Next {prediction.horizon_days} days forecast
          </h2>

          <p className="mt-2 text-sm leading-6 text-slatebrand/60">
            Forecasted future views, likes, comments and engagement rate.
          </p>
        </div>

        <span className="rounded-full bg-blue-50 px-4 py-2 text-sm font-black text-electric ring-1 ring-blue-100">
          {prediction.model_version}
        </span>
      </div>

      <div className="mt-6 grid gap-3 sm:grid-cols-3">
        <FutureMetric
          icon={TrendingUp}
          label="Views"
          current={prediction.current_views}
          predicted={prediction.predicted_views}
          growth={prediction.expected_view_growth_percent}
        />

        <FutureMetric
          icon={ThumbsUp}
          label="Likes"
          current={prediction.current_likes}
          predicted={prediction.predicted_likes}
          growth={prediction.expected_like_growth_percent}
        />

        <FutureMetric
          icon={MessageSquareText}
          label="Comments"
          current={prediction.current_comment_count}
          predicted={prediction.predicted_comment_count}
          growth={prediction.expected_comment_growth_percent}
        />
      </div>

      <div className="mt-5 rounded-2xl bg-lightbrand p-4">
        <div className="flex items-center justify-between gap-4">
          <span className="text-sm font-black text-slatebrand/60">
            Predicted engagement rate
          </span>

          <span className="text-xl font-black text-deepnavy">
            {formatPercent(prediction.predicted_engagement_rate, true)}
          </span>
        </div>
      </div>
    </div>
  );
}

function FutureMetric({
  icon: Icon,
  label,
  current,
  predicted,
  growth
}: {
  icon: LucideIcon;
  label: string;
  current: number;
  predicted: number;
  growth: number;
}) {
  const isPositive = growth >= 0;

  return (
    <div className="rounded-2xl bg-lightbrand p-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-black text-slatebrand/50">{label}</p>
        <Icon className="h-5 w-5 text-electric" />
      </div>

      <p className="mt-3 text-2xl font-black text-deepnavy">
        {formatNumber(predicted)}
      </p>

      <p className="mt-1 text-xs font-semibold text-slatebrand/50">
        Current: {formatFullNumber(current)}
      </p>

      <span
        className={`mt-3 inline-flex rounded-full px-3 py-1 text-xs font-black ring-1 ${
          isPositive
            ? 'bg-emerald-50 text-emerald-700 ring-emerald-200'
            : 'bg-rose-50 text-rose-700 ring-rose-200'
        }`}
      >
        {isPositive ? '+' : ''}
        {growth.toFixed(1)}%
      </span>
    </div>
  );
}

function TrailerDetailsPanel({ analysis }: { analysis: PopularityAnalysisData }) {
  return (
    <section className="rounded-[2rem] bg-white p-6 shadow-card ring-1 ring-slate-200/80">
      <div className="flex flex-wrap items-start justify-between gap-5">
        <div className="flex gap-4">
          {analysis.trailer.thumbnail_url && (
            <img
              src={analysis.trailer.thumbnail_url}
              alt={analysis.trailer.title}
              className="h-24 w-36 rounded-2xl object-cover ring-1 ring-slate-200"
            />
          )}

          <div>
            <p className="text-xs font-black uppercase tracking-widest text-electric">
              Trailer details
            </p>

            <h2 className="mt-2 max-w-2xl text-2xl font-black text-deepnavy">
              {analysis.trailer.title}
            </h2>

            <p className="mt-2 text-sm font-semibold text-slatebrand/60">
              {analysis.trailer.channel_name} • Published{' '}
              {formatDate(analysis.trailer.published_at)}
            </p>
          </div>
        </div>

        <a
          href={analysis.trailer.youtube_url}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-2 rounded-2xl bg-deepnavy px-4 py-3 text-sm font-black text-white"
        >
          <Film className="h-4 w-4" />
          Open trailer
        </a>
      </div>

      <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <SmallFeature label="Like ratio" value={formatPercent(analysis.features.like_ratio, true)} />
        <SmallFeature label="Comment rate" value={formatPercent(analysis.features.comment_rate, true)} />
        <SmallFeature label="Views per day" value={formatFullNumber(Math.round(analysis.features.views_per_day))} />
        <SmallFeature label="Video age" value={`${analysis.features.video_age_days} days`} />
      </div>
    </section>
  );
}

function SmallFeature({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-lightbrand p-4">
      <p className="text-xs font-black uppercase tracking-widest text-slatebrand/40">
        {label}
      </p>
      <p className="mt-2 text-lg font-black text-deepnavy">{value}</p>
    </div>
  );
}

function HistoryPanel({
  popularityHistory,
  futureHistory
}: {
  popularityHistory: PopularityHistoryRecord[];
  futureHistory: FutureMetricsHistoryRecord[];
}) {
  return (
    <section className="grid gap-6 lg:grid-cols-2">
      <div className="rounded-[2rem] bg-white p-6 shadow-card ring-1 ring-slate-200/80">
        <p className="text-xs font-black uppercase tracking-widest text-electric">
          Analysis history
        </p>

        <h2 className="mt-2 text-2xl font-black text-deepnavy">
          Recent reaction predictions
        </h2>

        <div className="mt-5 space-y-3">
          {popularityHistory.slice(0, 6).map((item, index) => {
            const reaction = reactionUi(String(item.predicted_reaction || ''));

            return (
              <div
                key={String(item.id || item.video_id || index)}
                className="rounded-2xl bg-lightbrand p-4"
              >
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="font-black text-deepnavy">
                      {String(item.title || item.video_id || 'Untitled trailer')}
                    </p>
                    <p className="mt-1 text-xs font-semibold text-slatebrand/50">
                      {formatDate(String(item.created_at || ''))}
                    </p>
                  </div>

                  <span
                    className={`rounded-full px-3 py-1 text-xs font-black ring-1 ${reaction.badge}`}
                  >
                    {reaction.short}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="rounded-[2rem] bg-white p-6 shadow-card ring-1 ring-slate-200/80">
        <p className="text-xs font-black uppercase tracking-widest text-electric">
          Forecast history
        </p>

        <h2 className="mt-2 text-2xl font-black text-deepnavy">
          Recent future predictions
        </h2>

        <div className="mt-5 space-y-3">
          {futureHistory.slice(0, 6).map((item, index) => (
            <div
              key={String(item.id || item.video_id || index)}
              className="rounded-2xl bg-lightbrand p-4"
            >
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="font-black text-deepnavy">
                    {String(item.title || item.video_id || 'Untitled trailer')}
                  </p>

                  <p className="mt-1 text-xs font-semibold text-slatebrand/50">
                    Next {Number(item.horizon_days || 0)} days •{' '}
                    {formatDate(String(item.created_at || ''))}
                  </p>
                </div>

                <div className="text-right">
                  <p className="text-sm font-black text-deepnavy">
                    {formatNumber(Number(item.predicted_views || 0))}
                  </p>

                  <p className="text-xs font-bold text-emerald-600">
                    {Number(item.expected_view_growth_percent || 0).toFixed(1)}%
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}