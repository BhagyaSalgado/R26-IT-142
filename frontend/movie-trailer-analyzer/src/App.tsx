import { useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { motion } from 'framer-motion';
import {
  Activity,
  AlertCircle,
  BrainCircuit,
  CheckCircle2,
  Clock3,
  Gauge,
  Heart,
  Loader2,
  MessageSquareText,
  RefreshCcw,
  Sparkles,
  TrendingUp
} from 'lucide-react';

import { useAuth } from './auth/AuthContext';
import {
  EmotionAnalysisCharts,
  FeatureBarChart,
  SceneIntensityChart,
  SentimentChart
} from './components/Charts';
import RecommendationOverviewSection from './components/dashboard/RecommendationOverviewSection';
import PopularityOverviewSection from './components/dashboard/PopularityOverviewSection';
import SentimentOverviewSection from './components/dashboard/SentimentOverviewSection';
import Footer from './components/Footer';
import Header from './components/Header';
import MetricCard from './components/MetricCard';
import ScoreRing from './components/ScoreRing';
import SectionTitle from './components/SectionTitle';
import UploadPanel from './components/UploadPanel';
import AuthPage from './pages/AuthPage';
import CommentSentimentAnalysis from './pages/CommentSentimentAnalysis';
import EmotionAnalysisPage from './pages/EmotionAnalysisPage';
import PopularityAnalysis from './pages/PopularityAnalysis';
import RecommendationsPage from './components/RecommendationsPage';
import {
  getFutureMetricsHistory,
  getPopularityHistory,
  type FutureMetricsHistoryRecord,
  type PopularityHistoryRecord
} from './services/popularityService';
import {
  getEmotionHistory,
  getEmotionHistoryDetail,
  type EmotionHistoryDetail,
  type EmotionHistoryItem
} from './services/videoEmotionApi';
import type { AnalysisResult, ReactionLevel } from './types';

type ViewKey =
  | 'dashboard'
  | 'analyze'
  | 'emotion_analysis'
  | 'components'
  | 'history'
  | 'popularity'
  | 'sentiment'
  | 'recommendations'
  | 'login'
  | 'register';

const reactionStyles: Record<ReactionLevel, string> = {
  High: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  Moderate: 'bg-amber-50 text-amber-700 ring-amber-200',
  Low: 'bg-rose-50 text-rose-700 ring-rose-200'
};

function formatLocalDateTime(value: string | null | undefined) {
  if (!value) return 'Date unavailable';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Date unavailable';

  return new Intl.DateTimeFormat(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  }).format(date);
}

function formatNumber(value: number) {
  return new Intl.NumberFormat('en', {
    notation: 'compact',
    maximumFractionDigits: 1
  }).format(value);
}

function App() {
  const { user, loading, logout } = useAuth();
  const [activeView, setActiveView] = useState<ViewKey>('dashboard');
  const [postAuthView, setPostAuthView] = useState<ViewKey>('popularity');
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [showToast, setShowToast] = useState(false);

  const metricCards = useMemo(() => {
    if (!analysis) return [];

    return [
    {
      title: 'Audience Score',
      value: `${analysis.audienceScore}%`,
      helper: `${analysis.overallReaction} predicted audience reaction with ${analysis.confidence}% model confidence.`,
      icon: Gauge,
      accent: '#2563EB'
    },
    {
      title: 'Engagement Forecast',
      value: `${analysis.engagementForecast}%`,
      helper: 'Predicted market interest from popularity metrics, sentiment and content intensity.',
      icon: TrendingUp,
      accent: '#06B6D4'
    },
    {
      title: 'Positive Sentiment',
      value: `${analysis.sentiment.positive}%`,
      helper: 'Comment sentiment proxy derived from the latest prediction score.',
      icon: Heart,
      accent: '#E11DFA'
    },
    {
      title: 'Engagement Rate',
      value: `${analysis.popularity.engagementRate}%`,
      helper: `${formatNumber(analysis.popularity.views)} views and ${formatNumber(analysis.popularity.comments)} comments in the dataset.`,
      icon: Activity,
      accent: '#7C3AED'
    }
    ];
  }, [analysis]);

  const isAuthenticated = Boolean(user);

  useEffect(() => {
    if (!showToast) return;
    const timer = window.setTimeout(() => setShowToast(false), 3200);
    return () => window.clearTimeout(timer);
  }, [showToast]);

  const isProtectedView = (view: ViewKey) =>
<<<<<<< HEAD
    ['analyze', 'emotion_analysis', 'history', 'popularity', 'sentiment', 'recommendations'].includes(view);
=======
    ['analyze', 'emotion_analysis', 'history', 'popularity'].includes(view);
>>>>>>> 0a27a033026d81eecd876c34fc200f4a0abdcb9b

  const handleNavigate = (view: ViewKey) => {
    if (!isAuthenticated && isProtectedView(view)) {
      setPostAuthView(view);
      setActiveView('login');
      return;
    }

    setActiveView(view);
  };

  const handleAnalysisCompleted = (result: AnalysisResult) => {
    setAnalysis(result);
    setShowToast(true);
    setActiveView('dashboard');
  };

  const handleLogout = async () => {
    await logout();
    setAnalysis(null);
    setActiveView('dashboard');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen text-sm font-black text-deepnavy">
        Loading authentication...
      </div>
    );
  }

  return (
    <div className="min-h-screen text-slatebrand">
      <Header
        activeView={activeView}
        onNavigate={handleNavigate}
        isAuthenticated={isAuthenticated}
        userLabel={user?.displayName || user?.email || undefined}
        onLogout={handleLogout}
      />

      {showToast && (
        <div className="fixed z-50 flex items-center gap-3 px-5 py-4 text-sm font-bold text-white right-5 top-24 rounded-2xl bg-deepnavy shadow-glow">
          <CheckCircle2 className="w-5 h-5 text-tealbrand" />
          Analysis completed and saved.
        </div>
      )}

      {activeView === 'login' || activeView === 'register' ? (
        <AuthPage
          initialMode={activeView}
          onAuthenticated={() => setActiveView(postAuthView)}
          onModeChange={setActiveView}
        />
      ) : (
<<<<<<< HEAD
        <main className="w-full px-4 py-8 mx-auto max-w-[98%] 2xl:max-w-[1920px] sm:px-6 lg:px-8 xl:px-10">
=======
        <main className="px-4 py-8 mx-auto max-w-7xl sm:px-6 lg:px-8">
>>>>>>> 0a27a033026d81eecd876c34fc200f4a0abdcb9b
          {activeView === 'dashboard' && (
            <DashboardView
              analysis={analysis}
              metricCards={metricCards}
              onNavigate={handleNavigate}
              isAuthenticated={isAuthenticated}
            />
          )}
          {activeView === 'analyze' && <AnalyzeView onCompleted={handleAnalysisCompleted} />}
          {activeView === 'emotion_analysis' && <EmotionAnalysisPage />}
          {activeView === 'history' && <HistoryView />}
          {activeView === 'popularity' && <PopularityAnalysis />}
          {activeView === 'sentiment' && <CommentSentimentAnalysis />}
          {activeView === 'recommendations' && <RecommendationsPage result={analysis} />}
        </main>
      )}

      <Footer onNavigate={handleNavigate} />
    </div>
  );
}

function DashboardView({
  analysis,
  metricCards,
  onNavigate,
  isAuthenticated
}: {
  analysis: AnalysisResult | null;
  metricCards: Array<{
    title: string;
    value: string;
    helper: string;
    icon: typeof Gauge;
    accent: string;
  }>;
  onNavigate: (view: ViewKey) => void;
  isAuthenticated: boolean;
}) {
  return (
    <div className="space-y-10">
      <HeroSection analysis={analysis} onNavigate={onNavigate} />

      {isAuthenticated && (
        <>
          <LatestEmotionDashboard isAuthenticated />
          <RecommendationOverviewSection />
          <PopularityOverviewSection />
          <SentimentOverviewSection />
        </>
      )}
      {!isAuthenticated && <AboutAppSection />}

      {analysis && (
        <>
          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {metricCards.map((card) => (
              <MetricCard key={card.title} {...card} />
            ))}
          </section>

          <section className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
            <ScoreRing
              value={analysis.audienceScore}
              label="Overall audience reaction"
              subLabel={`${analysis.overallReaction} reaction predicted`}
            />

            <div className="rounded-[2rem] bg-white p-6 shadow-card ring-1 ring-slate-200/80">
              <SectionTitle
                eyebrow="Recommendations"
                title="Ranked creator-facing improvements"
                description="Recommendations generated from the completed trailer analysis."
              />

              <div className="space-y-4">
                {analysis.recommendations.map((rec) => (
                  <div key={rec.id} className="p-4 border rounded-2xl border-slate-200 bg-lightbrand/70">
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                      <div>
                        <p className="text-xs font-black uppercase tracking-[0.18em] text-electric">
                          Priority {rec.priority}
                        </p>
                        <h3 className="mt-1 text-lg font-black text-deepnavy">{rec.title}</h3>
                      </div>
                      <span className="px-3 py-1 text-xs font-bold bg-white rounded-full shadow-sm text-slatebrand/60">
                        {rec.component}
                      </span>
                    </div>
                    <p className="mt-3 text-sm leading-6 text-slatebrand/70"><strong>Evidence:</strong> {rec.evidence}</p>
                    <p className="mt-2 text-sm leading-6 text-deepnavy"><strong>Action:</strong> {rec.action}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>

          <section className="grid gap-6 lg:grid-cols-3">
            <div className="rounded-[2rem] bg-white p-6 shadow-card ring-1 ring-slate-200/80">
              <SectionTitle eyebrow="NLP output" title="Sentiment split" description="Positive, neutral and negative audience comments." />
              <SentimentChart result={analysis} />
              <Legend items={[["Positive", "#2563EB"], ["Neutral", "#06B6D4"], ["Negative", "#E11DFA"]]} />
            </div>

            <div className="rounded-[2rem] bg-white p-6 shadow-card ring-1 ring-slate-200/80 lg:col-span-2">
              <SectionTitle eyebrow="Video + audio output" title="Scene intensity timeline" description="Visual emotion, motion level and audio energy across the trailer." />
              <SceneIntensityChart result={analysis} />
            </div>
          </section>

          <section className="rounded-[2rem] bg-white p-6 shadow-card ring-1 ring-slate-200/80">
            <SectionTitle eyebrow="Explainability" title="Top feature contributions" description="The strongest factors in the completed analysis." />
            <FeatureBarChart result={analysis} />
          </section>
        </>
      )}
    </div>
  );
}
function AboutAppSection() {
  const features = [
    [BrainCircuit, 'Emotion analysis', 'Understand scene intensity, visual emotion, motion and soundtrack energy.'],
    [TrendingUp, 'Popularity forecasting', 'Estimate audience reaction and future engagement from real trailer metrics.'],
    [Clock3, 'Saved history', 'Keep completed analyses together so you can compare trailers over time.']
  ] as const;

  return (
    <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-card sm:p-8">
      <div className="max-w-3xl">
        <p className="text-xs font-black uppercase tracking-[0.22em] text-electric">About the platform</p>
        <h2 className="mt-2 text-2xl font-black text-deepnavy sm:text-3xl">Make every trailer moment count.</h2>
        <p className="mt-4 text-sm font-semibold leading-7 text-slatebrand/60">
          This application combines audio, visual and audience signals to help creators understand emotional impact and potential popularity before release. Sign in to run analyses and securely review your saved results.
        </p>
      </div>

      <div className="grid gap-4 mt-7 md:grid-cols-3">
        {features.map(([Icon, title, description]) => (
          <div key={title} className="rounded-3xl bg-lightbrand/70 p-5 ring-1 ring-slate-200/70">
            <div className="flex items-center justify-center w-11 h-11 text-white rounded-2xl bg-deepnavy">
              <Icon className="w-5 h-5" />
            </div>
            <h3 className="mt-4 text-lg font-black text-deepnavy">{title}</h3>
            <p className="mt-2 text-sm font-semibold leading-6 text-slatebrand/55">{description}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function LatestEmotionDashboard({ isAuthenticated }: { isAuthenticated: boolean }) {
  const [latestEmotion, setLatestEmotion] = useState<EmotionHistoryItem | null>(null);
  const [latestDetail, setLatestDetail] = useState<EmotionHistoryDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isAuthenticated) {
      setLatestEmotion(null);
      setLatestDetail(null);
      setError('');
      setIsLoading(false);
      return;
    }

    let active = true;

    const loadLatestEmotion = async () => {
      setIsLoading(true);
      setError('');

      try {
        const items = await getEmotionHistory(1);
        if (!active) return;

        const latest = items[0] || null;
        setLatestEmotion(latest);
        setLatestDetail(null);

        if (latest) {
          try {
            const detail = await getEmotionHistoryDetail(latest.id);
            if (active) setLatestDetail(detail);
          } catch {
            // Summary metrics remain available when the optional detail route is unavailable.
          }
        }
      } catch (requestError) {
        if (active) {
          setError(
            requestError instanceof Error
              ? requestError.message
              : 'Unable to load the latest emotion analysis.'
          );
        }
      } finally {
        if (active) setIsLoading(false);
      }
    };

    void loadLatestEmotion();
    return () => {
      active = false;
    };
  }, [isAuthenticated]);

  return (
    <section className="overflow-hidden rounded-[2rem] border border-slate-200 bg-white shadow-card">
      <div className="flex flex-col gap-4 px-6 py-5 text-white bg-deepnavy sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4">
          <div className="flex items-center justify-center w-12 h-12 rounded-2xl bg-white/10 text-tealbrand ring-1 ring-white/10">
            <BrainCircuit className="w-6 h-6" />
          </div>
          <div>
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-tealbrand">Saved activity · Emotion engine</p>
            <h2 className="mt-1 text-xl font-black sm:text-2xl">Latest emotion analysis</h2>
          </div>
        </div>
        {!isLoading && latestEmotion?.created_at && (
          <p className="text-xs font-semibold text-white/45">{formatLocalDateTime(latestEmotion.created_at)}</p>
        )}
      </div>

      <div className="p-6">
        {isLoading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[1, 2, 3, 4].map((item) => <div key={item} className="h-28 animate-pulse rounded-2xl bg-slate-100" />)}
          </div>
        ) : error ? (
          <div className="px-5 py-4 text-sm font-bold rounded-2xl bg-rose-50 text-rose-700 ring-1 ring-rose-200">{error}</div>
        ) : !latestEmotion ? (
          <div className="px-5 py-8 text-sm font-semibold text-center border border-dashed rounded-2xl border-slate-200 bg-lightbrand/50 text-slatebrand/50">
            Complete an emotion analysis to show its data and graphs on the dashboard.
          </div>
        ) : (
          <div>
            <div className="flex flex-col gap-3 pb-5 border-b border-slate-100 sm:flex-row sm:items-center sm:justify-between">
              <div className="min-w-0">
                <p className="text-xs font-black uppercase tracking-[0.16em] text-electric">Most recent trailer</p>
                <h3 className="mt-1 text-xl font-black truncate text-deepnavy" title={latestEmotion.filename}>{latestEmotion.filename}</h3>
              </div>
              <span className="px-4 py-2 text-xs font-black rounded-full w-fit bg-electric/10 text-electric ring-1 ring-electric/15">{latestEmotion.engagement_level}</span>
            </div>

            <div className="grid gap-4 mt-5 sm:grid-cols-2 lg:grid-cols-4">
              <DashboardEmotionMetric label="Average intensity" value={Number(latestEmotion.average_emotional_intensity || 0).toFixed(2)} helper="Fused EI score" accent="bg-electric/10 text-electric" />
              <DashboardEmotionMetric label="Engagement" value={latestEmotion.engagement_level.replace(' trailer', '')} helper="Predicted response" accent="bg-purplebrand/10 text-purplebrand" />
              <DashboardEmotionMetric label="Scenes analyzed" value={String(latestEmotion.total_scenes)} helper="Timeline segments" accent="bg-tealbrand/10 text-tealbrand" />
              <DashboardEmotionMetric label="Peak scenes" value={String(latestEmotion.high_intensity_scenes)} helper="High-intensity moments" accent="bg-magentabrand/10 text-magentabrand" />
            </div>

            {latestDetail && <EmotionAnalysisCharts result={latestDetail} />}
          </div>
        )}
      </div>
    </section>
  );
}

function DashboardEmotionMetric({
  label,
  value,
  helper,
  accent
}: {
  label: string;
  value: string;
  helper: string;
  accent: string;
}) {
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

function HeroSection({
  analysis,
  onNavigate
}: {
  analysis: AnalysisResult | null;
  onNavigate: (view: ViewKey) => void;
}) {
  return (
    <section className="relative overflow-hidden rounded-[2.5rem] bg-deepnavy p-6 text-white shadow-glow sm:p-8 lg:p-10">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_15%_20%,rgba(37,99,235,0.35),transparent_28%),radial-gradient(circle_at_82%_18%,rgba(225,29,250,0.26),transparent_30%),linear-gradient(135deg,rgba(13,19,43,0)_0%,rgba(13,19,43,0.64)_100%)]" />

      <div className="relative grid gap-8 lg:grid-cols-[1.15fr_0.85fr] lg:items-center">
        <div>
          <motion.div initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.55 }}>
            <div className="inline-flex items-center gap-2 px-4 py-2 mb-5 text-sm font-bold border rounded-full border-white/10 bg-white/10 text-white/85">
              <Sparkles className="w-4 h-4 text-tealbrand" />
              AI-powered trailer intelligence
            </div>

            <h1 className="max-w-4xl text-3xl font-black tracking-tight sm:text-4xl lg:text-5xl">
              Predict audience reactions before trailer release.
            </h1>

            <p className="max-w-2xl mt-5 text-base leading-8 text-white/72">
              Analyze trailer emotion and audience popularity, then review real results saved securely to your account.
            </p>

            <div className="flex flex-wrap gap-3 mt-7">
              <button type="button" onClick={() => onNavigate('emotion_analysis')} className="inline-flex items-center gap-2 px-5 py-3 font-black text-white transition rounded-2xl bg-electric hover:-translate-y-0.5">
                <BrainCircuit className="w-5 h-5" /> Emotion Analysis
              </button>
              <button type="button" onClick={() => onNavigate('popularity')} className="inline-flex items-center gap-2 px-5 py-3 font-black text-white transition border rounded-2xl border-white/20 bg-white/10 hover:-translate-y-0.5 hover:bg-white/15">
                <TrendingUp className="w-5 h-5" /> Popularity Analysis
              </button>
              <button type="button" onClick={() => onNavigate('sentiment')} className="inline-flex items-center gap-2 px-5 py-3 font-black text-white transition border rounded-2xl border-white/20 bg-white/10 hover:-translate-y-0.5 hover:bg-white/15">
                <MessageSquareText className="w-5 h-5" /> Comment Sentiment
              </button>

              {analysis && (
                <>
                  <div className="px-4 py-3 bg-white shadow-lg rounded-2xl text-deepnavy">
                    <p className="text-xs font-bold tracking-wider uppercase text-slatebrand/50">Trailer</p>
                    <p className="font-black">{analysis.trailerTitle}</p>
                  </div>
                  <div className={`rounded-2xl px-4 py-3 ring-1 ${reactionStyles[analysis.overallReaction]}`}>
                    <p className="text-xs font-bold tracking-wider uppercase opacity-70">Predicted class</p>
                    <p className="font-black">{analysis.overallReaction} Reaction</p>
                  </div>
                </>
              )}
            </div>
          </motion.div>
        </div>

        <motion.div initial={{ opacity: 0, scale: 0.94 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.65 }} className="animate-float mx-auto w-full max-w-[400px] rounded-[2rem] bg-white/95 p-4 shadow-2xl">
          <img src="/logo-full.png" alt="AI-Powered Movie Trailer Analyzer brand logo" className="w-full h-auto rounded-[1.4rem] object-contain" />
          {analysis && (
            <div className="grid grid-cols-3 gap-3 mt-4">
              <MiniStat label="Confidence" value={`${analysis.confidence}%`} />
              <MiniStat label="Like ratio" value={`${analysis.popularity.likeRatio}%`} />
              <MiniStat label="Velocity" value={`${analysis.popularity.velocity}%`} />
            </div>
          )}
        </motion.div>
      </div>
    </section>
  );
}
function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-3 text-center rounded-2xl bg-lightbrand">
      <p className="text-xs font-bold text-slatebrand/50">{label}</p>
      <p className="mt-1 text-lg font-black text-deepnavy">{value}</p>
    </div>
  );
}

function AnalyzeView({
  onCompleted
}: {
  onCompleted: (result: AnalysisResult) => void;
}) {
  return (
    <div className="space-y-8">
      <SectionTitle
        eyebrow="Analyze trailer"
        title="Trailer Analysis Input"
        description="Submit a YouTube URL. Current YouTube data is simulated until YouTube API integration, while prediction uses trained backend models."
      />

      <UploadPanel onCompleted={onCompleted} />

    </div>
  );
}

function HistoryView() {
  const [trailerHistory, setTrailerHistory] = useState<PopularityHistoryRecord[]>([]);
  const [popularityHistory, setPopularityHistory] = useState<FutureMetricsHistoryRecord[]>([]);
  const [emotionHistory, setEmotionHistory] = useState<EmotionHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  const loadHistory = async () => {
    setIsLoading(true);
    setError('');

    const [emotionResult, trailerResult, popularityResult] = await Promise.allSettled([
      getEmotionHistory(50),
      getPopularityHistory(50),
      getFutureMetricsHistory(50)
    ]);

    setEmotionHistory(emotionResult.status === 'fulfilled' ? emotionResult.value : []);
    setTrailerHistory(trailerResult.status === 'fulfilled' ? trailerResult.value : []);
    setPopularityHistory(popularityResult.status === 'fulfilled' ? popularityResult.value : []);

    if (
      emotionResult.status === 'rejected' &&
      trailerResult.status === 'rejected' &&
      popularityResult.status === 'rejected'
    ) {
      setError('Saved history is currently unavailable. Please try again.');
    }

    setIsLoading(false);
  };

  useEffect(() => {
    loadHistory();
  }, []);

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <SectionTitle
          eyebrow="Saved analyses"
          title="Analysis History"
          description="Past trailer analyses and popularity forecasts saved to your account."
        />
        <button
          type="button"
          onClick={loadHistory}
          disabled={isLoading}
          className="inline-flex items-center gap-2 px-4 py-3 text-sm font-black rounded-2xl bg-lightbrand text-deepnavy ring-1 ring-slate-200 disabled:opacity-70"
        >
          {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCcw className="w-4 h-4" />}
          Refresh
        </button>
      </div>

      {error && (
        <div className="flex items-start gap-3 p-4 text-sm font-semibold rounded-2xl bg-rose-50 text-rose-700 ring-1 ring-rose-100">
          <AlertCircle className="mt-0.5 h-5 w-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <HistoryTable
        title="Emotion trailer analysis"
        columns={['Trailer', 'Date', 'Scenes', 'Average intensity', 'Engagement']}
        emptyText="No emotion trailer analysis history saved yet."
        isLoading={isLoading}
      >
        {emotionHistory.map((item) => (
          <div key={item.id} className="grid grid-cols-1 gap-4 border-b border-slate-100 p-5 text-sm last:border-b-0 md:grid-cols-[1.5fr_0.9fr_0.8fr_0.8fr_0.8fr] md:items-center">
            <div>
              <p className="font-black text-deepnavy">{item.filename || 'Untitled trailer'}</p>
              <p className="mt-1 text-xs text-slatebrand/50">{item.id}</p>
            </div>
            <span className="font-semibold text-slatebrand/70">{formatLocalDateTime(item.created_at)}</span>
            <span className="font-black text-deepnavy">{item.total_scenes}</span>
            <span className="font-black text-deepnavy">{Number(item.average_emotional_intensity || 0).toFixed(2)}</span>
            <span className="inline-flex items-center gap-2 px-3 py-1 text-xs font-bold rounded-full w-fit bg-electric/10 text-electric">
              {item.engagement_level}
            </span>
          </div>
        ))}
      </HistoryTable>

      <HistoryTable
        title="Trailer analysis"
        columns={['Trailer', 'Date', 'Reaction', 'Score', 'Status']}
        emptyText="No trailer analysis history saved yet."
        isLoading={isLoading}
      >
        {trailerHistory.map((item) => {
          const reaction = toReactionLevel(String(item.predicted_reaction || ''));
          return (
            <div key={String(item.id)} className="grid grid-cols-1 gap-4 border-b border-slate-100 p-5 text-sm last:border-b-0 md:grid-cols-[1.5fr_0.9fr_0.8fr_0.8fr_0.8fr] md:items-center">
              <div>
                <p className="font-black text-deepnavy">{String(item.title || item.video_id || 'Untitled trailer')}</p>
                <p className="mt-1 text-xs text-slatebrand/50">{String(item.video_id || item.id || '')}</p>
              </div>
              <span className="font-semibold text-slatebrand/70">{formatDate(String(item.created_at || ''))}</span>
              <span className={`w-fit rounded-full px-3 py-1 text-xs font-black ring-1 ${reactionStyles[reaction]}`}>{reaction}</span>
              <span className="font-black text-deepnavy">{Number(item.popularity_score || 0).toFixed(1)}%</span>
              <span className="inline-flex items-center gap-2 px-3 py-1 text-xs font-bold rounded-full w-fit bg-lightbrand text-slatebrand/70">
                <Clock3 className="h-3.5 w-3.5" />
                Saved
              </span>
            </div>
          );
        })}
      </HistoryTable>

      <HistoryTable
        title="Future popularity analysis"
        columns={['Trailer', 'Horizon', 'Future reaction', 'Predicted views', 'Date']}
        emptyText="No future popularity history saved yet."
        isLoading={isLoading}
      >
        {popularityHistory.map((item) => {
          const reaction = toReactionLevel(String(item.predicted_reaction || ''));
          return (
            <div key={String(item.id)} className="grid grid-cols-1 gap-4 border-b border-slate-100 p-5 text-sm last:border-b-0 md:grid-cols-[1.5fr_0.9fr_0.8fr_0.8fr_0.8fr] md:items-center">
              <div>
                <p className="font-black text-deepnavy">{String(item.title || item.video_id || 'Untitled trailer')}</p>
                <p className="mt-1 text-xs text-slatebrand/50">{String(item.video_id || item.id || '')}</p>
              </div>
              <span className="font-semibold text-slatebrand/70">{Number(item.horizon_days || 0)} days</span>
              <span className={`w-fit rounded-full px-3 py-1 text-xs font-black ring-1 ${reactionStyles[reaction]}`}>{reaction}</span>
              <span className="font-black text-deepnavy">{formatNumber(Number(item.predicted_views || 0))}</span>
              <span className="font-semibold text-slatebrand/70">{formatDate(String(item.created_at || ''))}</span>
            </div>
          );
        })}
      </HistoryTable>
    </div>
  );
}

function HistoryTable({
  title,
  columns,
  emptyText,
  isLoading,
  children
}: {
  title: string;
  columns: string[];
  emptyText: string;
  isLoading: boolean;
  children: ReactNode;
}) {
  const rows = Array.isArray(children) ? children : [children].filter(Boolean);

  return (
    <div className="overflow-hidden rounded-[2rem] bg-white shadow-card ring-1 ring-slate-200/80">
      <div className="p-5 border-b border-slate-200 bg-lightbrand">
        <h3 className="text-lg font-black text-deepnavy">{title}</h3>
      </div>
      <div className="grid grid-cols-1 gap-4 border-b border-slate-200 bg-lightbrand p-5 font-bold text-deepnavy md:grid-cols-[1.5fr_0.9fr_0.8fr_0.8fr_0.8fr]">
        {columns.map((column) => <span key={column}>{column}</span>)}
      </div>
      {!isLoading && rows.length === 0 && (
        <div className="p-5 text-sm font-semibold text-slatebrand/60">{emptyText}</div>
      )}
      {children}
    </div>
  );
}

function toReactionLevel(value: string): ReactionLevel {
  const normalized = value.toUpperCase();
  if (normalized.includes('HIGH')) return 'High';
  if (normalized.includes('LOW')) return 'Low';
  return 'Moderate';
}

function formatDate(value: string) {
  const date = new Date(value);
  if (!value || Number.isNaN(date.getTime())) return 'N/A';
  return new Intl.DateTimeFormat('en', { year: 'numeric', month: 'short', day: '2-digit' }).format(date);
}

function Legend({ items }: { items: Array<[string, string]> }) {
  return (
    <div className="flex flex-wrap justify-center gap-3">
      {items.map(([label, color]) => (
        <div
          key={label}
          className="flex items-center gap-2 px-3 py-1 text-xs font-bold rounded-full bg-lightbrand text-slatebrand/70"
        >
          <span
            className="h-2.5 w-2.5 rounded-full"
            style={{ backgroundColor: color }}
          />

          {label}
        </div>
      ))}
    </div>
  );
}

export default App;