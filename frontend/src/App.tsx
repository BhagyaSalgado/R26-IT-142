import { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Activity,
  BarChart3,
  BrainCircuit,
  CheckCircle2,
  Clock3,
  Film,
  Gauge,
  Heart,
  MessageSquareText,
  MousePointerClick,
  Play,
  Sparkles,
  TrendingUp,
  Users,
  WandSparkles
} from 'lucide-react';
import Header from './components/Header';
import SectionTitle from './components/SectionTitle';
import ScoreRing from './components/ScoreRing';
import MetricCard from './components/MetricCard';
import UploadPanel from './components/UploadPanel';
import { FeatureBarChart, SceneIntensityChart, SentimentChart } from './components/Charts';
import { CommentTopicsChart, RegionalInterestChart } from './components/CommentAnalysisCharts';
import { CommentInsights } from './components/CommentInsights';
import { DeeperEmotionsChart, EmotionDistributionChart, SentimentAndEmotionSummary } from './components/EmotionAnalysisCharts';
import { historyItems, mockAnalysisResult } from './data/mockBackend';
import type { AnalysisResult, ReactionLevel } from './types';

type ViewKey = 'dashboard' | 'analyze' | 'components' | 'history';

const reactionStyles: Record<ReactionLevel, string> = {
  High: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  Moderate: 'bg-amber-50 text-amber-700 ring-amber-200',
  Low: 'bg-rose-50 text-rose-700 ring-rose-200'
};

function formatNumber(value: number) {
  return new Intl.NumberFormat('en', { notation: 'compact', maximumFractionDigits: 1 }).format(value);
}

function App() {
  const [activeView, setActiveView] = useState<ViewKey>('dashboard');
  const [analysis, setAnalysis] = useState<AnalysisResult>(mockAnalysisResult);
  const [showToast, setShowToast] = useState(false);

  useEffect(() => {
    if (!showToast) return;
    const timer = window.setTimeout(() => setShowToast(false), 3200);
    return () => window.clearTimeout(timer);
  }, [showToast]);

  const metricCards = useMemo(() => [
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
      helper: 'Simulated BERT-based comment sentiment classification output.',
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
  ], [analysis]);

  const handleAnalysisCompleted = (result: AnalysisResult) => {
    setAnalysis(result);
    setShowToast(true);
    setActiveView('dashboard');
  };

  return (
    <div className="min-h-screen text-slatebrand">
      <Header activeView={activeView} onNavigate={setActiveView} />

      {showToast && (
        <div className="fixed right-5 top-24 z-50 flex items-center gap-3 rounded-2xl bg-deepnavy px-5 py-4 text-sm font-bold text-white shadow-glow">
          <CheckCircle2 className="h-5 w-5 text-tealbrand" />
          Simulated analysis completed successfully.
        </div>
      )}

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {activeView === 'dashboard' && <DashboardView analysis={analysis} metricCards={metricCards} />}
        {activeView === 'analyze' && <AnalyzeView onCompleted={handleAnalysisCompleted} />}
        {activeView === 'history' && <HistoryView />}
      </main>
    </div>
  );
}

interface DashboardViewProps {
  analysis: AnalysisResult;
  metricCards: Array<{
    title: string;
    value: string;
    helper: string;
    icon: typeof Gauge;
    accent: string;
  }>;
}

function DashboardView({ analysis, metricCards }: DashboardViewProps) {
  return (
    <div className="space-y-10">
      <HeroSection analysis={analysis} />

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {metricCards.map((card) => <MetricCard key={card.title} {...card} />)}
      </section>

      

      <section className="grid gap-6 lg:grid-cols-3">
        <div className="rounded-[2rem] bg-white p-6 shadow-card ring-1 ring-slate-200/80">
          <SectionTitle eyebrow="NLP output" title="Sentiment split" description="Positive, neutral and negative audience comments." />
          <SentimentChart result={analysis} />
          <Legend items={[['Positive', '#2563EB'], ['Neutral', '#06B6D4'], ['Negative', '#E11DFA']]} />
        </div>
        <div className="rounded-[2rem] bg-white p-6 shadow-card ring-1 ring-slate-200/80 lg:col-span-2">
          <SectionTitle eyebrow="Video + audio output" title="Scene intensity timeline" description="Visual emotion, motion level and audio energy are fused into scene intensity scores." />
          <SceneIntensityChart result={analysis} />
        </div>
      </section>

      <section className="">
        <div className="rounded-[2rem] bg-white p-6 shadow-card ring-1 ring-slate-200/80">
          <SectionTitle eyebrow="Explainability" title="Top feature contributions" description="The chart simulates Random Forest feature-importance evidence used by the recommendation engine." />
          <FeatureBarChart result={analysis} />
        </div>
      </section>

      {/* Emotion Analysis Section */}
      <section className="space-y-6">
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-[2rem] bg-white p-6 shadow-card ring-1 ring-slate-200/80">
            <SectionTitle eyebrow="Deep emotion analysis" title="Audience emotions" description="Deeper emotional responses: anticipation, excitement, and disappointment detected from comments." />
            <DeeperEmotionsChart result={analysis} />
          </div>
          <div className="rounded-[2rem] bg-white p-6 shadow-card ring-1 ring-slate-200/80">
            <SectionTitle eyebrow="Emotion metrics" title="Emotion distribution" description="Horizontal view of anticipation, excitement, and disappointment percentages." />
            <EmotionDistributionChart result={analysis} />
          </div>
        </div>
      </section>

      <section className="">
        <div className="rounded-[2rem] bg-white p-6 shadow-card ring-1 ring-slate-200/80">
          <SectionTitle eyebrow="Sentiment + Emotion" title="Sentiment and emotion summary" description="Comparing basic sentiments with deeper emotional responses." />
          <SentimentAndEmotionSummary result={analysis} />
        </div>
      </section>

      {/* Comment Sentiment Analysis Section */}
      <section className="space-y-6">
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="rounded-[2rem] bg-white p-6 shadow-card ring-1 ring-slate-200/80 lg:col-span-2">
            <SectionTitle eyebrow="NLP comment analysis" title="Top discussion topics" description="Frequently mentioned themes extracted from audience comments using topic modeling." />
            <CommentTopicsChart result={analysis} />
          </div>
          <div className="rounded-[2rem] bg-white p-6 shadow-card ring-1 ring-slate-200/80">
            <SectionTitle eyebrow="Language detection" title="Regional audience split" description="Geographic distribution estimated from comment languages and IP data." />
            <RegionalInterestChart result={analysis} />
          </div>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-3">
        <div className="rounded-[2rem] bg-white p-6 shadow-card ring-1 ring-slate-200/80 lg:col-span-3">
          <SectionTitle eyebrow="Comment sentiment insights" title="Audience reaction analysis" description="Key insights and metrics from comment sentiment classification and topic extraction." />
          <CommentInsights analysis={analysis} />
        </div>
      </section>
    </div>
  );
}

function HeroSection({ analysis }: { analysis: AnalysisResult }) {
  return (
    <section className="relative overflow-hidden rounded-[2.5rem] bg-deepnavy p-6 text-white shadow-glow sm:p-8 lg:p-10">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_15%_20%,rgba(37,99,235,0.35),transparent_28%),radial-gradient(circle_at_82%_18%,rgba(225,29,250,0.26),transparent_30%),linear-gradient(135deg,rgba(13,19,43,0)_0%,rgba(13,19,43,0.64)_100%)]" />
      <div className="relative grid gap-8 lg:grid-cols-[1.15fr_0.85fr] lg:items-center">
        <div>
          <motion.div initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.55 }}>
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/10 px-4 py-2 text-sm font-bold text-white/85">
              <Sparkles className="h-4 w-4 text-tealbrand" />
              AI-POWERED INSIGHTS
            </div>
            <h1 className="max-w-4xl text-4xl font-black tracking-tight sm:text-5xl lg:text-6xl">
              Predict audience reactions before trailer release.
            </h1>
            <p className="mt-5 max-w-2xl text-base leading-8 text-white/72">
              A modern dashboard for trailer creators, production teams and marketing analysts.
            </p>
            <div className="mt-7 flex flex-wrap gap-3">
              <div className="rounded-2xl bg-white px-4 py-3 text-deepnavy shadow-lg">
                <p className="text-xs font-bold uppercase tracking-wider text-slatebrand/50">Trailer</p>
                <p className="font-black">{analysis.trailerTitle}</p>
              </div>
              <div className={`rounded-2xl px-4 py-3 ring-1 ${reactionStyles[analysis.overallReaction]}`}>
                <p className="text-xs font-bold uppercase tracking-wider opacity-70">Predicted class</p>
                <p className="font-black">{analysis.overallReaction} Reaction</p>
              </div>
            </div>
          </motion.div>
        </div>
        <motion.div initial={{ opacity: 0, scale: 0.94 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.65 }} className="animate-float rounded-[2rem] bg-white/95 p-4 shadow-2xl">
          <img src="/logo-full.png" alt="AI-Powered Movie Trailer Analyzer brand logo" className="h-72 w-full rounded-[1.4rem] object-cover object-top" />
          <div className="mt-4 grid grid-cols-3 gap-3">
            <MiniStat label="Confidence" value={`${analysis.confidence}%`} />
            <MiniStat label="Like ratio" value={`${analysis.popularity.likeRatio}%`} />
            <MiniStat label="Velocity" value={`${analysis.popularity.velocity}%`} />
          </div>
        </motion.div>
      </div>
    </section>
  );
}

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-lightbrand p-3 text-center">
      <p className="text-xs font-bold text-slatebrand/50">{label}</p>
      <p className="mt-1 text-lg font-black text-deepnavy">{value}</p>
    </div>
  );
}

function AnalyzeView({ onCompleted }: { onCompleted: (result: AnalysisResult) => void }) {
  return (
    <div className="space-y-8">
      <SectionTitle
        eyebrow="Analyze trailer"
        title="Trailer Analysis Input"
        description="Submit a YouTube URL or choose a video file. The system waits briefly and returns a full analysis to populate the dashboard."
      />
      <UploadPanel onCompleted={onCompleted} />
    </div>
  );
}



function HistoryView() {
  return (
    <div className="space-y-8">
      <SectionTitle
        eyebrow="Saved analyses"
        title="Trailer Analysis History"
        description="Past records show how completed trailer analyses could be reviewed, shared or compared."
      />
      <div className="overflow-hidden rounded-[2rem] bg-white shadow-card ring-1 ring-slate-200/80">
        <div className="grid grid-cols-1 gap-4 border-b border-slate-200 bg-lightbrand p-5 font-bold text-deepnavy md:grid-cols-[1.5fr_0.9fr_0.8fr_0.7fr_0.9fr]">
          <span>Trailer</span>
          <span>Date</span>
          <span>Reaction</span>
          <span>Score</span>
          <span>Status</span>
        </div>
        {historyItems.map((item) => (
          <div key={item.id} className="grid grid-cols-1 gap-4 border-b border-slate-100 p-5 text-sm last:border-b-0 md:grid-cols-[1.5fr_0.9fr_0.8fr_0.7fr_0.9fr] md:items-center">
            <div>
              <p className="font-black text-deepnavy">{item.title}</p>
              <p className="mt-1 text-xs text-slatebrand/50">{item.id} • {item.sentiment}</p>
            </div>
            <span className="font-semibold text-slatebrand/70">{item.date}</span>
            <span className={`w-fit rounded-full px-3 py-1 text-xs font-black ring-1 ${reactionStyles[item.reaction]}`}>{item.reaction}</span>
            <span className="font-black text-deepnavy">{item.score}%</span>
            <span className="inline-flex w-fit items-center gap-2 rounded-full bg-lightbrand px-3 py-1 text-xs font-bold text-slatebrand/70">
              <Clock3 className="h-3.5 w-3.5" />
              {item.status}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function Legend({ items }: { items: Array<[string, string]> }) {
  return (
    <div className="flex flex-wrap justify-center gap-3">
      {items.map(([label, color]) => (
        <div key={label} className="flex items-center gap-2 rounded-full bg-lightbrand px-3 py-1 text-xs font-bold text-slatebrand/70">
          <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} />
          {label}
        </div>
      ))}
    </div>
  );
}

export default App;
