import { Bar, BarChart, CartesianGrid, Cell, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { AnalysisResult } from '../types';

const sentimentColors = ['#2563EB', '#06B6D4', '#E11DFA'];

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
