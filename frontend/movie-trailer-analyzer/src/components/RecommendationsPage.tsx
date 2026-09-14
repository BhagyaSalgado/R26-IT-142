import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Activity,
  AlertCircle,
  BrainCircuit,
  CheckCircle2,
  Clock3,
  Cpu,
  Film,
  Flame,
  Gauge,
  Lightbulb,
  ListChecks,
  Loader2,
  Play,
  RefreshCcw,
  Scissors,
  Sparkles,
  TrendingUp,
  Video,
  Volume2,
  Wand2,
  Layers,
  ChevronRight
} from 'lucide-react';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts';
import type { AnalysisResult } from '../types';
import {
  checkRecommendationHealth,
  getLatestRecommendationGuidance,
  getRecommendationGuidanceByPredictionId,
  type BackendRecommendation,
  type RecommendationGuidance
} from '../services/recommendationApi';
import {
  getEmotionHistory,
  type EmotionHistoryItem
} from '../services/videoEmotionApi';
import SectionTitle from './SectionTitle';
import ScoreRing from './ScoreRing';
import MetricCard from './MetricCard';

interface RecommendationsPageProps {
  result?: AnalysisResult | null;
  onNavigateToUpload?: () => void;
}

const categoryIcons = {
  Visual: Film,
  Audio: Volume2,
  Pacing: Scissors,
  Metadata: TrendingUp
};

const categoryColors = {
  Visual: '#2563EB',
  Audio: '#06B6D4',
  Pacing: '#E11DFA',
  Metadata: '#7C3AED'
};

const priorityStyles: Record<number, { label: string; badge: string; border: string; barColor: string }> = {
  1: {
    label: 'High Priority (P1)',
    badge: 'bg-rose-50 text-rose-700 ring-rose-600/20 border-rose-200',
    border: 'border-l-rose-500',
    barColor: '#E11D48'
  },
  2: {
    label: 'Medium Priority (P2)',
    badge: 'bg-amber-50 text-amber-700 ring-amber-600/20 border-amber-200',
    border: 'border-l-amber-500',
    barColor: '#F59E0B'
  },
  3: {
    label: 'Optimization (P3)',
    badge: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20 border-emerald-200',
    border: 'border-l-emerald-500',
    barColor: '#10B981'
  }
};

export default function RecommendationsPage({ result, onNavigateToUpload }: RecommendationsPageProps) {
  const [guidance, setGuidance] = useState<RecommendationGuidance | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [isBackendHealthy, setIsBackendHealthy] = useState<boolean | null>(null);
  const [activeFilter, setActiveFilter] = useState<'all' | '1' | '2' | '3'>('all');
  const [activeCategory, setActiveCategory] = useState<string>('all');
  const [emotionHistory, setEmotionHistory] = useState<EmotionHistoryItem[]>([]);
  const [selectedPredictionId, setSelectedPredictionId] = useState<string>('');
  const [statusMessage, setStatusMessage] = useState<string>('');

  const loadTrailersAndGuidance = async () => {
    setLoading(true);
    setStatusMessage('');
    try {
      const healthy = await checkRecommendationHealth();
      setIsBackendHealthy(healthy);

      // Load history of real uploaded trailers
      const historyItems = await getEmotionHistory(15).catch(() => []);
      setEmotionHistory(historyItems);

      let data: RecommendationGuidance;
      if (selectedPredictionId) {
        data = await getRecommendationGuidanceByPredictionId(selectedPredictionId);
      } else if (historyItems.length > 0) {
        setSelectedPredictionId(historyItems[0].id);
        data = await getRecommendationGuidanceByPredictionId(historyItems[0].id);
      } else {
        data = await getLatestRecommendationGuidance();
      }

      setGuidance(data);
    } catch (err) {
      console.error('Failed to load live recommendations:', err);
      setStatusMessage('Unable to connect to live recommendation engine. Ensure backends are running.');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectTrailer = async (predictionId: string) => {
    if (predictionId === selectedPredictionId && guidance) return;
    setSelectedPredictionId(predictionId);
    setLoading(true);
    setStatusMessage('');
    try {
      const data = await getRecommendationGuidanceByPredictionId(predictionId);
      setGuidance(data);
      setStatusMessage(`Loaded recommendations for ${data.trailerTitle}`);
    } catch (err) {
      console.error('Failed to switch trailer recommendations:', err);
      setStatusMessage('Error loading recommendations for this trailer.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTrailersAndGuidance();
  }, []);

  const filteredRecommendations = (guidance?.recommendations || []).filter((rec) => {
    const matchesPriority = activeFilter === 'all' || rec.priority.toString() === activeFilter;
    const matchesCategory = activeCategory === 'all' || rec.category === activeCategory;
    return matchesPriority && matchesCategory;
  });

  const chartData = (guidance?.recommendations || []).map((rec, index) => ({
    name: `S${rec.scene || index + 1}`,
    priorityScore: rec.priority === 1 ? 95 : rec.priority === 2 ? 70 : 45,
    impact: rec.priority === 1 ? 90 : rec.priority === 2 ? 75 : 60,
    category: rec.category,
    timeframe: rec.timeframe || `Cut ${index + 1}`
  }));

  const cleanTitle = (guidance?.trailerTitle || 'Uploaded Trailer')
    .replace(/\.[^/.]+$/, '')
    .replace(/[_-]+/g, ' ')
    .replace(/official trailer.*/i, '')
    .trim();

  // Deduplicate and get ONLY the last 5 unique analyzed trailers
  const recentFiveTrailers = (() => {
    const seen = new Set<string>();
    const uniqueList: EmotionHistoryItem[] = [];
    for (const item of emotionHistory) {
      const normalizedName = item.filename.toLowerCase().replace(/[^a-z0-9]/g, '');
      if (!seen.has(normalizedName)) {
        seen.add(normalizedName);
        uniqueList.push(item);
      }
      if (uniqueList.length >= 5) break;
    }
    return uniqueList.length > 0 ? uniqueList : emotionHistory.slice(0, 5);
  })();

  return (
    <div className="space-y-8 pb-16">
      {/* Header Banner */}
      <section className="relative overflow-hidden rounded-[2.5rem] bg-gradient-to-br from-[#0B132B] via-[#1C2541] to-[#0D1B2A] p-8 sm:p-10 text-white shadow-2xl ring-1 ring-white/10">
        <div className="absolute -right-20 -top-20 h-96 w-96 rounded-full bg-electric/25 blur-3xl pointer-events-none" />
        <div className="absolute -bottom-20 -left-20 h-96 w-96 rounded-full bg-magentabrand/20 blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="max-w-2xl space-y-3">
            <div className="inline-flex items-center gap-2 rounded-full border border-teal-400/30 bg-teal-400/10 px-4 py-1.5 text-xs font-black uppercase tracking-widest text-teal-300 backdrop-blur-md">
              <Sparkles className="h-3.5 w-3.5" />
              Cinematic AI Recommendation Engine
            </div>
            <h1 className="text-3xl font-black tracking-tight sm:text-4xl text-white">
              Trailer Optimization & Editorial Guidance
            </h1>
            <p className="text-sm font-medium leading-relaxed text-slate-300">
              Frame-accurate, multi-signal editorial recommendations synthesized from audio frequency spectra,
              facial emotion arcs, optical flow kinetic cadence, and YouTube audience retention signals.
            </p>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <button
              onClick={() => loadTrailersAndGuidance()}
              disabled={loading}
              className="inline-flex items-center justify-center gap-2 rounded-2xl bg-white px-5 py-3 text-xs font-black uppercase tracking-wider text-deepnavy transition hover:bg-slate-100 hover:shadow-lg active:scale-95 disabled:opacity-50"
            >
              <RefreshCcw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh Analysis
            </button>
          </div>
        </div>

        {/* Recent Analyzed Trailers Bar (Last 5 Only) */}
        {recentFiveTrailers.length > 0 && (
          <div className="relative z-10 mt-8 border-t border-white/15 pt-6">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-black uppercase tracking-wider text-teal-300 flex items-center gap-2">
                <Video className="h-4 w-4 text-teal-400" />
                Recent Analyzed Trailers (Last 5)
              </span>
              <div className="flex flex-wrap items-center gap-2 text-xs font-semibold text-slate-300">
                <span>Viewing: <strong className="text-white font-bold">{cleanTitle}</strong></span>
                <span className="inline-flex items-center gap-1.5 rounded-full bg-teal-400/20 px-3 py-0.5 text-[11px] font-black uppercase text-teal-300 border border-teal-400/30">
                  <Film className="h-3 w-3 text-teal-300" />
                  Genre: {guidance?.dominantGenre || 'Action'}{guidance?.secondaryGenre ? ` / ${guidance.secondaryGenre}` : ''}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2.5">
              {recentFiveTrailers.map((item) => {
                const isSelected = item.id === selectedPredictionId;
                const formattedName = item.filename
                  .replace(/\.[^/.]+$/, '')
                  .replace(/[_-]+/g, ' ')
                  .replace(/official trailer.*/i, '')
                  .replace(/trailer.*/i, '')
                  .trim() || item.filename;

                return (
                  <button
                    key={item.id}
                    onClick={() => handleSelectTrailer(item.id)}
                    disabled={loading}
                    className={`group relative flex items-center justify-between gap-2.5 rounded-2xl p-3 text-left transition-all duration-200 ${
                      isSelected
                        ? 'bg-electric text-white shadow-lg ring-2 ring-white/40 scale-[1.02]'
                        : 'bg-white/10 text-slate-200 hover:bg-white/20 hover:text-white backdrop-blur-md border border-white/10'
                    }`}
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-xl transition ${isSelected ? 'bg-white/20 text-white' : 'bg-white/10 text-teal-300'}`}>
                        <Film className="h-4 w-4" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-xs font-bold truncate leading-tight">{formattedName}</p>
                        <span className="text-[10px] font-semibold text-white/70 block mt-0.5">
                          {item.total_scenes} scenes
                        </span>
                      </div>
                    </div>
                    {isSelected && (
                      <div className="h-2 w-2 rounded-full bg-emerald-400 shrink-0 animate-pulse" />
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {statusMessage && (
          <p className="relative z-10 mt-3 text-xs font-bold text-teal-300">{statusMessage}</p>
        )}
      </section>

      {/* KPI Overview Grid */}
      <section className="grid gap-5 sm:grid-cols-2 lg:grid-cols-5">
        <MetricCard
          title="Movie Genre"
          value={guidance?.dominantGenre || 'Action'}
          helper={guidance?.secondaryGenre ? `Blend: +${guidance.secondaryGenre}` : "Multimodal Archetype"}
          icon={Film}
          accent="#10B981"
        />
        <MetricCard
          title="Overall Priority Index"
          value={guidance ? `${guidance.overallPriorityScore}/100` : '--/100'}
          helper="Synthesized priority index derived from multi-component confidence."
          icon={Gauge}
          accent="#2563EB"
        />
        <MetricCard
          title="Model Confidence"
          value={guidance ? `${guidance.modelConfidence}%` : '--%'}
          helper="Statistical certainty based on Random Forest multimodal validation."
          icon={BrainCircuit}
          accent="#06B6D4"
        />
        <MetricCard
          title="Estimated Impact"
          value={guidance ? `${guidance.targetAudienceReach}%` : '--%'}
          helper="Projected audience retention following visual and acoustic adjustments."
          icon={TrendingUp}
          accent="#E11DFA"
        />
        <div className="rounded-[2rem] bg-white p-6 shadow-card ring-1 ring-slate-200/80 transition hover:shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-black uppercase tracking-wider text-slate-500">Primary Focus Area</span>
            <div className="rounded-xl bg-purple-100 p-2 text-purple-600">
              <Lightbulb className="h-5 w-5" />
            </div>
          </div>
          <p className="mt-3 text-lg font-black text-deepnavy leading-tight">
            {guidance?.focusArea || 'Pacing & Harmonic Alignment'}
          </p>
          <p className="mt-2 text-xs font-semibold text-slate-500">
            High-impact structural & acoustic calibration across key narrative cuts.
          </p>
        </div>
      </section>

      {/* Main Two-Column Layout */}
      <div className="grid gap-8 lg:grid-cols-12">
        {/* Left Column: Recommendations Feed & Filters */}
        <div className="space-y-6 lg:col-span-8">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <SectionTitle
              eyebrow="Editorial Directives"
              title={`Frame-Accurate Action Items (${filteredRecommendations.length})`}
              description={`Specific edit, audio design, and pacing adjustments for '${cleanTitle}'.`}
            />

            {/* Filter Pills */}
            <div className="flex flex-wrap items-center gap-1.5">
              {(['all', '1', '2', '3'] as const).map((lvl) => (
                <button
                  key={lvl}
                  onClick={() => setActiveFilter(lvl)}
                  className={`rounded-xl px-3.5 py-1.5 text-xs font-black uppercase tracking-wider transition ${
                    activeFilter === lvl
                      ? 'bg-deepnavy text-white shadow-sm ring-2 ring-deepnavy/20'
                      : 'bg-white text-slate-600 hover:bg-slate-50 ring-1 ring-slate-200'
                  }`}
                >
                  {lvl === 'all' ? 'All' : `P${lvl}`}
                </button>
              ))}
            </div>
          </div>

          {/* Category Filter Tabs */}
          <div className="flex flex-wrap gap-2 border-b border-slate-200 pb-3">
            {['all', 'Visual', 'Audio', 'Pacing', 'Metadata'].map((cat) => (
              <button
                key={cat}
                onClick={() => setActiveCategory(cat)}
                className={`rounded-xl px-4 py-2 text-xs font-bold transition ${
                  activeCategory === cat
                    ? 'bg-electric text-white shadow-md'
                    : 'bg-white text-slate-600 hover:bg-slate-50 ring-1 ring-slate-200'
                }`}
              >
                {cat === 'all' ? 'All Domains' : cat}
              </button>
            ))}
          </div>

          {/* Priority Score Distribution Chart */}
          {chartData.length > 0 && (
            <div className="rounded-[2rem] bg-white p-6 shadow-card ring-1 ring-slate-200/80">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xs font-black uppercase tracking-wider text-deepnavy flex items-center gap-2">
                  <Activity className="h-4 w-4 text-electric" />
                  Scene-by-Scene Priority & Impact Index
                </h3>
                <span className="text-xs font-bold text-slate-500">{chartData.length} Scenes Evaluated</span>
              </div>
              <div className="h-40 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 5, right: 10, left: -25, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
                    <XAxis dataKey="name" tick={{ fontSize: 11, fontWeight: 700, fill: '#64748B' }} />
                    <YAxis domain={[0, 100]} tick={{ fontSize: 11, fontWeight: 700, fill: '#64748B' }} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0F172A', borderRadius: '1rem', border: 'none', color: '#fff', fontSize: '12px' }}
                    />
                    <Bar dataKey="priorityScore" radius={[6, 6, 0, 0]}>
                      {chartData.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={categoryColors[entry.category as keyof typeof categoryColors] || '#2563EB'}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Recommendation Cards List (Clean, Structured Arrangement) */}
          <div className="space-y-4">
            {loading ? (
              <div className="flex flex-col items-center justify-center p-16 rounded-[2rem] bg-white shadow-card ring-1 ring-slate-200/80 space-y-3">
                <Loader2 className="h-8 w-8 animate-spin text-electric" />
                <p className="text-sm font-bold text-deepnavy">Analyzing multi-modal signals & generating unique guidance...</p>
              </div>
            ) : filteredRecommendations.length === 0 ? (
              <div className="flex flex-col items-center justify-center p-16 rounded-[2rem] bg-white shadow-card ring-1 ring-slate-200/80 text-center space-y-3">
                <AlertCircle className="h-10 w-10 text-amber-500" />
                <h3 className="text-lg font-black text-deepnavy">No Recommendations in this Category</h3>
                <p className="text-xs font-semibold text-slate-500 max-w-md">
                  No issues found matching the selected filter. Try selecting 'All Domains' or 'All Priorities'.
                </p>
              </div>
            ) : (
              filteredRecommendations.map((rec) => {
                const IconComponent = categoryIcons[rec.category] || Film;
                const priorityInfo = priorityStyles[rec.priority] || priorityStyles[1];

                return (
                  <motion.div
                    key={rec.id}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`group relative overflow-hidden rounded-[2rem] bg-white p-6 sm:p-7 shadow-card ring-1 ring-slate-200/80 border-l-[6px] ${priorityInfo.border} transition-all duration-200 hover:shadow-xl hover:ring-slate-300`}
                  >
                    {/* Top Row: Meta Badges & Expected Impact */}
                    <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-100">
                      <div className="flex flex-wrap items-center gap-2">
                        {/* Domain Icon Pill */}
                        <div
                          className="flex h-7 w-7 items-center justify-center rounded-xl text-white shadow-sm shrink-0"
                          style={{ backgroundColor: categoryColors[rec.category] || '#2563EB' }}
                        >
                          <IconComponent className="h-4 w-4" />
                        </div>

                        {/* Priority Badge */}
                        <span className={`inline-flex items-center rounded-full px-3 py-1 text-[11px] font-black uppercase tracking-wider border ring-1 ${priorityInfo.badge}`}>
                          {priorityInfo.label}
                        </span>

                        {/* Domain Tag */}
                        <span className="rounded-full bg-slate-100 px-3 py-1 text-[11px] font-bold text-slate-700">
                          {rec.category}
                        </span>

                        {/* Cut Timeframe */}
                        {rec.timeframe && (
                          <span className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-3 py-1 text-[11px] font-bold text-blue-700">
                            <Clock3 className="h-3.5 w-3.5" />
                            {rec.timeframe}
                          </span>
                        )}

                        {/* Scene Badge */}
                        <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-black text-slate-800">
                          Scene {rec.scene || 1}
                        </span>
                      </div>

                      {/* Green Expected Impact Badge */}
                      {rec.expectedImpact && (
                        <div className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-3.5 py-1 text-xs font-black text-emerald-700 border border-emerald-200 shadow-sm">
                          <TrendingUp className="h-3.5 w-3.5 text-emerald-600" />
                          <span>{rec.expectedImpact}</span>
                        </div>
                      )}
                    </div>

                    {/* Main Headline */}
                    <h3 className="mt-4 text-xl font-black text-slate-900 group-hover:text-electric transition-colors leading-tight">
                      {rec.title}
                    </h3>

                    {/* Dual Container Split: Actionable Fix & Multi-Modal Evidence */}
                    <div className="mt-4 grid gap-3.5 sm:grid-cols-2">
                      {/* Left: Actionable Fix for Editor (Highlighted Accent Container) */}
                      <div className="rounded-2xl bg-gradient-to-br from-blue-50/90 to-indigo-50/80 p-4 border border-blue-200/80 shadow-sm space-y-1.5">
                        <div className="flex items-center gap-1.5 text-xs font-black uppercase tracking-wider text-blue-800">
                          <Wand2 className="h-4 w-4 text-blue-600" />
                          <span>Actionable Fix for Editor</span>
                        </div>
                        <p className="text-sm font-bold leading-relaxed text-slate-900">
                          {rec.action}
                        </p>
                      </div>

                      {/* Right: Multi-Modal Diagnostic Finding */}
                      <div className="rounded-2xl bg-slate-50/90 p-4 border border-slate-200/80 space-y-1.5">
                        <div className="flex items-center gap-1.5 text-xs font-black uppercase tracking-wider text-slate-600">
                          <Activity className="h-4 w-4 text-slate-500" />
                          <span>Diagnostic Finding & Signal Evidence</span>
                        </div>
                        <p className="text-xs font-semibold leading-relaxed text-slate-700">
                          {rec.evidence}
                        </p>
                      </div>
                    </div>

                    {/* Card Footer: Source & Priority Score */}
                    <div className="mt-4 flex flex-wrap items-center justify-between gap-2 pt-3 border-t border-slate-100 text-xs">
                      <div className="inline-flex items-center gap-1.5 font-bold text-slate-500">
                        <Cpu className="h-3.5 w-3.5 text-electric" />
                        <span>Source: <strong className="text-slate-800">{rec.component}</strong></span>
                      </div>
                      <span className="text-[11px] font-bold text-slate-400">
                        Target Focus: <strong className="text-slate-600">{rec.category} Calibration</strong>
                      </span>
                    </div>
                  </motion.div>
                );
              })
            )}
          </div>
        </div>

        {/* Right Column: Component Breakdown & Scene Roadmap */}
        <div className="space-y-6 lg:col-span-4">
          <SectionTitle
            eyebrow="AI Breakdown"
            title="Component Integration"
            description="Confidence across AI pipeline stages."
          />

          {/* AI Components Breakdown Card */}
          <div className="rounded-[2rem] bg-white p-6 shadow-card ring-1 ring-slate-200/80 space-y-4">
            <h4 className="text-xs font-black uppercase tracking-wider text-deepnavy">Component Confidence Weights</h4>

            <div className="space-y-3.5">
              <div>
                <div className="flex justify-between text-xs font-bold">
                  <span className="text-slate-600">Audio Extraction (Component 01)</span>
                  <span className="text-electric font-black">{guidance?.componentScores.audio || 80}%</span>
                </div>
                <div className="mt-1.5 h-2 w-full overflow-hidden rounded-full bg-slate-100">
                  <div className="h-full bg-electric rounded-full" style={{ width: `${guidance?.componentScores.audio || 80}%` }} />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs font-bold">
                  <span className="text-slate-600">Visual Detection (Component 02)</span>
                  <span className="text-tealbrand font-black">{guidance?.componentScores.visual || 88}%</span>
                </div>
                <div className="mt-1.5 h-2 w-full overflow-hidden rounded-full bg-slate-100">
                  <div className="h-full bg-tealbrand rounded-full" style={{ width: `${guidance?.componentScores.visual || 88}%` }} />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs font-bold">
                  <span className="text-slate-600">Metadata Analysis (Component 03)</span>
                  <span className="text-purplebrand font-black">{guidance?.componentScores.metadata || 84}%</span>
                </div>
                <div className="mt-1.5 h-2 w-full overflow-hidden rounded-full bg-slate-100">
                  <div className="h-full bg-purplebrand rounded-full" style={{ width: `${guidance?.componentScores.metadata || 84}%` }} />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs font-bold">
                  <span className="text-slate-600">Emotional Fusion (Component 04)</span>
                  <span className="text-magentabrand font-black">{guidance?.componentScores.fusion || 90}%</span>
                </div>
                <div className="mt-1.5 h-2 w-full overflow-hidden rounded-full bg-slate-100">
                  <div className="h-full bg-magentabrand rounded-full" style={{ width: `${guidance?.componentScores.fusion || 90}%` }} />
                </div>
              </div>
            </div>
          </div>

          {/* Timed Scene Roadmap */}
          <div className="rounded-[2rem] bg-white p-6 shadow-card ring-1 ring-slate-200/80 space-y-4">
            <div className="flex items-center gap-2">
              <ListChecks className="h-5 w-5 text-electric" />
              <h4 className="text-xs font-black uppercase tracking-wider text-deepnavy">Scene-by-Scene Roadmap</h4>
            </div>

            <div className="space-y-3 max-h-[580px] overflow-y-auto pr-1">
              {(guidance?.timings || []).map((t, idx) => (
                <div key={idx} className="rounded-2xl border border-slate-100 bg-slate-50/70 p-3.5 space-y-1 transition hover:bg-slate-100/80">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-black text-electric">{t.timeframe}</span>
                    <span className="rounded-full bg-slate-200/80 px-2.5 py-0.5 text-[10px] font-bold text-slate-700">
                      {t.scene}
                    </span>
                  </div>
                  <p className="text-xs font-bold text-deepnavy">{t.currentEmotion}</p>
                  <p className="text-[11px] font-semibold text-slate-600 leading-relaxed">{t.suggestion}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
