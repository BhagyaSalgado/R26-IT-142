import type {
  ApiResponse,
  FutureMetricsData,
  FutureMetricsPrediction,
  PopularityAnalysisData,
  PopularityCombinedResult,
  PopularityRequest
} from '../types/popularity';

const API_BASE_URL =
  import.meta.env.VITE_POPULARITY_API_BASE_URL?.replace(/\/$/, '') ||
  'http://127.0.0.1:8001/api/v1';

let authTokenProvider: (() => Promise<string | null>) | null = null;

export function setAuthTokenProvider(provider: () => Promise<string | null>) {
  authTokenProvider = provider;
}

export interface PopularityHistoryRecord {
  id?: string;
  video_id?: string;
  title?: string;
  predicted_reaction?: string;
  confidence_score?: number;
  popularity_score?: number;
  engagement_rate?: number;
  created_at?: string;
  [key: string]: unknown;
}

export interface FutureMetricsHistoryRecord {
  id?: string;
  video_id?: string;
  title?: string;
  horizon_days?: number;
  current_views?: number;
  predicted_views?: number;
  predicted_reaction?: string;
  confidence_score?: number;
  popularity_score?: number;
  expected_view_growth_percent?: number;
  created_at?: string;
  [key: string]: unknown;
}

export interface CombinedHistory {
  trailer_analysis: PopularityHistoryRecord[];
  popularity_analysis: FutureMetricsHistoryRecord[];
}

async function requestJson<T>(path: string, options?: RequestInit): Promise<T> {
  const token = authTokenProvider ? await authTokenProvider() : null;
  const isLocalBackend = /localhost|127\.0\.0\.1|0\.0\.0\.0/.test(API_BASE_URL);

  if (!token && !isLocalBackend) {
    throw new Error('Please login before running or loading saved analyses.');
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options?.headers || {})
    }
  });

  const contentType = response.headers.get('content-type') || '';
  const payload = contentType.includes('application/json')
    ? await response.json()
    : null;

  if (!response.ok) {
    const message =
      payload?.detail ||
      payload?.message ||
      `Backend request failed with status ${response.status}`;

    throw new Error(
      Array.isArray(message)
        ? message.map((item) => item.msg || item).join(', ')
        : message
    );
  }

  return payload as T;
}

/**
 * Analyze current trailer popularity and predict audience reaction.
 * Backend: POST /api/v1/analyze
 */
export async function analyzeTrailerPopularity(
  youtubeUrl: string
): Promise<PopularityAnalysisData> {
  const response = await requestJson<ApiResponse<PopularityAnalysisData>>('/analyze', {
    method: 'POST',
    body: JSON.stringify({
      youtube_url: youtubeUrl
    })
  });

  return response.data;
}

/**
 * Predict future views, likes, and comments.
 * Backend: POST /api/v1/future-metrics/predict
 */
export async function predictFutureMetrics(
  youtubeUrl: string,
  horizonDays = 7
): Promise<FutureMetricsData> {
  const response = await requestJson<ApiResponse<FutureMetricsData>>(
    '/future-metrics/predict',
    {
      method: 'POST',
      body: JSON.stringify({
        youtube_url: youtubeUrl,
        horizon_days: horizonDays,
        save_result: true
      })
    }
  );

  return response.data;
}

/**
 * Main frontend call.
 * It runs reaction analysis first, then optionally runs future prediction.
 */
export async function analyzePopularityWithFuture({
  youtubeUrl,
  horizonDays = 7,
  includeFuturePrediction = true
}: PopularityRequest): Promise<PopularityCombinedResult> {
  if (!includeFuturePrediction) {
    const analysis = await analyzeTrailerPopularity(youtubeUrl);
    return { analysis };
  }

  const future = await predictFutureMetrics(youtubeUrl, horizonDays);

  return {
    analysis: {
      video_id: future.video_id,
      trailer: future.trailer,
      metrics: future.metrics,
      features: future.features,
      prediction: future.prediction || {
        predicted_reaction: 'MEDIUM_REACTION',
        confidence_score: 0,
        model_name: future.future_prediction.model_name,
        model_version: future.future_prediction.model_version,
        probabilities: {},
        recommendation: 'Future metrics generated successfully.'
      }
    },
    future
  };
}

export async function getCombinedHistory(limit = 20): Promise<CombinedHistory> {
  const response = await requestJson<ApiResponse<CombinedHistory>>(
    `/history/combined?limit=${limit}`
  );

  return response.data;
}

/**
 * Get previous popularity analysis records.
 * Backend: GET /api/v1/history?limit=20
 */
export async function getPopularityHistory(
  limit = 20
): Promise<PopularityHistoryRecord[]> {
  const response = await requestJson<ApiResponse<PopularityHistoryRecord[]>>(
    `/history?limit=${limit}`
  );

  return response.data;
}

/**
 * Get previous future metric prediction records.
 * Backend: GET /api/v1/future-metrics/history?limit=20
 */
export async function getFutureMetricsHistory(
  limit = 20
): Promise<FutureMetricsHistoryRecord[]> {
  const response = await requestJson<ApiResponse<FutureMetricsHistoryRecord[]>>(
    `/future-metrics/history?limit=${limit}`
  );

  return response.data;
}

/**
 * Get saved future prediction for a video.
 * Backend: GET /api/v1/future-metrics/{video_id}?horizon_days=7
 */
export async function getSavedFuturePrediction(
  videoId: string,
  horizonDays = 7
): Promise<FutureMetricsPrediction> {
  const response = await requestJson<ApiResponse<FutureMetricsPrediction>>(
    `/future-metrics/${videoId}?horizon_days=${horizonDays}`
  );

  return response.data;
}

export function getApiBaseUrl() {
  return API_BASE_URL;
}
