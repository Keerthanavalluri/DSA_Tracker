"use client";

import React from 'react';

type StatsProps = {
  totalSolved: number;
  acceptanceRate: number;
  currentStreak: number;
  longestStreak: number;
};

export default function StatsBar({ totalSolved, acceptanceRate, currentStreak, longestStreak }: StatsProps) {
  const StatItem = ({ label, value, highlight }: { label: string; value: string | number; highlight?: boolean }) => (
    <div className="glass-card animate-fade-in" style={{ flex: 1, minWidth: '200px', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
      <span style={{ fontSize: '0.875rem', color: 'var(--secondary-foreground)', opacity: 0.8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        {label}
      </span>
      <span style={{ fontSize: '2.5rem', fontWeight: 700, color: highlight ? 'var(--primary)' : 'var(--foreground)', lineHeight: 1 }}>
        {value}
      </span>
    </div>
  );

  return (
    <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', marginBottom: '2rem' }}>
      <StatItem label="Total Solved" value={totalSolved} highlight />
      <StatItem label="Acceptance Rate" value={`${acceptanceRate}%`} />
      <StatItem label="Current Streak" value={`${currentStreak} 🔥`} highlight={currentStreak > 0} />
      <StatItem label="Longest Streak" value={longestStreak} />
    </div>
  );
}
