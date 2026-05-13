import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import clsx from "clsx";
import { Loader2, Upload, Sparkles, Folder, Image, Music, Compass, Activity,
         History, Users, Film, Gauge, Layers, Disc, MapPin, Cloud, Bell, Mic } from "lucide-react";
import { useApp } from "../store";
import { api, type Track } from "../api";
import { PanelTrackPicker } from "../components/pro/PanelTrackPicker";
import { TrackList } from "../components/TrackList";

const MODULES = [
  { id: "autotag",    icon: Folder,    color: "from-neon-blue to-neon-purple" },
  { id: "cover",      icon: Image,     color: "from-neon-pink to-neon-yellow" },
  { id: "vibe",       icon: Sparkles,  color: "from-neon-purple to-neon-pink" },
  { id: "vocal",      icon: Mic,       color: "from-neon-pink to-neon-blue" },
  { id: "sonic",      icon: Compass,   color: "from-neon-blue to-neon-green" },
  { id: "tracklist",  icon: Music,     color: "from-neon-green to-neon-blue" },
  { id: "history",    icon: History,   color: "from-neon-purple to-neon-blue" },
  { id: "mimic",      icon: Activity,  color: "from-neon-pink to-neon-purple" },
  { id: "b2b",        icon: Users,     color: "from-neon-yellow to-neon-pink" },
  { id: "highlight",  icon: Film,      color: "from-neon-pink to-neon-yellow" },
  { id: "bpmramp",    icon: Gauge,     color: "from-neon-blue to-neon-pink" },
  { id: "samples",    icon: Layers,    color: "from-neon-green to-neon-blue" },
  { id: "master",     icon: Disc,      color: "from-neon-yellow to-neon-pink" },
  { id: "venue",      icon: MapPin,    color: "from-neon-pink to-neon-blue" },
  { id: "style",      icon: Activity,  color: "from-neon-blue to-neon-purple" },
  { id: "cloud",      icon: Cloud,     color: "from-neon-blue to-neon-green" },
  { id: "releases",   icon: Bell,      color: "from-neon-pink to-neon-yellow" },
] as const;
type ModuleId = typeof MODULES[number]["id"];

export function ProPlus() {
  const { t } = useApp();
  const [active, setActive] = useState<ModuleId>("autotag");

  return (
    <div className="flex-1 overflow-hidden flex flex-col grid-bg bg-bg-0">
      <div className="px-6 pt-6 pb-3 border-b border-neon-purple/20 backdrop-blur-sm bg-bg-0/60">
        <h2 className="font-display text-3xl font-bold tracking-wider">
          <span className="text-neon-yellow neon-text">PRO</span>{" "}
          <span className="text-neon-pink neon-text">PLUS</span>
        </h2>
        <p className="text-neutral-400 font-mono text-xs mt-1">{t("proplus.subtitle")}</p>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* 16-module grid sidebar */}
        <div className="w-72 shrink-0 border-r border-neon-purple/20 overflow-y-auto p-3 space-y-1.5">
          {MODULES.map((m) => {
            const Icon = m.icon;
            const isActive = active === m.id;
            return (
              <motion.button
                key={m.id}
                whileHover={{ scale: 1.01, x: 3 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setActive(m.id)}
                className={clsx(
                  "w-full text-left p-2.5 rounded-lg border transition-colors",
                  isActive
                    ? `bg-gradient-to-r ${m.color} bg-opacity-10 border-current shadow-[0_0_15px_rgba(255,46,166,0.2)]`
                    : "border-white/10 hover:border-neon-purple/40 bg-bg-1/50"
                )}
              >
                <div className="flex items-center gap-2.5">
                  <Icon size={16} className={isActive ? "text-white" : "text-neon-purple"} />
                  <div className="flex-1 min-w-0">
                    <div className={clsx(
                      "font-display font-bold tracking-wider text-xs",
                      isActive ? "text-white" : "text-neutral-300"
                    )}>
                      {t(`ppx.${m.id === "cover" ? "cover" : m.id === "vibe" ? "vibe"
                          : m.id === "vocal" ? "vocal"
                          : m.id === "sonic" ? "sonic" : m.id === "tracklist" ? "tracklist"
                          : m.id === "history" ? "history" : m.id === "mimic" ? "mimic"
                          : m.id === "b2b" ? "b2b" : m.id === "highlight" ? "highlight"
                          : m.id === "bpmramp" ? "bpmramp" : m.id === "samples" ? "samples"
                          : m.id === "master" ? "master" : m.id === "venue" ? "venue"
                          : m.id === "style" ? "style" : m.id === "cloud" ? "cloud"
                          : m.id === "releases" ? "releases" : "autotag"}.name`)}
                    </div>
                  </div>
                </div>
              </motion.button>
            );
          })}
        </div>

        {/* Active panel area */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-3xl mx-auto">
            <AnimatePresence mode="wait">
              <motion.div
                key={active}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -16 }}
                transition={{ duration: 0.25 }}
              >
                {active === "autotag"   && <AutoTagPanel />}
                {active === "cover"     && <CoverPanel />}
                {active === "vibe"      && <VibePanel />}
                {active === "vocal"     && <VocalPanel />}
                {active === "sonic"     && <SonicPanel />}
                {active === "tracklist" && <TracklistPanel />}
                {active === "history"   && <HistoryPanel />}
                {active === "mimic"     && <MimicPanel />}
                {active === "b2b"       && <B2BPanel />}
                {active === "highlight" && <HighlightPanel />}
                {active === "bpmramp"   && <BPMRampPanel />}
                {active === "samples"   && <SamplesPanel />}
                {active === "master"    && <MasterPanel />}
                {active === "venue"     && <VenuePanel />}
                {active === "style"     && <StylePanel />}
                {active === "cloud"     && <CloudPanel />}
                {active === "releases"  && <ReleasesPanel />}
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Reusable shells ─────────────────────────────────────────────────────────

function PanelHeader({ icon: Icon, titleKey }: { icon: any; titleKey: string }) {
  const { t } = useApp();
  return (
    <div className="mb-4 flex items-center gap-3">
      <Icon size={28} className="text-neon-pink" />
      <div>
        <h3 className="font-display text-2xl font-bold tracking-wider text-white">
          {t(titleKey + ".name")}
        </h3>
        <p className="text-xs text-neutral-400 font-mono">{t(titleKey + ".desc")}</p>
      </div>
    </div>
  );
}

function Btn({ onClick, disabled, children, primary = true, small = false }: any) {
  return (
    <motion.button
      whileHover={!disabled ? { scale: 1.03 } : {}}
      whileTap={!disabled ? { scale: 0.97 } : {}}
      onClick={onClick}
      disabled={disabled}
      className={clsx(
        "rounded-lg font-display font-bold tracking-wider flex items-center gap-2 disabled:opacity-40 transition",
        small ? "px-3 py-1.5 text-xs" : "px-4 py-2 text-sm",
        primary
          ? "bg-gradient-to-r from-neon-pink to-neon-purple text-white"
          : "bg-bg-1 text-neutral-300 border border-neon-purple/30 hover:text-white"
      )}
    >
      {children}
    </motion.button>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1">
      <label className="text-xs font-mono text-neon-purple uppercase tracking-wider">{label}</label>
      {children}
    </div>
  );
}

function TextInput(p: any) {
  return <input {...p} className="w-full bg-bg-1 border border-neon-purple/30 rounded px-3 py-2 font-mono text-sm" />;
}

function ResultBox({ data }: { data: any }) {
  if (!data) return null;
  return (
    <pre className="glass rounded-lg p-3 font-mono text-[11px] text-neutral-300 overflow-x-auto max-h-96">
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}

// ── Panel implementations ─────────────────────────────────────────────────

function AutoTagPanel() {
  const { t } = useApp();
  const [outRoot, setOutRoot] = useState("");
  const [mode, setMode] = useState<"copy" | "move">("copy");
  const [plan, setPlan] = useState<any[]>([]);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const doPlan = async () => {
    setLoading(true);
    try {
      const r = await api.pp.autotagPlan(outRoot);
      setPlan(r.plan);
    } finally { setLoading(false); }
  };
  const doExec = async () => {
    setLoading(true);
    try {
      const r = await api.pp.autotagExecute(outRoot, mode);
      setResult(r);
    } finally { setLoading(false); }
  };

  return (
    <>
      <PanelHeader icon={Folder} titleKey="ppx.autotag" />
      <div className="space-y-3">
        <Field label={t("ppx.path")}>
          <TextInput value={outRoot} onChange={(e: any) => setOutRoot(e.target.value)}
                     placeholder="/Music/Organized" />
        </Field>
        <div className="flex items-center gap-2">
          <select value={mode} onChange={(e) => setMode(e.target.value as any)}
                  className="bg-bg-1 border border-neon-purple/30 rounded px-3 py-2 font-mono text-sm">
            <option value="copy">{t("ppx.copy")}</option>
            <option value="move">{t("ppx.move")}</option>
          </select>
          <Btn onClick={doPlan} disabled={!outRoot || loading} primary={false} small>
            {loading ? <Loader2 size={12} className="animate-spin" /> : null}
            {t("ppx.preview")}
          </Btn>
          <Btn onClick={doExec} disabled={!outRoot || loading} small>
            {loading ? <Loader2 size={12} className="animate-spin" /> : null}
            {t("ppx.execute")}
          </Btn>
        </div>
        {plan.length > 0 && !result && (
          <div className="glass rounded-lg p-3 max-h-80 overflow-y-auto font-mono text-[11px] space-y-1">
            <div className="text-neon-blue mb-2">{plan.length} planned moves</div>
            {plan.slice(0, 60).map((p, i) => (
              <div key={i} className="flex items-center gap-2 text-neutral-400">
                <span className={p.action === "skip" ? "text-yellow-500" : "text-neon-green"}>
                  {p.action}
                </span>
                <span className="text-neon-pink">{p.genre}</span>
                <span>·</span>
                <span className="text-neon-blue">{p.bucket}</span>
                <span className="truncate flex-1">{p.dst_path}</span>
              </div>
            ))}
            {plan.length > 60 && <div className="text-neutral-600">... and {plan.length - 60} more</div>}
          </div>
        )}
        <ResultBox data={result} />
      </div>
    </>
  );
}

function CoverPanel() {
  const { t } = useApp();
  const [online, setOnline] = useState(true);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const run = async () => {
    setLoading(true);
    try { setResult(await api.pp.coverRun(online)); }
    finally { setLoading(false); }
  };
  return (
    <>
      <PanelHeader icon={Image} titleKey="ppx.cover" />
      <div className="space-y-3">
        <label className="flex items-center gap-2 font-mono text-xs">
          <input type="checkbox" checked={online} onChange={(e) => setOnline(e.target.checked)}
                 className="accent-neon-pink" />
          Use online lookup (iTunes / MusicBrainz)
        </label>
        <Btn onClick={run} disabled={loading}>
          {loading ? <Loader2 size={14} className="animate-spin" /> : <Image size={14} />}
          {t("ppx.run")}
        </Btn>
        <ResultBox data={result} />
      </div>
    </>
  );
}

function VibePanel() {
  const { t } = useApp();
  const [filters, setFilters] = useState({ mood: "", texture: "", time: "", element: "" });
  const [tracks, setTracks] = useState<Track[]>([]);
  const [loading, setLoading] = useState(false);

  const tagAll = async () => {
    setLoading(true);
    try { await api.pp.vibeTag(); }
    finally { setLoading(false); }
  };
  const search = async () => {
    setLoading(true);
    try {
      const r = await api.pp.vibeFind(filters);
      setTracks(r.tracks);
    } finally { setLoading(false); }
  };

  return (
    <>
      <PanelHeader icon={Sparkles} titleKey="ppx.vibe" />
      <div className="space-y-3">
        <Btn onClick={tagAll} disabled={loading} primary={false} small>
          {loading ? <Loader2 size={12} className="animate-spin" /> : "🔁"} Re-tag library
        </Btn>
        <div className="grid grid-cols-4 gap-2">
          {[
            { k: "mood",    opts: ["dark", "euphoric", "melancholic", "uplifting", "neutral"] },
            { k: "texture", opts: ["driving", "groovy", "hypnotic", "ethereal", "funky"] },
            { k: "time",    opts: ["sunset", "late_night", "sunrise", "daytime", "anytime"] },
            { k: "element", opts: ["vocal", "instrumental", "acid", "classic", "modern"] },
          ].map(({ k, opts }) => (
            <select key={k} value={(filters as any)[k]}
                    onChange={(e) => setFilters({ ...filters, [k]: e.target.value })}
                    className="bg-bg-1 border border-neon-purple/30 rounded px-2 py-1 font-mono text-xs">
              <option value="">— {k} —</option>
              {opts.map((o) => (<option key={o} value={o}>{t(`vibe.${o}`)}</option>))}
            </select>
          ))}
        </div>
        <Btn onClick={search} disabled={loading}>
          {loading ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
          Search
        </Btn>
        {tracks.length > 0 && <TrackList tracks={tracks} />}
      </div>
    </>
  );
}

function SonicPanel() {
  const { t } = useApp();
  const [track, setTrack] = useState<Track | null>(null);
  const [tracks, setTracks] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const run = async () => {
    if (!track) return;
    setLoading(true);
    try { setTracks((await api.pp.sonicSimilarity(track.id)).tracks); }
    finally { setLoading(false); }
  };
  return (
    <>
      <PanelHeader icon={Compass} titleKey="ppx.sonic" />
      <div className="space-y-3">
        <PanelTrackPicker value={track} onChange={setTrack} />
        <Btn onClick={run} disabled={!track || loading}>
          {loading ? <Loader2 size={14} className="animate-spin" /> : <Compass size={14} />}
          Find sonic neighbors
        </Btn>
        {tracks.length > 0 && (
          <div className="glass rounded-lg overflow-hidden">
            {tracks.map((t: any, i: number) => (
              <div key={i} className="px-3 py-2 border-b border-white/5 flex items-center gap-3 text-xs font-mono">
                <span className="text-neon-pink w-12">{(t.similarity_score * 100).toFixed(1)}%</span>
                <span className="text-neon-blue w-12">{t.bpm} BPM</span>
                <span className="text-neon-purple w-10">{t.camelot}</span>
                <span className="text-neutral-300 truncate">{t.artist} — {t.title}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}

function TracklistPanel() {
  const { t } = useApp();
  const [path, setPath] = useState("");
  const [loading, setLoading] = useState(false);
  const [tracklist, setTracklist] = useState<any>(null);
  const [text, setText] = useState("");
  const recover = async () => {
    setLoading(true);
    try { setTracklist(await api.pp.tracklistRecover(path)); }
    finally { setLoading(false); }
  };
  const exportText = async () => {
    if (!tracklist) return;
    const r = await api.pp.tracklistFormat(tracklist, "1001tracklists");
    setText(r.text);
  };
  return (
    <>
      <PanelHeader icon={Music} titleKey="ppx.tracklist" />
      <div className="space-y-3">
        <Field label={t("ppx.upload")}>
          <TextInput value={path} onChange={(e: any) => setPath(e.target.value)}
                     placeholder="/path/to/your/set-recording.mp3" />
        </Field>
        <div className="flex gap-2">
          <Btn onClick={recover} disabled={!path || loading}>
            {loading ? <Loader2 size={14} className="animate-spin" /> : <Music size={14} />}
            Recover
          </Btn>
          {tracklist && <Btn onClick={exportText} primary={false}>{t("ppx.export")} 1001tracklists</Btn>}
        </div>
        {tracklist?.entries && (
          <div className="glass rounded-lg p-3 space-y-1 font-mono text-[11px] max-h-96 overflow-y-auto">
            {tracklist.entries.map((e: any, i: number) => {
              const m = Math.floor(e.start_sec / 60), s = Math.floor(e.start_sec % 60);
              return (
                <div key={i} className="flex items-center gap-2">
                  <span className="text-neon-pink w-12">{m}:{String(s).padStart(2, "0")}</span>
                  <span className="text-neon-green w-10">{Math.round(e.confidence * 100)}%</span>
                  <span className="text-neutral-300 truncate">
                    {e.track_id ? `${e.artist} — ${e.title}` : "ID? (low confidence)"}
                  </span>
                </div>
              );
            })}
          </div>
        )}
        {text && <pre className="glass rounded-lg p-3 font-mono text-[11px] text-neutral-300">{text}</pre>}
      </div>
    </>
  );
}

function HistoryPanel() {
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const load = async () => {
    setLoading(true);
    try { setProfile(await api.pp.historyProfile()); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);
  return (
    <>
      <PanelHeader icon={History} titleKey="ppx.history" />
      <div className="space-y-3">
        <Btn onClick={load} disabled={loading} primary={false} small>
          {loading ? <Loader2 size={12} className="animate-spin" /> : "🔄"} Refresh
        </Btn>
        {profile && (
          <div className="grid grid-cols-3 gap-3 font-mono text-xs">
            <div className="glass rounded-lg p-3">
              <div className="text-neon-purple uppercase text-[10px] tracking-wider">Sets played</div>
              <div className="text-2xl text-neon-pink font-display font-black">{profile.sets_played}</div>
            </div>
            <div className="glass rounded-lg p-3">
              <div className="text-neon-purple uppercase text-[10px] tracking-wider">Total plays</div>
              <div className="text-2xl text-neon-blue font-display font-black">{profile.total_plays}</div>
            </div>
            <div className="glass rounded-lg p-3">
              <div className="text-neon-purple uppercase text-[10px] tracking-wider">Reuse rate</div>
              <div className="text-2xl text-neon-yellow font-display font-black">{(profile.reuse_rate * 100).toFixed(0)}%</div>
            </div>
            <div className="col-span-3 glass rounded-lg p-3">
              <div className="text-neon-purple uppercase text-[10px] tracking-wider mb-2">Top tracks</div>
              {(profile.top_tracks || []).slice(0, 10).map((t: any, i: number) => (
                <div key={i} className="flex justify-between text-neutral-300">
                  <span className="truncate">{i + 1}. {t.artist} — {t.title}</span>
                  <span className="text-neon-pink ml-3">{t.count}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </>
  );
}

function MimicPanel() {
  const [refTracks, setRefTracks] = useState("");
  const [fp, setFp] = useState<any>(null);
  const [setlist, setSetlist] = useState<Track[]>([]);
  const [loading, setLoading] = useState(false);
  const buildFP = async () => {
    setLoading(true);
    try {
      // Each line: "artist - title"
      const tracks = refTracks.split("\n").filter(l => l.trim()).map(l => {
        const [artist, ...rest] = l.split(" - ");
        return { artist: artist?.trim(), title: rest.join(" - ").trim() };
      });
      const r = await api.pp.mimicFingerprint(tracks);
      setFp(r);
    } finally { setLoading(false); }
  };
  const generate = async () => {
    if (!fp) return;
    setLoading(true);
    try { setSetlist((await api.pp.mimicGenerate(fp)).tracks); }
    finally { setLoading(false); }
  };
  return (
    <>
      <PanelHeader icon={Activity} titleKey="ppx.mimic" />
      <div className="space-y-3">
        <Field label="Reference tracklist (one per line: 'Artist - Title')">
          <textarea value={refTracks} onChange={(e) => setRefTracks(e.target.value)}
                    rows={6}
                    className="w-full bg-bg-1 border border-neon-purple/30 rounded px-3 py-2 font-mono text-xs"
                    placeholder="Adam Beyer - Your Mind&#10;Charlotte de Witte - Doppler" />
        </Field>
        <div className="flex gap-2">
          <Btn onClick={buildFP} disabled={!refTracks || loading} primary={false} small>Build fingerprint</Btn>
          <Btn onClick={generate} disabled={!fp || loading}>Generate setlist</Btn>
        </div>
        {fp && <ResultBox data={fp} />}
        {setlist.length > 0 && <TrackList tracks={setlist} />}
      </div>
    </>
  );
}

function B2BPanel() {
  const [partnerJson, setPartnerJson] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const run = async () => {
    setLoading(true);
    try {
      const partner = JSON.parse(partnerJson);
      const yourTracks = (await api.listTracks({ limit: 1000 })).tracks;
      const r = await api.pp.b2bCompare(yourTracks.map(t => t.id), partner);
      setResult(r);
    } catch (e: any) { alert(e.message); }
    finally { setLoading(false); }
  };
  return (
    <>
      <PanelHeader icon={Users} titleKey="ppx.b2b" />
      <div className="space-y-3">
        <Field label="Partner library JSON (their MixMind cloud export)">
          <textarea value={partnerJson} onChange={(e) => setPartnerJson(e.target.value)} rows={6}
                    className="w-full bg-bg-1 border border-neon-purple/30 rounded px-3 py-2 font-mono text-xs"
                    placeholder='[{"artist":"...","title":"...","bpm":124,"camelot":"8A","audio_fingerprint":"..."}]' />
        </Field>
        <Btn onClick={run} disabled={!partnerJson || loading}>Compare</Btn>
        {result && (
          <div className="glass rounded-lg p-3 font-mono text-xs space-y-2">
            <div>Your library: <span className="text-neon-blue">{result.your_track_count}</span></div>
            <div>Partner: <span className="text-neon-pink">{result.partner_track_count}</span></div>
            <div>Common: <span className="text-neon-green text-lg">{result.common_count}</span></div>
            <div>Partner-only: <span className="text-neon-yellow">{result.partner_only_count}</span></div>
          </div>
        )}
      </div>
    </>
  );
}

function HighlightPanel() {
  const [path, setPath] = useState("");
  const [out, setOut] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const run = async () => {
    setLoading(true);
    try { setOut(await api.pp.highlightFind(path, 30, 3)); }
    finally { setLoading(false); }
  };
  return (
    <>
      <PanelHeader icon={Film} titleKey="ppx.highlight" />
      <div className="space-y-3">
        <Field label="Set recording path">
          <TextInput value={path} onChange={(e: any) => setPath(e.target.value)} placeholder="/path/to/set.mp3" />
        </Field>
        <Btn onClick={run} disabled={!path || loading}>Find top 3 hype clips</Btn>
        {out?.clips?.map((c: any, i: number) => (
          <div key={i} className="glass rounded-lg p-3 font-mono text-xs flex items-center gap-3">
            <span className="text-neon-pink text-lg font-display font-black">#{i + 1}</span>
            <span className="text-neon-blue">{Math.floor(c.start_sec / 60)}:{String(Math.floor(c.start_sec % 60)).padStart(2, "0")}</span>
            <span className="text-neon-purple">→</span>
            <span className="text-neon-blue">{Math.floor(c.end_sec / 60)}:{String(Math.floor(c.end_sec % 60)).padStart(2, "0")}</span>
            <span className="text-neon-yellow ml-auto">hype {c.hype_score.toFixed(3)}</span>
          </div>
        ))}
      </div>
    </>
  );
}

function BPMRampPanel() {
  const [a, setA] = useState({ bpm: 124, outro: 240, dur: 360 });
  const [b, setB] = useState(128);
  const [result, setResult] = useState<any>(null);
  const run = async () => {
    setResult(await api.pp.bpmRamp(a.bpm, b, a.outro, a.dur));
  };
  return (
    <>
      <PanelHeader icon={Gauge} titleKey="ppx.bpmramp" />
      <div className="space-y-3">
        <div className="grid grid-cols-4 gap-2 font-mono text-xs">
          <Field label="A BPM"><TextInput type="number" value={a.bpm} onChange={(e: any) => setA({...a, bpm: +e.target.value})} /></Field>
          <Field label="A outro start (s)"><TextInput type="number" value={a.outro} onChange={(e: any) => setA({...a, outro: +e.target.value})} /></Field>
          <Field label="A duration (s)"><TextInput type="number" value={a.dur} onChange={(e: any) => setA({...a, dur: +e.target.value})} /></Field>
          <Field label="B BPM"><TextInput type="number" value={b} onChange={(e: any) => setB(+e.target.value)} /></Field>
        </div>
        <Btn onClick={run}>Plan ramp</Btn>
        {result?.schedule && (
          <div className="glass rounded-lg overflow-hidden">
            <div className="px-3 py-2 bg-neon-purple/10 text-xs font-mono text-neon-purple">
              Total pitch: {result.total_pitch_pct}% over {result.n_steps} steps · {result.advice}
            </div>
            {result.schedule.map((s: any, i: number) => (
              <div key={i} className="px-3 py-1.5 border-b border-white/5 flex items-center gap-3 text-xs font-mono">
                <span className="text-neon-pink w-6">#{s.step}</span>
                <span className="text-neon-blue">{s.from_bpm}</span>
                <span>→</span>
                <span className="text-neon-blue">{s.to_bpm}</span>
                <span className="text-neutral-500 ml-3">@ {s.start_sec}s</span>
                <span className="text-neon-yellow ml-auto">+{s.pitch_pct_total}%</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}

function SamplesPanel() {
  const [folder, setFolder] = useState("");
  const [type, setType] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const scan = async () => {
    setLoading(true);
    try { await api.pp.samplesScan(folder); }
    finally { setLoading(false); }
  };
  const find = async () => {
    setLoading(true);
    try {
      const r = await api.pp.samplesFind({ sample_type: type });
      setResults(r.samples);
    } finally { setLoading(false); }
  };
  return (
    <>
      <PanelHeader icon={Layers} titleKey="ppx.samples" />
      <div className="space-y-3">
        <Field label="Sample folder path">
          <TextInput value={folder} onChange={(e: any) => setFolder(e.target.value)} placeholder="/Samples/Vocal Chops" />
        </Field>
        <div className="flex gap-2">
          <Btn onClick={scan} disabled={!folder || loading} primary={false} small>Scan folder</Btn>
          <select value={type} onChange={(e) => setType(e.target.value)}
                  className="bg-bg-1 border border-neon-purple/30 rounded px-2 py-1 font-mono text-xs">
            <option value="">All types</option>
            {["acapella","instrumental","vocal_chop","drum_loop","bass_loop","fx_riser","fx_impact","fx_drop","one_shot_kick","one_shot_snare","one_shot_perc","ambient_pad"].map(o => (
              <option key={o} value={o}>{o}</option>
            ))}
          </select>
          <Btn onClick={find} disabled={loading} small>Find</Btn>
        </div>
        {results.length > 0 && (
          <div className="glass rounded-lg overflow-hidden max-h-96 overflow-y-auto">
            {results.map((s: any) => (
              <div key={s.id} className="px-3 py-1.5 border-b border-white/5 flex items-center gap-3 text-xs font-mono">
                <span className="text-neon-pink">{s.sample_type}</span>
                <span className="text-neon-blue">{s.bpm ?? "?"} BPM</span>
                <span className="text-neon-purple">{s.camelot ?? "-"}</span>
                <span className="text-neutral-300 truncate">{s.filename}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}

function MasterPanel() {
  const { t } = useApp();
  const [outDir, setOutDir] = useState("");
  const [target, setTarget] = useState(-8);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const run = async () => {
    setLoading(true);
    try {
      const tracks = (await api.listTracks({ rating: 1, limit: 1000 })).tracks;
      const r = await api.pp.masterBatch(tracks.map(t => t.id), outDir, target);
      setResult(r);
    } finally { setLoading(false); }
  };
  return (
    <>
      <PanelHeader icon={Disc} titleKey="ppx.master" />
      <div className="space-y-3">
        <p className="text-[10px] font-mono text-neutral-500">Masters all liked tracks (rating ≥ 1)</p>
        <div className="grid grid-cols-2 gap-2">
          <Field label="Output folder">
            <TextInput value={outDir} onChange={(e: any) => setOutDir(e.target.value)} />
          </Field>
          <Field label={t("ppx.target_lufs")}>
            <TextInput type="number" value={target} onChange={(e: any) => setTarget(+e.target.value)} />
          </Field>
        </div>
        <Btn onClick={run} disabled={!outDir || loading}>
          {loading ? <Loader2 size={14} className="animate-spin" /> : <Disc size={14} />}
          Master batch
        </Btn>
        {result && <ResultBox data={result} />}
      </div>
    </>
  );
}

function VenuePanel() {
  const { t } = useApp();
  const [venues, setVenues] = useState<any[]>([]);
  const [active, setActive] = useState("");
  const [duration, setDuration] = useState(60);
  const [tracks, setTracks] = useState<Track[]>([]);
  useEffect(() => { api.pp.venuesList().then(r => setVenues(r.venues)); }, []);
  const run = async () => {
    if (!active) return;
    setTracks((await api.pp.venueSetlist(active, duration)).tracks);
  };
  return (
    <>
      <PanelHeader icon={MapPin} titleKey="ppx.venue" />
      <div className="space-y-3">
        <div className="grid grid-cols-3 gap-2">
          {venues.map((v) => (
            <button key={v.id} onClick={() => setActive(v.id)}
                    className={clsx("p-2 rounded border text-left text-xs font-mono transition",
                      active === v.id
                        ? "bg-neon-pink/15 border-neon-pink text-white"
                        : "border-white/10 text-neutral-400 hover:border-neon-purple/40")}>
              <div className="font-bold">{t(`venue.${v.id}`)}</div>
              <div className="text-[10px] opacity-70">{v.bpm_min}-{v.bpm_max} BPM</div>
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <Field label="Duration (min)">
            <TextInput type="number" value={duration} onChange={(e: any) => setDuration(+e.target.value)} />
          </Field>
          <div className="self-end">
            <Btn onClick={run} disabled={!active}>Generate</Btn>
          </div>
        </div>
        {tracks.length > 0 && <TrackList tracks={tracks} />}
      </div>
    </>
  );
}

function StylePanel() {
  const [track, setTrack] = useState<Track | null>(null);
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const run = async () => {
    if (!track) return;
    setLoading(true);
    try { setData(await api.pp.styleAnalysis(track.id)); }
    finally { setLoading(false); }
  };
  return (
    <>
      <PanelHeader icon={Activity} titleKey="ppx.style" />
      <div className="space-y-3">
        <PanelTrackPicker value={track} onChange={setTrack} />
        <Btn onClick={run} disabled={!track || loading}>
          {loading ? <Loader2 size={14} className="animate-spin" /> : <Activity size={14} />}
          Analyze sections
        </Btn>
        {data?.sections && (
          <div className="glass rounded-lg overflow-hidden">
            {data.sections.map((s: any) => (
              <div key={s.label} className="px-3 py-2 border-b border-white/5 grid grid-cols-7 gap-2 text-xs font-mono">
                <span className="text-neon-pink font-bold">{s.label}</span>
                <span className="text-neutral-400">{Math.floor(s.start_sec)}–{Math.floor(s.end_sec)}s</span>
                <span className="text-neon-yellow">RMS {s.rms_db}dB</span>
                <span className="text-neon-blue">low {s.low_energy_pct}%</span>
                <span className="text-neon-purple">mid {s.mid_energy_pct}%</span>
                <span className="text-neon-green">high {s.high_energy_pct}%</span>
                <span className="text-neutral-300">{s.onset_density}/s</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}

function CloudPanel() {
  const [outPath, setOutPath] = useState("");
  const [packPath, setPackPath] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const exp = async () => { setLoading(true); try { setResult(await api.pp.cloudExport(outPath)); } finally { setLoading(false); } };
  const imp = async () => { setLoading(true); try { setResult(await api.pp.cloudImport(packPath)); } finally { setLoading(false); } };
  const diff = async () => { setLoading(true); try { setResult(await api.pp.cloudDiff(packPath)); } finally { setLoading(false); } };
  return (
    <>
      <PanelHeader icon={Cloud} titleKey="ppx.cloud" />
      <div className="space-y-3">
        <Field label="Export to (.mixmind-pack zip)">
          <TextInput value={outPath} onChange={(e: any) => setOutPath(e.target.value)} placeholder="/Dropbox/MixMind/library.mixmind-pack" />
        </Field>
        <Btn onClick={exp} disabled={!outPath || loading} small>Export</Btn>
        <Field label="Import / diff from">
          <TextInput value={packPath} onChange={(e: any) => setPackPath(e.target.value)} />
        </Field>
        <div className="flex gap-2">
          <Btn onClick={diff} disabled={!packPath || loading} primary={false} small>Diff</Btn>
          <Btn onClick={imp} disabled={!packPath || loading} small>Import</Btn>
        </div>
        {result && <ResultBox data={result} />}
      </div>
    </>
  );
}

function ReleasesPanel() {
  const [feed, setFeed] = useState<any[]>([]);
  const [subs, setSubs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const refresh = async () => {
    setSubs((await api.pp.releasesSubscriptions()).subscriptions || []);
    setFeed((await api.pp.releasesFeed()).releases || []);
  };
  useEffect(() => { refresh(); }, []);
  const auto = async () => { setLoading(true); try { await api.pp.releasesAuto(); await refresh(); } finally { setLoading(false); } };
  const check = async () => { setLoading(true); try { await api.pp.releasesCheck(); await refresh(); } finally { setLoading(false); } };

  return (
    <>
      <PanelHeader icon={Bell} titleKey="ppx.releases" />
      <div className="space-y-3">
        <div className="flex gap-2">
          <Btn onClick={auto} disabled={loading} primary={false} small>Auto-subscribe from library</Btn>
          <Btn onClick={check} disabled={loading} small>
            {loading ? <Loader2 size={12} className="animate-spin" /> : "🔔"} Check now
          </Btn>
        </div>
        <div className="glass rounded-lg p-3 max-h-32 overflow-y-auto">
          <div className="text-xs font-mono text-neon-purple mb-2">Subscribed: {subs.length}</div>
          <div className="flex flex-wrap gap-1">
            {subs.slice(0, 30).map((s: any) => (
              <span key={s.id} className="text-[10px] font-mono px-2 py-0.5 rounded bg-neon-blue/10 border border-neon-blue/30 text-neon-blue">
                {s.kind}: {s.name}
              </span>
            ))}
          </div>
        </div>
        <div className="text-xs font-mono text-neon-pink">New releases ({feed.length})</div>
        {feed.map((r) => (
          <div key={r.id} className="glass rounded-lg p-2 flex items-center gap-3 text-xs font-mono">
            <span className="text-neon-yellow w-12">{r.subscription_name?.slice(0,12)}</span>
            <span className="text-neutral-300 truncate">{r.artist} — {r.title}</span>
            {r.url && <a href={r.url} target="_blank" rel="noopener noreferrer" className="text-neon-blue hover:underline">↗</a>}
          </div>
        ))}
      </div>
    </>
  );
}




function VocalPanel() {
  const { t } = useApp();
  const [track, setTrack] = useState<Track | null>(null);
  const [trackResult, setTrackResult] = useState<any>(null);
  const [batchResult, setBatchResult] = useState<any>(null);
  const [filter, setFilter] = useState<{ gender: string; bpm_min: string; bpm_max: string }>(
    { gender: "", bpm_min: "", bpm_max: "" }
  );
  const [results, setResults] = useState<Track[]>([]);
  const [loading, setLoading] = useState(false);

  const analyzeAll = async () => {
    setLoading(true);
    try { setBatchResult(await api.pp.vocalAnalyze()); }
    finally { setLoading(false); }
  };

  const analyzeOne = async () => {
    if (!track) return;
    setLoading(true);
    try { setTrackResult(await api.pp.vocalForTrack(track.id)); }
    finally { setLoading(false); }
  };

  const search = async () => {
    setLoading(true);
    try {
      const params: Record<string, any> = {
        gender: filter.gender || undefined,
        bpm_min: filter.bpm_min ? Number(filter.bpm_min) : undefined,
        bpm_max: filter.bpm_max ? Number(filter.bpm_max) : undefined,
      };
      const r = await api.pp.vocalFind(params);
      setResults(r.tracks);
    } finally { setLoading(false); }
  };

  // Color per gender bucket
  const genderClass = (g: string) =>
    g === "male" ? "text-neon-blue"
    : g === "female" ? "text-neon-pink"
    : g === "mixed" ? "text-neon-yellow"
    : "text-neutral-500";

  return (
    <>
      <div className="mb-4 flex items-center gap-3">
        <span className="text-3xl">🎤</span>
        <div>
          <h3 className="font-display text-2xl font-bold tracking-wider text-white">
            {t("ppx.vocal.name")}
          </h3>
          <p className="text-xs text-neutral-400 font-mono">{t("ppx.vocal.desc")}</p>
        </div>
      </div>

      <div className="space-y-4">
        {/* Single track analyze */}
        <div className="space-y-2">
          <PanelTrackPicker value={track} onChange={setTrack} />
          <Btn onClick={analyzeOne} disabled={!track || loading} primary={false} small>
            {loading ? <Loader2 size={12} className="animate-spin" /> : <Mic size={12} />}
            {t("vocal.run_track")}
          </Btn>
        </div>

        {/* Single-track result */}
        {trackResult && !trackResult.error && (
          <div className="glass rounded-lg p-3 space-y-2 font-mono text-xs">
            <div className="flex items-center gap-3">
              <span className={`text-2xl font-display font-black ${genderClass(trackResult.vocal_gender)}`}>
                {t(`vocal.${trackResult.vocal_gender}`)}
              </span>
              <span className="text-neutral-500">
                {Math.round(trackResult.vocal_confidence * 100)}% conf
              </span>
            </div>
            <div className="grid grid-cols-3 gap-2 text-[11px]">
              <div>
                <div className="text-neon-purple text-[10px] uppercase">{t("vocal.presence")}</div>
                <div className="text-neon-green">
                  {(trackResult.vocal_presence * 100).toFixed(1)}%
                </div>
              </div>
              {trackResult.vocal_f0_hz && (
                <div>
                  <div className="text-neon-purple text-[10px] uppercase">{t("vocal.f0")}</div>
                  <div className="text-neon-blue">{trackResult.vocal_f0_hz} Hz</div>
                </div>
              )}
              {trackResult.vocal_f0_lo && (
                <div>
                  <div className="text-neon-purple text-[10px] uppercase">{t("vocal.f0_range")}</div>
                  <div className="text-neon-yellow">
                    {trackResult.vocal_f0_lo}–{trackResult.vocal_f0_hi} Hz
                  </div>
                </div>
              )}
            </div>
            {trackResult.notes?.length > 0 && (
              <ul className="text-[10px] text-neutral-400 list-disc list-inside">
                {trackResult.notes.map((n: string, i: number) => <li key={i}>{n}</li>)}
              </ul>
            )}
          </div>
        )}

        {/* Batch analysis */}
        <div className="border-t border-white/5 pt-4">
          <Btn onClick={analyzeAll} disabled={loading}>
            {loading ? <Loader2 size={14} className="animate-spin" /> : <Mic size={14} />}
            {t("vocal.run_library")}
          </Btn>
          {batchResult && (
            <div className="mt-3 glass rounded-lg p-3 font-mono text-xs">
              <div className="text-neon-purple text-[10px] uppercase tracking-wider mb-2">
                {t("vocal.distribution")} · {t("vocal.processed")}: {batchResult.processed}
              </div>
              <div className="grid grid-cols-4 gap-2">
                {(["male", "female", "mixed", "none"] as const).map((g) => (
                  <div key={g} className="text-center">
                    <div className={`text-2xl font-display font-black ${genderClass(g)}`}>
                      {batchResult.distribution[g] || 0}
                    </div>
                    <div className="text-[10px] text-neutral-400">{t(`vocal.${g}`)}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Find by gender */}
        <div className="border-t border-white/5 pt-4 space-y-2">
          <div className="text-xs font-mono text-neon-purple uppercase tracking-wider">
            {t("vocal.find_filter")}
          </div>
          <div className="flex gap-2 flex-wrap items-center">
            <select
              value={filter.gender}
              onChange={(e) => setFilter({ ...filter, gender: e.target.value })}
              className="bg-bg-1 border border-neon-purple/30 rounded px-2 py-1 font-mono text-xs"
            >
              <option value="">{t("vocal.any")}</option>
              <option value="male">{t("vocal.male")}</option>
              <option value="female">{t("vocal.female")}</option>
              <option value="mixed">{t("vocal.mixed")}</option>
              <option value="none">{t("vocal.none")}</option>
            </select>
            <input
              type="number"
              value={filter.bpm_min}
              onChange={(e) => setFilter({ ...filter, bpm_min: e.target.value })}
              placeholder="BPM min"
              className="w-24 bg-bg-1 border border-neon-purple/30 rounded px-2 py-1 font-mono text-xs"
            />
            <input
              type="number"
              value={filter.bpm_max}
              onChange={(e) => setFilter({ ...filter, bpm_max: e.target.value })}
              placeholder="BPM max"
              className="w-24 bg-bg-1 border border-neon-purple/30 rounded px-2 py-1 font-mono text-xs"
            />
            <Btn onClick={search} disabled={loading} small>
              <Mic size={12} />
              Search
            </Btn>
          </div>
          {results.length > 0 && (
            <div className="glass rounded-lg overflow-hidden max-h-96 overflow-y-auto">
              {results.map((tr) => (
                <div key={tr.id} className="px-3 py-2 border-b border-white/5 flex items-center gap-3 text-xs font-mono">
                  <span className={`w-16 ${genderClass(tr.vocal_gender || "none")}`}>
                    {t(`vocal.${tr.vocal_gender || "none"}`)}
                  </span>
                  <span className="text-neutral-500 w-16">
                    {tr.vocal_f0_hz ? `${tr.vocal_f0_hz} Hz` : "-"}
                  </span>
                  <span className="text-neon-blue w-12">{tr.bpm} BPM</span>
                  <span className="text-neon-purple w-10">{tr.camelot}</span>
                  <span className="text-neutral-300 truncate">
                    {tr.artist} - {tr.title}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
