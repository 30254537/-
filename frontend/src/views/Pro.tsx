import { useState } from "react";
import { useApp } from "../store";
import clsx from "clsx";
import { PanelTrackId } from "../components/pro/PanelTrackId";
import { PanelLiveMix } from "../components/pro/PanelLiveMix";
import { PanelPhraseGrid } from "../components/pro/PanelPhraseGrid";
import { PanelStems } from "../components/pro/PanelStems";
import { PanelGigExport } from "../components/pro/PanelGigExport";
import { PanelTrends } from "../components/pro/PanelTrends";
import { PanelQuality } from "../components/pro/PanelQuality";
import { PanelHotCues } from "../components/pro/PanelHotCues";

const MODULES = [
  { id: "trackid",     icon: "🎯", color: "from-neon-green to-neon-blue",   panel: PanelTrackId },
  { id: "livemix",     icon: "🎚️", color: "from-neon-pink to-neon-purple",  panel: PanelLiveMix },
  { id: "phrasegrid",  icon: "📐", color: "from-neon-blue to-neon-purple",  panel: PanelPhraseGrid },
  { id: "hotcues",     icon: "🔥", color: "from-neon-pink to-neon-yellow",  panel: PanelHotCues },
  { id: "quality",     icon: "🎵", color: "from-neon-yellow to-neon-pink",  panel: PanelQuality },
  { id: "trends",      icon: "📡", color: "from-neon-blue to-neon-green",   panel: PanelTrends },
  { id: "stems",       icon: "💎", color: "from-neon-purple to-neon-blue",  panel: PanelStems },
  { id: "gig",         icon: "📦", color: "from-neon-yellow to-neon-pink",  panel: PanelGigExport },
] as const;

export function Pro() {
  const { t } = useApp();
  const [active, setActive] = useState<typeof MODULES[number]["id"]>("trackid");

  const ActivePanel = MODULES.find((m) => m.id === active)!.panel;

  return (
    <div className="flex-1 overflow-hidden flex flex-col grid-bg">
      <div className="px-6 pt-6 pb-3 border-b border-neon-purple/20">
        <h2 className="font-display text-3xl font-bold tracking-wider">
          <span className="text-neon-pink neon-text">{t("pro.title")}</span>{" "}
          <span className="text-neon-blue neon-text">{t("pro.title2")}</span>
        </h2>
        <p className="text-neutral-400 font-mono text-xs mt-1">{t("pro.subtitle")}</p>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar with 8 module buttons */}
        <div className="w-72 shrink-0 border-r border-neon-purple/20 overflow-y-auto p-3 space-y-2">
          {MODULES.map((m) => {
            const isActive = active === m.id;
            return (
              <button
                key={m.id}
                onClick={() => setActive(m.id)}
                className={clsx(
                  "w-full text-left p-3 rounded-lg transition-all border",
                  isActive
                    ? `bg-gradient-to-r ${m.color} bg-opacity-10 border-current shadow-[0_0_18px_rgba(255,46,166,0.25)]`
                    : "border-white/10 hover:border-neon-purple/40 bg-bg-1/50"
                )}
              >
                <div className="flex items-start gap-3">
                  <span className="text-2xl leading-none">{m.icon}</span>
                  <div className="flex-1 min-w-0">
                    <div
                      className={clsx(
                        "font-display font-bold tracking-wider text-sm",
                        isActive ? "text-white" : "text-neutral-300"
                      )}
                    >
                      {t(`pro.${m.id}.name`)}
                    </div>
                    <div className="text-[10px] font-mono text-neutral-400 mt-1 leading-snug">
                      {t(`pro.${m.id}.desc`)}
                    </div>
                  </div>
                </div>
              </button>
            );
          })}
        </div>

        {/* Active panel */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-3xl mx-auto">
            <div className="mb-4 flex items-center gap-3">
              <span className="text-3xl">{MODULES.find((m) => m.id === active)!.icon}</span>
              <h3 className="font-display text-2xl font-bold tracking-wider text-white">
                {t(`pro.${active}.name`)}
              </h3>
            </div>
            <ActivePanel />
          </div>
        </div>
      </div>
    </div>
  );
}
