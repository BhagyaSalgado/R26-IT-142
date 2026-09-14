import type {
  CommentApiResponse,
  CommentSentimentData,
  CommentSentimentHistoryRecord,
  DetailedCommentResult
} from '../types/commentSentiment';

const rawBaseUrl = (
  import.meta.env.VITE_SENTIMENT_API_BASE_URL || 'http://127.0.0.1:5000'
).replace(/\/$/, '');

const SENTIMENT_API_BASE_URL = rawBaseUrl.endsWith('/api/sentiment')
  ? rawBaseUrl
  : `${rawBaseUrl}/api/sentiment`;

let authTokenProvider: (() => Promise<string | null>) | null = null;

export function setAuthTokenProvider(provider: () => Promise<string | null>) {
  authTokenProvider = provider;
}

async function requestJson<T>(path: string, options?: RequestInit): Promise<T> {
  const token = authTokenProvider ? await authTokenProvider() : null;

  const response = await fetch(`${SENTIMENT_API_BASE_URL}${path}`, {
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

  if (!response.ok || payload?.success === false) {
    const message =
      payload?.error || `Sentiment backend request failed with status ${response.status}`;
    throw new Error(message);
  }

  return payload as T;
}

/**
 * Fetch YouTube comments for a trailer URL and run the full NLP pipeline.
 * Backend: POST /api/sentiment/analyze/from-url
 */
export async function analyzeCommentsFromUrl(
  trailerUrl: string,
  trailerTitle?: string
): Promise<CommentSentimentData> {
  const response = await requestJson<CommentApiResponse<CommentSentimentData>>(
    '/analyze/from-url',
    {
      method: 'POST',
      body: JSON.stringify({
        trailer_url: trailerUrl,
        trailer_title: trailerTitle
      })
    }
  );

  return { ...response.data, trailerTitle: response.trailer_title };
}

/**
 * Analyze an already-fetched list of comments.
 * Backend: POST /api/sentiment/analyze
 */
export async function analyzeComments(
  comments: string[],
  trailerId = 'unknown'
): Promise<CommentSentimentData> {
  const response = await requestJson<CommentApiResponse<CommentSentimentData>>(
    '/analyze',
    {
      method: 'POST',
      body: JSON.stringify({
        comments,
        trailer_id: trailerId
      })
    }
  );

  return response.data;
}

/**
 * Analyze a single comment across all 4 NLP modules.
 * Backend: POST /api/sentiment/analyze-single
 */
export async function analyzeSingleComment(
  comment: string
): Promise<DetailedCommentResult> {
  const response = await requestJson<CommentApiResponse<DetailedCommentResult>>(
    '/analyze-single',
    {
      method: 'POST',
      body: JSON.stringify({ comment })
    }
  );

  return response.data;
}

/**
 * Get a previously saved analysis result for a trailer/video id.
 * Backend: GET /api/sentiment/analyze/{trailer_id}
 */
export async function getCachedCommentAnalysis(
  trailerId: string
): Promise<CommentSentimentData> {
  const response = await requestJson<CommentApiResponse<CommentSentimentData>>(
    `/analyze/${trailerId}`
  );

  return response.data;
}

export function getSentimentApiBaseUrl() {
  return SENTIMENT_API_BASE_URL;
}

/**
 * Get the most recently analyzed trailers.
 * Backend: GET /api/sentiment/history?limit=5
 */
export async function getCommentSentimentHistory(
  limit = 5
): Promise<CommentSentimentHistoryRecord[]> {
  const response = await requestJson<CommentApiResponse<CommentSentimentHistoryRecord[]>>(
    `/history?limit=${limit}`
  );

  return response.data;
}
