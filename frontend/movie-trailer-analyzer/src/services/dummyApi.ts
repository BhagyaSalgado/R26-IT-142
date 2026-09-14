import type { AnalysisResult, AnalyzeRequest, TrailerHistoryItem } from '../types';
import { historyItems, mockAnalysisResult } from '../data/mockBackend';

const wait = (ms: number) => new Promise((resolve) => window.setTimeout(resolve, ms));

export async function analyzeTrailer(request: AnalyzeRequest): Promise<AnalysisResult> {
  await wait(1200);

  return {
    ...mockAnalysisResult,
    id: `ANL-${Date.now().toString().slice(-6)}`,
    trailerTitle: request.trailerName || mockAnalysisResult.trailerTitle,
    sourceUrl: request.trailerUrl || 'Uploaded trailer file',
    generatedAt: new Date().toLocaleString()
  };
}

export async function getLatestAnalysis(): Promise<AnalysisResult> {
  await wait(500);
  return mockAnalysisResult;
}

export async function getAnalysisHistory(): Promise<TrailerHistoryItem[]> {
  await wait(300);
  return historyItems;
}
