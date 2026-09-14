import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { motion } from 'framer-motion';
import { Activity, CheckCircle2, Clock3, Play, X } from 'lucide-react';

import type { VideoAnalysisResponse } from '../../services/videoEmotionApi';

function formatLocalDateTime(value: string | null | undefined) {
  if (!value) return 'Date unavailable';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Date unavailable';
  return new Intl.DateTimeFormat(undefined, {
    year: 'numeric', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit', second: '2-digit'
  }).format(date);
}

// Present a complete analysis in a full-screen workspace without changing routes.
export function TrailerResultPopup({
  videoName,
  videoUrl,
  result,
  analyzedAt,
  onClose
}: {
  videoName: string;
  videoUrl: string;
  result: VideoAnalysisResponse;
  analyzedAt?: string | null;
  onClose: () => void;
}) {
  return createPortal(
    <div
      className="fixed inset-0 z-[100] bg-[#eef2f7]"
      onClick={onClose}
      role="presentation"
    >
      <div
        className="h-screen w-screen overflow-y-auto bg-[radial-gradient(circle_at_top_right,rgba(37,99,235,0.10),transparent_30rem),linear-gradient(180deg,#f8fafc_0%,#eef2f7_100%)] p-4 sm:p-6 lg:p-8"
        onClick={(event) => event.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="trailer-result-title"
      >
        <div className="relative mb-8 flex w-full flex-col gap-5 overflow-hidden rounded-[2rem] bg-deepnavy p-6 text-white shadow-glow sm:flex-row sm:items-center sm:justify-between sm:p-8">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.25em] text-tealbrand">
              Live API output
            </p>
            <h2 id="trailer-result-title" className="mt-2 text-2xl font-black text-white sm:text-3xl">
              Trailer Analysis Result
            </h2>
            <p className="mt-2 text-sm text-white/55">
              Uploaded video:{' '}
              <span className="font-bold text-white">{videoName}</span>
            </p>
            {analyzedAt && (
              <p className="flex flex-wrap items-center gap-2 mt-2 text-xs font-semibold text-white/45">
                <Clock3 className="w-4 h-4 text-tealbrand" />
                Analyzed {formatLocalDateTime(analyzedAt)}
              </p>
            )}
          </div>

          <button
            type="button"
            onClick={onClose}
            className="inline-flex items-center justify-center gap-2 rounded-2xl bg-white px-5 py-3 text-sm font-black text-deepnavy shadow-lg transition hover:-translate-y-0.5"
          >
            <X className="w-4 h-4" />
            Close
          </button>
        </div>

        <ApiResult result={result} videoUrl={videoUrl} videoName={videoName} />
      </div>
    </div>,
    document.body
  );
}

function formatApiLabel(value: string) {
  // Normalize backend field names and values for creator-facing tables.
  return value
    .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
    .replace(/_/g, ' ')
    .replace(/^./, (letter) => letter.toUpperCase());
}

function formatApiValue(value: unknown): string {
  if (value === null || value === undefined) return '—';
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function asRows(value: unknown): Array<Record<string, unknown>> {
  return Array.isArray(value)
    ? value.filter(
        (item): item is Record<string, unknown> =>
          Boolean(item) && typeof item === 'object' && !Array.isArray(item)
      )
    : [];
}

function toNumber(value: unknown) {
  const number = Number(value);
  return Number.isFinite(number) ? number : 0;
}

type OutputColumn = {
  label: string;
  aliases: string[];
  format?: 'score' | 'number';
};

const FINAL_OUTPUT_COLUMNS: OutputColumn[] = [
  { label: 'Scene', aliases: ['scene', 'scene_id', 'scene_number'] },
  { label: 'Scene Type', aliases: ['scene_type', 'sceneType', 'type'] },
  { label: 'M', aliases: ['M', 'motion', 'motion_intensity'], format: 'score' },
  { label: 'A', aliases: ['A', 'audio_energy', 'audioEnergy'], format: 'score' },
  { label: 'O', aliases: ['O', 'object_score', 'objectScore'], format: 'score' },
  { label: 'F', aliases: ['F', 'face_emotion_confidence', 'faceEmotionConfidence', 'facial_emotion_confidence', 'emotion_confidence', 'face_confidence'], format: 'score' },
  { label: 'EI', aliases: ['EI', 'emotional_intensity', 'intensity_score'], format: 'score' },
  { label: 'Level', aliases: ['level', 'intensity_level', 'engagement_level'] }
];

const AUDIO_OUTPUT_COLUMNS: OutputColumn[] = [
  { label: 'Scene', aliases: ['scene', 'scene_id', 'scene_number'] },
  { label: 'Time', aliases: ['time', 'timestamp', 'time_range'] },
  { label: 'Tempo (BPM)', aliases: ['tempo_bpm', 'tempoBpm', 'tempo', 'bpm'], format: 'number' },
  { label: 'Audio Energy (A)', aliases: ['audio_energy', 'audioEnergy', 'A'], format: 'score' },
  { label: 'MFCC Mean', aliases: ['mfcc_mean', 'mfccMean'], format: 'number' },
  { label: 'Spectral Centroid', aliases: ['spectral_centroid', 'spectralCentroid'], format: 'number' },
  { label: 'Audio Mood', aliases: ['audio_mood', 'audioMood', 'mood'] }
];

const VISUAL_OUTPUT_COLUMNS: OutputColumn[] = [
  { label: 'Scene', aliases: ['scene', 'scene_id', 'scene_number'] },
  { label: 'Time', aliases: ['time', 'timestamp', 'time_range'] },
  { label: 'Objects', aliases: ['objects', 'detected_objects', 'object_labels'] },
  { label: 'Object Score (O)', aliases: ['object_score', 'objectScore', 'O'], format: 'score' },
  { label: 'Face Emotion', aliases: ['face_emotion', 'faceEmotion', 'facial_emotion', 'visual_emotion', 'emotion'] },
  { label: 'Face Emotion Confidence (F)', aliases: ['face_emotion_confidence', 'faceEmotionConfidence', 'facial_emotion_confidence', 'emotion_confidence', 'face_confidence', 'F'], format: 'score' },
  { label: 'Motion (M)', aliases: ['motion', 'motion_intensity', 'M'], format: 'score' },
  { label: 'Scene Type', aliases: ['scene_type', 'sceneType', 'type'] }
];

function firstValue(row: Record<string, unknown>, aliases: string[]) {
  const key = aliases.find((alias) => row[alias] !== undefined && row[alias] !== null);
  return key ? row[key] : undefined;
}

function formatOutputValue(value: unknown, format?: OutputColumn['format']) {
  if (value === undefined || value === null || value === '') return '—';
  if (Array.isArray(value)) return value.map(String).join(', ');

  const numericValue = Number(value);
  if (format === 'score' && Number.isFinite(numericValue)) return numericValue.toFixed(2);
  if (format === 'number' && Number.isFinite(numericValue)) {
    return Number.isInteger(numericValue) ? String(numericValue) : numericValue.toFixed(2);
  }
  return formatApiValue(value);
}

function getAnalysisPayload(result: VideoAnalysisResponse) {
  const nestingKeys = ['data', 'result', 'analysis', 'prediction', 'outputs'];
  const outputKeys = [
    'final_system_output', 'finalSystemOutput', 'final_output',
    'audio_feature_output', 'audioFeatureOutput', 'audio_features',
    'visual_feature_output', 'visualFeatureOutput', 'visual_features'
  ];
  const candidates: Array<Record<string, unknown>> = [result];

  // Inspect common response wrappers without assuming one backend envelope shape.
  for (let index = 0; index < candidates.length && candidates.length < 20; index += 1) {
    nestingKeys.forEach((key) => {
      const nested = asRecord(candidates[index][key]);
      if (Object.keys(nested).length > 0 && !candidates.includes(nested)) candidates.push(nested);
    });
  }

  return candidates.reduce((best, candidate) => {
    const score = outputKeys.filter((key) => candidate[key] !== undefined).length;
    const bestScore = outputKeys.filter((key) => best[key] !== undefined).length;
    return score > bestScore ? candidate : best;
  }, result);
}

function getOutputRows(payload: Record<string, unknown>, aliases: string[]) {
  for (const alias of aliases) {
    const value = payload[alias];
    if (Array.isArray(value)) return asRows(value);

    const record = asRecord(value);
    if (Array.isArray(record.items)) return asRows(record.items);
    const recordValues = Object.values(record);
    if (recordValues.length > 0 && recordValues.every((item) => item && typeof item === 'object')) {
      return asRows(recordValues);
    }
  }
  return [];
}

function useVideoThumbnail(videoUrl: string, fallbackThumbnailUrl?: string) {
  // Capture a representative video frame or use the backend generated scene thumbnail
  const [thumbnailUrl, setThumbnailUrl] = useState(fallbackThumbnailUrl || '');

  useEffect(() => {
    if (fallbackThumbnailUrl) {
      setThumbnailUrl(fallbackThumbnailUrl);
    }
  }, [fallbackThumbnailUrl]);

  useEffect(() => {
    if (!videoUrl) {
      if (!fallbackThumbnailUrl) setThumbnailUrl('');
      return;
    }

    let cancelled = false;
    const video = document.createElement('video');
    
    // Only set crossOrigin for remote http(s) URLs, never on blob: URLs
    if (videoUrl.startsWith('http://') || videoUrl.startsWith('https://')) {
      video.crossOrigin = 'anonymous';
    }
    
    video.preload = 'auto';
    video.muted = true;
    video.playsInline = true;

    const captureFrame = () => {
      if (cancelled || !video.videoWidth || !video.videoHeight) return;
      const canvas = document.createElement('canvas');
      const maximumWidth = 960;
      const scale = Math.min(1, maximumWidth / video.videoWidth);
      canvas.width = Math.round(video.videoWidth * scale);
      canvas.height = Math.round(video.videoHeight * scale);
      const context = canvas.getContext('2d');
      if (!context) return;

      try {
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        const dataUrl = canvas.toDataURL('image/jpeg', 0.85);
        if (dataUrl && dataUrl.length > 100) {
          setThumbnailUrl(dataUrl);
        }
      } catch {
        if (fallbackThumbnailUrl) {
          setThumbnailUrl(fallbackThumbnailUrl);
        }
      }
    };

    video.onloadeddata = captureFrame;
    video.oncanplay = captureFrame;
    video.onseeked = captureFrame;

    video.onloadedmetadata = () => {
      const duration = Number.isFinite(video.duration) ? video.duration : 0;
      video.currentTime = Math.min(1.5, Math.max(0.1, duration * 0.05));
    };

    video.onerror = () => {
      if (!cancelled && fallbackThumbnailUrl) {
        setThumbnailUrl(fallbackThumbnailUrl);
      }
    };

    video.src = videoUrl;
    video.load();

    return () => {
      cancelled = true;
      video.removeAttribute('src');
      video.load();
    };
  }, [videoUrl, fallbackThumbnailUrl]);

  return thumbnailUrl || fallbackThumbnailUrl || '';
}

// Convert the flexible API payload into stable collections used by each result section.
function ApiResult({
  result,
  videoUrl,
  videoName
}: {
  result: VideoAnalysisResponse;
  videoUrl: string;
  videoName: string;
}) {
  const payload = getAnalysisPayload(result);
  const insights = asRecord(payload.insights);
  const finalRows = getOutputRows(payload, ['final_system_output', 'finalSystemOutput', 'final_output']);
  const audioRows = getOutputRows(payload, ['audio_feature_output', 'audioFeatureOutput', 'audio_features']);
  const visualRows = getOutputRows(payload, ['visual_feature_output', 'visualFeatureOutput', 'visual_features']);
  
  // Calculate directly from the exact scene rows for 100% mathematical precision
  const totalScenes = finalRows.length > 0 ? finalRows.length : (toNumber(payload.total_scenes ?? result.total_scenes) || 0);
  const averageIntensity = finalRows.length > 0
    ? (finalRows.reduce((acc, row) => acc + toNumber(firstValue(row, ['EI', 'emotional_intensity', 'intensity_score'])), 0) / finalRows.length)
    : toNumber(insights.average_emotional_intensity);
  const peakScenes = finalRows.length > 0
    ? finalRows.filter((row) => toNumber(firstValue(row, ['EI', 'emotional_intensity', 'intensity_score'])) >= 0.70)
    : asRows(insights.high_intensity_scenes);
  const engagementLevel = (insights.engagement_level && insights.engagement_level !== 'Not available')
    ? String(insights.engagement_level)
    : (averageIntensity >= 0.70 ? 'High engagement trailer' : averageIntensity >= 0.40 ? 'Medium engagement trailer' : 'Low engagement trailer');

  const [isVideoPlayerOpen, setIsVideoPlayerOpen] = useState(false);
  const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
  const runId = String(firstValue(payload, ['run_id', 'id', 'firestore_id']) || '');
  const rawThumb = String(firstValue(payload, ['thumbnail_url', 'thumbnailUrl', 'thumbnail']) || '');
  const fallbackThumbnailUrl = rawThumb 
    ? (rawThumb.startsWith('http') ? rawThumb : `${apiBaseUrl}${rawThumb}`)
    : (runId ? `${apiBaseUrl}/api/v1/predict/history/${encodeURIComponent(runId)}/thumbnail` : '');

  const videoThumbnailUrl = useVideoThumbnail(videoUrl, fallbackThumbnailUrl);

  return (
    <div className="w-full max-w-full min-w-0 pb-8 space-y-8 overflow-x-hidden">
      <section className="relative overflow-hidden rounded-[2rem] bg-deepnavy p-6 text-white shadow-glow sm:p-8">
        <div className="absolute rounded-full -right-20 -top-24 h-72 w-72 bg-electric/30 blur-3xl" />
        <div className="absolute w-64 h-64 rounded-full -bottom-28 left-1/3 bg-magentabrand/20 blur-3xl" />
        <div className="relative">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/10 px-3 py-1.5 text-xs font-black uppercase tracking-[0.18em] text-tealbrand">
                <CheckCircle2 className="w-4 h-4" /> Analysis complete
              </div>
              <h3 className="mt-4 text-2xl font-black tracking-tight sm:text-3xl">
                Emotional performance overview
              </h3>
              <p className="max-w-2xl mt-2 text-sm leading-6 text-white/55">
                Start with the fused result, then review the audio and visual
                evidence behind each scene score.
              </p>
            </div>

          </div>

          <div className="grid gap-3 mt-7 sm:grid-cols-2 xl:grid-cols-4">
            <ResultMetric label="Scenes analyzed" value={String(totalScenes)} helper="Complete timeline" />
            <ResultMetric label="Average intensity" value={averageIntensity.toFixed(2)} helper="Fused EI score" accent />
            <ResultMetric label="Engagement" value={engagementLevel} helper="Predicted response" />
            <ResultMetric label="Peak scenes" value={String(peakScenes.length)} helper="High-intensity moments" />
          </div>
        </div>
      </section>

      <section className="overflow-hidden rounded-[2rem] border border-slate-200 bg-white shadow-card">
        <div className="flex flex-col gap-3 px-5 py-4 border-b border-slate-100 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center min-w-0 gap-3">
            <span className="flex items-center justify-center w-10 h-10 text-white shrink-0 rounded-xl bg-electric">
              <Play className="w-5 h-5" />
            </span>
            <div className="min-w-0">
              <p className="text-[10px] font-black uppercase tracking-[0.18em] text-electric">
                Uploaded trailer
              </p>
              <h3 className="text-lg font-black truncate text-deepnavy">
                {videoName}
              </h3>
            </div>
          </div>
          <p className="text-xs font-semibold text-slatebrand/45">
            Select the thumbnail to play
          </p>
        </div>

        <button
          type="button"
          onClick={() => videoUrl && setIsVideoPlayerOpen(true)}
          disabled={!videoUrl}
          className="relative block w-full overflow-hidden bg-black group disabled:cursor-not-allowed"
          aria-label={`Play ${videoName}`}
        >
          {videoThumbnailUrl ? (
            <img
              src={videoThumbnailUrl}
              alt={`Automatically generated preview for ${videoName}`}
              className="pointer-events-none mx-auto aspect-video max-h-[380px] w-full bg-black object-contain opacity-85 transition duration-300 group-hover:scale-[1.01] group-hover:opacity-65"
            />
          ) : videoUrl ? (
            <div className="flex aspect-video max-h-[380px] flex-col items-center justify-center gap-3 text-sm font-bold text-white/55">
              <Activity className="w-6 h-6 animate-spin text-tealbrand" />
              Generating video thumbnail...
            </div>
          ) : (
            <div className="flex aspect-video max-h-[380px] items-center justify-center text-sm font-bold text-white/50">
              Video preview unavailable
            </div>
          )}
          {videoUrl && (
            <span className="absolute inset-0 flex items-center justify-center">
              <span className="flex h-20 w-20 items-center justify-center rounded-full bg-white/95 text-electric shadow-[0_20px_60px_rgba(0,0,0,0.45)] ring-8 ring-white/15 transition duration-300 group-hover:scale-110">
                <Play className="w-8 h-8 ml-1 fill-current" />
              </span>
            </span>
          )}
        </button>
      </section>

      <section className="grid gap-6 xl:grid-cols-2">
        <ResultPanel number="01" eyebrow="Creator insight" title="Peak emotional moments" description="The strongest audience-attention moments in the trailer.">
          {peakScenes.length > 0 ? (
            <div className="grid gap-3 mt-6 sm:grid-cols-2">
              {peakScenes.map((scene, index) => (
                <div key={`${formatApiValue(scene.scene)}-${index}`} className="rounded-2xl border border-electric/10 bg-gradient-to-br from-electric/[0.07] to-purplebrand/[0.05] p-5">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-xs font-black uppercase tracking-[0.16em] text-electric">Scene {formatApiValue(scene.scene)}</p>
                      <h4 className="mt-2 text-xl font-black text-deepnavy">{formatApiValue(scene.scene_type)}</h4>
                      <p className="mt-1 text-sm font-semibold text-slatebrand/50">{formatApiValue(scene.time)}</p>
                    </div>
                    <div className="flex items-center justify-center text-lg font-black text-white shadow-lg h-14 w-14 rounded-2xl bg-deepnavy">
                      {toNumber(scene.EI).toFixed(2)}
                    </div>
                  </div>
                  <div className="h-2 mt-5 overflow-hidden bg-white rounded-full ring-1 ring-slate-200">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-electric via-purplebrand to-magentabrand"
                      style={{ width: `${Math.min(100, toNumber(scene.EI) * 100)}%` }}
                    />
                  </div>
                  <div className="mt-3 flex items-center justify-between text-[10px] font-black uppercase tracking-[0.12em] text-slatebrand/40">
                    <span>Emotional intensity</span>
                    <span>{Math.round(toNumber(scene.EI) * 100)}%</span>
                  </div>
                </div>
              ))}
            </div>
          ) : <EmptyResult message="No high-intensity scenes were returned." />}
        </ResultPanel>

        <ResultPanel number="02" eyebrow="Emotional mix" title="Mood distribution" description="Visual emotion and soundtrack mood across the trailer.">
          <div className="grid gap-6 mt-6 sm:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2">
            <DistributionBars title="Visual emotion" values={asRecord(insights.video_emotion_distribution)} />
            <DistributionBars title="Audio mood" values={asRecord(insights.audio_mood_distribution)} />
          </div>
        </ResultPanel>
      </section>

      {isVideoPlayerOpen && videoUrl &&
        createPortal(
          <div
            className="fixed inset-0 z-[140] flex items-center justify-center bg-black/90 p-4 backdrop-blur-md"
            onClick={() => setIsVideoPlayerOpen(false)}
            role="presentation"
          >
            <div
              className="relative w-full max-w-6xl"
              onClick={(event) => event.stopPropagation()}
              role="dialog"
              aria-modal="true"
              aria-label="Video player"
            >
              <button
                type="button"
                onClick={() => setIsVideoPlayerOpen(false)}
                className="absolute right-0 inline-flex items-center gap-2 px-4 py-2 text-sm font-black text-white transition -top-14 rounded-xl bg-white/10 hover:bg-white hover:text-deepnavy"
              >
                <X className="w-4 h-4" /> Close
              </button>
              <video
                src={videoUrl}
                controls
                autoPlay
                playsInline
                className="max-h-[82vh] w-full rounded-2xl bg-black shadow-2xl ring-1 ring-white/15"
              >
                Your browser does not support video playback.
              </video>
            </div>
          </div>,
          document.body
        )}

      <section className="grid w-full min-w-0 grid-cols-1 gap-6 xl:grid-cols-3">
        <OutputSection
          number="03"
          eyebrow="Primary model output"
          title="Final System Output"
          description="Scene type, fused motion, audio, object and facial-emotion scores returned by the backend."
          rows={finalRows}
          columns={FINAL_OUTPUT_COLUMNS}
          emptyMessage="The API did not return final scene output."
        />
        <OutputSection
          number="04"
          eyebrow="Audio evidence"
          title="Audio Feature Extraction Output"
          description="Tempo, energy, MFCC, spectral centroid and predicted audio mood for each scene."
          rows={audioRows}
          columns={AUDIO_OUTPUT_COLUMNS}
          emptyMessage="No audio feature rows were returned."
        />
        <OutputSection
          number="05"
          eyebrow="Visual evidence"
          title="Visual Feature Detection Output"
          description="Detected objects, face emotion confidence, motion and scene type for each scene."
          rows={visualRows}
          columns={VISUAL_OUTPUT_COLUMNS}
          emptyMessage="No visual feature rows were returned."
        />
      </section>

    </div>
  );
}

function ResultMetric({ label, value, helper, accent = false }: { label: string; value: string; helper: string; accent?: boolean }) {
  return (
    <div className={`rounded-2xl border p-4 ${accent ? 'border-tealbrand/25 bg-tealbrand/15' : 'border-white/10 bg-white/10'}`}>
      <p className="text-[10px] font-black uppercase tracking-[0.17em] text-white/40">{label}</p>
      <p className={`mt-2 break-words text-2xl font-black ${accent ? 'text-tealbrand' : 'text-white'}`}>{value}</p>
      <p className="mt-1 text-xs text-white/40">{helper}</p>
    </div>
  );
}

function SectionHeading({ number, eyebrow, title, description }: { number: string; eyebrow: string; title: string; description: string }) {
  return (
    <div className="flex items-start gap-4">
      <span className="flex items-center justify-center w-10 h-10 text-xs font-black text-white shrink-0 rounded-xl bg-deepnavy">{number}</span>
      <div>
        <p className="text-[10px] font-black uppercase tracking-[0.18em] text-electric">{eyebrow}</p>
        <h3 className="mt-1 text-lg font-black text-deepnavy sm:text-xl">{title}</h3>
        <p className="max-w-3xl mt-2 text-sm leading-6 text-slatebrand/55">{description}</p>
      </div>
    </div>
  );
}

function ResultPanel({ number, eyebrow, title, description, children }: { number: string; eyebrow: string; title: string; description: string; children: React.ReactNode }) {
  return (
    <div className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-card sm:p-7">
      <SectionHeading number={number} eyebrow={eyebrow} title={title} description={description} />
      {children}
    </div>
  );
}

// Scale distribution values relative to the largest category for easy comparison.
function DistributionBars({ title, values }: { title: string; values: Record<string, unknown> }) {
  const entries = Object.entries(values).sort(
    ([, first], [, second]) => toNumber(second) - toNumber(first)
  );
  const total = entries.reduce((sum, [, value]) => sum + toNumber(value), 0);
  const palette = [
    'from-electric to-tealbrand',
    'from-purplebrand to-magentabrand',
    'from-amber-400 to-orange-500',
    'from-emerald-400 to-teal-500'
  ];

  return (
    <div className="p-4 rounded-2xl bg-lightbrand/70 ring-1 ring-slate-200/70">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-black text-deepnavy">{title}</p>
        <span className="rounded-full bg-white px-2.5 py-1 text-[10px] font-black uppercase tracking-[0.12em] text-slatebrand/45 shadow-sm">
          {total} scenes
        </span>
      </div>
      {entries.length > 0 ? (
        <div className="mt-5 space-y-4">
          {entries.map(([label, value], index) => {
            const count = toNumber(value);
            const percentage = total > 0 ? (count / total) * 100 : 0;
            return (
              <div key={label}>
                <div className="flex items-center justify-between mb-2 text-xs font-bold">
                  <span className="text-slatebrand/65">{formatApiLabel(label)}</span>
                  <span className="text-deepnavy">{count} · {Math.round(percentage)}%</span>
                </div>
                <div className="h-2.5 overflow-hidden rounded-full bg-white shadow-inner">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${Math.max(4, percentage)}%` }}
                    transition={{ duration: 0.7, delay: index * 0.08, ease: 'easeOut' }}
                    className={`h-full rounded-full bg-gradient-to-r ${palette[index % palette.length]}`}
                  />
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <p className="mt-4 text-sm text-slatebrand/45">No distribution data.</p>
      )}
    </div>
  );
}

// Reuse one output shell for final, audio, and visual evidence tables.
function OutputSection({ number, eyebrow, title, description, rows, columns, emptyMessage }: { number: string; eyebrow: string; title: string; description: string; rows: Array<Record<string, unknown>>; columns: OutputColumn[]; emptyMessage: string }) {
  return (
    <section className="w-full min-w-0 max-w-full overflow-hidden rounded-[2rem] border border-slate-200 bg-white p-4 shadow-card sm:p-6">
      <div className="px-1 pb-5"><SectionHeading number={number} eyebrow={eyebrow} title={title} description={description} /></div>
      {rows.length > 0 ? (
        <ResultTable
          title={`${rows.length} scene${rows.length === 1 ? '' : 's'} returned`}
          description="Scroll horizontally to review all model fields."
          columns={columns.map((column) => column.label)}
          rows={rows.map((row) =>
            columns.map((column) =>
              formatOutputValue(firstValue(row, column.aliases), column.format)
            )
          )}
        />
      ) : <EmptyResult message={emptyMessage} />}
    </section>
  );
}

function EmptyResult({ message }: { message: string }) {
  return <div className="px-5 py-8 mt-5 text-sm font-semibold text-center border border-dashed rounded-2xl border-slate-200 bg-lightbrand/60 text-slatebrand/45">{message}</div>;
}

function ResultTable({
  title,
  description,
  columns,
  rows
}: {
  title: string;
  description: string;
  columns: string[];
  rows: Array<Array<string | number>>;
}) {
  return (
    <div className="w-full min-w-0 max-w-full overflow-hidden rounded-[1.5rem] border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-5">
        <h3 className="text-xl font-black text-deepnavy">{title}</h3>

        <p className="mt-1 text-sm text-slatebrand/60">{description}</p>
      </div>

      <div className="w-full max-w-full overflow-x-auto overscroll-x-contain">
        <table className="min-w-[760px] text-sm text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-200 bg-lightbrand">
              {columns.map((column) => (
                <th
                  key={column}
                  className="px-4 py-3 font-black text-deepnavy"
                >
                  {column}
                </th>
              ))}
            </tr>
          </thead>

          <tbody>
            {rows.map((row, rowIndex) => (
              <tr
                key={rowIndex}
                className="border-b border-slate-100 last:border-b-0"
              >
                {row.map((cell, cellIndex) => (
                  <td
                    key={cellIndex}
                    className="px-4 py-3 font-semibold text-slatebrand/75"
                  >
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
