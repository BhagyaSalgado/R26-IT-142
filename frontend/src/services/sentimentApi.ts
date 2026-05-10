import type { AnalysisResult } from '../types';

// API Configuration (Using Vite import.meta.env instead of process.env)
const API_BASE_URL = import.meta.env.REACT_APP_API_URL || 'http://localhost:5000/api';

interface CommentAnalysisRequest {
  trailerUrl: string;
  trailerTitle: string;
}

export interface CommentAnalysisResponse {
  sentiment: {
    positive: number;
    neutral: number;
    negative: number;
  };
  commentTopics: Array<{
    topic: string;
    mentions: number;
  }>;
  regionalInterest: Array<{
    region: string;
    value: number;
  }>;
  totalComments: number;
  modelMetrics: {
    accuracy: number;
    precision: number;
    recall: number;
    f1Score: number;
  };
}

/**
 * Analyze movie trailer comments for sentiment
 * @param request - Trailer URL and metadata
 * @returns Sentiment analysis results
 */
export async function analyzeCommentSentiment(
  request: CommentAnalysisRequest
): Promise<CommentAnalysisResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/sentiment/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        trailer_url: request.trailerUrl,
        trailer_title: request.trailerTitle,
      }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    const data: CommentAnalysisResponse = await response.json();
    return data;
  } catch (error) {
    console.error('Comment sentiment analysis error:', error);
    throw error;
  }
}

/**
 * Get comment topics for a specific trailer
 * @param trailerId - The trailer ID
 * @returns Array of discussion topics with mention counts
 */
export async function getCommentTopics(
  trailerId: string
): Promise<Array<{ topic: string; mentions: number }>> {
  try {
    const response = await fetch(`${API_BASE_URL}/sentiment/topics/${trailerId}`);

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    const data = await response.json();
    return data.topics;
  } catch (error) {
    console.error('Error fetching comment topics:', error);
    throw error;
  }
}

/**
 * Get regional audience distribution based on comment language
 * @param trailerId - The trailer ID
 * @returns Array of regions with audience percentage
 */
export async function getRegionalDistribution(
  trailerId: string
): Promise<Array<{ region: string; value: number }>> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/sentiment/regional-distribution/${trailerId}`
    );

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    const data = await response.json();
    return data.regions;
  } catch (error) {
    console.error('Error fetching regional distribution:', error);
    throw error;
  }
}

/**
 * Get detailed sentiment metrics
 * @param trailerId - The trailer ID
 * @returns Sentiment distribution and model performance metrics
 */
export async function getSentimentMetrics(
  trailerId: string
): Promise<{
  sentiment: { positive: number; neutral: number; negative: number };
  metrics: { accuracy: number; precision: number; recall: number; f1Score: number };
}> {
  try {
    const response = await fetch(`${API_BASE_URL}/sentiment/metrics/${trailerId}`);

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching sentiment metrics:', error);
    throw error;
  }
}

/**
 * Get individual comment details with sentiment labels
 * @param trailerId - The trailer ID
 * @param limit - Maximum number of comments to retrieve
 * @returns Array of comments with sentiment classification
 */
export async function getCommentDetails(
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
  try {
    const response = await fetch(
      `${API_BASE_URL}/sentiment/comments/${trailerId}?limit=${limit}`
    );

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    const data = await response.json();
    return data.comments;
  } catch (error) {
    console.error('Error fetching comment details:', error);
    throw error;
  }
}
