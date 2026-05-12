import { Heart, Play } from "lucide-react";
import clsx from "clsx";
import type { Track } from "../api";
import { useApp } from "../store";

export function TrackList({ tracks }: { tracks: Track[] }) {
  const { currentTrack, setCurrentTrack, setIsPlaying, rate } = useApp();

  const energyColor = (e?: number) => {
    if (e === undefined) return "text-neutral-500";
    if (e < 4) return "text-neon-blue";
    if (e < 6) return "text-neon-green";
    if (e < 8) return "text-neon-yellow";
    return "text-neon-pink";
  };

  return (
    <div className="glass rounded-xl overflow-hidden">
      <table className="w-full text-sm font-mono">
        <thead className="border-b border-neon-purple/20">
          <tr className="text-xs text-neon-purple uppercase tracking-wider">
            <th className="p-3 text-left w-10">#</th>
            <th className="p-3 text-left">Artist / Title</th>
            <th className="p-3 text-right">BPM</th>
            <th className="p-3 text-center">Key</th>
            <th className="p-3 text-center">Energy</th>
            <th className="p-3 text-left">Genre</th>
            <th className="p-3 text-left">Mood</th>
            <th className="p-3 text-center w-10"></th>
          </tr>
        </thead>
        <tbody>
          {tracks.map((t, i) => {
            const active = currentTrack?.id === t.id;
            return (
              <tr
                key={t.id}
                className={clsx(
                  "border-b border-white/5 cursor-pointer transition group",
                  active
                    ? "bg-neon-pink/10 text-white"
                    : "text-neutral-300 hover:bg-white/5"
                )}
                onClick={() => {
                  setCurrentTrack(t);
                  setIsPlaying(true);
                }}
              >
                <td className="p-3 text-neutral-500 relative">
                  <span className={active ? "hidden" : "group-hover:hidden"}>{i + 1}</span>
                  <Play
                    size={14}
                    className={clsx(
                      "absolute top-1/2 -translate-y-1/2",
                      active ? "text-neon-pink animate-pulse" : "hidden group-hover:block text-white"
                    )}
                  />
                </td>
                <td className="p-3 max-w-xs">
                  <div className="truncate font-semibold">
                    {t.title ?? t.filename}
                  </div>
                  <div className="truncate text-xs text-neon-purple">
                    {t.artist ?? "Unknown"}
                  </div>
                </td>
                <td className="p-3 text-right text-neon-pink font-bold">
                  {t.bpm ? t.bpm.toFixed(1) : "-"}
                </td>
                <td className="p-3 text-center">
                  <span className="px-2 py-0.5 rounded bg-neon-blue/10 text-neon-blue text-xs border border-neon-blue/20">
                    {t.camelot ?? "-"}
                  </span>
                </td>
                <td className={clsx("p-3 text-center font-bold", energyColor(t.energy))}>
                  {t.energy ?? "-"}
                </td>
                <td className="p-3 text-xs">{t.genre_ai ?? "-"}</td>
                <td className="p-3 text-xs text-neon-green">{t.mood_label ?? "-"}</td>
                <td className="p-3">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      rate(t.id, (t.rating ?? 0) >= 1 ? 0 : 1);
                    }}
                    className={clsx(
                      "p-1 rounded transition",
                      (t.rating ?? 0) >= 1 ? "text-neon-pink" : "text-neutral-600 hover:text-neon-pink"
                    )}
                  >
                    <Heart size={14} fill={(t.rating ?? 0) >= 1 ? "currentColor" : "none"} />
                  </button>
                </td>
              </tr>
            );
          })}
          {tracks.length === 0 && (
            <tr>
              <td colSpan={8} className="p-12 text-center text-neutral-500">
                No tracks. Run a scan to get started.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
