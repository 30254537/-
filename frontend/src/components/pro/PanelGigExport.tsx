import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { useApp } from "../../store";
import { api } from "../../api";

export function PanelGigExport() {
  const { t } = useApp();
  const [outRoot, setOutRoot] = useState("");
  const [playlistId, setPlaylistId] = useState<number | null>(null);
  const [normalize, setNormalize] = useState(-8);
  const [covers, setCovers] = useState(true);
  const [playlists, setPlaylists] = useState<Array<{ id: number; name: string; track_count: number }>>([]);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<any>(null);

  useEffect(() => {
    fetch("/api/playlists")
      .then((r) => r.json())
      .then((d) => setPlaylists(d.playlists ?? []))
      .catch(() => {});
  }, []);

  const run = async () => {
    if (!outRoot || playlistId === null) return;
    setBusy(true);
    setResult(null);
    try {
      const r = await api.pro.gigExport({
        out_root: outRoot,
        playlist_id: playlistId,
        playlist_name: playlists.find((p) => p.id === playlistId)?.name || "Gig",
        normalize_lufs: normalize,
        include_covers: covers,
      });
      setResult(r);
    } catch (e: any) {
      alert(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-3">
      <div>
        <label className="text-xs font-mono uppercase text-neon-purple block mb-1">
          {t("pro.gig.out_dir")}
        </label>
        <input
          value={outRoot}
          onChange={(e) => setOutRoot(e.target.value)}
          placeholder={t("pro.gig.placeholder")}
          className="w-full bg-bg-1 border border-neon-purple/30 rounded px-3 py-2 font-mono text-sm"
        />
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div>
          <label className="text-xs font-mono uppercase text-neon-purple block mb-1">
            {t("pro.gig.playlist")}
          </label>
          <select
            value={playlistId ?? ""}
            onChange={(e) => setPlaylistId(e.target.value ? Number(e.target.value) : null)}
            className="w-full bg-bg-1 border border-neon-purple/30 rounded px-3 py-2 font-mono text-sm"
          >
            <option value="">—</option>
            {playlists.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.track_count})
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="text-xs font-mono uppercase text-neon-purple block mb-1">
            {t("pro.gig.normalize")}
          </label>
          <input
            type="number"
            value={normalize}
            onChange={(e) => setNormalize(Number(e.target.value))}
            className="w-full bg-bg-1 border border-neon-purple/30 rounded px-3 py-2 font-mono text-sm"
          />
        </div>
        <div className="flex items-end">
          <label className="flex items-center gap-2 font-mono text-xs">
            <input
              type="checkbox"
              checked={covers}
              onChange={(e) => setCovers(e.target.checked)}
              className="accent-neon-pink"
            />
            {t("pro.gig.covers")}
          </label>
        </div>
      </div>

      <button
        onClick={run}
        disabled={busy || !outRoot || playlistId === null}
        className="px-4 py-2 rounded-lg bg-gradient-to-r from-neon-yellow to-neon-pink text-black font-display font-bold tracking-wider flex items-center gap-2 disabled:opacity-40"
      >
        {busy ? <Loader2 size={14} className="animate-spin" /> : "📦"}
        {t("pro.gig.go")}
      </button>

      {result && (
        <div className="glass rounded-lg p-3 space-y-2 text-xs font-mono">
          <div className="text-neon-green">✓ {t("pro.gig.success")}</div>
          <div>
            <span className="text-neutral-500">{t("pro.gig.tracks")}:</span>{" "}
            <span className="text-neon-pink">{result.track_count}</span>
          </div>
          <div>
            <span className="text-neutral-500">{t("pro.gig.size")}:</span>{" "}
            <span className="text-neon-blue">{result.total_size_mb} MB</span>
          </div>
          <div className="text-[10px] text-neutral-400 truncate">{result.out_dir}</div>
          {result.failures?.length > 0 && (
            <div className="text-red-400">
              ⚠ {result.failures.length} failures
            </div>
          )}
        </div>
      )}
    </div>
  );
}
