export type ReactionLevel = 'High' | 'Moderate' | 'Low';
export type ComponentStatus = 'Completed' | 'Processing' | 'Queued';

export interface SentimentDistribution {
  positive: number;
  neutral: number;
  negative: number;
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

export interface ComponentSummary {
  id: string;
  name: string;
  owner: string;
  purpose: string;
  status: ComponentStatus;
  progress: number;
  outputs: string[];
  endpoint: string;
  model: string;
  accent: string;
}

export interface FeatureContribution {
  feature: string;
  importance: number;
}

export interface FinalModelOutput {
  scene: number;
  sceneType: string;
  M: number;
  A: number;
  O: number;
  F: number;
  EI: number;
  level: 'High' | 'Medium' | 'Low';
}

export interface AudioFeatureOutput {
  scene: number;
  time: string;
  tempoBpm: number;
  audioEnergy: number;
  mfccMean: number;
  spectralCentroid: number;
  audioMood: string;
}

export interface VisualFeatureOutput {
  scene: number;
  time: string;
  objects: string;
  objectScore: number;
  emotion: string;
  emotionConfidence: number;
  motion: number;
  sceneType: string;
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
  popularity: PopularityMetrics;
  sceneIntensities: SceneIntensity[];
  recommendations: RecommendationCard[];
  components: ComponentSummary[];
  topFeatures: FeatureContribution[];
  commentTopics: Array<{ topic: string; mentions: number }>;
  regionalInterest: Array<{ region: string; value: number }>;
  modelMetrics: Array<{ metric: string; value: number }>;

  finalModelOutput: FinalModelOutput[];
  audioFeatureOutput: AudioFeatureOutput[];
  visualFeatureOutput: VisualFeatureOutput[];

  dominantGenre?: string;
  secondaryGenre?: string;
  genreConfidence?: number;
  genreMixture?: Record<string, number>;
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