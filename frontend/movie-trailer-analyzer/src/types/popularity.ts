export type ReactionClass = 'LOW_REACTION' | 'MEDIUM_REACTION' | 'HIGH_REACTION' | string;

export interface ApiResponse<T> {
  status?: string;
  message: string;
  data: T;
}

export interface Trailer {
  id: string;
  youtube_video_id: string;
  youtube_url: string;
  title: string;
  channel_name: string;
  published_at: string;
  thumbnail_url?: string;
  created_at?: string;
  updated_at?: string;
}

export interface TrailerMetrics {
  id?: string;
  trailer_id?: string;
  view_count: number;
  like_count: number;
  comment_count: number;
  favorite_count?: number;
  collected_at?: string;
  source?: string;
}

export interface TrailerFeatures {
  id?: string;
  trailer_id?: string;
  views: number;
  likes: number;
  comment_count: number;
  video_age_days: number;
  engagement_rate: number;
  like_ratio: number;
  comment_rate: number;
  comments_per_1000_views: number;
  views_per_day: number;
  likes_per_day: number;
  comments_per_day: number;
  log_views?: number;
  log_likes?: number;
  log_comments?: number;
  growth_rate?: number;
  popularity_score: number;
  created_at?: string;
}

export interface ReactionPrediction {
  id?: string;
  trailer_id?: string;
  predicted_reaction: ReactionClass;
  confidence_score: number;
  model_name: string;
  model_version: string;
  probabilities: Record<string, number>;
  recommendation?: string;
  created_at?: string;
}

export interface PopularityAnalysisData {
  video_id: string;
  trailer: Trailer;
  metrics: TrailerMetrics;
  features: TrailerFeatures;
  prediction: ReactionPrediction;
}

export interface FutureMetricsPrediction {
  id: string;
  trailer_id: string;
  horizon_days: number;
  current_views: number;
  current_likes: number;
  current_comment_count: number;
  predicted_views: number;
  predicted_likes: number;
  predicted_comment_count: number;
  expected_view_growth: number;
  expected_like_growth: number;
  expected_comment_growth: number;
  expected_view_growth_percent: number;
  expected_like_growth_percent: number;
  expected_comment_growth_percent: number;
  predicted_engagement_rate: number;
  predicted_reaction?: ReactionClass;
  confidence_score?: number;
  probabilities?: Record<string, number>;
  recommendation?: string;
  popularity_score?: number;
  model_name: string;
  model_version: string;
  source_model_path?: string;
  created_at: string;
}

export interface FutureMetricsData {
  video_id: string;
  trailer: Trailer;
  metrics: TrailerMetrics;
  features: TrailerFeatures;
  prediction?: ReactionPrediction;
  future_prediction: FutureMetricsPrediction;
}

export interface PopularityCombinedResult {
  analysis: PopularityAnalysisData;
  future?: FutureMetricsData;
}

export interface PopularityRequest {
  youtubeUrl: string;
  horizonDays?: number;
  includeFuturePrediction?: boolean;
}

export interface ArtifactStatus {
  artifacts_dir?: string;
  available_horizons?: number[];
  [key: string]: unknown;
}
