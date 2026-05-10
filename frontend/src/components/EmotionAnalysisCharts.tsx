import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie,
} from 'recharts';
import type { AnalysisResult } from '../types';

interface EmotionChartsProps {
  result: AnalysisResult;
}

const sentimentColors = {
  positive: '#2563EB',
  neutral: '#06B6D4',
  negative: '#E11DFA'
};

const emotionColors = {
  anticipation: '#F59E0B',
  excitement: '#EC4899',
  disappointment: '#8B5CF6'
};

export function SentimentEmotionComparison({ result }: EmotionChartsProps) {
  const data = [
    {
      name: 'Sentiment',
      positive: result.sentiment.positive,
      neutral: result.sentiment.neutral,
      negative: result.sentiment.negative
    },
    {
      name: 'Emotions',
      positive: result.deeperEmotions.excitement,
      neutral: result.deeperEmotions.anticipation,
      negative: result.deeperEmotions.disappointment
    }
  ];

  return (
    <div className="h-72">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
          <XAxis dataKey="name" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip />
          <Legend />
          <Bar dataKey="positive" stackId="a" fill="#2563EB" name="Positive/Excitement" />
          <Bar dataKey="neutral" stackId="a" fill="#06B6D4" name="Neutral/Anticipation" />
          <Bar dataKey="negative" stackId="a" fill="#E11DFA" name="Negative/Disappointment" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function DeeperEmotionsChart({ result }: EmotionChartsProps) {
  const data = [
    { name: 'Anticipation', value: result.deeperEmotions.anticipation },
    { name: 'Excitement', value: result.deeperEmotions.excitement },
    { name: 'Disappointment', value: result.deeperEmotions.disappointment }
  ];

  return (
    <div className="h-72">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            outerRadius={100}
            paddingAngle={3}
          >
            {data.map((entry, index) => (
              <Cell
                key={entry.name}
                fill={Object.values(emotionColors)[index]}
              />
            ))}
          </Pie>
          <Tooltip formatter={(value) => [`${value}%`, 'Share']} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

export function EmotionDistributionChart({ result }: EmotionChartsProps) {
  const data = [
    { name: 'Anticipation', value: result.deeperEmotions.anticipation, fill: emotionColors.anticipation },
    { name: 'Excitement', value: result.deeperEmotions.excitement, fill: emotionColors.excitement },
    { name: 'Disappointment', value: result.deeperEmotions.disappointment, fill: emotionColors.disappointment }
  ];

  return (
    <div className="h-72">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          margin={{ top: 10, right: 8, left: -16, bottom: 0 }}
          layout="vertical"
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
          <XAxis type="number" tick={{ fontSize: 11 }} />
          <YAxis dataKey="name" type="category" tick={{ fontSize: 11 }} width={100} />
          <Tooltip />
          <Bar dataKey="value" radius={[0, 8, 8, 0]}>
            {data.map((entry) => (
              <Cell key={entry.name} fill={entry.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function SentimentAndEmotionSummary({ result }: EmotionChartsProps) {
  const sentiments = [
    { label: 'Positive', value: result.sentiment.positive, color: sentimentColors.positive },
    { label: 'Neutral', value: result.sentiment.neutral, color: sentimentColors.neutral },
    { label: 'Negative', value: result.sentiment.negative, color: sentimentColors.negative }
  ];

  const emotions = [
    { label: 'Anticipation', value: result.deeperEmotions.anticipation, color: emotionColors.anticipation },
    { label: 'Excitement', value: result.deeperEmotions.excitement, color: emotionColors.excitement },
    { label: 'Disappointment', value: result.deeperEmotions.disappointment, color: emotionColors.disappointment }
  ];

  return (
    <div className="space-y-6">
      {/* Sentiment Distribution */}
      <div>
        <h4 className="mb-3 text-sm font-bold text-slate-700">Basic Sentiment Distribution</h4>
        <div className="flex gap-3">
          {sentiments.map((item) => (
            <div key={item.label} className="flex-1">
              <div className="mb-2 flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-600">{item.label}</span>
                <span className="text-sm font-black text-slate-900">{item.value}%</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-slate-200">
                <div
                  className="h-full transition-all duration-500"
                  style={{ width: `${item.value}%`, backgroundColor: item.color }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Deeper Emotions Distribution */}
      <div>
        <h4 className="mb-3 text-sm font-bold text-slate-700">Deeper Audience Emotions</h4>
        <div className="flex gap-3">
          {emotions.map((item) => (
            <div key={item.label} className="flex-1">
              <div className="mb-2 flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-600">{item.label}</span>
                <span className="text-sm font-black text-slate-900">{item.value}%</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-slate-200">
                <div
                  className="h-full transition-all duration-500"
                  style={{ width: `${item.value}%`, backgroundColor: item.color }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
