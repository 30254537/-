import { LayoutDashboard, Music2, Sparkles, ListMusic, Copy } from "lucide-react";
import { useApp } from "../store";
import clsx from "clsx";

const ITEMS = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "library", label: "Library", icon: Music2 },
  { id: "recommend", label: "AI Recommend", icon: Sparkles },
  { id: "playlist", label: "Playlist Builder", icon: ListMusic },
  { id: "dedupe", label: "Duplicates", icon: Copy },
] as const;

export function Sidebar() {
  const { view, setView, stats } = useApp();

  return (
    <aside className="w-60 glass flex flex-col gap-1 p-4 border-r border-neon-purple/20">
      <div className="mb-6">
        <h1 className="font-display text-2xl font-bold tracking-widest">
          <span className="text-neon-pink neon-text">MIX</span>
          <span className="text-neon-blue neon-text">MIND</span>
        </h1>
        <p className="text-xs text-neon-purple font-mono mt-1">DJ // v0.3.0</p>
      </div>

      {ITEMS.map((item) => {
        const Icon = item.icon;
        const active = view === item.id;
        return (
          <button
            key={item.id}
            onClick={() => setView(item.id as any)}
            className={clsx(
              "flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-mono transition-all",
              active
                ? "bg-gradient-to-r from-neon-pink/20 to-neon-purple/20 text-white border border-neon-pink/40 shadow-[0_0_20px_rgba(255,46,166,0.3)]"
                : "text-neutral-400 hover:text-white hover:bg-white/5"
            )}
          >
            <Icon size={18} className={active ? "text-neon-pink" : ""} />
            {item.label}
          </button>
        );
      })}

      <div className="mt-auto p-3 rounded-lg glass text-xs space-y-2">
        <div className="flex justify-between">
          <span className="text-neutral-400">Tracks</span>
          <span className="text-neon-blue">{stats?.total_tracks ?? 0}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-neutral-400">Liked</span>
          <span className="text-neon-green">{stats?.liked ?? 0}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-neutral-400">Hours</span>
          <span className="text-neon-purple">{stats?.total_hours ?? 0}h</span>
        </div>
      </div>
    </aside>
  );
}
