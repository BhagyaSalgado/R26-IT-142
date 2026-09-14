import { ChangeEvent, FormEvent, useState } from 'react';
import { AlertCircle, CloudUpload, Film, Loader2, PlayCircle } from 'lucide-react';
import type { AnalysisResult } from '../types';
import { componentSummaries } from '../data/mockBackend';
import { analyzeTrailerPopularity } from '../services/popularityService';
import type { PopularityAnalysisData } from '../types/popularity';

interface UploadPanelProps {
  onCompleted: (result: AnalysisResult) => void;
}

export default function UploadPanel({ onCompleted }: UploadPanelProps) {
  const [trailerUrl, setTrailerUrl] = useState('https://youtube.com/watch?v=dummy-trailer');
  const [trailerName, setTrailerName] = useState('Shadow Horizon - Official Trailer');
  const [selectedFile, setSelectedFile] = useState<string>('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [mode, setMode] = useState<'youtube' | 'upload'>('youtube');
  const [error, setError] = useState('');

  const handleFile = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setSelectedFile(file.name);
    setMode('upload');
    setTrailerName(file.name.replace(/\.[^/.]+$/, ''));
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');

    if (mode === 'upload') {
      setError('Video file upload is not available in the backend yet. Use a YouTube URL for saved analysis.');
      return;
    }

    setIsAnalyzing(true);

    try {
      const backendResult = await analyzeTrailerPopularity(trailerUrl);
      onCompleted(mapPopularityToDashboardResult(backendResult, trailerName));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not analyze this trailer.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="">
      <div className="rounded-[2rem] bg-white p-6 shadow-card ring-1 ring-slate-200/80">
        <div className="mb-6 flex items-center gap-3">
          <div className="rounded-2xl bg-electric/10 p-3 text-electric">
            <Film className="h-6 w-6" />
          </div>
          <div>
            <h3 className="text-xl font-black text-deepnavy">Trailer input</h3>
            <p className="text-sm text-slatebrand/60">Use a YouTube link or upload field.</p>
          </div>
        </div>

        <div className="grid gap-4">
          <label className="grid gap-2">
            <span className="text-sm font-bold text-deepnavy">Trailer name</span>
            <input
              value={trailerName}
              onChange={(event) => setTrailerName(event.target.value)}
              className="rounded-2xl border border-slate-200 bg-lightbrand px-4 py-3 text-sm font-semibold text-deepnavy outline-none transition focus:border-electric focus:bg-white focus:ring-4 focus:ring-electric/10"
              placeholder="Enter trailer title"
            />
          </label>

          <label className="grid gap-2">
            <span className="text-sm font-bold text-deepnavy">YouTube trailer URL</span>
            <input
              value={trailerUrl}
              onChange={(event) => {
                setTrailerUrl(event.target.value);
                setMode('youtube');
              }}
              className="rounded-2xl border border-slate-200 bg-lightbrand px-4 py-3 text-sm font-semibold text-deepnavy outline-none transition focus:border-electric focus:bg-white focus:ring-4 focus:ring-electric/10"
              placeholder="https://youtube.com/watch?v=..."
            />
          </label>

          <label className="group flex cursor-pointer flex-col items-center justify-center rounded-[1.5rem] border-2 border-dashed border-electric/25 bg-electric/5 px-6 py-8 text-center transition hover:border-electric/60 hover:bg-electric/10">
            <CloudUpload className="h-10 w-10 text-electric" />
            <span className="mt-3 text-sm font-black text-deepnavy">Upload trailer file</span>
            <span className="mt-1 text-xs text-slatebrand/60">MP4, MOV or WEBM for future backend integration</span>
            <input type="file" accept="video/*" className="hidden" onChange={handleFile} />
            {selectedFile && <span className="mt-3 rounded-full bg-white px-3 py-1 text-xs font-bold text-electric shadow-sm">{selectedFile}</span>}
          </label>
        </div>

        {error && (
          <div className="mt-5 flex items-start gap-3 rounded-2xl bg-rose-50 p-4 text-sm font-semibold text-rose-700 ring-1 ring-rose-100">
            <AlertCircle className="mt-0.5 h-5 w-5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <button
          type="submit"
          disabled={isAnalyzing}
          className="mt-6 flex w-full items-center justify-center gap-3 rounded-2xl bg-deepnavy px-6 py-4 text-sm font-black uppercase tracking-[0.18em] text-white shadow-glow transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-70"
        >
          {isAnalyzing ? <Loader2 className="h-5 w-5 animate-spin" /> : <PlayCircle className="h-5 w-5" />}
          {isAnalyzing ? 'Analysing...' : 'Run analysis'}
        </button>
      </div>

      
    </form>
  );
}

function mapReaction(value: string): AnalysisResult['overallReaction'] {
  const reaction = value.toUpperCase();

  if (reaction.includes('HIGH')) return 'High';
  if (reaction.includes('LOW')) return 'Low';
  return 'Moderate';
}

function mapPopularityToDashboardResult(
  data: PopularityAnalysisData,
  fallbackTitle: string
): AnalysisResult {
  const confidence = Math.round(data.prediction.confidence_score * 100);
  const engagementRate = Number((data.features.engagement_rate * 100).toFixed(2));
  const likeRatio = Number((data.features.like_ratio * 100).toFixed(2));
  const velocity = Math.min(100, Math.round(data.features.views_per_day / 1000));
  const audienceScore = Math.round(data.features.popularity_score);

  return {
    id: data.video_id,
    trailerTitle: data.trailer.title || fallbackTitle,
    sourceUrl: data.trailer.youtube_url,
    generatedAt: data.prediction.created_at || new Date().toLocaleString(),
    overallReaction: mapReaction(data.prediction.predicted_reaction),
    confidence,
    audienceScore,
    engagementForecast: Math.min(100, Math.round(data.features.popularity_score + engagementRate)),
    sentiment: {
      positive: Math.max(0, Math.min(100, audienceScore)),
      neutral: Math.max(0, Math.min(100, 100 - audienceScore)),
      negative: Math.max(0, Math.min(100, 100 - confidence))
    },
    popularity: {
      views: data.metrics.view_count,
      likes: data.metrics.like_count,
      comments: data.metrics.comment_count,
      engagementRate,
      likeRatio,
      velocity
    },
    sceneIntensities: [
      {
        scene: 'Opening',
        timestamp: '0:00',
        visualEmotion: 'Interest',
        sceneType: 'Trailer metrics',
        intensityScore: Math.min(100, audienceScore),
        motionLevel: audienceScore > 70 ? 'High' : audienceScore > 40 ? 'Medium' : 'Low',
        audioEnergy: Math.min(100, confidence)
      }
    ],
    recommendations: [
      {
        id: 1,
        title: 'Backend recommendation',
        priority: 1,
        evidence: data.prediction.recommendation || 'Prediction generated from saved backend features.',
        action: data.prediction.recommendation || 'Review engagement, title, thumbnail, and publishing timing.',
        component: data.prediction.model_name
      }
    ],
    components: componentSummaries,
    topFeatures: [
      { feature: 'Popularity score', importance: data.features.popularity_score },
      { feature: 'Engagement rate', importance: engagementRate },
      { feature: 'Like ratio', importance: likeRatio },
      { feature: 'Views per day', importance: Math.min(100, velocity) }
    ],
    commentTopics: [],
    regionalInterest: [],
    modelMetrics: [
      { metric: data.prediction.model_name, value: confidence },
      { metric: data.prediction.model_version, value: audienceScore }
    ],
    finalModelOutput: [],
    audioFeatureOutput: [],
    visualFeatureOutput: []
  };
}
