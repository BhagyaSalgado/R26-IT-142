import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, PieChart, Pie, Legend as RechartsLegend } from 'recharts';
import type { AnalysisResult } from '../types';

interface CommentChartsProps {
  result: AnalysisResult;
}

const topicColors = ['#2563EB', '#06B6D4', '#E11DFA', '#7C3AED', '#F59E0B'];

export function CommentTopicsChart({ result }: CommentChartsProps) {
  const data = result.commentTopics.map((topic) => ({
    name: topic.topic,
    mentions: topic.mentions
  }));

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
          <YAxis dataKey="name" type="category" tick={{ fontSize: 11 }} width={80} />
          <Tooltip />
          <Bar dataKey="mentions" radius={[0, 8, 8, 0]}>
            {data.map((entry, index) => (
              <Cell key={entry.name} fill={topicColors[index % topicColors.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function RegionalInterestChart({ result }: CommentChartsProps) {
  const data = result.regionalInterest.map((region) => ({
    name: region.region,
    value: region.value
  }));

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
            outerRadius={90}
            paddingAngle={4}
          >
            {data.map((entry, index) => (
              <Cell key={entry.name} fill={topicColors[index % topicColors.length]} />
            ))}
          </Pie>
          <Tooltip formatter={(value) => [`${value}%`, 'Share']} />
          <RechartsLegend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
