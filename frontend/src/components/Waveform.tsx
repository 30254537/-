import { useMemo } from "react";
import type { Track } from "../api";

/**
 * Multi-band waveform render (low/mid/high).
 * Uses the track's stored waveform_bands if analyzed, otherwise a placeholder.
 * Professional DJ tools render RMS + peaks per band — we mirror that.
 */
export function Waveform({
  track,
  height = 80,
  progress = 0,
}: {
  track: Track | null;
  height?: number;
  progress?: number; // 0..1
}) {
  const bands = useMemo(() => {
    if (!track || !(track as any).waveform_bands) {
      // No data yet — draw a quiet placeholder
      return Array.from({ length: 200 }, () => [0.1, 0.1, 0.1]);
    }
    try {
      const raw = (track as any).waveform_bands;
      const parsed = typeof raw === "string" ? JSON.parse(raw) : raw;
      return parsed as number[][];
    } catch {
      return [];
    }
  }, [track]);

  const peak = track?.peak_start ?? null;
  const duration = track?.duration ?? 0;
  const peakX = peak && duration ? (peak / duration) * 100 : null;

  return (
    <div
      className="relative w-full rounded-lg overflow-hidden glass border border-neon-blue/20"
      style={{ height }}
    >
      <div className="absolute inset-0 grid-bg opacity-30" />

      <svg
        width="100%"
        height="100%"
        viewBox={`0 0 ${Math.max(bands.length, 1)} 100`}
        preserveAspectRatio="none"
        className="relative"
      >
        {/* High band (top, brightest) */}
        {bands.map((b, i) => {
          const h = Math.max(1, (b[2] ?? 0) * 50);
          return (
            <rect
              key={`h${i}`}
              x={i}
              y={50 - h}
              width={1}
              height={h}
              fill="#00e5ff"
              opacity={0.8}
            />
          );
        })}
        {/* Mid band */}
        {bands.map((b, i) => {
          const h = Math.max(1, (b[1] ?? 0) * 50);
          return (
            <rect
              key={`m${i}`}
              x={i}
              y={50 - h}
              width={1}
              height={h * 0.6}
              fill="#9d00ff"
              opacity={0.9}
            />
          );
        })}
        {/* Low band (bass — most prominent) */}
        {bands.map((b, i) => {
          const h = Math.max(1, (b[0] ?? 0) * 50);
          return (
            <rect
              key={`l${i}`}
              x={i}
              y={50 - h * 0.5}
              width={1}
              height={h}
              fill="#ff2ea6"
              opacity={1}
            />
          );
        })}
        {/* Mirror below */}
        {bands.map((b, i) => {
          const h = Math.max(1, (b[0] ?? 0) * 40);
          return (
            <rect
              key={`lb${i}`}
              x={i}
              y={50}
              width={1}
              height={h}
              fill="#ff2ea6"
              opacity={0.7}
            />
          );
        })}
      </svg>

      {/* Progress marker */}
      <div
        className="absolute top-0 bottom-0 w-0.5 bg-neon-green shadow-[0_0_10px_#00ff9d] pointer-events-none"
        style={{ left: `${progress * 100}%` }}
      />

      {/* Hook/drop marker */}
      {peakX !== null && (
        <div
          className="absolute top-0 bottom-0 border-l-2 border-neon-yellow border-dashed pointer-events-none"
          style={{ left: `${peakX}%` }}
        >
          <div className="absolute -top-1 -left-3 text-[9px] text-neon-yellow font-mono bg-bg-1/80 px-1 rounded">
            DROP
          </div>
        </div>
      )}
    </div>
  );
}
