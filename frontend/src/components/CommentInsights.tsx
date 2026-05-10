import { MessageSquareText, Lightbulb } from 'lucide-react';
import type { AnalysisResult } from '../types';

interface CommentInsightsProps {
  analysis: AnalysisResult;
}

export function CommentInsights({ analysis }: CommentInsightsProps) {
  // Generate insights based on sentiment distribution
  const insights = generateInsights(analysis);

  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        {/* Total Comments */}
        <div className="rounded-2xl border border-slate-200/80 bg-gradient-to-br from-blue-50 to-blue-100/50 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-slate-600">Total Comments</p>
              <p className="mt-1 text-2xl font-bold text-deepnavy">
                {formatNumber(analysis.popularity.comments)}
              </p>
            </div>
            <MessageSquareText className="h-8 w-8 text-blue-500 opacity-30" />
          </div>
        </div>

        {/* Sentiment Dominance */}
        <div className="rounded-2xl border border-slate-200/80 bg-gradient-to-br from-emerald-50 to-emerald-100/50 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-slate-600">Sentiment Dominance</p>
              <p className="mt-1 text-2xl font-bold text-emerald-700">
                {analysis.sentiment.positive > analysis.sentiment.negative ? 'Positive' : 'Negative'}
              </p>
              <p className="mt-1 text-xs text-slate-600">
                {Math.abs(analysis.sentiment.positive - analysis.sentiment.negative)}% difference
              </p>
            </div>
            <Lightbulb className="h-8 w-8 text-emerald-500 opacity-30" />
          </div>
        </div>
      </div>

      {/* Key Insights */}
      <div className="rounded-2xl border border-slate-200/80 bg-slate-50/40 p-5">
        <h3 className="mb-3 text-sm font-bold text-slate-700">Key Insights</h3>
        <ul className="space-y-2">
          {insights.map((insight, index) => (
            <li key={index} className="flex items-start gap-3 text-sm text-slate-600">
              <span className="mt-1 inline-block h-1.5 w-1.5 rounded-full bg-tealbrand flex-shrink-0" />
              <span>{insight}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Top Discussion Topics */}
      {analysis.commentTopics.length > 0 && (
        <div className="rounded-2xl border border-slate-200/80 bg-slate-50/40 p-5">
          <h3 className="mb-3 text-sm font-bold text-slate-700">Top Discussion Topics</h3>
          <div className="flex flex-wrap gap-2">
            {analysis.commentTopics.slice(0, 5).map((topic) => (
              <span
                key={topic.topic}
                className="inline-flex items-center gap-2 rounded-full border border-tealbrand/30 bg-tealbrand/5 px-3 py-1.5 text-xs font-semibold text-tealbrand"
              >
                {topic.topic}
                <span className="opacity-70">({topic.mentions})</span>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function generateInsights(analysis: AnalysisResult): string[] {
  const insights: string[] = [];
  const { sentiment, commentTopics, regionalInterest } = analysis;

  // Sentiment insights
  if (sentiment.positive > 60) {
    insights.push('🌟 Overwhelmingly positive sentiment - audience highly engaged with this trailer');
  } else if (sentiment.positive > 50) {
    insights.push('✅ Strong positive reception with room for improvement in specific areas');
  } else if (sentiment.negative > sentiment.positive) {
    insights.push('⚠️ Mixed to negative reception - consider analyzing critical feedback');
  }

  // Topic insights
  if (commentTopics.length > 0) {
    const topTopic = commentTopics[0];
    insights.push(`💬 Most discussed element: ${topTopic.topic} (${topTopic.mentions} mentions)`);
  }

  // Regional insights
  if (regionalInterest.length > 0) {
    const topRegion = regionalInterest.reduce((prev, current) =>
      prev.value > current.value ? prev : current
    );
    insights.push(`🌍 Strongest audience engagement from ${topRegion.region} region`);
  }

  // Engagement quality
  if (analysis.popularity.likeRatio > 90) {
    insights.push('👍 Exceptional like-to-comment ratio indicates high content quality');
  }

  // Velocity insights
  if (analysis.popularity.velocity > 70) {
    insights.push('⚡ Rapid engagement growth - viral potential detected');
  }

  return insights.length > 0
    ? insights
    : [
        'Analyzing comment patterns...',
        'Monitoring sentiment trends...',
        'Tracking audience discussions...'
      ];
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat('en', {
    notation: 'compact',
    maximumFractionDigits: 1
  }).format(value);
}
