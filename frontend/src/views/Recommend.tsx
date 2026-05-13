import { useEffect, useState } from "react";
import { Sparkles, Brain } from "lucide-react";
import { TrackList } from "../components/TrackList";
import { api, type Track } from "../api";
import { useApp } from "../store";

export function Recommend() {
  const { t } = useApp();
  const [tracks, setTracks] = useState<Track[]>([]);
  const [loading, setLoading] = useState(false);
  const [training, setTraining] = useState(false);
  const [trainResult, setTrainResult] = useState<any>(null);

  const load = async () => {
    setLoading(true);
    try {
      const { tracks } = await api.recommend(40);
      setTracks(tracks);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const train = async () => {
    setTraining(true);
    try {
      const r = await api.train();
      setTrainResult(r);
      await load();
    } finally {
      setTraining(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-4 grid-bg">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-display text-3xl font-bold tracking-wider">
            <span className="text-neon-pink neon-text">AI</span>{" "}
            <span className="text-neon-blue neon-text">{t("recommend.title").replace("AI ", "")}</span>
          </h2>
          <p className="text-neutral-400 font-mono text-sm mt-1">{t("recommend.subtitle")}</p>
        </div>
        <button
          onClick={train}
          disabled={training}
          className="px-4 py-2 rounded-lg bg-gradient-to-r from-neon-purple to-neon-blue font-mono text-sm flex items-center gap-2 hover:shadow-[0_0_20px_rgba(0,229,255,0.5)] transition disabled:opacity-40"
        >
          <Brain size={16} className={training ? "animate-pulse" : ""} />
          {training ? t("recommend.training") : t("recommend.retrain")}
        </button>
      </div>

      {trainResult && (
        <div className="glass rounded-xl p-4 text-sm font-mono">
          {trainResult.trained ? (
            <>
              <span className="text-neon-green">✓ Trained</span>
              <span className="text-neutral-400 ml-4">Mode: {trainResult.mode}</span>
              <span className="text-neon-pink ml-4">♥ {trainResult.liked}</span>
              <span className="text-red-400 ml-4">✗ {trainResult.disliked}</span>
              {trainResult.score && (
                <span className="text-neon-blue ml-4">Acc: {(trainResult.score * 100).toFixed(1)}%</span>
              )}
            </>
          ) : (
            <span className="text-yellow-400">{trainResult.reason}</span>
          )}
        </div>
      )}

      {loading ? (
        <div className="glass rounded-xl p-12 text-center text-neutral-500 font-mono">
          <Sparkles className="mx-auto mb-3 animate-pulse text-neon-pink" size={40} />
          {t("common.thinking")}
        </div>
      ) : tracks.length === 0 ? (
        <div className="glass rounded-xl p-12 text-center text-neutral-500 font-mono">
          <Sparkles className="mx-auto mb-3 text-neon-purple" size={40} />
          <p>{t("recommend.empty")}</p>
          <p className="text-xs mt-2">{t("recommend.empty_sub")}</p>
        </div>
      ) : (
        <TrackList tracks={tracks} />
      )}
    </div>
  );
}
