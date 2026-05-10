/**
 * Mock Backend Server for Testing
 * This simulates API responses without needing a real backend
 * 
 * Usage:
 * 1. Import this in sentimentApi.ts
 * 2. Set REACT_APP_USE_MOCK=true in .env
 * 3. API calls will return mock data instead of calling backend
 */

import type { CommentAnalysisResponse } from './sentimentApi';

// Simulate network delay
const RESPONSE_DELAY_MS = 1500;

// Multiple mock responses to test different scenarios
const MOCK_RESPONSES: Record<string, CommentAnalysisResponse> = {
  positive_trailer: {
    sentiment: {
      positive: 72,
      neutral: 18,
      negative: 10
    },
    commentTopics: [
      { topic: 'Lead actor', mentions: 5200 },
      { topic: 'Background music', mentions: 3800 },
      { topic: 'Visual effects', mentions: 2650 },
      { topic: 'Storyline', mentions: 1850 },
      { topic: 'Release date', mentions: 1200 }
    ],
    regionalInterest: [
      { region: 'United States', value: 35 },
      { region: 'India', value: 25 },
      { region: 'United Kingdom', value: 15 },
      { region: 'Sri Lanka', value: 12 },
      { region: 'Other', value: 13 }
    ],
    totalComments: 22500,
    modelMetrics: {
      accuracy: 0.89,
      precision: 0.91,
      recall: 0.87,
      f1Score: 0.89
    }
  },

  mixed_trailer: {
    sentiment: {
      positive: 48,
      neutral: 32,
      negative: 20
    },
    commentTopics: [
      { topic: 'Plot concerns', mentions: 3200 },
      { topic: 'Cast debate', mentions: 2800 },
      { topic: 'Special effects', mentions: 2100 },
      { topic: 'Dialogue quality', mentions: 1600 },
      { topic: 'Expectations', mentions: 1100 }
    ],
    regionalInterest: [
      { region: 'United States', value: 32 },
      { region: 'India', value: 22 },
      { region: 'Europe', value: 20 },
      { region: 'Asia', value: 15 },
      { region: 'Other', value: 11 }
    ],
    totalComments: 15800,
    modelMetrics: {
      accuracy: 0.84,
      precision: 0.86,
      recall: 0.82,
      f1Score: 0.84
    }
  },

  negative_trailer: {
    sentiment: {
      positive: 25,
      neutral: 28,
      negative: 47
    },
    commentTopics: [
      { topic: 'Negative reaction', mentions: 4500 },
      { topic: 'Story concerns', mentions: 3800 },
      { topic: 'Visual quality', mentions: 2200 },
      { topic: 'Actor concerns', mentions: 1900 },
      { topic: 'Franchise worry', mentions: 1600 }
    ],
    regionalInterest: [
      { region: 'United States', value: 40 },
      { region: 'United Kingdom', value: 20 },
      { region: 'Canada', value: 15 },
      { region: 'Australia', value: 12 },
      { region: 'Other', value: 13 }
    ],
    totalComments: 19200,
    modelMetrics: {
      accuracy: 0.87,
      precision: 0.88,
      recall: 0.86,
      f1Score: 0.87
    }
  }
};

/**
 * Determine which mock response to return based on URL
 */
export function getMockResponseForUrl(trailerUrl: string): CommentAnalysisResponse {
  const urlLower = trailerUrl.toLowerCase();

  // Keyword-based routing
  if (
    urlLower.includes('positive') ||
    urlLower.includes('amazing') ||
    urlLower.includes('great')
  ) {
    return MOCK_RESPONSES.positive_trailer;
  }

  if (urlLower.includes('negative') || urlLower.includes('bad')) {
    return MOCK_RESPONSES.negative_trailer;
  }

  if (urlLower.includes('mixed') || urlLower.includes('average')) {
    return MOCK_RESPONSES.mixed_trailer;
  }

  // Default: return based on URL hash (consistent for same URL)
  const hash = trailerUrl
    .split('')
    .reduce((acc, char) => acc + char.charCodeAt(0), 0);
  const responses = Object.values(MOCK_RESPONSES);
  return responses[hash % responses.length];
}

/**
 * Simulate API call delay
 */
function simulateDelay(ms: number = RESPONSE_DELAY_MS): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Mock implementation of analyzeCommentSentiment
 */
export async function mockAnalyzeCommentSentiment(
  trailerUrl: string
): Promise<CommentAnalysisResponse> {
  await simulateDelay();
  return getMockResponseForUrl(trailerUrl);
}

/**
 * Mock implementation of getCommentTopics
 */
export async function mockGetCommentTopics(
  trailerId: string
): Promise<Array<{ topic: string; mentions: number }>> {
  await simulateDelay(800);
  
  // Simulate different topics for different trailers
  const hash = trailerId.length % 3;
  const responses = [
    MOCK_RESPONSES.positive_trailer.commentTopics,
    MOCK_RESPONSES.mixed_trailer.commentTopics,
    MOCK_RESPONSES.negative_trailer.commentTopics
  ];
  
  return responses[hash];
}

/**
 * Mock implementation of getRegionalDistribution
 */
export async function mockGetRegionalDistribution(
  trailerId: string
): Promise<Array<{ region: string; value: number }>> {
  await simulateDelay(800);

  const hash = trailerId.charCodeAt(0) % 3;
  const responses = [
    MOCK_RESPONSES.positive_trailer.regionalInterest,
    MOCK_RESPONSES.mixed_trailer.regionalInterest,
    MOCK_RESPONSES.negative_trailer.regionalInterest
  ];

  return responses[hash];
}

/**
 * Mock implementation of getSentimentMetrics
 */
export async function mockGetSentimentMetrics(
  trailerId: string
): Promise<{
  sentiment: { positive: number; neutral: number; negative: number };
  metrics: { accuracy: number; precision: number; recall: number; f1Score: number };
}> {
  await simulateDelay(600);

  const response = getMockResponseForUrl(trailerId);
  return {
    sentiment: response.sentiment,
    metrics: response.modelMetrics
  };
}

/**
 * Mock implementation of getCommentDetails
 */
export async function mockGetCommentDetails(
  trailerId: string,
  limit: number = 50
): Promise<
  Array<{
    id: string;
    text: string;
    sentiment: 'positive' | 'neutral' | 'negative';
    confidence: number;
    language: string;
    likes: number;
  }>
> {
  await simulateDelay(1200);

  const SAMPLE_COMMENTS = [
    {
      id: 'c1',
      text: 'This trailer is absolutely amazing! Cannot wait for the movie!',
      sentiment: 'positive' as const,
      confidence: 0.95,
      language: 'en',
      likes: 2500
    },
    {
      id: 'c2',
      text: 'The visual effects look incredible',
      sentiment: 'positive' as const,
      confidence: 0.87,
      language: 'en',
      likes: 1800
    },
    {
      id: 'c3',
      text: 'I have mixed feelings about this',
      sentiment: 'neutral' as const,
      confidence: 0.71,
      language: 'en',
      likes: 650
    },
    {
      id: 'c4',
      text: 'The plot seems a bit weak',
      sentiment: 'negative' as const,
      confidence: 0.82,
      language: 'en',
      likes: 420
    },
    {
      id: 'c5',
      text: 'Great music and cinematography!',
      sentiment: 'positive' as const,
      confidence: 0.91,
      language: 'en',
      likes: 3200
    },
    {
      id: 'c6',
      text: 'I am not sure about this one',
      sentiment: 'neutral' as const,
      confidence: 0.64,
      language: 'en',
      likes: 380
    },
    {
      id: 'c7',
      text: 'Disappointed with the direction',
      sentiment: 'negative' as const,
      confidence: 0.88,
      language: 'en',
      likes: 920
    },
    {
      id: 'c8',
      text: 'This is exactly what I wanted!',
      sentiment: 'positive' as const,
      confidence: 0.93,
      language: 'en',
      likes: 2100
    }
  ];

  return SAMPLE_COMMENTS.slice(0, limit);
}

/**
 * List of all available mock scenarios
 */
export const MOCK_SCENARIOS = {
  positive: {
    name: 'Positive Reception',
    url: 'https://youtube.com/watch?v=positive-trailer',
    description: '72% positive sentiment'
  },
  mixed: {
    name: 'Mixed Reception',
    url: 'https://youtube.com/watch?v=mixed-trailer',
    description: '48% positive, 32% neutral, 20% negative'
  },
  negative: {
    name: 'Negative Reception',
    url: 'https://youtube.com/watch?v=negative-trailer',
    description: '47% negative sentiment'
  }
};

/**
 * Console helper: List all available scenarios
 */
export function listMockScenarios(): void {
  console.log('Available Mock Scenarios:');
  Object.entries(MOCK_SCENARIOS).forEach(([key, scenario]) => {
    console.log(`  ${key}: ${scenario.name}`);
    console.log(`    URL: ${scenario.url}`);
    console.log(`    ${scenario.description}`);
  });
}
