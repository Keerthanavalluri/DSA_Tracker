"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/components/AuthContext";
import { fetchAPI } from "@/lib/api";

export default function StudyPlanGenerator() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [planData, setPlanData] = useState<any>(null);
  const [days, setDays] = useState(7);

  const loadLatestPlan = async () => {
    try {
      const res = await fetchAPI("/study-plan/latest");
      if (res && res.plan && res.plan.length > 0) {
        setPlanData(res);
      }
    } catch (err) {
      console.error("No existing plan found.");
    }
  };

  useEffect(() => {
    if (user) {
      loadLatestPlan();
    }
  }, [user]);

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchAPI(`/study-plan/generate?days=${days}`, { method: "POST" });
      setPlanData(res);
    } catch (err: any) {
      setError(err.message || "Failed to generate study plan");
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return <div className="glass-card"><p>Please log in to generate a study plan.</p></div>;
  }

  return (
    <div className="animate-fade-in" style={{ maxWidth: '1000px', margin: '0 auto' }}>
      
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '2rem' }}>
        <div>
          <h1 style={{ fontSize: '2.5rem', marginBottom: '0.25rem', color: 'var(--primary)' }}>AI Study Plan</h1>
          <p style={{ color: 'var(--secondary-foreground)' }}>Let Grok build a personalized, day-by-day practice schedule for you.</p>
        </div>
      </div>

      {!planData && !loading && (
        <div className="glass-card" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
          <h2 style={{ marginBottom: '1rem' }}>No Active Plan</h2>
          <p style={{ color: 'var(--secondary-foreground)', marginBottom: '2rem' }}>
            Generate a targeted schedule based on your weakest topics and current progression.
          </p>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '1rem', background: 'rgba(255,255,255,0.05)', padding: '1rem', borderRadius: 'var(--radius)' }}>
            <label style={{ fontWeight: 500 }}>Duration:</label>
            <select 
              value={days} 
              onChange={(e) => setDays(Number(e.target.value))}
              className="input"
              style={{ width: '120px', margin: 0 }}
            >
              <option value={3}>3 Days</option>
              <option value={7}>1 Week</option>
              <option value={14}>2 Weeks</option>
              <option value={30}>1 Month</option>
            </select>
            <button className="btn btn-primary" onClick={handleGenerate} style={{ padding: '0.75rem 1.5rem' }}>
              Generate Plan
            </button>
          </div>
          {error && <p style={{ color: 'var(--danger)', marginTop: '1rem' }}>{error}</p>}
        </div>
      )}

      {loading && (
        <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '4rem 2rem' }}>
          <div className="spinner" style={{ width: '40px', height: '40px', marginBottom: '1.5rem' }}></div>
          <h3>Consulting Grok...</h3>
          <p style={{ color: 'var(--secondary-foreground)', marginTop: '0.5rem' }}>Analyzing your topic matrix and finding the best problems.</p>
        </div>
      )}

      {planData && !loading && (
        <>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem', background: 'rgba(99, 102, 241, 0.1)', padding: '1.5rem', borderRadius: 'var(--radius)', border: '1px solid var(--primary)' }}>
            <div>
              <h2 style={{ color: 'var(--primary)', marginBottom: '0.25rem' }}>{planData.durationDays}-Day Schedule</h2>
              <p style={{ fontSize: '0.875rem', color: 'var(--secondary-foreground)' }}>
                Generated on {new Date(planData.generatedAt).toLocaleDateString()}
              </p>
            </div>
            <div style={{ display: 'flex', gap: '1rem' }}>
              <select 
                value={days} 
                onChange={(e) => setDays(Number(e.target.value))}
                className="input"
                style={{ width: '120px', margin: 0, height: '40px' }}
              >
                <option value={3}>3 Days</option>
                <option value={7}>1 Week</option>
                <option value={14}>2 Weeks</option>
                <option value={30}>1 Month</option>
              </select>
              <button className="btn btn-secondary" onClick={handleGenerate} style={{ height: '40px' }}>
                Regenerate
              </button>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {planData.plan.map((dayItem: any, idx: number) => (
              <div key={idx} className="glass-card" style={{ position: 'relative', overflow: 'hidden' }}>
                {idx === 0 && (
                  <div style={{ position: 'absolute', top: 0, left: 0, width: '4px', height: '100%', background: 'var(--accent)' }}></div>
                )}
                
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.25rem' }}>
                  <div style={{ 
                    background: idx === 0 ? 'var(--accent)' : 'rgba(255,255,255,0.1)', 
                    color: idx === 0 ? '#000' : 'var(--foreground)',
                    padding: '0.5rem 1rem', 
                    borderRadius: '20px',
                    fontWeight: 'bold',
                    fontSize: '0.875rem'
                  }}>
                    Day {dayItem.day}
                  </div>
                  <h3 style={{ margin: 0, fontSize: '1.25rem' }}>{dayItem.focus}</h3>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
                  {dayItem.tasks && dayItem.tasks.map((task: any, tIdx: number) => (
                    <div key={tIdx} style={{ 
                      background: 'rgba(0,0,0,0.2)', 
                      padding: '1rem', 
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--border)',
                      transition: 'transform 0.2s, border-color 0.2s',
                      cursor: 'pointer'
                    }}
                    onMouseOver={(e) => {
                      e.currentTarget.style.transform = 'translateY(-2px)';
                      e.currentTarget.style.borderColor = 'var(--primary)';
                    }}
                    onMouseOut={(e) => {
                      e.currentTarget.style.transform = 'translateY(0)';
                      e.currentTarget.style.borderColor = 'var(--border)';
                    }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                        <h4 style={{ margin: 0, fontSize: '1rem' }}>{task.title}</h4>
                        <span style={{ 
                          fontSize: '0.7rem', 
                          padding: '2px 6px', 
                          borderRadius: '10px', 
                          background: task.platform === 'LC' ? 'rgba(255,161,22,0.15)' : 'rgba(99,102,241,0.15)',
                          color: task.platform === 'LC' ? '#ffa116' : 'var(--primary)',
                          fontWeight: 'bold'
                        }}>
                          {task.platform}
                        </span>
                      </div>
                      <p style={{ fontSize: '0.85rem', color: 'var(--secondary-foreground)', margin: 0, lineHeight: 1.5 }}>
                        {task.reason}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
