export interface CommentApiResponse<T> {
  success: boolean;
  data: T;
  trailer_id?: string;
  trailer_title?: string;
  timestamp?: string;
  error?: string;
}

export interface CommentSentimentSplit {
  positive: number;
  neutral: number;
  negative: number;
}

export interface DeeperEmotions {
  joy: number;
  excitement: number;
  anger: number;
  sadness: number;
  fear: number;
  surprise: number;
}

export interface CommentTopic {
  topic: string;
  mentions: number;
}

export interface RegionalInterest {
  region: string;
  value: number;
}

export interface DetailedCommentResult {
  text: string;
  cleaned_text?: string;
  language?: string;
  country?: string;
  sentiment: string;
  sentiment_confidence?: number;
  emotion: string;
  emotion_confidence?: number;
  topic: string;
  model_used?: string;
  error?: string;
}

export interface CommentModelMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1Score: number;
}

export interface CommentSentimentData {
  sentiment: CommentSentimentSplit;
  deeperEmotions: DeeperEmotions;
  commentTopics: CommentTopic[];
  regionalInterest: RegionalInterest[];
  totalComments: number;
  detailedResults: DetailedCommentResult[];
  modelMetrics: CommentModelMetrics;
  modelUsed: string;
  trailerTitle?: string;
  error?: string;
}

export interface CommentSentimentHistoryRecord {
  trailer_id: string;
  trailer_title?: string;
  timestamp?: string;
  totalComments?: number;
  sentiment?: CommentSentimentSplit;
  modelUsed?: string;
}
