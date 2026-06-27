import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";
import { AuthProvider } from "@/components/AuthContext";
import { ToastProvider } from "@/components/Toast";

export const metadata: Metadata = {
  title: "DSAtracker | Competitive Programming Dashboard",
  description: "AI-powered competitive programming performance tracker and study planner",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <div className="app-layout">
          <aside className="sidebar">
            <div style={{ paddingBottom: "2rem", borderBottom: "1px solid var(--border)" }}>
              <h2 style={{ color: "var(--primary)", margin: 0, fontSize: "1.5rem" }}>DSA<span style={{color: "var(--foreground)"}}>tracker</span></h2>
            </div>
            
            <nav style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              <Link href="/dashboard" className="btn btn-secondary" style={{justifyContent: "flex-start", padding: "0.75rem 1rem"}}>
                Dashboard
              </Link>
              <Link href="/problems" className="btn btn-secondary" style={{justifyContent: "flex-start", padding: "0.75rem 1rem"}}>
                Study Plan
              </Link>
              <Link href="/analytics" className="btn btn-secondary" style={{justifyContent: "flex-start", padding: "0.75rem 1rem"}}>
                Analytics
              </Link>
              <Link href="/ai" className="btn btn-secondary" style={{justifyContent: "flex-start", padding: "0.75rem 1rem", border: "1px solid var(--primary)", color: "var(--primary)"}}>
                AI Coach
              </Link>
              <Link href="/settings" className="btn btn-secondary" style={{justifyContent: "flex-start", padding: "0.75rem 1rem"}}>
                Settings
              </Link>
            </nav>
            
            <div style={{ marginTop: "auto", fontSize: "0.8rem", color: "var(--secondary-foreground)", opacity: 0.7 }}>
              &copy; 2026 DSAtracker
            </div>
          </aside>
          
          <main className="main-content">
            <ToastProvider>
              <AuthProvider>
                {children}
              </AuthProvider>
            </ToastProvider>
          </main>
        </div>
      </body>
    </html>
  );
}
