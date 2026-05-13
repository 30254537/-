import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
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
import { Scene3DPro } from "../components/Scene3DPro";
import { CamelotMini } from "../components/CamelotMini";

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

type ModuleId = typeof MODULES[number]["id"];

export function Pro() {
  const { t } = useApp();
  const [active, setActive] = useState<ModuleId>("trackid");

  const ActivePanel = MODULES.find((m) => m.id === active)!.panel;
  const activeModule = MODULES.find((m) => m.id === active)!;

  return (
    <div className="relative flex-1 overflow-hidden flex flex-col">
      {/* Animated 3D background — module-aware */}
      <div className="absolute inset-0 z-0 opacity-40">
        <AnimatePresence mode="wait">
          <motion.div
            key={active}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.6 }}
            className="absolute inset-0"
          >
            <Scene3DPro module={active} />
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Scanline overlay */}
      <div className="absolute inset-0 pointer-events-none grid-bg opacity-50 z-0" />

      {/* Header */}
      <motion.div
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.4 }}
        className="relative z-10 px-6 pt-6 pb-3 border-b border-neon-purple/20 backdrop-blur-sm bg-bg-0/40 flex items-center justify-between"
      >
        <div>
          <h2 className="font-display text-3xl font-bold tracking-wider">
            <span className="text-neon-pink neon-text">{t("pro.title")}</span>{" "}
            <span className="text-neon-blue neon-text">{t("pro.title2")}</span>
          </h2>
          <p className="text-neutral-400 font-mono text-xs mt-1">{t("pro.subtitle")}</p>
        </div>
        <CamelotMini size={84} />
      </motion.div>

      <div className="relative z-10 flex-1 flex overflow-hidden">
        {/* Sidebar with 8 module buttons — staggered entry */}
        <motion.div
          initial="hidden"
          animate="visible"
          variants={{
            hidden: { opacity: 0 },
            visible: {
              opacity: 1,
              transition: { staggerChildren: 0.05 },
            },
          }}
          className="w-72 shrink-0 border-r border-neon-purple/20 overflow-y-auto p-3 space-y-2 backdrop-blur-md bg-bg-0/50"
        >
          {MODULES.map((m) => {
            const isActive = active === m.id;
            return (
              <motion.button
                key={m.id}
                variants={{
                  hidden: { opacity: 0, x: -20 },
                  visible: { opacity: 1, x: 0 },
                }}
                whileHover={{ scale: 1.02, x: 4 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setActive(m.id)}
                className={clsx(
                  "w-full text-left p-3 rounded-lg transition-colors border",
                  isActive
                    ? `bg-gradient-to-r ${m.color} bg-opacity-10 border-current shadow-[0_0_18px_rgba(255,46,166,0.25)]`
                    : "border-white/10 hover:border-neon-purple/40 bg-bg-1/50"
                )}
              >
                <div className="flex items-start gap-3">
                  <motion.span
                    animate={isActive ? { scale: [1, 1.2, 1], rotate: [0, -8, 8, 0] } : {}}
                    transition={{ duration: 0.6 }}
                    className="text-2xl leading-none inline-block"
                  >
                    {m.icon}
                  </motion.span>
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
              </motion.button>
            );
          })}
        </motion.div>

        {/* Active panel — slide+fade transition */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-3xl mx-auto">
            <AnimatePresence mode="wait">
              <motion.div
                key={active}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -16 }}
                transition={{ duration: 0.3 }}
              >
                <div className="mb-4 flex items-center gap-3">
                  <motion.span
                    initial={{ scale: 0, rotate: -180 }}
                    animate={{ scale: 1, rotate: 0 }}
                    transition={{ type: "spring", stiffness: 240, damping: 14 }}
                    className="text-3xl inline-block"
                  >
                    {activeModule.icon}
                  </motion.span>
                  <h3 className="font-display text-2xl font-bold tracking-wider text-white">
                    {t(`pro.${active}.name`)}
                  </h3>
                </div>
                <ActivePanel />
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  );
}
