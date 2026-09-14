import type {
  AnalysisResult,
  ComponentSummary,
  TrailerHistoryItem
} from '../types';

export const componentSummaries: ComponentSummary[] = [
  {
    id: 'audio',
    name: 'Audio Feature Extraction',
    owner: 'Component 01',
    purpose:
      'Extracts trailer audio features such as tempo, audio energy, MFCC mean and spectral centroid from each scene.',
    status: 'Completed',
    progress: 95,
    outputs: ['Tempo BPM', 'Audio Energy A', 'MFCC Mean', 'Audio Mood'],
    endpoint: '/api/v1/audio/analyze',
    model: 'Librosa + trained audio emotion model',
    accent: '#2563EB'
  },
  {
    id: 'visual',
    name: 'Visual Feature Detection',
    owner: 'Component 02',
    purpose:
      'Detects objects, facial emotion confidence, motion intensity and scene type from video frames.',
    status: 'Completed',
    progress: 92,
    outputs: ['Objects', 'Object Score O', 'Emotion F', 'Motion M'],
    endpoint: '/api/v1/video/analyze',
    model: 'YOLOv8 + trained visual emotion model',
    accent: '#06B6D4'
  },
  {
    id: 'metadata',
    name: 'Trailer Metadata Analysis',
    owner: 'Component 03',
    purpose:
      'Uses YouTube trailer dataset values such as views, likes, comments, sentiment and favorability.',
    status: 'Completed',
    progress: 88,
    outputs: ['Views', 'Likes', 'Comments', 'Sentiment', 'Favorability'],
    endpoint: '/api/v1/metadata/predict',
    model: 'Random Forest metadata model',
    accent: '#7C3AED'
  },
  {
    id: 'fusion',
    name: 'Final Emotional Intensity Fusion',
    owner: 'Component 04',
    purpose:
      'Combines motion intensity, audio energy, object score and facial emotion confidence to calculate EI and level.',
    status: 'Completed',
    progress: 96,
    outputs: ['M', 'A', 'O', 'F', 'EI', 'Level'],
    endpoint: '/api/v1/final/emotional-intensity',
    model: 'Weighted fusion formula',
    accent: '#E11DFA'
  }
];

export const mockAnalysisResult: AnalysisResult = {
  id: 'AN-001',
  trailerTitle: 'Uploaded Trailer Demo',
  sourceUrl: '',
  generatedAt: '2026-05-06T10:30:00.000Z',

  overallReaction: 'High',
  confidence: 91,
  audienceScore: 82,
  engagementForecast: 78,

  sentiment: {
    positive: 68,
    neutral: 22,
    negative: 10
  },

  popularity: {
    views: 1250000,
    likes: 98000,
    comments: 18400,
    engagementRate: 7.8,
    likeRatio: 94,
    velocity: 81
  },

  sceneIntensities: [
    {
      scene: 'Scene 1',
      timestamp: '00:00-00:08',
      visualEmotion: 'surprise',
      sceneType: 'Action',
      intensityScore: 0.83,
      motionLevel: 'High',
      audioEnergy: 0.8
    },
    {
      scene: 'Scene 2',
      timestamp: '00:08-00:16',
      visualEmotion: 'neutral',
      sceneType: 'Dialogue',
      intensityScore: 0.37,
      motionLevel: 'Low',
      audioEnergy: 0.4
    },
    {
      scene: 'Scene 3',
      timestamp: '00:16-00:25',
      visualEmotion: 'angry',
      sceneType: 'Thriller',
      intensityScore: 0.76,
      motionLevel: 'High',
      audioEnergy: 0.75
    },
    {
      scene: 'Scene 4',
      timestamp: '00:25-00:35',
      visualEmotion: 'sad',
      sceneType: 'Emotional',
      intensityScore: 0.5,
      motionLevel: 'Medium',
      audioEnergy: 0.55
    }
  ],

  recommendations: [
    {
      id: 1,
      priority: 1,
      title: 'Improve low-intensity dialogue section',
      component: 'Final Emotional Intensity Fusion',
      evidence: 'Scene 2 has low emotional intensity with EI = 0.37.',
      action:
        'Add stronger background music, shorter cuts, or a more expressive visual moment to increase engagement.'
    },
    {
      id: 2,
      priority: 2,
      title: 'Keep high-impact action scenes',
      component: 'Video + Audio Emotion Analysis',
      evidence:
        'Scene 1 and Scene 3 contain high motion, high object score and high audio energy.',
      action:
        'Use these scenes near the opening and ending of the trailer to increase audience attention.'
    },
    {
      id: 3,
      priority: 3,
      title: 'Balance emotional pacing',
      component: 'Trailer Scene Analysis',
      evidence:
        'The trailer moves from a high-intensity action scene to a low-intensity dialogue scene.',
      action:
        'Place suspense audio or emotional buildup before the dialogue scene to maintain viewer interest.'
    }
  ],

  components: componentSummaries,

  topFeatures: [
    { feature: 'Motion Intensity', importance: 35 },
    { feature: 'Audio Energy', importance: 30 },
    { feature: 'Object Score', importance: 20 },
    { feature: 'Facial Emotion Confidence', importance: 15 }
  ],

  commentTopics: [
    { topic: 'Action scenes', mentions: 420 },
    { topic: 'Music', mentions: 310 },
    { topic: 'Actors', mentions: 260 },
    { topic: 'Story curiosity', mentions: 190 }
  ],

  regionalInterest: [
    { region: 'Sri Lanka', value: 82 },
    { region: 'India', value: 76 },
    { region: 'United States', value: 68 },
    { region: 'United Kingdom', value: 61 }
  ],

  modelMetrics: [
    { metric: 'Accuracy', value: 91 },
    { metric: 'Precision', value: 89 },
    { metric: 'Recall', value: 87 },
    { metric: 'F1 Score', value: 88 }
  ],

  finalModelOutput: [
    {
      scene: 1,
      sceneType: 'Action',
      M: 0.85,
      A: 0.8,
      O: 0.9,
      F: 0.72,
      EI: 0.83,
      level: 'High'
    },
    {
      scene: 2,
      sceneType: 'Dialogue',
      M: 0.3,
      A: 0.4,
      O: 0.2,
      F: 0.6,
      EI: 0.37,
      level: 'Low'
    },
    {
      scene: 3,
      sceneType: 'Thriller',
      M: 0.78,
      A: 0.75,
      O: 0.8,
      F: 0.68,
      EI: 0.76,
      level: 'High'
    },
    {
      scene: 4,
      sceneType: 'Emotional',
      M: 0.45,
      A: 0.55,
      O: 0.35,
      F: 0.7,
      EI: 0.5,
      level: 'Medium'
    }
  ],

  audioFeatureOutput: [
    {
      scene: 1,
      time: '00:00-00:08',
      tempoBpm: 140,
      audioEnergy: 0.8,
      mfccMean: -12.5,
      spectralCentroid: 3250,
      audioMood: 'intense'
    },
    {
      scene: 2,
      time: '00:08-00:16',
      tempoBpm: 90,
      audioEnergy: 0.4,
      mfccMean: -18.2,
      spectralCentroid: 1800,
      audioMood: 'calm'
    },
    {
      scene: 3,
      time: '00:16-00:25',
      tempoBpm: 150,
      audioEnergy: 0.75,
      mfccMean: -10.8,
      spectralCentroid: 3500,
      audioMood: 'suspense'
    },
    {
      scene: 4,
      time: '00:25-00:35',
      tempoBpm: 110,
      audioEnergy: 0.55,
      mfccMean: -15.4,
      spectralCentroid: 2400,
      audioMood: 'emotional'
    }
  ],

  visualFeatureOutput: [
    {
      scene: 1,
      time: '00:00-00:08',
      objects: 'explosion, car',
      objectScore: 0.9,
      emotion: 'surprise',
      emotionConfidence: 0.72,
      motion: 0.85,
      sceneType: 'Action'
    },
    {
      scene: 2,
      time: '00:08-00:16',
      objects: 'person',
      objectScore: 0.2,
      emotion: 'neutral',
      emotionConfidence: 0.6,
      motion: 0.3,
      sceneType: 'Dialogue'
    },
    {
      scene: 3,
      time: '00:16-00:25',
      objects: 'weapon, fire',
      objectScore: 0.8,
      emotion: 'angry',
      emotionConfidence: 0.68,
      motion: 0.78,
      sceneType: 'Thriller'
    },
    {
      scene: 4,
      time: '00:25-00:35',
      objects: 'person, room',
      objectScore: 0.35,
      emotion: 'sad',
      emotionConfidence: 0.7,
      motion: 0.45,
      sceneType: 'Emotional'
    }
  ]
};

export const backendSteps = [
  'POST /api/v1/trailer/upload',
  'POST /api/v1/audio/extract-features',
  'POST /api/v1/video/extract-features',
  'POST /api/v1/metadata/predict',
  'POST /api/v1/final/emotional-intensity',
  'GET /api/v1/trailer/analysis/{analysis_id}'
];

export const historyItems: TrailerHistoryItem[] = [
  {
    id: 'TR-001',
    title: 'Uploaded Trailer Demo',
    date: '2026-05-06',
    reaction: 'High',
    score: 82,
    sentiment: 'Positive sentiment dominant',
    status: 'Ready'
  },
  {
    id: 'TR-002',
    title: 'Drama Trailer Demo',
    date: '2026-05-05',
    reaction: 'Moderate',
    score: 64,
    sentiment: 'Neutral sentiment dominant',
    status: 'Reviewed'
  },
  {
    id: 'TR-003',
    title: 'Action Trailer Test',
    date: '2026-05-04',
    reaction: 'High',
    score: 88,
    sentiment: 'High excitement comments',
    status: 'Shared'
  }
];