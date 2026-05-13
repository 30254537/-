import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { useApp } from "../../store";
import { api } from "../../api";

export function PanelTrends() {
  const { t } = useApp();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const refresh = async (force = false) => {
    setLoading(true);
    try {
      const r = await api.pro.trends(undefined, force);
      setData(r);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  return (
    <div className="space-y-3">
      <button
        onClick={() => refresh(true)}
        disabled={loading}
        className="px-4 py-2 rounded-lg bg-gradient-to-r from-neon-blue to-neon-purple text-white font-display font-bold tracking-wider flex items-center gap-2 disabled:opacity-40"
      >
        {loading ? <Loader2 size={14} className="animate-spin" /> : "📡"}
        {t("pro.trends.refresh")}
      </button>

      {data?.online === false && (
        <p className="text-xs text-neutral-500 font-mono">{t("pro.trends.empty")}</p>
      )}

      {data?.sections?.map((sec: any) => (
        <div key={sec.chart} className="glass rounded-lg p-3 space-y-2">
          <div className="flex items-center justify-between text-xs font-mono">
            <span className="text-neon-pink uppercase tracking-wider">{sec.chart}</span>
            <span className="text-neutral-400">
              <span className="text-neon-green">✓ {sec.have_count}</span>
              <span className="mx-2 text-neutral-600">|</span>
              <span className="text-neon-yellow">! {sec.missing_count}</span>
            </span>
          </div>

          <div className="h-2 rounded-full bg-bg-1 overflow-hidden flex">
            <div
              className="bg-gradient-to-r from-neon-green to-neon-blue"
              style={{ width: `${(sec.have_count / Math.max(1, sec.total)) * 100}%` }}
            />
            <div
              className="bg-gradient-to-r from-neon-yellow to-neon-pink"
              style={{ width: `${(sec.missing_count / Math.max(1, sec.total)) * 100}%` }}
            />
          </div>

          <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
            <div>
              <div className="text-neon-green mb-1">{t("pro.trends.have")}</div>
              <div className="space-y-0.5 max-h-32 overflow-y-auto">
                {sec.have.slice(0, 6).map((h: any, i: number) => (
                  <div key={i} className="text-neutral-300 truncate">
                    #{h.rank} {h.artist} — {h.title}
                  </div>
                ))}
                {sec.have.length === 0 && <div className="text-neutral-500">—</div>}
              </div>
            </div>
            <div>
              <div className="text-neon-yellow mb-1">{t("pro.trends.missing")}</div>
              <div className="space-y-0.5 max-h-32 overflow-y-auto">
                {sec.missing.slice(0, 6).map((m: any, i: number) => (
                  <div key={i} className="text-neutral-300 truncate">
                    #{m.rank} {m.artist} — {m.title}
                  </div>
                ))}
                {sec.missing.length === 0 && <div className="text-neutral-500">—</div>}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
