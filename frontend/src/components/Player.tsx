import { useEffect, useRef, useState } from "react";
import { Heart, HeartOff, Play, Pause, SkipBack, SkipForward } from "lucide-react";
import { useApp } from "../store";
import { api } from "../api";
import { Waveform } from "./Waveform";
import clsx from "clsx";

function fmtTime(sec: number) {
  if (!isFinite(sec)) return "0:00";
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function Player() {
  const { currentTrack, isPlaying, setIsPlaying, rate, t: tr } = useApp();
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [progress, setProgress] = useState(0);
  const [time, setTime] = useState(0);

  useEffect(() => {
    if (!audioRef.current) return;
    if (currentTrack) {
      audioRef.current.src = api.audioUrl(currentTrack.id);
      audioRef.current.load();
      if (isPlaying) audioRef.current.play().catch(() => setIsPlaying(false));
    }
  }, [currentTrack?.id]);

  useEffect(() => {
    if (!audioRef.current) return;
    if (isPlaying) audioRef.current.play().catch(() => setIsPlaying(false));
    else audioRef.current.pause();
  }, [isPlaying]);

  const onTime = () => {
    const a = audioRef.current;
    if (!a) return;
    setTime(a.currentTime);
    setProgress(a.duration ? a.currentTime / a.duration : 0);
  };

  const jumpToDrop = () => {
    if (audioRef.current && currentTrack?.peak_start) {
      audioRef.current.currentTime = currentTrack.peak_start;
    }
  };

  if (!currentTrack) {
    return (
      <div className="glass border-t border-neon-purple/20 h-24 flex items-center justify-center text-neutral-500 font-mono text-sm">
        {tr("common.no_track")}
      </div>
    );
  }

  const track = currentTrack;
  const rating = track.rating ?? 0;

  return (
    <div className="glass border-t border-neon-purple/20 px-6 py-3 flex items-center gap-6">
      <audio ref={audioRef} onTimeUpdate={onTime} onEnded={() => setIsPlaying(false)} />

      <div className="w-64 min-w-0">
        <div className="font-mono text-sm text-white truncate">{track.title ?? track.filename}</div>
        <div className="font-mono text-xs text-neon-purple truncate">
          {track.artist ?? tr("common.unknown")}
        </div>
        <div className="flex gap-2 mt-1 text-[10px] font-mono">
          {track.bpm && <span className="text-neon-pink">{track.bpm} BPM</span>}
          {track.camelot && <span className="text-neon-blue">{track.camelot}</span>}
          {track.energy !== undefined && <span className="text-neon-yellow">E{track.energy}</span>}
          {track.genre_ai && <span className="text-neon-green">{track.genre_ai}</span>}
        </div>
      </div>

      <div className="flex-1 flex flex-col gap-1 min-w-0">
        <div className="flex items-center justify-center gap-3">
          <button
            onClick={() => audioRef.current && (audioRef.current.currentTime = 0)}
            className="text-neutral-400 hover:text-white"
          >
            <SkipBack size={18} />
          </button>
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className="w-10 h-10 rounded-full bg-gradient-to-br from-neon-pink to-neon-purple flex items-center justify-center text-white shadow-[0_0_20px_rgba(255,46,166,0.5)] hover:scale-105 transition"
          >
            {isPlaying ? <Pause size={18} /> : <Play size={18} className="ml-0.5" />}
          </button>
          <button onClick={jumpToDrop} className="text-neon-yellow hover:text-white">
            <SkipForward size={18} />
          </button>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="text-neutral-400 w-10 text-right">{fmtTime(time)}</span>
          <div
            className="flex-1 cursor-pointer"
            onClick={(e) => {
              const rect = (e.target as HTMLElement).getBoundingClientRect();
              const x = (e.clientX - rect.left) / rect.width;
              if (audioRef.current && audioRef.current.duration) {
                audioRef.current.currentTime = x * audioRef.current.duration;
              }
            }}
          >
            <Waveform track={track} height={40} progress={progress} />
          </div>
          <span className="text-neutral-400 w-10">{fmtTime(track.duration ?? 0)}</span>
        </div>
      </div>

      <div className="flex items-center gap-1">
        <button
          onClick={() => rate(track.id, rating === -1 ? 0 : -1)}
          className={clsx(
            "p-2 rounded-lg transition",
            rating === -1
              ? "bg-red-500/20 text-red-400 border border-red-500/40"
              : "text-neutral-500 hover:text-red-400"
          )}
        >
          <HeartOff size={18} />
        </button>
        <button
          onClick={() => rate(track.id, rating >= 1 ? 0 : 1)}
          className={clsx(
            "p-2 rounded-lg transition",
            rating >= 1
              ? "bg-neon-pink/20 text-neon-pink border border-neon-pink/40 shadow-[0_0_12px_rgba(255,46,166,0.5)]"
              : "text-neutral-500 hover:text-neon-pink"
          )}
        >
          <Heart size={18} fill={rating >= 1 ? "currentColor" : "none"} />
        </button>
      </div>
    </div>
  );
}
