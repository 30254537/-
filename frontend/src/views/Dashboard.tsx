import { useEffect, useState } from "react";
import { Sparkles, Music2, Clock, Heart, FolderSearch, Loader2 } from "lucide-react";
import { useApp } from "../store";
import { Scene3D } from "../components/Scene3D";
import { api } from "../api";

export function Dashboard() {
  const { stats, loadStats, currentTrack } = useApp();
  const [scanFolder, setScanFolder] = useState("");
  const [scanJob, setScanJob] = useState<{ id: string; status: string; done: number; total: number } | null>(null);

  useEffect(() => {
    loadStats();
  }, []);

  useEffect(() => {
    if (!scanJob || scanJob.status === "done" || scanJob.status === "error") return;
    const t = setInterval(async () => {
      try {
        const s = await api.jobStatus(scanJob.id);
        setScanJob({ ...scanJob, ...s });
        if (s.status === "done") loadStats();
      } catch (e) {
        console.error(e);
      }
    }, 1000);
    return () => clearInterval(t);
  }, [scanJob?.status, scanJob?.id]);

  const startScan = async () => {
    if (!scanFolder) return;
    try {
      const { job_id } = await api.startScan(scanFolder);
      setScanJob({ id: job_id, status: "starting", done: 0, total: 0 });
    } catch (e: any) {
      alert(e.message);
    }
  };

  return (
    <div className="relative flex-1 overflow-hidden">
      {/* Full-screen 3D background */}
      <div className="absolute inset-0">
        <Scene3D
          energy={currentTrack?.energy ?? 5}
          bpm={currentTrack?.bpm ?? 120}
          activeKey={currentTrack?.camelot}
        />
      </div>

      <div className="relative z-10 h-full overflow-y-auto p-8 grid-bg">
        <div className="max-w-6xl mx-auto space-y-6">
          <div>
            <h2 className="font-display text-5xl font-black tracking-wider">
              <span className="text-neon-pink neon-text">WELCOME</span>{" "}
              <span className="text-neon-blue neon-text">DJ</span>
            </h2>
            <p className="text-neutral-400 font-mono text-sm mt-2">
              Professional-grade audio analysis. Camelot key detection. Real-time AI taste learning.
            </p>
          </div>

          <div className="grid grid-cols-4 gap-4">
            <StatCard icon={Music2} label="Tracks" value={stats?.total_tracks ?? 0} color="blue" />
            <StatCard icon={Clock} label="Hours" value={`${stats?.total_hours ?? 0}h`} color="purple" />
            <StatCard icon={Heart} label="Liked" value={stats?.liked ?? 0} color="pink" />
            <StatCard icon={Sparkles} label="Analyzed" value={stats?.analyzed ?? 0} color="green" />
          </div>

          <div className="glass rounded-xl p-6 space-y-3 neon-border">
            <div className="flex items-center gap-2 mb-2">
              <FolderSearch className="text-neon-pink" size={20} />
              <h3 className="font-display font-bold text-lg tracking-wider">SCAN MUSIC LIBRARY</h3>
            </div>
            <div className="flex gap-2">
              <input
                value={scanFolder}
                onChange={(e) => setScanFolder(e.target.value)}
                placeholder="D:\Music\NewDownloads"
                className="flex-1 bg-bg-1 border border-neon-purple/30 rounded-lg px-4 py-2 font-mono text-sm focus:border-neon-pink focus:outline-none focus:shadow-[0_0_20px_rgba(255,46,166,0.3)]"
              />
              <button
                onClick={startScan}
                disabled={!scanFolder || (scanJob && scanJob.status !== "done" && scanJob.status !== "error")}
                className="px-6 py-2 rounded-lg bg-gradient-to-r from-neon-pink to-neon-purple text-white font-bold tracking-wider text-sm disabled:opacity-40 hover:shadow-[0_0_20px_rgba(255,46,166,0.5)] transition"
              >
                SCAN
              </button>
            </div>
            {scanJob && (
              <div className="space-y-1 font-mono text-xs">
                <div className="flex justify-between">
                  <span className="text-neon-blue">
                    {scanJob.status === "done" ? "✓ DONE" : scanJob.status.toUpperCase()}
                    {scanJob.status !== "done" && (
                      <Loader2 size={10} className="inline ml-2 animate-spin" />
                    )}
                  </span>
                  <span className="text-neutral-400">
                    {scanJob.done} / {scanJob.total}
                  </span>
                </div>
                <div className="h-1.5 rounded-full bg-bg-1 overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-neon-pink to-neon-blue transition-all"
                    style={{
                      width: `${scanJob.total ? (scanJob.done / scanJob.total) * 100 : 0}%`,
                    }}
                  />
                </div>
              </div>
            )}
          </div>

          {stats?.genres && stats.genres.length > 0 && (
            <div className="glass rounded-xl p-6">
              <h3 className="font-display font-bold text-lg tracking-wider mb-4 text-neon-blue">
                GENRE BREAKDOWN
              </h3>
              <div className="space-y-2">
                {stats.genres.slice(0, 8).map((g) => {
                  const pct = (g.c / stats.total_tracks) * 100;
                  return (
                    <div key={g.genre_ai}>
                      <div className="flex justify-between text-xs font-mono mb-1">
                        <span>{g.genre_ai}</span>
                        <span className="text-neon-purple">
                          {g.c} ({pct.toFixed(1)}%)
                        </span>
                      </div>
                      <div className="h-1.5 rounded-full bg-bg-1 overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-neon-pink to-neon-purple"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: any;
  label: string;
  value: string | number;
  color: "pink" | "blue" | "purple" | "green";
}) {
  const colorMap = {
    pink: "text-neon-pink border-neon-pink/30",
    blue: "text-neon-blue border-neon-blue/30",
    purple: "text-neon-purple border-neon-purple/30",
    green: "text-neon-green border-neon-green/30",
  };
  return (
    <div className={`glass rounded-xl p-5 border ${colorMap[color]}`}>
      <Icon className={colorMap[color]} size={24} />
      <div className="font-display font-black text-3xl mt-2">{value}</div>
      <div className="text-neutral-400 font-mono text-xs uppercase tracking-wider">{label}</div>
    </div>
  );
}
