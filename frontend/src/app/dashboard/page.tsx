"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "@/components/AuthContext";
import { fetchAPI } from "@/lib/api";
import StatsBar from "@/components/StatsBar";
import HeatmapCalendar from "@/components/HeatmapCalendar";
import TagRadarChart from "@/components/TagRadarChart";
import TimerWidget from "@/components/TimerWidget";

export default function Dashboard() {
  const { user, loading } = useAuth();
  
  const [stats, setStats] = useState<any>(null);
  const [heatmapData, setHeatmapData] = useState<any>(null);
  const [topicData, setTopicData] = useState<any>(null);
  const [dataLoading, setDataLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user || loading) return;
    
    const loadData = async () => {
      setDataLoading(true);
      try {
        const [statsRes, heatmapRes, topicRes] = await Promise.all([
          fetchAPI("/analytics/stats"),
          fetchAPI("/analytics/heatmap?days=180"),
          fetchAPI("/analytics/topic-matrix")
        ]);
        
        setStats(statsRes);
        setHeatmapData(heatmapRes.heatmap);
        setTopicData(topicRes.topics);
      } catch (err: any) {
        setError(err.message || "Failed to load dashboard data");
      } finally {
        setDataLoading(false);
      }
    };
    
    loadData();
  }, [user, loading]);

  if (loading || dataLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', flexDirection: 'column', gap: '1rem' }}>
        <div className="spinner"></div>
        <p style={{ color: 'var(--secondary-foreground)' }}>Loading dashboard...</p>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="glass-card">
        <h2>Not Authenticated</h2>
        <p>Please log in to view your dashboard.</p>
        <a href="/" className="btn btn-primary" style={{ marginTop: '1rem' }}>Go to Login</a>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-card" style={{ borderLeft: '4px solid var(--danger)' }}>
        <h3 style={{ color: 'var(--danger)' }}>Error Loading Dashboard</h3>
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      <header>
        <h1 style={{ fontSize: '2rem', marginBottom: '0.25rem' }}>Welcome back, {user.username} 👋</h1>
        <p style={{ color: 'var(--secondary-foreground)' }}>Here's an overview of your competitive programming journey.</p>
      </header>

      {stats && (
        <StatsBar 
          totalSolved={stats.totalSolved} 
          acceptanceRate={stats.acceptanceRate} 
          currentStreak={stats.currentStreak} 
          longestStreak={stats.longestStreak} 
        />
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1.5rem' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {heatmapData && <HeatmapCalendar data={heatmapData} days={180} />}
          
          <div className="glass-card">
            <h3>Recent Platforms</h3>
            <p style={{ color: 'var(--secondary-foreground)', fontSize: '0.875rem' }}>
              Your activity breakdown by platform.
            </p>
            <div style={{ marginTop: '1rem', display: 'flex', gap: '1rem' }}>
              {stats?.byPlatform && Object.entries(stats.byPlatform).length > 0 ? (
                Object.entries(stats.byPlatform).map(([platform, count]) => (
                  <div key={platform} style={{ padding: '0.5rem 1rem', background: 'rgba(255,255,255,0.05)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
                    <span style={{ textTransform: 'capitalize', fontWeight: 500 }}>{platform}</span>
                    <span style={{ marginLeft: '0.5rem', color: 'var(--accent)' }}>{String(count)}</span>
                  </div>
                ))
              ) : (
                <p style={{ color: 'var(--secondary-foreground)' }}>No platforms connected yet.</p>
              )}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {topicData && <TagRadarChart data={topicData} />}
          <TimerWidget />
        </div>
      </div>
    </div>
  );
}
