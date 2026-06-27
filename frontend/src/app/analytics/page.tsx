"use client";

import React from "react";

export default function Analytics() {
  return (
    <div className="animate-fade-in" style={{ maxWidth: '800px' }}>
      <h1 style={{ fontSize: '2rem', marginBottom: '2rem' }}>Detailed Analytics</h1>
      <div className="glass-card">
        <h2>Coming Soon</h2>
        <p style={{ color: 'var(--secondary-foreground)', marginTop: '1rem' }}>
          This page will hold more detailed charts and graphs. For now, an overview of your stats 
          can be found on the main Dashboard.
        </p>
      </div>
    </div>
  );
}
