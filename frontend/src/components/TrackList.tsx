import { Heart, Play } from "lucide-react";
import clsx from "clsx";
import type { Track } from "../api";
import { useApp } from "../store";

export function TrackList({
  tracks,
  onSelect,
  selectedId,
}: {
  tracks: Track[];
  onSelect?: (t: Track) => void;
  selectedId?: number;
}) {
  const { currentTrack, setCurrentTrack, setIsPlaying, rate, t } = useApp();

  const energyColor = (e?: number) => {
    if (e === undefined) return "text-neutral-500";
    if (e < 4) return "text-neon-blue";
    if (e < 6) return "text-neon-green";
    if (e < 8) return "text-neon-yellow";
    return "text-neon-pink";
  };

  const vocalBadge = (g?: string) => {
    if (!g || g === "none") return { label: "—", cls: "text-neutral-600 bg-transparent border-transparent" };
    if (g === "male")   return { label: "♂", cls: "text-neon-blue bg-neon-blue/10 border-neon-blue/40" };
    if (g === "female") return { label: "♀", cls: "text-neon-pink bg-neon-pink/10 border-neon-pink/40" };
    if (g === "mixed")  return { label: "♂♀", cls: "text-neon-yellow bg-neon-yellow/10 border-neon-yellow/40" };
    return { label: "—", cls: "text-neutral-600 bg-transparent border-transparent" };
  };

  return (
    <div className="glass rounded-xl overflow-hidden">
      <table className="w-full text-sm font-mono">
        <thead className="border-b border-neon-purple/20">
          <tr className="text-xs text-neon-purple uppercase tracking-wider">
            <th className="p-3 text-left w-10">#</th>
            <th className="p-3 text-left">{t("table.artist_title")}</th>
            <th className="p-3 text-right">{t("table.bpm")}</th>
            <th className="p-3 text-center">{t("table.key")}</th>
            <th className="p-3 text-center">{t("table.energy")}</th>
            <th className="p-3 text-center">{t("library.gender")}</th>
            <th className="p-3 text-left">{t("table.genre")}</th>
            <th className="p-3 text-left">{t("table.mood")}</th>
            <th className="p-3 text-center w-10"></th>
          </tr>
        </thead>
        <tbody>
          {tracks.map((track, i) => {
            const active = currentTrack?.id === track.id;
            const selected = selectedId === track.id;
            return (
              <tr
                key={track.id}
                className={clsx(
                  "border-b border-white/5 cursor-pointer transition group",
                  selected
                    ? "bg-neon-blue/15 text-white border-l-2 border-l-neon-blue"
                    : active
                    ? "bg-neon-pink/10 text-white"
                    : "text-neutral-300 hover:bg-white/5"
                )}
                onClick={() => {
                  if (onSelect) {
                    onSelect(track);
                  } else {
                    setCurrentTrack(track);
                    setIsPlaying(true);
                  }
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
                    {track.title ?? track.filename}
                  </div>
                  <div className="truncate text-xs text-neon-purple">
                    {track.artist ?? t("common.unknown")}
                  </div>
                </td>
                <td className="p-3 text-right text-neon-pink font-bold">
                  {track.bpm ? track.bpm.toFixed(1) : "-"}
                </td>
                <td className="p-3 text-center">
                  <span className="px-2 py-0.5 rounded bg-neon-blue/10 text-neon-blue text-xs border border-neon-blue/20">
                    {track.camelot ?? "-"}
                  </span>
                </td>
                <td className={clsx("p-3 text-center font-bold", energyColor(track.energy))}>
                  {track.energy ?? "-"}
                </td>
                <td className="p-3 text-center">
                  {(() => {
                    const b = vocalBadge(track.vocal_gender);
                    return (
                      <span
                        className={clsx(
                          "px-1.5 py-0.5 rounded text-xs border font-bold",
                          b.cls
                        )}
                        title={track.vocal_gender ?? "none"}
                      >
                        {b.label}
                      </span>
                    );
                  })()}
                </td>
                <td className="p-3 text-xs">{track.genre_ai ?? "-"}</td>
                <td className="p-3 text-xs text-neon-green">
                  {track.mood_label ? t(`mood.${track.mood_label}`) : "-"}
                </td>
                <td className="p-3">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      rate(track.id, (track.rating ?? 0) >= 1 ? 0 : 1);
                    }}
                    className={clsx(
                      "p-1 rounded transition",
                      (track.rating ?? 0) >= 1
                        ? "text-neon-pink"
                        : "text-neutral-600 hover:text-neon-pink"
                    )}
                  >
                    <Heart
                      size={14}
                      fill={(track.rating ?? 0) >= 1 ? "currentColor" : "none"}
                    />
                  </button>
                </td>
              </tr>
            );
          })}
          {tracks.length === 0 && (
            <tr>
              <td colSpan={9} className="p-12 text-center text-neutral-500">
                {t("table.empty")}
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
