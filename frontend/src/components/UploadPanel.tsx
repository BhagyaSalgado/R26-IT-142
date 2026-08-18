import { ChangeEvent, FormEvent, useState } from 'react';
import { CloudUpload, Film, Loader2, PlayCircle } from 'lucide-react';
import type { AnalysisResult } from '../types';
import { analyzeTrailer } from '../services/api';

interface UploadPanelProps {
  onCompleted: (result: AnalysisResult) => void;
}

export default function UploadPanel({ onCompleted }: UploadPanelProps) {
  const [trailerUrl, setTrailerUrl] = useState('https://youtube.com/watch?v=dummy-trailer');
  const [trailerName, setTrailerName] = useState('Shadow Horizon - Official Trailer');
  const [selectedFile, setSelectedFile] = useState<string>('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string>('');
  const [mode, setMode] = useState<'youtube' | 'upload'>('youtube');

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
    setIsAnalyzing(true);
    try {
      const result = await analyzeTrailer({ trailerUrl, trailerName, mode });
      setIsAnalyzing(false);
      onCompleted(result);
    } catch (err) {
      setIsAnalyzing(false);
      const errorMessage = err instanceof Error ? err.message : 'Analysis failed. Make sure backend is running on port 5000.';
      setError(errorMessage);
      console.error('Analysis error:', err);
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

          {error && (
            <div className="rounded-2xl bg-red-50 px-4 py-3 text-sm font-semibold text-red-700 ring-1 ring-red-200">
              {error}
            </div>
          )}
        </div>

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
