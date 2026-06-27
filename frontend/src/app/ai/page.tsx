"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/components/AuthContext";
import { fetchAPI } from "@/lib/api";

export default function AICoach() {
  const { user } = useAuth();
  
  const [recommendation, setRecommendation] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAdvice = async (force: boolean = false) => {
    setLoading(true);
    setError(null);
    try {
      if (force) {
        const res = await fetchAPI(`/ai/analyze?force_refresh=true`, { method: "POST" });
        setRecommendation(res);
      } else {
        const res = await fetchAPI("/ai/recommendations");
        setRecommendation(res);
      }
    } catch (err: any) {
      setError(err.message || "Failed to fetch AI analysis");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      fetchAdvice(false);
    }
  }, [user]);

  if (!user) {
    return <div className="glass-card"><p>Please log in to access the AI Coach.</p></div>;
  }

  return (
    <div className="animate-fade-in" style={{ maxWidth: '900px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '2rem' }}>
        <div>
          <h1 style={{ fontSize: '2rem', marginBottom: '0.25rem', color: 'var(--primary)' }}>Grok AI Coach</h1>
          <p style={{ color: 'var(--secondary-foreground)' }}>Personalized weakness analysis and problem recommendations.</p>
        </div>
        <button 
          className="btn btn-primary" 
          onClick={() => fetchAdvice(true)}
          disabled={loading}
        >
          {loading ? "Analyzing..." : "Generate Analysis"}
        </button>
      </div>

      {loading && !recommendation ? (
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', padding: '2rem' }} className="glass-card">
          <div className="spinner"></div>
          <p style={{ color: 'var(--secondary-foreground)' }}>Grok is analyzing your topic matrix...</p>
        </div>
      ) : error ? (
        <div className="glass-card" style={{ borderLeft: '4px solid var(--danger)' }}>
          <h3 style={{ color: 'var(--danger)' }}>Analysis Failed</h3>
          <p>{error}</p>
        </div>
      ) : recommendation?.error ? (
        <div className="glass-card" style={{ borderLeft: '4px solid var(--warning)' }}>
          <h3 style={{ color: 'var(--warning)' }}>Not Ready Yet</h3>
          <p>{recommendation.error}</p>
          <p style={{ marginTop: '1rem', fontSize: '0.875rem', color: 'var(--secondary-foreground)' }}>
            Go to Settings and connect your Codeforces or LeetCode account first, then come back here.
          </p>
        </div>
      ) : recommendation ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          {/* Strengths & Weaknesses */}
          <div className="glass-card" style={{ borderTop: '4px solid var(--primary)' }}>
            <h2 style={{ marginBottom: '1rem' }}>Strengths & Weaknesses</h2>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
              <div>
                <h3 style={{ color: 'var(--accent)', marginBottom: '0.75rem', fontSize: '1rem' }}>Strong Topics</h3>
                <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                  {(recommendation.strengthTopics || []).map((t: string) => (
                    <li key={t} style={{ padding: '0.5rem 0', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span style={{ color: 'var(--accent)' }}>&#10003;</span> {t}
                    </li>
                  ))}
                  {(!recommendation.strengthTopics || recommendation.strengthTopics.length === 0) && 
                    <p style={{ color: 'var(--secondary-foreground)', opacity: 0.7 }}>Need more data</p>}
                </ul>
              </div>
              <div>
                <h3 style={{ color: 'var(--danger)', marginBottom: '0.75rem', fontSize: '1rem' }}>Weak Topics</h3>
                <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                  {(recommendation.weakTopics || []).map((t: string) => (
                    <li key={t} style={{ padding: '0.5rem 0', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span style={{ color: 'var(--danger)' }}>!</span> {t}
                    </li>
                  ))}
                  {(!recommendation.weakTopics || recommendation.weakTopics.length === 0) && 
                    <p style={{ color: 'var(--secondary-foreground)', opacity: 0.7 }}>Need more data</p>}
                </ul>
              </div>
            </div>
          </div>

          {/* Suggested Problems */}
          {recommendation.suggestedProblems && recommendation.suggestedProblems.length > 0 && (
            <div className="glass-card">
              <h2 style={{ marginBottom: '1rem' }}>Recommended Problems</h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {recommendation.suggestedProblems.map((p: any, i: number) => (
                  <div key={i} style={{ 
                    padding: '1rem', 
                    background: 'rgba(255,255,255,0.03)', 
                    borderRadius: 'var(--radius-sm)', 
                    border: '1px solid var(--border)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}>
                    <div>
                      <div style={{ fontWeight: 500, marginBottom: '0.25rem' }}>
                        {p.title || p.slug}
                        <span style={{ 
                          marginLeft: '0.5rem', 
                          fontSize: '0.75rem', 
                          padding: '2px 8px', 
                          borderRadius: '12px', 
                          background: p.platform === 'LC' ? 'rgba(255,161,22,0.15)' : 'rgba(99,102,241,0.15)',
                          color: p.platform === 'LC' ? '#ffa116' : 'var(--primary)'
                        }}>
                          {p.platform}
                        </span>
                      </div>
                      <p style={{ fontSize: '0.8rem', color: 'var(--secondary-foreground)' }}>{p.reason}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Study Hints */}
          {recommendation.studyHints && recommendation.studyHints.length > 0 && (
            <div className="glass-card">
              <h2 style={{ marginBottom: '1rem' }}>Study Tips</h2>
              <ul style={{ paddingLeft: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {recommendation.studyHints.map((hint: string, i: number) => (
                  <li key={i} style={{ color: 'var(--secondary-foreground)', lineHeight: 1.6 }}>{hint}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Weekly Goal */}
          {recommendation.weeklyGoal && (
            <div className="glass-card" style={{ borderLeft: '4px solid var(--accent)' }}>
              <h2 style={{ marginBottom: '0.5rem' }}>Weekly Goal</h2>
              <p style={{ color: 'var(--secondary-foreground)', lineHeight: 1.6 }}>{recommendation.weeklyGoal}</p>
            </div>
          )}

          {recommendation.generatedAt && (
            <p style={{ fontSize: '0.75rem', color: 'var(--secondary-foreground)', opacity: 0.5, textAlign: 'right' }}>
              Generated: {new Date(recommendation.generatedAt).toLocaleString()}
            </p>
          )}
        </div>
      ) : null}
    </div>
  );
}
