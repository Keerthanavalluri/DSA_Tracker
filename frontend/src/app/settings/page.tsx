"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/components/AuthContext";
import { fetchAPI } from "@/lib/api";
import { useToast } from "@/components/Toast";

export default function Settings() {
  const { user } = useAuth();
  const { toast } = useToast();
  
  const [cfHandle, setCfHandle] = useState("");
  const [lcUsername, setLcUsername] = useState("");
  const [lcCookie, setLcCookie] = useState("");
  const [ccUsername, setCcUsername] = useState("");
  
  const [cfLoading, setCfLoading] = useState(false);
  const [lcLoading, setLcLoading] = useState(false);
  const [ccLoading, setCcLoading] = useState(false);
  const [platforms, setPlatforms] = useState<any[]>([]);

  useEffect(() => {
    if (user) {
      fetchAPI("/platforms/status")
        .then(setPlatforms)
        .catch(console.error);
    }
  }, [user]);

  const handleConnectCF = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!cfHandle.trim()) return;
    
    setCfLoading(true);
    try {
      const res = await fetchAPI("/platforms/connect/codeforces", {
        method: "POST",
        body: JSON.stringify({ handle: cfHandle })
      });
      toast(res.message || `Connected Codeforces as ${cfHandle}`, "success");
      const p = await fetchAPI("/platforms/status");
      setPlatforms(p);
    } catch (err: any) {
      toast(err.message || "Failed to connect Codeforces", "error");
    } finally {
      setCfLoading(false);
    }
  };

  const handleConnectLC = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!lcUsername.trim() || !lcCookie.trim()) return;
    
    setLcLoading(true);
    try {
      const res = await fetchAPI("/platforms/connect/leetcode", {
        method: "POST",
        body: JSON.stringify({ username: lcUsername, session_cookie: lcCookie })
      });
      toast(res.message || `Connected LeetCode as ${lcUsername}`, "success");
      const p = await fetchAPI("/platforms/status");
      setPlatforms(p);
    } catch (err: any) {
      toast(err.message || "Failed to connect LeetCode", "error");
    } finally {
      setLcLoading(false);
    }
  };

  const handleConnectCC = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ccUsername.trim()) return;
    setCcLoading(true);
    try {
      const res = await fetchAPI("/platforms/connect/codechef", {
        method: "POST",
        body: JSON.stringify({ username: ccUsername })
      });
      toast(res.message || `Connected CodeChef as ${ccUsername}`, "success");
      const p = await fetchAPI("/platforms/status");
      setPlatforms(p);
    } catch (err: any) {
      toast(err.message || "Failed to connect CodeChef", "error");
    } finally {
      setCcLoading(false);
    }
  };

  const cfAccount = platforms.find(p => p.platform === "codeforces");
  const lcAccount = platforms.find(p => p.platform === "leetcode");
  const ccAccount = platforms.find(p => p.platform === "codechef");

  return (
    <div className="animate-fade-in" style={{ maxWidth: '800px' }}>
      <h1 style={{ fontSize: '2rem', marginBottom: '2rem' }}>Settings</h1>

      {/* Codeforces */}
      <div className="glass-card" style={{ marginBottom: '2rem' }}>
        <h2 style={{ marginBottom: '1rem', color: 'var(--primary)' }}>Codeforces Integration</h2>
        
        {cfAccount ? (
          <div style={{ padding: '1rem', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid var(--accent)', borderRadius: 'var(--radius-sm)', marginBottom: '1.5rem' }}>
            <p style={{ color: 'var(--accent)', fontWeight: 500 }}>
              Connected as <strong>{cfAccount.handle}</strong>
            </p>
            <p style={{ fontSize: '0.875rem', marginTop: '0.5rem', color: 'var(--secondary-foreground)' }}>
              Last Synced: {cfAccount.last_synced_at ? new Date(cfAccount.last_synced_at).toLocaleString() : "Sync in progress..."}
            </p>
          </div>
        ) : (
          <p style={{ color: 'var(--secondary-foreground)', marginBottom: '1.5rem' }}>
            Connect your Codeforces account to start tracking.
          </p>
        )}

        <form onSubmit={handleConnectCF} style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end' }}>
          <div className="form-group" style={{ flex: 1, margin: 0 }}>
            <label>Codeforces Handle</label>
            <input 
              type="text" 
              className="input" 
              placeholder="e.g. tourist"
              value={cfHandle}
              onChange={e => setCfHandle(e.target.value)}
            />
          </div>
          <button type="submit" className="btn btn-primary" disabled={cfLoading} style={{ height: '42px', padding: '0 1.5rem' }}>
            {cfLoading ? "Connecting..." : (cfAccount ? "Update" : "Connect")}
          </button>
        </form>
      </div>

      {/* LeetCode */}
      <div className="glass-card" style={{ marginBottom: '2rem' }}>
        <h2 style={{ marginBottom: '1rem', color: '#ffa116' }}>LeetCode Integration</h2>
        
        {lcAccount ? (
          <div style={{ padding: '1rem', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid var(--accent)', borderRadius: 'var(--radius-sm)', marginBottom: '1.5rem' }}>
            <p style={{ color: 'var(--accent)', fontWeight: 500 }}>
              Connected as <strong>{lcAccount.handle}</strong>
            </p>
            <p style={{ fontSize: '0.875rem', marginTop: '0.5rem', color: 'var(--secondary-foreground)' }}>
              Last Synced: {lcAccount.last_synced_at ? new Date(lcAccount.last_synced_at).toLocaleString() : "Sync in progress..."}
            </p>
          </div>
        ) : (
          <p style={{ color: 'var(--secondary-foreground)', marginBottom: '1rem' }}>
            Connect your LeetCode account using your session cookie.
          </p>
        )}

        <div className="glass-card" style={{ background: 'rgba(255, 161, 22, 0.05)', border: '1px solid rgba(255, 161, 22, 0.2)', marginBottom: '1.5rem', padding: '1rem' }}>
          <h4 style={{ color: '#ffa116', marginBottom: '0.5rem', fontSize: '0.875rem' }}>How to get your LEETCODE_SESSION cookie:</h4>
          <ol style={{ fontSize: '0.8rem', color: 'var(--secondary-foreground)', paddingLeft: '1.25rem', lineHeight: 1.8 }}>
            <li>Log in to <a href="https://leetcode.com" target="_blank" style={{ color: '#ffa116', textDecoration: 'underline' }}>leetcode.com</a></li>
            <li>Press <kbd style={{ padding: '2px 6px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', fontSize: '0.75rem' }}>F12</kbd> to open Developer Tools</li>
            <li>Go to <strong>Application</strong> tab &rarr; <strong>Cookies</strong> &rarr; <strong>leetcode.com</strong></li>
            <li>Find the cookie named <code style={{ background: 'rgba(255,255,255,0.1)', padding: '2px 6px', borderRadius: '4px' }}>LEETCODE_SESSION</code></li>
            <li>Copy its entire value and paste it below</li>
          </ol>
        </div>

        <form onSubmit={handleConnectLC}>
          <div className="form-group">
            <label>LeetCode Username</label>
            <input 
              type="text" 
              className="input" 
              placeholder="your LeetCode username"
              value={lcUsername}
              onChange={e => setLcUsername(e.target.value)}
            />
          </div>
          <div className="form-group">
            <label>LEETCODE_SESSION Cookie</label>
            <textarea 
              className="input" 
              placeholder="Paste your LEETCODE_SESSION cookie value here..."
              value={lcCookie}
              onChange={e => setLcCookie(e.target.value)}
              rows={3}
              style={{ resize: 'vertical', fontFamily: 'monospace', fontSize: '0.8rem' }}
            />
          </div>
          <button type="submit" className="btn btn-primary" disabled={lcLoading} style={{ padding: '0.75rem 1.5rem' }}>
            {lcLoading ? "Connecting..." : (lcAccount ? "Update & Re-sync" : "Connect LeetCode")}
          </button>
        </form>
      </div>
      
      {/* CodeChef */}
      <div className="glass-card" style={{ marginBottom: '2rem' }}>
        <h2 style={{ marginBottom: '1rem', color: '#5b4638' }}>CodeChef Integration</h2>
        
        {ccAccount ? (
          <div style={{ padding: '1rem', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid var(--accent)', borderRadius: 'var(--radius-sm)', marginBottom: '1.5rem' }}>
            <p style={{ color: 'var(--accent)', fontWeight: 500 }}>
              Connected as <strong>{ccAccount.handle}</strong>
            </p>
            <p style={{ fontSize: '0.875rem', marginTop: '0.5rem', color: 'var(--secondary-foreground)' }}>
              Last Synced: {ccAccount.last_synced_at ? new Date(ccAccount.last_synced_at).toLocaleString() : "Sync in progress..."}
            </p>
          </div>
        ) : (
          <p style={{ color: 'var(--secondary-foreground)', marginBottom: '1.5rem' }}>
            Connect your CodeChef account to track contest submissions.
          </p>
        )}

        <form onSubmit={handleConnectCC} style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end' }}>
          <div className="form-group" style={{ flex: 1, margin: 0 }}>
            <label>CodeChef Username</label>
            <input 
              type="text" 
              className="input" 
              placeholder="your CodeChef username"
              value={ccUsername}
              onChange={e => setCcUsername(e.target.value)}
            />
          </div>
          <button type="submit" className="btn btn-primary" disabled={ccLoading} style={{ height: '42px', padding: '0 1.5rem' }}>
            {ccLoading ? "Connecting..." : (ccAccount ? "Update" : "Connect")}
          </button>
        </form>
      </div>
    </div>
  );
}
