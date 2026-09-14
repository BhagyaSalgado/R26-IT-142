import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts';
import type { AnalysisResult } from '../types';
import type {
  CommentTopic,
  DeeperEmotions,
  RegionalInterest
} from '../types/commentSentiment';
import type { BackendRecommendation } from '../services/recommendationApi';

const sentimentColors = ['#2563EB', '#06B6D4', '#E11DFA'];

const recommendationCategoryColors: Record<string, string> = {
  Visual: '#2563EB',
  Audio: '#06B6D4',
  Pacing: '#E11DFA',
  Metadata: '#7C3AED'
};

interface ChartsProps {
  result: AnalysisResult;
}

export function SentimentChart({ result }: ChartsProps) {
  const data = [
    { name: 'Positive', value: result.sentiment.positive },
    { name: 'Neutral', value: result.sentiment.neutral },
    { name: 'Negative', value: result.sentiment.negative }
  ];

  return (
    <div className="h-72">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie data={data} dataKey="value" nameKey="name" innerRadius={70} outerRadius={100} paddingAngle={4}>
            {data.map((entry, index) => <Cell key={entry.name} fill={sentimentColors[index]} />)}
          </Pie>
          <Tooltip formatter={(value) => [`${value}%`, 'Share']} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

export function SceneIntensityChart({ result }: ChartsProps) {
  const data = result.sceneIntensities.map((scene) => ({
    name: scene.scene.replace(' sequence', '').replace(' shot', ''),
    intensity: Math.round(scene.intensityScore * 100),
    audio: Math.round(scene.audioEnergy * 100)
  }));

  return (
    <div className="h-72">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 10, right: 8, left: -16, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
          <XAxis dataKey="name" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip />
          <Line type="monotone" dataKey="intensity" stroke="#7C3AED" strokeWidth={4} dot={{ r: 5 }} />
          <Line type="monotone" dataKey="audio" stroke="#06B6D4" strokeWidth={3} dot={{ r: 4 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function FeatureBarChart({ result }: ChartsProps) {
  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={result.topFeatures} layout="vertical" margin={{ top: 8, right: 12, left: 36, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
          <XAxis type="number" tick={{ fontSize: 11 }} />
          <YAxis dataKey="feature" type="category" width={126} tick={{ fontSize: 11 }} />
          <Tooltip />
          <Bar dataKey="importance" radius={[0, 10, 10, 0]} fill="#2563EB" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function CommentSentimentChart({ sentiment }: { sentiment: { positive: number; neutral: number; negative: number } }) {
  const data = [
    { name: 'Positive', value: sentiment.positive },
    { name: 'Neutral', value: sentiment.neutral },
    { name: 'Negative', value: sentiment.negative }
  ];

  return (
    <div className="h-72">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie data={data} dataKey="value" nameKey="name" innerRadius={70} outerRadius={100} paddingAngle={4}>
            {data.map((entry, index) => <Cell key={entry.name} fill={sentimentColors[index]} />)}
          </Pie>
          <Tooltip formatter={(value: number, name: string) => [`${value}%`, name]} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

export function TopicBarChart({ commentTopics }: { commentTopics: CommentTopic[] }) {
  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={commentTopics} layout="vertical" margin={{ top: 8, right: 12, left: 36, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
          <XAxis type="number" tick={{ fontSize: 11 }} />
          <YAxis dataKey="topic" type="category" width={110} tick={{ fontSize: 11 }} />
          <Tooltip />
          <Bar dataKey="mentions" radius={[0, 10, 10, 0]} fill="#7C3AED" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function RegionalBarChart({ regionalInterest }: { regionalInterest: RegionalInterest[] }) {
  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={regionalInterest} margin={{ top: 8, right: 12, left: -16, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
          <XAxis dataKey="region" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip formatter={(value) => [`${value}%`, 'Audience share']} />
          <Bar dataKey="value" radius={[10, 10, 0, 0]} fill="#06B6D4" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function EmotionRadarChart({ deeperEmotions }: { deeperEmotions: DeeperEmotions }) {
  const data = [
    { emotion: 'Joy', value: deeperEmotions.joy },
    { emotion: 'Excitement', value: deeperEmotions.excitement },
    { emotion: 'Anger', value: deeperEmotions.anger },
    { emotion: 'Sadness', value: deeperEmotions.sadness },
    { emotion: 'Fear', value: deeperEmotions.fear },
    { emotion: 'Surprise', value: deeperEmotions.surprise }
  ];

  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data} outerRadius="75%">
          <PolarGrid stroke="#E2E8F0" />
          <PolarAngleAxis dataKey="emotion" tick={{ fontSize: 12 }} />
          <PolarRadiusAxis tick={{ fontSize: 10 }} />
          <Radar dataKey="value" name="Intensity" stroke="#E11DFA" fill="#E11DFA" fillOpacity={0.35} />
          <Tooltip formatter={(value: number, name: string) => [`${value}%`, name]} />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function EmotionAnalysisCharts({ result }: { result: Record<string, unknown> }) {
  // Safely normalize optional emotion-model fields before passing them to Recharts.
  const finalRows = Array.isArray(result.final_system_output)
    ? result.final_system_output.filter(
        (row): row is Record<string, unknown> => Boolean(row) && typeof row === 'object' && !Array.isArray(row)
      )
    : [];
  const intensityData = finalRows.map((row, index) => ({
    scene: String(row.scene ?? row.scene_id ?? index + 1),
    intensity: Number(row.EI ?? row.emotional_intensity ?? row.intensity_score ?? 0),
    motion: Number(row.M ?? row.motion ?? row.motion_intensity ?? 0),
    audio: Number(row.A ?? row.audio_energy ?? 0)
  }));

  const insights = result.insights && typeof result.insights === 'object' && !Array.isArray(result.insights)
    ? (result.insights as Record<string, unknown>)
    : {};
  const distribution = insights.video_emotion_distribution;
  const emotionData = distribution && typeof distribution === 'object' && !Array.isArray(distribution)
    ? Object.entries(distribution as Record<string, unknown>).map(([emotion, value]) => ({
        emotion,
        value: Number(value ?? 0)
      }))
  // Hide the chart region when the saved analysis has no graphable detail payload.
    : [];

  if (intensityData.length === 0 && emotionData.length === 0) return null;

  return (
    <div className="grid gap-6 mt-6 lg:grid-cols-2">
      {intensityData.length > 0 && (
        <div className="rounded-3xl border border-slate-200 bg-lightbrand/40 p-5">
          <div className="mb-4">
            <p className="text-xs font-black uppercase tracking-[0.18em] text-electric">Scene timeline</p>
            <h3 className="mt-1 text-lg font-black text-deepnavy">Emotional intensity</h3>
          </div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={intensityData} margin={{ top: 8, right: 10, left: -18, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis dataKey="scene" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Line type="monotone" dataKey="intensity" name="Intensity" stroke="#7C3AED" strokeWidth={4} dot={{ r: 4 }} />
                <Line type="monotone" dataKey="motion" name="Motion" stroke="#2563EB" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="audio" name="Audio" stroke="#06B6D4" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {emotionData.length > 0 && (
        <div className="rounded-3xl border border-slate-200 bg-lightbrand/40 p-5">
          <div className="mb-4">
            <p className="text-xs font-black uppercase tracking-[0.18em] text-purplebrand">Emotion mix</p>
            <h3 className="mt-1 text-lg font-black text-deepnavy">Detected visual emotions</h3>
          </div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={emotionData} margin={{ top: 8, right: 10, left: -18, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis dataKey="emotion" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="value" name="Scenes" radius={[10, 10, 0, 0]} fill="#7C3AED" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}

export function RecommendationPriorityChart({ recommendations }: { recommendations: BackendRecommendation[] }) {
  const data = recommendations.map((rec, index) => ({
    name: `S${rec.scene ?? index + 1}`,
    priorityScore: rec.priority === 1 ? 95 : rec.priority === 2 ? 70 : 45,
    category: rec.category
  }));

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 10, left: -18, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
          <XAxis dataKey="name" tick={{ fontSize: 11 }} />
          <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
          <Tooltip />
          <Bar dataKey="priorityScore" name="Priority score" radius={[8, 8, 0, 0]}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={recommendationCategoryColors[entry.category] || '#2563EB'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function PopularityGrowthChart({
  data
}: {
  data: Array<{ name: string; current: number; predicted: number }>;
}) {
  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 10, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
          <XAxis dataKey="name" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} tickFormatter={(value: number) => new Intl.NumberFormat('en', { notation: 'compact' }).format(value)} />
          <Tooltip formatter={(value: number) => new Intl.NumberFormat('en').format(value)} />
          <Legend wrapperStyle={{ fontSize: 11, fontWeight: 700 }} />
          <Bar dataKey="current" name="Current" fill="#2563EB" radius={[6, 6, 0, 0]} />
          <Bar dataKey="predicted" name="Predicted" fill="#06B6D4" radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function PopularityGrowthPercentChart({ data }: { data: Array<{ name: string; value: number }> }) {
  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 10, left: -18, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
          <XAxis dataKey="name" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} unit="%" />
          <Tooltip formatter={(value: number) => [`${value.toFixed(1)}%`, 'Growth']} />
          <Bar dataKey="value" name="Growth" radius={[8, 8, 0, 0]}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.value < 0 ? '#E11D48' : entry.value < 15 ? '#F59E0B' : '#10B981'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
