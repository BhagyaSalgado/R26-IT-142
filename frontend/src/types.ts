export type ReactionLevel = 'High' | 'Moderate' | 'Low';
export type ComponentStatus = 'Completed' | 'Processing' | 'Queued';

export interface SentimentDistribution {
  positive: number;
  neutral: number;
  negative: number;
}

export interface DeeperEmotions {
  joy?: number;
  excitement?: number;
  anger?: number;
  sadness?: number;
  fear?: number;
  surprise?: number;
  anticipation?: number;
  disappointment?: number;
}

export interface PopularityMetrics {
  views: number;
  likes: number;
  comments: number;
  engagementRate: number;
  likeRatio: number;
  velocity: number;
}

export interface SceneIntensity {
  scene: string;
  timestamp: string;
  visualEmotion: string;
  sceneType: string;
  intensityScore: number;
  motionLevel: 'Low' | 'Medium' | 'High';
  audioEnergy: number;
}

export interface RecommendationCard {
  id: number;
  title: string;
  priority: number;
  evidence: string;
  action: string;
  component: string;
}



export interface FeatureContribution {
  feature: string;
  importance: number;
}

export interface AnalysisResult {
  id: string;
  trailerTitle: string;
  sourceUrl: string;
  generatedAt: string;
  overallReaction: ReactionLevel;
  confidence: number;
  audienceScore: number;
  engagementForecast: number;
  sentiment: SentimentDistribution;
  deeperEmotions: DeeperEmotions;
  popularity: PopularityMetrics;
  sceneIntensities: SceneIntensity[];
  recommendations: RecommendationCard[];
  topFeatures: FeatureContribution[];
  commentTopics: Array<{ topic: string; mentions: number }>;
  regionalInterest: Array<{ region: string; value: number }>;
  modelMetrics: Array<{ metric: string; value: number }>;
}

export interface TrailerHistoryItem {
  id: string;
  title: string;
  date: string;
  reaction: ReactionLevel;
  score: number;
  sentiment: string;
  status: 'Ready' | 'Reviewed' | 'Shared';
}

export interface AnalyzeRequest {
  trailerUrl: string;
  trailerName: string;
  mode: 'youtube' | 'upload';
}
