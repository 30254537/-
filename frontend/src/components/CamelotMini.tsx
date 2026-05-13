import { useApp } from "../store";

/**
 * Compact 12-segment Camelot wheel widget.
 * Highlights the active key for whichever track is currently playing
 * or last selected.
 */
export function CamelotMini({ size = 100 }: { size?: number }) {
  const { currentTrack } = useApp();
  const activeKey = currentTrack?.camelot;

  const cx = size / 2;
  const cy = size / 2;
  const rOuter = size / 2 - 2;
  const rInner = rOuter * 0.55;

  // Build 12 wedge pairs (1A..12A inner, 1B..12B outer)
  const wedges: Array<{ key: string; path: string; cx: number; cy: number; isActive: boolean }> = [];
  for (let i = 0; i < 12; i++) {
    const startAngle = (i / 12) * Math.PI * 2 - Math.PI / 2;
    const endAngle = ((i + 1) / 12) * Math.PI * 2 - Math.PI / 2;

    // Outer ring (B keys)
    const xo1 = cx + Math.cos(startAngle) * rOuter;
    const yo1 = cy + Math.sin(startAngle) * rOuter;
    const xo2 = cx + Math.cos(endAngle) * rOuter;
    const yo2 = cy + Math.sin(endAngle) * rOuter;
    const xi1 = cx + Math.cos(startAngle) * rInner;
    const yi1 = cy + Math.sin(startAngle) * rInner;
    const xi2 = cx + Math.cos(endAngle) * rInner;
    const yi2 = cy + Math.sin(endAngle) * rInner;
    const keyB = `${i + 1}B`;
    const keyA = `${i + 1}A`;
    const labelAngle = (startAngle + endAngle) / 2;

    wedges.push({
      key: keyB,
      path: `M ${xo1} ${yo1} A ${rOuter} ${rOuter} 0 0 1 ${xo2} ${yo2} L ${xi2} ${yi2} A ${rInner} ${rInner} 0 0 0 ${xi1} ${yi1} Z`,
      cx: cx + Math.cos(labelAngle) * (rOuter + rInner) / 2,
      cy: cy + Math.sin(labelAngle) * (rOuter + rInner) / 2,
      isActive: activeKey === keyB,
    });

    // Inner ring (A keys)
    const rCenter = rInner * 0.55;
    const xc1 = cx + Math.cos(startAngle) * rInner;
    const yc1 = cy + Math.sin(startAngle) * rInner;
    const xc2 = cx + Math.cos(endAngle) * rInner;
    const yc2 = cy + Math.sin(endAngle) * rInner;
    const xcc1 = cx + Math.cos(startAngle) * rCenter;
    const ycc1 = cy + Math.sin(startAngle) * rCenter;
    const xcc2 = cx + Math.cos(endAngle) * rCenter;
    const ycc2 = cy + Math.sin(endAngle) * rCenter;
    wedges.push({
      key: keyA,
      path: `M ${xc1} ${yc1} A ${rInner} ${rInner} 0 0 1 ${xc2} ${yc2} L ${xcc2} ${ycc2} A ${rCenter} ${rCenter} 0 0 0 ${xcc1} ${ycc1} Z`,
      cx: cx + Math.cos(labelAngle) * (rInner + rCenter) / 2,
      cy: cy + Math.sin(labelAngle) * (rInner + rCenter) / 2,
      isActive: activeKey === keyA,
    });
  }

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="drop-shadow-[0_0_8px_rgba(0,229,255,0.4)]">
      {wedges.map((w) => (
        <g key={w.key}>
          <path
            d={w.path}
            fill={w.isActive ? "#ff2ea6" : "#0b0b15"}
            stroke={w.isActive ? "#ffffff" : "#9d00ff"}
            strokeWidth={w.isActive ? 1.5 : 0.4}
            opacity={w.isActive ? 1 : 0.85}
            style={{
              filter: w.isActive ? "drop-shadow(0 0 6px #ff2ea6)" : undefined,
              transition: "all 0.3s ease",
            }}
          />
          <text
            x={w.cx}
            y={w.cy}
            textAnchor="middle"
            dominantBaseline="central"
            fontSize={size > 90 ? 7 : 5}
            fill={w.isActive ? "#ffffff" : "#888"}
            fontFamily="JetBrains Mono, monospace"
            fontWeight={w.isActive ? "bold" : "normal"}
            style={{ pointerEvents: "none" }}
          >
            {w.key}
          </text>
        </g>
      ))}
      {/* Center label */}
      <circle cx={cx} cy={cy} r={rInner * 0.55} fill="#05050a" stroke="#9d00ff" strokeWidth={0.5} />
      <text
        x={cx}
        y={cy - 4}
        textAnchor="middle"
        dominantBaseline="central"
        fontSize={6}
        fill="#9d00ff"
        fontFamily="Orbitron, sans-serif"
      >
        KEY
      </text>
      <text
        x={cx}
        y={cy + 6}
        textAnchor="middle"
        dominantBaseline="central"
        fontSize={9}
        fill={activeKey ? "#ff2ea6" : "#444"}
        fontFamily="Orbitron, sans-serif"
        fontWeight="bold"
      >
        {activeKey ?? "—"}
      </text>
    </svg>
  );
}
