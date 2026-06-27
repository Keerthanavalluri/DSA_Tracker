"use client";

import React, { useState } from "react";
import { useAuth } from "@/components/AuthContext";
import { fetchAPI } from "@/lib/api";
import { useRouter } from "next/navigation";

export default function Home() {
  const { user, login } = useAuth();
  const router = useRouter();
  
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // If already logged in, redirect to dashboard
  if (user) {
    router.push("/dashboard");
    return null;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      if (isLogin) {
        const res = await fetchAPI("/auth/login", {
          method: "POST",
          body: JSON.stringify({ email, password }),
        });
        login(res.access_token);
        router.push("/dashboard");
      } else {
        const res = await fetchAPI("/auth/register", {
          method: "POST",
          body: JSON.stringify({ email, username, password }),
        });
        login(res.access_token);
        router.push("/dashboard");
      }
    } catch (err: any) {
      setError(err.message || "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
      <div className="glass-card animate-fade-in" style={{ width: '100%', maxWidth: '450px', padding: '2.5rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <h1 style={{ color: 'var(--primary)', fontSize: '2.5rem', marginBottom: '0.5rem' }}>
            DSA<span style={{color: 'var(--foreground)'}}>tracker</span>
          </h1>
          <p style={{ color: 'var(--secondary-foreground)', opacity: 0.8 }}>
            Master competitive programming with AI-driven insights.
          </p>
        </div>

        {error && (
          <div style={{ padding: '0.75rem', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid var(--danger)', borderRadius: 'var(--radius-sm)', color: 'var(--danger)', marginBottom: '1.5rem', fontSize: '0.875rem' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {!isLogin && (
            <div className="form-group">
              <label>Username</label>
              <input 
                type="text" 
                className="input" 
                value={username} 
                onChange={(e) => setUsername(e.target.value)}
                required={!isLogin}
              />
            </div>
          )}
          
          <div className="form-group">
            <label>Email Address</label>
            <input 
              type="email" 
              className="input" 
              value={email} 
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label>Password</label>
            <input 
              type="password" 
              className="input" 
              value={password} 
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button 
            type="submit" 
            className="btn btn-primary" 
            style={{ width: '100%', marginTop: '1rem', padding: '0.75rem' }}
            disabled={loading}
          >
            {loading ? <div className="spinner" style={{width: '18px', height: '18px'}} /> : (isLogin ? "Sign In" : "Create Account")}
          </button>
        </form>

        <div style={{ marginTop: '1.5rem', textAlign: 'center', fontSize: '0.875rem' }}>
          <span style={{ color: 'var(--secondary-foreground)' }}>
            {isLogin ? "Don't have an account? " : "Already have an account? "}
          </span>
          <button 
            type="button" 
            onClick={() => setIsLogin(!isLogin)}
            style={{ background: 'none', border: 'none', color: 'var(--accent)', cursor: 'pointer', fontWeight: 500 }}
          >
            {isLogin ? "Sign up" : "Sign in"}
          </button>
        </div>
      </div>
    </div>
  );
}
