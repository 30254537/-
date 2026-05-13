import { useState } from "react";
import { Copy, Loader2 } from "lucide-react";
import { api, type Track } from "../api";
import { useApp } from "../store";

export function Dedupe() {
  const { t } = useApp();
  const [groups, setGroups] = useState<Track[][]>([]);
  const [running, setRunning] = useState(false);
  const [summary, setSummary] = useState<{ groups: number; tracks: number } | null>(null);

  const run = async () => {
    setRunning(true);
    try {
      const r = await api.dedupe();
      setGroups(r.data);
      setSummary({ groups: r.groups, tracks: r.tracks });
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-4 grid-bg">
      <div className="flex items-center justify-between">
        <h2 className="font-display text-3xl font-bold tracking-wider">
          <span className="text-neon-yellow neon-text">{t("dd.title1")}</span>{" "}
          <span className="text-neon-pink neon-text">{t("dd.title2")}</span>
        </h2>
        <button
          onClick={run}
          disabled={running}
          className="px-4 py-2 rounded-lg bg-gradient-to-r from-neon-yellow to-neon-pink text-black font-display font-bold tracking-wider flex items-center gap-2 hover:scale-105 transition disabled:opacity-40"
        >
          {running ? <Loader2 size={16} className="animate-spin" /> : <Copy size={16} />}
          {running ? t("dd.scanning") : t("dd.run")}
        </button>
      </div>

      {summary && (
        <div className="glass rounded-xl p-4 font-mono text-sm">
          {t("dd.found")}{" "}
          <span className="text-neon-yellow font-bold">{summary.groups}</span> {t("dd.groups")}{" "}
          <span className="text-neon-pink font-bold">{summary.tracks}</span> {t("dd.tracks")}
          <span className="text-neutral-400 ml-2">{t("dd.advice")}</span>
        </div>
      )}

      {groups.map((g, i) => {
        return (
          <div key={i} className="glass rounded-xl overflow-hidden">
            <div className="px-4 py-2 bg-neon-yellow/10 border-b border-neon-yellow/20 font-mono text-xs text-neon-yellow">
              {t("dd.group")} #{g[0].duplicate_group_id}
            </div>
            <div className="divide-y divide-white/5">
              {g.map((tr, idx) => (
                <div key={tr.id} className="p-3 flex items-center gap-4 text-sm font-mono">
                  <span
                    className={`w-20 text-xs font-bold ${
                      idx === 0 ? "text-neon-green" : "text-red-400"
                    }`}
                  >
                    {idx === 0 ? t("dd.keep") : t("dd.remove")}
                  </span>
                  <span className="flex-1 truncate">
                    {tr.artist} - {tr.title}
                  </span>
                  <span className="text-neutral-400 text-xs">
                    {tr.bpm ? `${tr.bpm} BPM` : ""}
                  </span>
                  <span className="text-neutral-500 text-xs w-20 text-right">
                    {(((tr as any).filesize ?? 0) / 1024 / 1024).toFixed(1)} MB
                  </span>
                </div>
              ))}
            </div>
          </div>
        );
      })}

      {!running && groups.length === 0 && summary && summary.groups === 0 && (
        <div className="glass rounded-xl p-12 text-center text-neutral-500 font-mono">
          {t("dd.empty")}
        </div>
      )}
    </div>
  );
}
