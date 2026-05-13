import type { AnalysisResult, AnalyzeRequest } from '../types';

// Backend URL - Change port if different
const API_BASE_URL = 'http://localhost:5000/api';

export interface BackendResponse<T> {
  success: boolean;
  data: T;
  timestamp: string;
  error?: string;
}

/**
 * Analyze comments from YouTube trailer
 * Sends comments to backend BERT model for sentiment analysis
 */
export async function analyzeTrailer(request: AnalyzeRequest): Promise<AnalysisResult> {
  try {
    // For now, simulate a batch of comments from the trailer
    const dummyComments = [
      'This movie looks absolutely amazing!',
      'I cannot wait for this release!',
      'The action scenes are incredible',
      'Best trailer I have ever seen',
      'Not interested in this movie',
      'The plot seems confusing',
      'This is just okay, nothing special',
      'Loved the cinematography',
      'The dialogue seems awkward',
      'This will definitely be a hit'
    ];

    // Call backend sentiment analysis endpoint
    const response = await fetch(`${API_BASE_URL}/sentiment/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        comments: dummyComments,
        trailer_id: `trailer-${Date.now()}`
      })
    });

    if (!response.ok) {
      throw new Error(`Backend error: ${response.statusText}`);
    }

    const backendData: BackendResponse<any> = await response.json();

    if (!backendData.success) {
      throw new Error(backendData.error || 'Analysis failed');
    }

    // Transform backend response to frontend format
    const analysis = backendData.data;
    
    return {
      id: `ANL-${Date.now().toString().slice(-6)}`,
      trailerTitle: request.trailerName || 'Untitled Trailer',
      sourceUrl: request.trailerUrl || 'Uploaded trailer file',
      generatedAt: new Date().toLocaleString(),
      
      // Sentiment from backend
      sentiment: {
        positive: analysis.sentiment?.positive || 0,
        negative: analysis.sentiment?.negative || 0,
        neutral: analysis.sentiment?.neutral || 0
      },

      // Overall metrics
      audienceScore: analysis.sentiment?.positive || 0,
      confidence: 92,
      overallReaction: (analysis.sentiment?.positive || 0) > 50 ? 'High' : (analysis.sentiment?.negative || 0) > 50 ? 'Low' : 'Moderate',
      
      // Engagement forecast
      engagementForecast: Math.round((analysis.sentiment?.positive || 0) * 0.8 + 20),

      // Popularity metrics with required fields
      popularity: {
        views: 125430,
        likes: 8234,
        comments: 1523,
        engagementRate: 7.8,
        likeRatio: 0.067,
        velocity: 0.85
      },

      // Emotions from backend (backend returns as deeperEmotions)
      deeperEmotions: {
        anticipation: analysis.deeperEmotions?.anticipation || 35,
        excitement: analysis.deeperEmotions?.excitement || 40,
        disappointment: analysis.deeperEmotions?.disappointment || 15
      },

      // Topics and regions from backend
      commentTopics: (analysis.commentTopics || []).map((t: any) => ({ topic: t.topic || t, mentions: t.count || 0 })),
      regionalInterest: analysis.regionalInterest || [],

      // Mock data for charts (these would come from video analysis in phase 2)
      sceneIntensities: [
        { scene: 'Opening sequence', timestamp: '0:00', visualEmotion: 'Curious', sceneType: 'Setup', intensityScore: 0.7, motionLevel: 'Low', audioEnergy: 0.6 },
        { scene: 'Action shot', timestamp: '1:15', visualEmotion: 'Intense', sceneType: 'Action', intensityScore: 0.9, motionLevel: 'High', audioEnergy: 0.85 },
        { scene: 'Dialogue scene', timestamp: '2:30', visualEmotion: 'Contemplative', sceneType: 'Dialogue', intensityScore: 0.4, motionLevel: 'Low', audioEnergy: 0.5 },
        { scene: 'Climax sequence', timestamp: '3:45', visualEmotion: 'Climactic', sceneType: 'Action', intensityScore: 0.95, motionLevel: 'High', audioEnergy: 0.9 },
        { scene: 'Ending shot', timestamp: '4:50', visualEmotion: 'Resolute', sceneType: 'Conclusion', intensityScore: 0.6, motionLevel: 'Medium', audioEnergy: 0.7 }
      ],
      topFeatures: [
        { feature: 'Action', importance: 92 },
        { feature: 'Cinematography', importance: 85 },
        { feature: 'Soundtrack', importance: 78 },
        { feature: 'Dialogue', importance: 65 }
      ],
      recommendations: [
        { id: 1, title: 'Trending Action Focus', priority: 95, evidence: 'High action intensity detected', action: 'Promote action sequences', component: 'Action' },
        { id: 2, title: 'Strong Sentiment', priority: 87, evidence: '70% positive sentiment', action: 'Feature audience testimonials', component: 'Sentiment' },
        { id: 3, title: 'Target Demographics', priority: 82, evidence: 'Strong US engagement', action: 'Run US-targeted campaigns', component: 'Regional' },
        { id: 4, title: 'Engagement Peak', priority: 78, evidence: 'High excitement detected', action: 'Release at peak hours', component: 'Timing' }
      ],
      modelMetrics: [
        { metric: 'Accuracy', value: 0.87 },
        { metric: 'Precision', value: 0.89 },
        { metric: 'Recall', value: 0.85 },
        { metric: 'F1 Score', value: 0.87 }
      ]
    };
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
}

/**
 * Check backend health status
 */
export async function checkBackendHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/sentiment/status`);
    const data: BackendResponse<any> = await response.json();
    return data.success;
  } catch (error) {
    console.error('Backend health check failed:', error);
    return false;
  }
}

/**
 * Get model information from backend
 */
export async function getModelInfo(): Promise<any> {
  try {
    const response = await fetch(`${API_BASE_URL}/sentiment/model-info`);
    const data: BackendResponse<any> = await response.json();
    return data.data;
  } catch (error) {
    console.error('Failed to get model info:', error);
    return null;
  }
}

// Mock functions for compatibility during transition
export async function getLatestAnalysis(): Promise<AnalysisResult> {
  // This would fetch from backend cache in production
  throw new Error('Not implemented yet');
}

export async function getAnalysisHistory(): Promise<any[]> {
  // This would fetch from backend database in production
  return [];
}
