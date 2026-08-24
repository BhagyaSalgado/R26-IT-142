import type { AnalysisResult, TrailerHistoryItem } from '../types';



export const mockAnalysisResult: AnalysisResult = {
  id: 'ANL-2026-0427',
  trailerTitle: 'Shadow Horizon - Official Trailer',
  sourceUrl: 'https://youtube.com/watch?v=dummy-trailer',
  generatedAt: '2026-05-02 12:38',
  overallReaction: 'High',
  confidence: 88,
  audienceScore: 84,
  engagementForecast: 76,
  sentiment: {
    positive: 64,
    neutral: 22,
    negative: 14
  },
  deeperEmotions: {
    anticipation: 58,
    excitement: 52,
    disappointment: 12
  },
  popularity: {
    views: 1280000,
    likes: 93200,
    comments: 18400,
    engagementRate: 8.7,
    likeRatio: 93.8,
    velocity: 71
  },
  sceneIntensities: [
    {
      scene: 'Opening mystery shot',
      timestamp: '00:00-00:18',
      visualEmotion: 'Curiosity',
      sceneType: 'Suspense',
      intensityScore: 0.52,
      motionLevel: 'Medium',
      audioEnergy: 0.44
    },
    {
      scene: 'Hero reveal sequence',
      timestamp: '00:19-00:46',
      visualEmotion: 'Excitement',
      sceneType: 'Action',
      intensityScore: 0.83,
      motionLevel: 'High',
      audioEnergy: 0.79
    },
    {
      scene: 'Dialogue conflict',
      timestamp: '00:47-01:10',
      visualEmotion: 'Tension',
      sceneType: 'Drama',
      intensityScore: 0.61,
      motionLevel: 'Medium',
      audioEnergy: 0.48
    },
    {
      scene: 'Final montage',
      timestamp: '01:11-01:42',
      visualEmotion: 'Fear / Surprise',
      sceneType: 'Action Thriller',
      intensityScore: 0.91,
      motionLevel: 'High',
      audioEnergy: 0.86
    }
  ],
  recommendations: [
    {
      id: 1,
      title: 'Strengthen the first 15 seconds',
      priority: 94,
      evidence: 'Opening intensity is moderate while later scenes peak above 0.80, creating a slower hook.',
      action: 'Move one high-impact visual or music hit into the first 10-15 seconds to raise early retention.',
      component: 'Video & Audio Analysis'
    },
    {
      id: 2,
      title: 'Highlight the most discussed character moment',
      priority: 89,
      evidence: 'Comment topics show strong audience discussion around the lead actor and final reveal.',
      action: 'Use a shorter teaser cut that emphasizes the lead character reveal and invite social sharing.',
      component: 'Comment Sentiment Analysis'
    },
    {
      id: 3,
      title: 'Improve comment-to-view conversion',
      priority: 81,
      evidence: 'Views and like ratio are high, but comment activity is below the strongest benchmark trailer set.',
      action: 'Add a pinned question, countdown post, or interactive poll to increase active conversation.',
      component: 'Popularity Metrics Analysis'
    },
    {
      id: 4,
      title: 'Balance action with story clarity',
      priority: 74,
      evidence: 'MTIRF weak-signal fusion detects high action intensity but only medium storyline topic confidence.',
      action: 'Add one clearer plot line or character motivation caption before the final montage.',
      component: 'Recommendation Engine'
    }
  ],
  topFeatures: [
    { feature: 'Positive comment share', importance: 86 },
    { feature: 'Emotional intensity peak', importance: 79 },
    { feature: 'Like ratio', importance: 72 },
    { feature: 'View velocity', importance: 68 },
    { feature: 'Opening scene score', importance: 54 },
    { feature: 'Topic clarity', importance: 49 }
  ],
  commentTopics: [
    { topic: 'Lead actor', mentions: 4200 },
    { topic: 'Background music', mentions: 3100 },
    { topic: 'Visual effects', mentions: 2850 },
    { topic: 'Storyline clarity', mentions: 1960 },
    { topic: 'Release date', mentions: 1480 }
  ],
  regionalInterest: [
    { region: 'United States', value: 31 },
    { region: 'India', value: 22 },
    { region: 'United Kingdom', value: 16 },
    { region: 'Sri Lanka', value: 12 },
    { region: 'Other', value: 19 }
  ],
  modelMetrics: [
    { metric: 'Accuracy', value: 88 },
    { metric: 'Precision', value: 84 },
    { metric: 'Recall', value: 82 },
    { metric: 'F1-score', value: 85 }
  ]
};

export const historyItems: TrailerHistoryItem[] = [
  {
    id: 'ANL-2026-0427',
    title: 'Shadow Horizon - Official Trailer',
    date: '2026-05-02',
    reaction: 'High',
    score: 84,
    sentiment: 'Positive 64%',
    status: 'Ready'
  },
  {
    id: 'ANL-2026-0415',
    title: 'Neon Run - Teaser Cut',
    date: '2026-04-28',
    reaction: 'Moderate',
    score: 67,
    sentiment: 'Positive 48%',
    status: 'Reviewed'
  },
  {
    id: 'ANL-2026-0398',
    title: 'Ocean City - Trailer V2',
    date: '2026-04-12',
    reaction: 'Low',
    score: 44,
    sentiment: 'Negative 38%',
    status: 'Shared'
  }
];


