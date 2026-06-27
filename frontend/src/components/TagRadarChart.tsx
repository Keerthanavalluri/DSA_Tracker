"use client";

import React from 'react';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip } from 'recharts';

type RadarProps = {
  data: { topic: string; solved: number; failed: number }[];
};

export default function TagRadarChart({ data }: RadarProps) {
  // Take top 8 topics for the radar chart to keep it clean
  const chartData = data.slice(0, 8).map(d => ({
    subject: d.topic,
    A: d.solved,
    B: d.failed,
    fullMark: Math.max(10, d.solved + d.failed)
  }));

  if (chartData.length === 0) {
    return (
      <div className="glass-card" style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <p style={{ color: 'var(--secondary-foreground)', opacity: 0.7 }}>Not enough data for radar chart.</p>
      </div>
    );
  }

  return (
    <div className="glass-card animate-fade-in" style={{ height: '350px', display: 'flex', flexDirection: 'column' }}>
      <h3 style={{ marginBottom: '0.5rem', color: 'var(--foreground)' }}>Topic Strengths</h3>
      <div style={{ flex: 1, minHeight: 0 }}>
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart cx="50%" cy="50%" outerRadius="70%" data={chartData}>
            <PolarGrid stroke="rgba(255,255,255,0.1)" />
            <PolarAngleAxis dataKey="subject" tick={{ fill: 'rgba(255,255,255,0.7)', fontSize: 12 }} />
            <PolarRadiusAxis angle={30} domain={[0, 'auto']} tick={false} axisLine={false} />
            <Tooltip 
              contentStyle={{ backgroundColor: 'var(--background)', border: '1px solid var(--border)', borderRadius: '8px' }}
              itemStyle={{ color: 'var(--foreground)' }}
            />
            <Radar name="Solved" dataKey="A" stroke="var(--accent)" fill="var(--accent)" fillOpacity={0.5} />
            <Radar name="Failed" dataKey="B" stroke="var(--danger)" fill="var(--danger)" fillOpacity={0.5} />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
