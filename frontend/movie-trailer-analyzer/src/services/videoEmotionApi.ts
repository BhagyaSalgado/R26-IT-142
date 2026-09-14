export type VideoAnalysisResponse = Record<string, unknown>;

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
).replace(/\/$/, '');

let authTokenProvider: (() => Promise<string | null>) | null = null;

export function setAuthTokenProvider(provider: () => Promise<string | null>) {
  authTokenProvider = provider;
}

async function authHeaders(): Promise<HeadersInit> {
  const token = authTokenProvider ? await authTokenProvider() : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function apiErrorMessage(payload: unknown, status: number) {
  if (payload && typeof payload === 'object') {
    const data = payload as Record<string, unknown>;

    if (typeof data.detail === 'string') return data.detail;
    if (typeof data.message === 'string') return data.message;

    if (Array.isArray(data.detail)) {
      return data.detail
        .map((item) =>
          item && typeof item === 'object' && 'msg' in item
            ? String((item as { msg: unknown }).msg)
            : String(item)
        )
        .join(', ');
    }
  }

  return `Video analysis failed (HTTP ${status}).`;
}

export async function analyzeEmotionVideo(
  video: File,
  signal?: AbortSignal
): Promise<VideoAnalysisResponse> {
  const formData = new FormData();
  formData.append('video', video);

  const response = await fetch(`${API_BASE_URL}/api/v1/predict/video`, {
    method: 'POST',
    headers: await authHeaders(),
    body: formData,
    signal
  });

  const contentType = response.headers.get('content-type') || '';
  const payload: unknown = contentType.includes('application/json')
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    throw new Error(apiErrorMessage(payload, response.status));
  }

  return payload && typeof payload === 'object' && !Array.isArray(payload)
    ? (payload as VideoAnalysisResponse)
    : { result: payload };
}
export interface EmotionHistoryItem {
  id: string;
  filename: string;
  created_at: string | null;
  total_scenes: number;
  average_emotional_intensity: number;
  engagement_level: string;
  high_intensity_scenes: number;
}

export async function getEmotionHistory(
  limit = 12
): Promise<EmotionHistoryItem[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/predict/history?limit=${limit}`,
    { headers: await authHeaders() }
  );
  const payload: unknown = await response.json();

  if (!response.ok) {
    throw new Error(apiErrorMessage(payload, response.status));
  }

  if (!payload || typeof payload !== 'object' || !('items' in payload)) {
    return [];
  }

  const items = (payload as { items: unknown }).items;
  return Array.isArray(items) ? (items as EmotionHistoryItem[]) : [];
}
export type EmotionHistoryDetail = VideoAnalysisResponse & {
  id: string;
  filename: string;
  created_at: string | null;
  video_url: string;
};

export async function getEmotionHistoryDetail(
  predictionId: string
): Promise<EmotionHistoryDetail> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/predict/history/${encodeURIComponent(predictionId)}`,
    { headers: await authHeaders() }
  );
  const payload: unknown = await response.json();

  if (!response.ok) {
    throw new Error(apiErrorMessage(payload, response.status));
  }
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    throw new Error('The saved analysis response is invalid.');
  }

  const detail = payload as EmotionHistoryDetail;
  if (detail.video_url?.startsWith('/')) {
    detail.video_url = `${API_BASE_URL}${detail.video_url}`;
  }
  return detail;
}