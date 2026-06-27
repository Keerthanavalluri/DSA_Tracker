"use client";

import React, { useState, useEffect, useRef } from "react";
import { fetchAPI } from "@/lib/api";

export default function TimerWidget() {
  const [active, setActive] = useState(false);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const [studyStats, setStudyStats] = useState<any>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const heartbeatRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Load study stats on mount
  useEffect(() => {
    loadStats();
  }, []);

  // Cleanup intervals on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (heartbeatRef.current) clearInterval(heartbeatRef.current);
    };
  }, []);

  const loadStats = async () => {
    try {
      const stats = await fetchAPI("/study/stats");
      setStudyStats(stats);
    } catch (err) {
      console.error("Failed to load study stats:", err);
    }
  };

  const startSession = async () => {
    try {
      const res = await fetchAPI("/study/start", {
        method: "POST",
        body: JSON.stringify({ problem_id: null }),
      });
      setSessionId(res.session_id);
      setActive(true);
      setElapsed(0);

      // Start local timer (1s tick)
      timerRef.current = setInterval(() => {
        setElapsed((prev) => prev + 1);
      }, 1000);

      // Start heartbeat (every 30s)
      heartbeatRef.current = setInterval(async () => {
        try {
          await fetchAPI("/study/heartbeat", { method: "POST" });
        } catch (err) {
          console.error("Heartbeat failed:", err);
        }
      }, 30000);
    } catch (err) {
      console.error("Failed to start session:", err);
    }
  };

  const endSession = async () => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (heartbeatRef.current) clearInterval(heartbeatRef.current);
    timerRef.current = null;
    heartbeatRef.current = null;

    try {
      await fetchAPI("/study/end", { method: "POST" });
    } catch (err) {
      console.error("Failed to end session:", err);
    }

    setActive(false);
    setSessionId(null);
    setElapsed(0);
    loadStats();
  };

  const formatTime = (totalSeconds: number) => {
    const h = Math.floor(totalSeconds / 3600);
    const m = Math.floor((totalSeconds % 3600) / 60);
    const s = totalSeconds % 60;
    return `${h.toString().padStart(2, "0")}:${m
      .toString()
      .padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  return (
    <div className="glass-card animate-fade-in">
      <h3 style={{ marginBottom: "1rem" }}>Study Timer</h3>

      {/* Timer display */}
      <div
        style={{
          textAlign: "center",
          padding: "1.5rem 0",
        }}
      >
        <div
          style={{
            fontSize: "3rem",
            fontWeight: 700,
            fontFamily: "monospace",
            color: active ? "var(--accent)" : "var(--foreground)",
            letterSpacing: "0.05em",
            transition: "color 0.3s ease",
          }}
        >
          {formatTime(elapsed)}
        </div>
        {active && (
          <div
            style={{
              fontSize: "0.8rem",
              color: "var(--accent)",
              marginTop: "0.5rem",
              animation: "pulse 2s infinite",
            }}
          >
            Session active...
          </div>
        )}
      </div>

      {/* Controls */}
      <div style={{ display: "flex", gap: "0.75rem", justifyContent: "center" }}>
        {!active ? (
          <button
            className="btn btn-primary"
            onClick={startSession}
            style={{ padding: "0.75rem 2rem" }}
          >
            Start Studying
          </button>
        ) : (
          <button
            className="btn"
            onClick={endSession}
            style={{
              padding: "0.75rem 2rem",
              backgroundColor: "var(--danger)",
              color: "white",
            }}
          >
            Stop Session
          </button>
        )}
      </div>

      {/* Study Stats */}
      {studyStats && (
        <div
          style={{
            marginTop: "1.5rem",
            paddingTop: "1rem",
            borderTop: "1px solid var(--border)",
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: "1rem",
          }}
        >
          <div>
            <span
              style={{
                fontSize: "0.75rem",
                color: "var(--secondary-foreground)",
                opacity: 0.7,
                textTransform: "uppercase",
                letterSpacing: "0.05em",
              }}
            >
              Today
            </span>
            <div style={{ fontSize: "1.25rem", fontWeight: 600 }}>
              {studyStats.today_minutes} min
            </div>
          </div>
          <div>
            <span
              style={{
                fontSize: "0.75rem",
                color: "var(--secondary-foreground)",
                opacity: 0.7,
                textTransform: "uppercase",
                letterSpacing: "0.05em",
              }}
            >
              This Week
            </span>
            <div style={{ fontSize: "1.25rem", fontWeight: 600 }}>
              {studyStats.week_minutes} min
            </div>
          </div>
          <div>
            <span
              style={{
                fontSize: "0.75rem",
                color: "var(--secondary-foreground)",
                opacity: 0.7,
                textTransform: "uppercase",
                letterSpacing: "0.05em",
              }}
            >
              All Time
            </span>
            <div style={{ fontSize: "1.25rem", fontWeight: 600 }}>
              {studyStats.total_minutes} min
            </div>
          </div>
          <div>
            <span
              style={{
                fontSize: "0.75rem",
                color: "var(--secondary-foreground)",
                opacity: 0.7,
                textTransform: "uppercase",
                letterSpacing: "0.05em",
              }}
            >
              Sessions
            </span>
            <div style={{ fontSize: "1.25rem", fontWeight: 600 }}>
              {studyStats.total_sessions}
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        @keyframes pulse {
          0%,
          100% {
            opacity: 1;
          }
          50% {
            opacity: 0.5;
          }
        }
      `}</style>
    </div>
  );
}
