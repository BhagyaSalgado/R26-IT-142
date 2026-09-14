import React, { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Activity, BrainCircuit, CheckCircle2, Clock3,
  Film, Play, Search, Sparkles
} from 'lucide-react';

import { AnalysisLoadingOverlay } from '../components/emotion/AnalysisLoadingOverlay';

import { TrailerResultPopup } from '../components/emotion/TrailerResultPopup';
import {
  analyzeEmotionVideo,
  getEmotionHistory,
  getEmotionHistoryDetail,
  type EmotionHistoryDetail,
  type EmotionHistoryItem,
  type VideoAnalysisResponse
} from '../services/videoEmotionApi';

function formatLocalDateTime(value: string | null | undefined) {
  if (!value) return 'Date unavailable';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Date unavailable';
  return new Intl.DateTimeFormat(undefined, {
    year: 'numeric', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit', second: '2-digit'
  }).format(date);
}

export default function EmotionAnalysisPage() {
  // Page-level state coordinates uploads, analysis progress, history, and result modals.
  const [selectedVideo, setSelectedVideo] = useState<File | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [showResultPopup, setShowResultPopup] = useState(false);
  const [analysisResult, setAnalysisResult] =
    useState<VideoAnalysisResponse | null>(null);
  const [analysisError, setAnalysisError] = useState('');
  const [videoPreviewUrl, setVideoPreviewUrl] = useState('');
  const [emotionHistory, setEmotionHistory] = useState<EmotionHistoryItem[]>([]);
  const [isHistoryLoading, setIsHistoryLoading] = useState(true);
  const [historyError, setHistoryError] = useState('');
  const [historySearch, setHistorySearch] = useState('');
  const [historyPreview, setHistoryPreview] =
    useState<EmotionHistoryDetail | null>(null);
  const [loadingHistoryId, setLoadingHistoryId] = useState<string | null>(null);
  const [historyDetailError, setHistoryDetailError] = useState('');
  const analysisAbortController = useRef<AbortController | null>(null);

  // Keep saved emotion analyses in sync after page load and each completed run.
  const loadEmotionHistory = async () => {
    setIsHistoryLoading(true);
    setHistoryError('');

    try {
      setEmotionHistory(await getEmotionHistory());
    } catch (error) {
      setHistoryError(
        error instanceof Error
          ? error.message
          : 'Unable to load previous emotion analyses.'
      );
    } finally {
      setIsHistoryLoading(false);
    }
  };

  useEffect(() => {
    void loadEmotionHistory();
  }, []);

  // Browser object URLs provide a local preview and must be released when the file changes.
  useEffect(() => {
    if (!selectedVideo) {
      setVideoPreviewUrl('');
      return;
    }

    const objectUrl = URL.createObjectURL(selectedVideo);
    setVideoPreviewUrl(objectUrl);

    return () => URL.revokeObjectURL(objectUrl);
  }, [selectedVideo]);

  useEffect(() => {
    if (!isAnalyzing && !showResultPopup && !historyPreview) return;

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [historyPreview, isAnalyzing, showResultPopup]);

  // Load the full saved result only when the user chooses a history item.
  const handleHistoryPreview = async (item: EmotionHistoryItem) => {
    if (loadingHistoryId) return;

    setLoadingHistoryId(item.id);
    setHistoryDetailError('');
    try {
      setHistoryPreview(await getEmotionHistoryDetail(item.id));
    } catch (error) {
      setHistoryDetailError(
        error instanceof Error
          ? error.message
          : 'Unable to open this saved analysis.'
      );
    } finally {
      setLoadingHistoryId(null);
    }
  };

  const handleVideoUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];

    if (!file) return;

    setSelectedVideo(file);
    setAnalysisResult(null);
    setAnalysisError('');
    setShowResultPopup(false);
  };

  // Run one cancellable video analysis and refresh history after a successful response.
  const handleAnalyzeVideo = async () => {
    if (!selectedVideo || isAnalyzing) return;

    const controller = new AbortController();
    analysisAbortController.current = controller;
    setIsAnalyzing(true);
    setAnalysisError('');

    try {
      const result = await analyzeEmotionVideo(selectedVideo, controller.signal);
      setAnalysisResult(result);
      setShowResultPopup(true);
      void loadEmotionHistory();
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') {
        setAnalysisError('Video analysis was stopped.');
      } else {
        setAnalysisError(
          error instanceof Error
            ? error.message
            : 'Unable to analyze this video. Please try again.'
        );
      }
    } finally {
      if (analysisAbortController.current === controller) {
        analysisAbortController.current = null;
      }
      setIsAnalyzing(false);
    }
  };

  const stopVideoAnalysis = () => {
    analysisAbortController.current?.abort();
  };

  const normalizedHistorySearch = historySearch.trim().toLowerCase();
  const filteredEmotionHistory = emotionHistory.filter((item) => {
    if (!normalizedHistorySearch) return true;
    const searchableValues = [
      item.filename,
      item.engagement_level,
      formatLocalDateTime(item.created_at),
      `${item.total_scenes} scenes`,
      `${item.high_intensity_scenes} peaks`,
      String(item.average_emotional_intensity)
    ];
    return searchableValues.some((value) =>
      value.toLowerCase().includes(normalizedHistorySearch)
    );
  });

  return (
    <div className="space-y-6">
      <section className="relative overflow-hidden rounded-[2.5rem] bg-deepnavy px-6 py-8 text-white shadow-glow sm:px-9 sm:py-10 lg:px-12">
        <div className="absolute rounded-full -right-24 -top-24 h-80 w-80 bg-electric/30 blur-3xl" />
        <div className="absolute rounded-full -bottom-32 left-1/3 h-80 w-80 bg-magentabrand/20 blur-3xl" />
        <div className="absolute inset-0 bg-[linear-gradient(120deg,rgba(255,255,255,0.06),transparent_38%,rgba(37,99,235,0.12))]" />

        <div className="relative grid gap-8 lg:grid-cols-[1.35fr_0.65fr] lg:items-end">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/10 px-4 py-2 text-xs font-black uppercase tracking-[0.2em] text-tealbrand">
              <span className="relative flex w-2 h-2">
                <span className="absolute inline-flex w-full h-full rounded-full animate-ping bg-tealbrand opacity-70" />
                <span className="relative inline-flex w-2 h-2 rounded-full bg-tealbrand" />
              </span>
              Emotion engine online
            </div>
            <h1 className="max-w-3xl mt-6 text-2xl font-black tracking-tight sm:text-3xl lg:text-4xl">
              Turn trailer moments into emotional intelligence.
            </h1>
            <p className="max-w-2xl mt-5 text-base leading-8 text-white/65">
              Upload one trailer. The model reads its audio, visual rhythm,
              facial emotion and scene intensity, then returns a structured
              creator-ready analysis.
            </p>
          </div>

          <div className="grid grid-cols-3 gap-2 lg:grid-cols-1">
            {[
              ['Input', 'MP4 · MOV · AVI'],
              ['Engine', 'Audio + Vision'],
              ['Output', 'Scene insights']
            ].map(([label, value]) => (
              <div
                key={label}
                className="px-3 py-4 border rounded-2xl border-white/10 bg-white/10 backdrop-blur-md lg:px-4"
              >
                <p className="text-[10px] font-black uppercase tracking-[0.18em] text-white/40">
                  {label}
                </p>
                <p className="mt-1 text-xs font-black text-white sm:text-sm">
                  {value}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>


      <section className="grid gap-6 lg:grid-cols-[1.25fr_0.75fr]">
        <div className="overflow-hidden rounded-[2rem] bg-white shadow-card ring-1 ring-slate-200/80">
          <div className="flex flex-col gap-4 px-6 py-5 border-b border-slate-100 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-10 h-10 text-sm font-black text-white rounded-xl bg-electric">
                01
              </div>
              <div>
                <h2 className="text-xl font-black text-deepnavy">
                  Trailer workspace
                </h2>
                <p className="text-sm text-slatebrand/50">
                  Review your video before sending it to the model.
                </p>
              </div>
            </div>
            {selectedVideo && (
              <span className="inline-flex w-fit items-center gap-2 rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-black text-emerald-700 ring-1 ring-emerald-200">
                <CheckCircle2 className="w-4 h-4" /> Ready to analyze
              </span>
            )}
          </div>

          <div className="p-5 sm:p-6">
            {!selectedVideo ? (
              <label className="group flex min-h-[420px] cursor-pointer flex-col items-center justify-center rounded-[1.75rem] border-2 border-dashed border-slate-200 bg-gradient-to-b from-lightbrand/70 to-white px-6 text-center transition hover:border-electric/50 hover:bg-electric/[0.03]">
                <motion.div
                  whileHover={{ scale: 1.05, rotate: -3 }}
                  className="flex h-24 w-24 items-center justify-center rounded-[2rem] bg-deepnavy text-white shadow-glow"
                >
                  <Film className="h-11 w-11" />
                </motion.div>
                <h3 className="text-xl font-black mt-7 text-deepnavy sm:text-2xl">
                  Drop in your movie trailer
                </h3>
                <p className="max-w-sm mt-3 text-sm leading-6 text-slatebrand/55">
                  Choose a video from your device. You will preview it here
                  before analysis begins.
                </p>
                <span className="mt-6 inline-flex items-center gap-2 rounded-2xl bg-electric px-6 py-3 text-sm font-black text-white shadow-lg transition group-hover:-translate-y-0.5">
                  <Play className="w-4 h-4" /> Choose video
                </span>
                <p className="mt-4 text-xs font-semibold text-slatebrand/40">
                  MP4, MOV, AVI, MKV or WebM
                </p>
                <input
                  type="file"
                  accept="video/*"
                  className="hidden"
                  onChange={handleVideoUpload}
                />
              </label>
            ) : (
              <div className="space-y-5">
                <div className="relative overflow-hidden rounded-[1.75rem] bg-black shadow-2xl ring-1 ring-black/10">
                  {videoPreviewUrl && (
                    <video
                      key={videoPreviewUrl}
                      src={videoPreviewUrl}
                      controls
                      preload="metadata"
                      className="max-h-[560px] min-h-[300px] w-full bg-black object-contain"
                    >
                      Your browser does not support video playback.
                    </video>
                  )}
                  <div className="pointer-events-none absolute left-4 top-4 max-w-[70%] rounded-xl bg-black/65 px-3 py-2 text-xs font-bold text-white backdrop-blur-md">
                    <span className="block truncate">{selectedVideo.name}</span>
                  </div>
                </div>

                <div className="flex flex-col gap-3 sm:flex-row">
                  <label className="inline-flex cursor-pointer items-center justify-center gap-2 rounded-2xl border border-slate-200 bg-white px-5 py-3.5 text-sm font-black text-deepnavy transition hover:border-electric/30 hover:bg-lightbrand sm:w-auto">
                    <Film className="w-4 h-4" /> Change video
                    <input
                      type="file"
                      accept="video/*"
                      className="hidden"
                      onChange={handleVideoUpload}
                    />
                  </label>
                  <button
                    type="button"
                    onClick={handleAnalyzeVideo}
                    disabled={isAnalyzing}
                    className="group inline-flex flex-1 items-center justify-center gap-3 rounded-2xl bg-gradient-to-r from-electric via-purplebrand to-magentabrand px-6 py-3.5 text-sm font-black text-white shadow-[0_16px_35px_rgba(124,58,237,0.25)] transition hover:-translate-y-0.5 hover:shadow-[0_20px_45px_rgba(124,58,237,0.35)] disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    <BrainCircuit className="w-5 h-5 transition group-hover:rotate-6" />
                    {analysisResult ? 'Run a new analysis' : 'Analyze emotion'}
                    <Sparkles className="w-4 h-4 text-white/75" />
                  </button>
                </div>
              </div>
            )}

            {analysisError && (
              <div
                role="alert"
                className="px-4 py-3 mt-5 text-sm font-bold rounded-2xl bg-rose-50 text-rose-700 ring-1 ring-rose-200"
              >
                {analysisError}
              </div>
            )}
          </div>
        </div>

        <aside className="space-y-6">
          <div className="rounded-[2rem] bg-deepnavy p-6 text-white shadow-glow sm:p-7">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-black uppercase tracking-[0.22em] text-tealbrand">
                  Model journey
                </p>
                <h2 className="mt-2 text-xl font-black sm:text-2xl">What happens next</h2>
              </div>
              <BrainCircuit className="w-8 h-8 text-white/25" />
            </div>

            <div className="space-y-2 mt-7">
              {[
                ['01', 'Ingest trailer', 'Securely prepare the uploaded video.', Film],
                ['02', 'Read the soundtrack', 'Measure mood, energy and audio features.', Activity],
                ['03', 'Understand each scene', 'Detect motion, objects and visual emotion.', Play],
                ['04', 'Fuse the signals', 'Calculate intensity and creator insights.', Sparkles]
              ].map(([number, title, copy, Icon], index) => {
                const StageIcon = Icon as typeof Film;
                return (
                  <div key={title as string} className="relative flex gap-4 rounded-2xl border border-white/10 bg-white/[0.06] p-4">
                    {index < 3 && (
                      <span className="absolute left-[1.95rem] top-14 h-6 w-px bg-gradient-to-b from-tealbrand/50 to-transparent" />
                    )}
                    <div className="flex items-center justify-center w-10 h-10 shrink-0 rounded-xl bg-white/10">
                      <StageIcon className="w-5 h-5 text-tealbrand" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-black tracking-[0.18em] text-white/30">
                          {number as string}
                        </span>
                        <p className="text-sm font-black">{title as string}</p>
                      </div>
                      <p className="mt-1 text-xs leading-5 text-white/50">
                        {copy as string}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-card">
            <div className="flex items-start gap-4">
              <div className="flex items-center justify-center h-11 w-11 shrink-0 rounded-2xl bg-tealbrand/10 text-tealbrand">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <div>
                <h3 className="font-black text-deepnavy">Designed for review</h3>
                <p className="mt-2 text-sm leading-6 text-slatebrand/55">
                  Results open in a full-screen workspace with scene tables,
                  model insights and creator-ready results.
                </p>
              </div>
            </div>
          </div>
        </aside>
      </section>

      <section className="overflow-hidden rounded-[2rem] border border-slate-200 bg-white shadow-card">
        <div className="flex flex-col gap-4 px-6 py-5 border-b border-slate-100 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center h-11 w-11 rounded-2xl bg-purplebrand/10 text-purplebrand">
              <Clock3 className="w-6 h-6" />
            </div>
            <div>
              <p className="text-[10px] font-black uppercase tracking-[0.2em] text-purplebrand">
                Saved analyses
              </p>
              <h2 className="mt-1 text-lg font-black text-deepnavy sm:text-xl">
                Previous emotion analyses
              </h2>
              <p className="mt-1 text-sm text-slatebrand/50">
                Recent trailer results saved to your account.
              </p>
            </div>
          </div>
          <div className="flex flex-col w-full gap-2 sm:w-auto sm:flex-row">
            <label className="relative min-w-0 sm:w-72">
              <span className="sr-only">Search previous emotion analyses</span>
              <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slatebrand/35" />
              <input
                type="search"
                value={historySearch}
                onChange={(event) => setHistorySearch(event.target.value)}
                placeholder="Search trailer or emotion..."
                disabled={isHistoryLoading}
                className="w-full rounded-2xl border border-slate-200 bg-lightbrand/60 py-2.5 pl-10 pr-4 text-sm font-semibold text-deepnavy outline-none transition placeholder:text-slatebrand/35 focus:border-electric/40 focus:bg-white focus:ring-4 focus:ring-electric/10 disabled:opacity-50"
              />
            </label>
            <button
              type="button"
              onClick={() => void loadEmotionHistory()}
              disabled={isHistoryLoading}
              className="inline-flex items-center justify-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-black text-deepnavy transition hover:border-electric/30 hover:bg-lightbrand disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Activity className={`h-4 w-4 ${isHistoryLoading ? 'animate-spin text-electric' : ''}`} />
              Refresh
            </button>
          </div>
        </div>

        <div className="p-5 sm:p-6">
          {isHistoryLoading ? (
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {[1, 2, 3].map((item) => (
                <div key={item} className="h-44 animate-pulse rounded-3xl bg-slate-100" />
              ))}
            </div>
          ) : historyError ? (
            <div className="px-5 py-4 text-sm font-bold rounded-2xl bg-rose-50 text-rose-700 ring-1 ring-rose-200">
              {historyError}
            </div>
          ) : emotionHistory.length === 0 ? (
            <div className="px-6 py-12 text-center border border-dashed rounded-3xl border-slate-200 bg-lightbrand/50">
              <BrainCircuit className="mx-auto h-9 w-9 text-slatebrand/25" />
              <p className="mt-3 font-black text-deepnavy">No saved analyses yet</p>
              <p className="mt-1 text-sm text-slatebrand/50">
                Your completed emotion analyses will appear here.
              </p>
            </div>
          ) : filteredEmotionHistory.length === 0 ? (
            <div className="px-6 py-12 text-center border border-dashed rounded-3xl border-slate-200 bg-lightbrand/50">
              <Search className="mx-auto h-9 w-9 text-slatebrand/25" />
              <p className="mt-3 font-black text-deepnavy">No matching analyses</p>
              <p className="mt-1 text-sm text-slatebrand/50">
                Try another trailer name, emotion, date, or metric.
              </p>
            </div>
          ) : (
            <div>
              {historyDetailError && (
                <div className="px-5 py-4 mb-4 text-sm font-bold rounded-2xl bg-rose-50 text-rose-700 ring-1 ring-rose-200">
                  {historyDetailError}
                </div>
              )}
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {filteredEmotionHistory.map((item) => (
                <button
                  type="button"
                  key={item.id}
                  onClick={() => void handleHistoryPreview(item)}
                  disabled={Boolean(loadingHistoryId)}
                  className="p-5 text-left transition border group rounded-3xl border-slate-200 bg-gradient-to-br from-white to-lightbrand/60 hover:-translate-y-1 hover:border-electric/20 hover:shadow-card disabled:cursor-wait disabled:opacity-65"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0">
                      <p className="text-base font-black truncate text-deepnavy" title={item.filename}>
                        {item.filename}
                      </p>
                      <p className="mt-1 text-xs font-semibold text-slatebrand/40">
                        {formatLocalDateTime(item.created_at)}
                      </p>
                    </div>
                    <div className="flex flex-col items-center justify-center text-white shadow-lg h-14 w-14 shrink-0 rounded-2xl bg-deepnavy">
                      <span className="text-lg font-black">
                        {Number(item.average_emotional_intensity || 0).toFixed(2)}
                      </span>
                      <span className="text-[9px] font-black uppercase tracking-wider text-white/40">EI</span>
                    </div>
                  </div>

                  <div className="p-3 mt-5 bg-white rounded-2xl ring-1 ring-slate-100">
                    <p className="text-[10px] font-black uppercase tracking-[0.14em] text-slatebrand/40">
                      Engagement
                    </p>
                    <p className="mt-1 text-sm font-black text-electric">
                      {item.engagement_level}
                    </p>
                  </div>

                  <div className="flex items-center gap-2 mt-4 text-xs font-bold text-slatebrand/50">
                    <span className="rounded-full bg-white px-3 py-1.5 ring-1 ring-slate-100">
                      {item.total_scenes} scenes
                    </span>
                    <span className="rounded-full bg-white px-3 py-1.5 ring-1 ring-slate-100">
                      {item.high_intensity_scenes} peaks
                    </span>
                  </div>
                </button>
              ))}
              </div>
            </div>
          )}
        </div>
      </section>

      {isAnalyzing && (
        <AnalysisLoadingOverlay
          message="Analyzing video..."
          onStop={stopVideoAnalysis}
        />
      )}
      {loadingHistoryId && (
        <AnalysisLoadingOverlay message="Loading saved analysis..." />
      )}

      {historyPreview && (
        <TrailerResultPopup
          videoName={historyPreview.filename}
          videoUrl={historyPreview.video_url}
          result={historyPreview}
          analyzedAt={historyPreview.created_at}
          onClose={() => setHistoryPreview(null)}
        />
      )}

      {showResultPopup && analysisResult && (
        <TrailerResultPopup
          videoName={selectedVideo?.name || 'Uploaded trailer'}
          videoUrl={videoPreviewUrl}
          result={analysisResult}
          onClose={() => setShowResultPopup(false)}
        />
      )}
    </div>
  );
}
