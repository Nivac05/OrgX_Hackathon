import React, { useState, useEffect } from 'react';
import {
  AreaChart, Area, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell
} from 'recharts';

const API_BASE = 'http://localhost:8081';
const FOG = '#cfcaca';

// ─── Helpers ─────────────────────────────────────────────────────────────────

function randomBetween(a: number, b: number) {
  return Math.floor(Math.random() * (b - a + 1)) + a;
}

function timeLabel() {
  return new Date().toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

// ─── Sub-components ──────────────────────────────────────────────────────────

function Card({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return (
    <div
      className={`rounded-2xl border bg-white/30 backdrop-blur-sm ${className}`}
      style={{ borderColor: 'rgba(0,0,0,0.08)' }}
    >
      {children}
    </div>
  );
}

function KPIBox({
  label, value, sub, accent = false
}: { label: string; value: string; sub?: string; accent?: boolean }) {
  return (
    <Card className="p-6 flex flex-col gap-1">
      <span className="text-xs font-medium tracking-widest uppercase" style={{ color: 'rgba(0,0,0,0.38)' }}>{label}</span>
      <span
        className="text-3xl font-semibold tracking-tighter leading-none mt-1"
        style={{ color: accent ? '#c0392b' : '#0f0f0f' }}
      >
        {value}
      </span>
      {sub && <span className="text-xs mt-1" style={{ color: 'rgba(0,0,0,0.38)' }}>{sub}</span>}
    </Card>
  );
}

const SUSPICIOUS_MOCK = [
  { id: 'u_anon_9f82', prob: 0.94, events: 247 },
  { id: 'u_bot_master', prob: 0.87, events: 188 },
];

// ─── Main App ────────────────────────────────────────────────────────────────

export default function App() {
  const [ingestion, setIngestion] = useState<{ time: string; rps: number; bot: number }[]>(() =>
    Array.from({ length: 24 }, (_, i) => ({
      time: new Date(Date.now() - (24 - i) * 2000).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      rps: randomBetween(10, 60),
      bot: Math.random() * 0.4,
    }))
  );

  const [liveStats, setLiveStats] = useState({ total_users: 1482, working_threads: 4, suspicious: 2 });
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const tick = async () => {
      try {
        const [met, sus] = await Promise.all([
          fetch(`${API_BASE}/metrics`).then(r => r.json()),
          fetch(`${API_BASE}/suspicious`).then(r => r.json()),
        ]);
        setLiveStats({ total_users: met.total_users, working_threads: met.working_threads, suspicious: sus.suspicious_count });
        setConnected(true);
      } catch {
        setConnected(false);
        // Simulate live fluctuation
        setLiveStats(prev => ({
          ...prev,
          total_users: prev.total_users + randomBetween(0, 3),
        }));
      }
      // Advance chart
      setIngestion(prev => {
        const next = {
          time: timeLabel(),
          rps: randomBetween(8, 72),
          bot: Math.round(Math.random() * 45) / 100,
        };
        return [...prev.slice(1), next];
      });
    };

    const iv = setInterval(tick, 2000);
    tick();
    return () => clearInterval(iv);
  }, []);

  // Bot probability distribution mock
  const botDistribution = [
    { name: 'Low (0–0.3)', value: 68, color: '#b5c4b1' },
    { name: 'Medium (0.3–0.7)', value: 22, color: '#8a9e85' },
    { name: 'High (>0.7)', value: 10, color: '#5a3e3e' },
  ];

  return (
    <div className="min-h-screen" style={{ background: FOG }}>
      {/* ── Topbar ── */}
      <header
        className="sticky top-0 z-50 flex items-center justify-between px-8 py-4"
        style={{ background: `${FOG}cc`, backdropFilter: 'blur(12px)', borderBottom: '1px solid rgba(0,0,0,0.07)' }}
      >
        <div className="flex items-center gap-4">
          <a
            href="http://localhost:3000"
            className="text-sm tracking-tight flex items-center gap-1.5 font-medium"
            style={{ color: 'rgba(0,0,0,0.45)' }}
          >
            ← WpDev
          </a>
          <span style={{ color: 'rgba(0,0,0,0.15)' }}>|</span>
          <h1 className="text-sm font-semibold tracking-tight" style={{ color: '#0f0f0f' }}>
            Analytics Engine
          </h1>
        </div>
        <div className="flex items-center gap-2">
          <div
            className="w-1.5 h-1.5 rounded-full"
            style={{ background: connected ? '#4ade80' : '#f59e0b' }}
          />
          <span className="text-xs tracking-wide" style={{ color: 'rgba(0,0,0,0.4)' }}>
            {connected ? 'Connected to C++ backend' : 'Simulating · backend offline'}
          </span>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-8 py-10 space-y-8">

        {/* ── KPI Row ── */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <KPIBox label="Total Users" value={liveStats.total_users.toLocaleString()} sub="tracked in WAL" />
          <KPIBox label="Ingestion Rate" value={`${ingestion[ingestion.length - 1]?.rps ?? 0} req/s`} sub="rolling 2s window" />
          <KPIBox label="Active Threads" value={liveStats.working_threads.toString()} sub="POSIX pool workers" />
          <KPIBox label="Flagged Actors" value={liveStats.suspicious.toString()} sub="bot prob > 0.8" accent={liveStats.suspicious > 0} />
        </div>

        {/* ── Charts Row ── */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Real-time ingestion */}
          <Card className="lg:col-span-2 p-6">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h2 className="text-base font-semibold tracking-tighter" style={{ color: '#0f0f0f' }}>Real-Time Ingestion</h2>
                <p className="text-xs mt-0.5" style={{ color: 'rgba(0,0,0,0.38)' }}>Requests per second · live</p>
              </div>
              <div className="flex items-center gap-4 text-xs" style={{ color: 'rgba(0,0,0,0.38)' }}>
                <span className="flex items-center gap-1.5"><span className="w-3 h-0.5 inline-block rounded-full bg-stone-600" /> Requests</span>
                <span className="flex items-center gap-1.5"><span className="w-3 h-0.5 inline-block rounded-full" style={{ background: '#b5746a' }} /> Bot score</span>
              </div>
            </div>
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={ingestion} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="gRps" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#5a5a5a" stopOpacity={0.18} />
                      <stop offset="95%" stopColor="#5a5a5a" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="gBot" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#b5746a" stopOpacity={0.18} />
                      <stop offset="95%" stopColor="#b5746a" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="2 4" stroke="rgba(0,0,0,0.07)" vertical={false} />
                  <XAxis dataKey="time" stroke="rgba(0,0,0,0.2)" fontSize={10} tickLine={false} axisLine={false} interval={5} />
                  <YAxis stroke="rgba(0,0,0,0.2)" fontSize={10} tickLine={false} axisLine={false} />
                  <Tooltip
                    contentStyle={{ background: '#e8e4e4', border: '1px solid rgba(0,0,0,0.09)', borderRadius: '10px', fontSize: 12 }}
                    labelStyle={{ color: 'rgba(0,0,0,0.5)' }}
                  />
                  <Area type="monotone" dataKey="rps" stroke="#5a5a5a" strokeWidth={1.5} fill="url(#gRps)" isAnimationActive={false} />
                  <Area type="monotone" dataKey="bot" stroke="#b5746a" strokeWidth={1.5} fill="url(#gBot)" isAnimationActive={false} yAxisId={0} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Card>

          {/* Bot distribution pie */}
          <Card className="p-6 flex flex-col">
            <h2 className="text-base font-semibold tracking-tighter mb-1" style={{ color: '#0f0f0f' }}>Bot Probability</h2>
            <p className="text-xs mb-6" style={{ color: 'rgba(0,0,0,0.38)' }}>Distribution across tracked users</p>
            <div className="flex-1 flex items-center justify-center">
              <PieChart width={160} height={160}>
                <Pie data={botDistribution} cx={80} cy={80} innerRadius={46} outerRadius={72} paddingAngle={3} dataKey="value">
                  {botDistribution.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
              </PieChart>
            </div>
            <div className="space-y-2 mt-4">
              {botDistribution.map((d, i) => (
                <div key={i} className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full" style={{ background: d.color }} />
                    <span style={{ color: 'rgba(0,0,0,0.55)' }}>{d.name}</span>
                  </div>
                  <span className="font-medium" style={{ color: '#0f0f0f' }}>{d.value}%</span>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* ── Thread Load + Suspicious ── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Thread / WAL activity */}
          <Card className="p-6">
            <h2 className="text-base font-semibold tracking-tighter mb-1" style={{ color: '#0f0f0f' }}>Thread Pool Activity</h2>
            <p className="text-xs mb-6" style={{ color: 'rgba(0,0,0,0.38)' }}>POSIX concurrent workers over time</p>
            <div className="h-40">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={ingestion} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="2 4" stroke="rgba(0,0,0,0.07)" vertical={false} />
                  <XAxis dataKey="time" stroke="rgba(0,0,0,0.2)" fontSize={10} tickLine={false} axisLine={false} interval={5} />
                  <YAxis stroke="rgba(0,0,0,0.2)" fontSize={10} tickLine={false} axisLine={false} domain={[0, 4]} />
                  <Tooltip
                    contentStyle={{ background: '#e8e4e4', border: '1px solid rgba(0,0,0,0.09)', borderRadius: '10px', fontSize: 12 }}
                  />
                  <Line type="stepAfter" dataKey="rps" stroke="#8a7e78" strokeWidth={1.5} dot={false} isAnimationActive={false} name="RPS" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Card>

          {/* Suspicious users */}
          <Card className="p-6">
            <div className="flex justify-between items-center mb-4">
              <div>
                <h2 className="text-base font-semibold tracking-tighter" style={{ color: '#0f0f0f' }}>Flagged Actors</h2>
                <p className="text-xs mt-0.5" style={{ color: 'rgba(0,0,0,0.38)' }}>High LR probability · WAL logged</p>
              </div>
              <span
                className="text-xs px-2.5 py-1 rounded-full font-medium"
                style={{ background: 'rgba(90,62,62,0.12)', color: '#5a3e3e' }}
              >
                {SUSPICIOUS_MOCK.length} flagged
              </span>
            </div>
            <div className="space-y-3">
              {SUSPICIOUS_MOCK.map((u, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between p-3.5 rounded-xl"
                  style={{ background: 'rgba(90,62,62,0.06)', border: '1px solid rgba(90,62,62,0.12)' }}
                >
                  <div>
                    <p className="font-mono text-sm font-medium" style={{ color: '#5a3e3e' }}>{u.id}</p>
                    <p className="text-xs mt-0.5" style={{ color: 'rgba(0,0,0,0.35)' }}>{u.events} events</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold" style={{ color: '#5a3e3e' }}>{(u.prob * 100).toFixed(0)}%</p>
                    <p className="text-xs mt-0.5" style={{ color: 'rgba(0,0,0,0.35)' }}>bot prob</p>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* ── System Info Footer ── */}
        <div className="flex flex-wrap items-center justify-between gap-4 pt-2 pb-10"
          style={{ borderTop: '1px solid rgba(0,0,0,0.07)' }}>
          <div className="flex gap-8 text-xs" style={{ color: 'rgba(0,0,0,0.35)' }}>
            <span>C++17 Engine · Crow REST API</span>
            <span>POSIX Thread Pool · 4 workers</span>
            <span>Write-Ahead Log · crash-safe</span>
            <span>Logistic Regression Inference</span>
          </div>
          <span className="text-xs" style={{ color: 'rgba(0,0,0,0.25)' }}>WpDev Behavioural Analytics · 2026</span>
        </div>
      </main>
    </div>
  );
}
