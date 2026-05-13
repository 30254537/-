// Bilingual EN / ZH translations for MixMind DJ.
// All user-facing strings funnel through `t(key)` so changing language
// triggers a full UI re-render via the zustand store.

export type Lang = "en" | "zh";

const TRANSLATIONS: Record<string, { en: string; zh: string }> = {
  // ── Brand / chrome ────────────────────────────────────────────────
  "brand.tagline":         { en: "DJ // v0.4.0", zh: "DJ 专业版 // v0.4.0" },
  "lang.en":               { en: "EN", zh: "EN" },
  "lang.zh":               { en: "中文", zh: "中文" },

  // ── Sidebar nav ───────────────────────────────────────────────────
  "nav.dashboard":         { en: "Dashboard",        zh: "总览" },
  "nav.library":           { en: "Library",          zh: "曲库" },
  "nav.recommend":         { en: "AI Recommend",     zh: "AI 推荐" },
  "nav.playlist":          { en: "Playlist Builder", zh: "歌单生成器" },
  "nav.dedupe":            { en: "Duplicates",       zh: "重复检测" },
  "nav.pro":               { en: "Pro Tools",        zh: "专业工具" },

  "sidebar.tracks":        { en: "Tracks",           zh: "曲目数" },
  "sidebar.liked":         { en: "Liked",            zh: "已喜欢" },
  "sidebar.hours":         { en: "Hours",            zh: "总时长" },

  // ── Dashboard ─────────────────────────────────────────────────────
  "dashboard.welcome":     { en: "WELCOME",          zh: "欢迎" },
  "dashboard.dj":          { en: "DJ",               zh: "DJ" },
  "dashboard.tagline":     { en: "Professional-grade audio analysis. Camelot key detection. Real-time AI taste learning.",
                             zh: "专业级音频分析 · Camelot 调性检测 · 实时 AI 喜好学习" },
  "dashboard.scan_title":  { en: "SCAN MUSIC LIBRARY", zh: "扫描音乐库" },
  "dashboard.scan_btn":    { en: "SCAN",             zh: "开始扫描" },
  "dashboard.placeholder": { en: "D:\\Music\\NewDownloads", zh: "D:\\Music\\NewDownloads" },
  "dashboard.genres":      { en: "GENRE BREAKDOWN",  zh: "风格分布" },
  "dashboard.stat.tracks": { en: "Tracks",           zh: "曲目" },
  "dashboard.stat.hours":  { en: "Hours",            zh: "小时" },
  "dashboard.stat.liked":  { en: "Liked",            zh: "已喜欢" },
  "dashboard.stat.analyzed":{en: "Analyzed",         zh: "已分析" },
  "dashboard.scan.done":   { en: "✓ DONE",           zh: "✓ 完成" },

  // ── Library ───────────────────────────────────────────────────────
  "library.title":         { en: "LIBRARY",          zh: "曲库" },
  "library.search":        { en: "Search artist, title...", zh: "搜索艺术家 / 歌名..." },
  "library.all_genres":    { en: "All Genres",       zh: "所有风格" },
  "library.all_moods":     { en: "All Moods",        zh: "所有氛围" },
  "library.bpm_min":       { en: "BPM min",          zh: "BPM 最低" },
  "library.bpm_max":       { en: "BPM max",          zh: "BPM 最高" },

  "table.artist_title":    { en: "Artist / Title",   zh: "艺术家 / 标题" },
  "table.bpm":             { en: "BPM",              zh: "BPM" },
  "table.key":             { en: "Key",              zh: "调性" },
  "table.energy":          { en: "Energy",           zh: "能量" },
  "table.genre":           { en: "Genre",            zh: "风格" },
  "table.mood":            { en: "Mood",             zh: "氛围" },
  "table.empty":           { en: "No tracks. Run a scan to get started.",
                             zh: "暂无曲目，请先扫描音乐文件夹" },

  "mood.chill":            { en: "Chill",            zh: "舒缓" },
  "mood.warmup":           { en: "Warmup",           zh: "暖场" },
  "mood.groove":           { en: "Groove",           zh: "律动" },
  "mood.peak":             { en: "Peak",             zh: "高潮" },
  "mood.intense":          { en: "Intense",          zh: "炸场" },

  // ── Recommend ─────────────────────────────────────────────────────
  "recommend.title":       { en: "AI RECOMMENDATIONS", zh: "AI 推荐" },
  "recommend.subtitle":    { en: "Tracks scored by cosine similarity to your taste centroid.",
                             zh: "基于你的喜好中心向量按余弦相似度评分" },
  "recommend.retrain":     { en: "RETRAIN MODEL",    zh: "重训模型" },
  "recommend.training":    { en: "TRAINING...",      zh: "训练中..." },
  "recommend.empty":       { en: "Like some tracks first, then come back here.",
                             zh: "先标记几首喜欢的曲目，然后回到这里" },
  "recommend.empty_sub":   { en: "AI needs at least 1 liked track to start recommending.",
                             zh: "AI 至少需要 1 首喜欢的曲目才能开始推荐" },

  // ── Playlist Builder ──────────────────────────────────────────────
  "pl.title":              { en: "PLAYLIST",         zh: "歌单" },
  "pl.title2":             { en: "BUILDER",          zh: "生成器" },
  "pl.duration":           { en: "Duration (min)",   zh: "时长（分钟）" },
  "pl.genre":              { en: "Genre",            zh: "风格" },
  "pl.bpm_min":            { en: "BPM min",          zh: "BPM 最低" },
  "pl.bpm_max":            { en: "BPM max",          zh: "BPM 最高" },
  "pl.save_as":            { en: "Save as",          zh: "另存为" },
  "pl.save_placeholder":   { en: "Club Night — Fri", zh: "周五 Club Night" },
  "pl.generate":           { en: "GENERATE",         zh: "生成" },
  "pl.export":             { en: "EXPORT .M3U8",     zh: "导出 .M3U8" },
  "pl.any":                { en: "Any",              zh: "任意" },
  "pl.curve.warmup":       { en: "Warmup",           zh: "暖场" },
  "pl.curve.warmup_desc":  { en: "Ease in — low to mid energy (3 → 6)",
                             zh: "渐入 · 能量从低到中（3 → 6）" },
  "pl.curve.peak":         { en: "Peak Time",        zh: "黄金时段" },
  "pl.curve.peak_desc":    { en: "Classic arc, big energy at center",
                             zh: "经典弧形 · 中段最炸" },
  "pl.curve.after":        { en: "After Hours",      zh: "尾场" },
  "pl.curve.after_desc":   { en: "Wind-down — high to low (5 → 2)",
                             zh: "收尾 · 能量从高到低（5 → 2）" },
  "pl.curve.festival":     { en: "Festival",         zh: "音乐节" },
  "pl.curve.festival_desc":{ en: "Relentless ramp to full energy",
                             zh: "持续冲刺到满能量" },
  "pl.curve.journey":      { en: "DJ Journey",       zh: "三段式" },
  "pl.curve.journey_desc": { en: "3-act — warmup, peak, cooldown",
                             zh: "三幕 · 暖场 / 高潮 / 收尾" },
  "pl.tracks_count":       { en: "tracks",           zh: "首" },
  "pl.minutes":            { en: "min",              zh: "分钟" },

  // ── Dedupe ────────────────────────────────────────────────────────
  "dd.title1":             { en: "DUPLICATE",        zh: "重复" },
  "dd.title2":             { en: "DETECTOR",         zh: "检测器" },
  "dd.run":                { en: "RUN DEDUPE",       zh: "开始检测" },
  "dd.scanning":           { en: "SCANNING...",      zh: "扫描中..." },
  "dd.found":              { en: "Found",            zh: "发现" },
  "dd.groups":             { en: "duplicate groups covering", zh: "组重复，共" },
  "dd.tracks":             { en: "tracks.",          zh: "首" },
  "dd.advice":             { en: "Keep the largest file in each group, delete the rest.",
                             zh: "建议保留每组中文件最大的，删除其余" },
  "dd.empty":              { en: "No duplicates found. Your library is clean.",
                             zh: "未发现重复，曲库非常干净" },
  "dd.keep":               { en: "✓ KEEP",           zh: "✓ 保留" },
  "dd.remove":             { en: "✗ REMOVE",         zh: "✗ 移除" },
  "dd.group":              { en: "GROUP",            zh: "组" },

  // ── Pro Tools — module names ──────────────────────────────────────
  "pro.title":             { en: "PRO",              zh: "专业" },
  "pro.title2":             { en: "TOOLS",            zh: "工具" },
  "pro.subtitle":          { en: "8 modules for the working DJ — built on professional-grade DSP.",
                             zh: "面向职业 DJ 的 8 大模块 · 基于专业级 DSP 算法" },

  "pro.trackid.name":      { en: "Track ID Studio",  zh: "曲目识别" },
  "pro.trackid.tag":       { en: "🎯",                zh: "🎯" },
  "pro.trackid.desc":      { en: "Identify unknown tracks via audio fingerprint, AcoustID, and Discogs validation.",
                             zh: "通过音频指纹 + AcoustID + Discogs 三重验证识别未知曲目" },

  "pro.livemix.name":      { en: "Live Mix Assistant", zh: "实时混音助手" },
  "pro.livemix.tag":       { en: "🎚️",               zh: "🎚️" },
  "pro.livemix.desc":      { en: "Real-time next-track suggestions with mix-in points and reasons.",
                             zh: "实时推荐下一首 · 提供混入点与推荐理由" },

  "pro.phrasegrid.name":   { en: "Phrase Grid",      zh: "乐句网格" },
  "pro.phrasegrid.tag":    { en: "📐",                zh: "📐" },
  "pro.phrasegrid.desc":   { en: "32-bar structural ribbon — perfect mix-in / mix-out points.",
                             zh: "32 小节结构带 · 标出最佳混入 / 混出点" },

  "pro.stems.name":        { en: "AI Stems",         zh: "AI 分轨" },
  "pro.stems.tag":         { en: "💎",                zh: "💎" },
  "pro.stems.desc":        { en: "4-stem separation: vocals / drums / bass / other. Demucs / Spleeter.",
                             zh: "4 轨分离：人声 / 鼓 / 贝斯 / 其他 · Demucs / Spleeter" },

  "pro.gig.name":          { en: "Gig USB Export",   zh: "演出包导出" },
  "pro.gig.tag":           { en: "📦",                zh: "📦" },
  "pro.gig.desc":          { en: "One-click pack: audio + Rekordbox XML + Serato + M3U8 + covers.",
                             zh: "一键打包：音频 + Rekordbox XML + Serato + M3U8 + 封面" },

  "pro.trends.name":       { en: "Trend Radar",      zh: "潮流雷达" },
  "pro.trends.tag":        { en: "📡",                zh: "📡" },
  "pro.trends.desc":       { en: "Compare your library against Beatport / RA / TikTok charts.",
                             zh: "对比 Beatport / RA / TikTok 等全球榜单" },

  "pro.quality.name":      { en: "Quality Audit",    zh: "音质审计" },
  "pro.quality.tag":       { en: "🎵",                zh: "🎵" },
  "pro.quality.desc":      { en: "Spectral analysis to detect fake 320 kbps files (transcoded from 128).",
                             zh: "频谱分析揪出冒牌 320 kbps（从 128 转码而来）" },

  "pro.hotcues.name":      { en: "Auto Hot Cues",    zh: "自动热 Cue" },
  "pro.hotcues.tag":       { en: "🔥",                zh: "🔥" },
  "pro.hotcues.desc":      { en: "8 pro Hot Cues per track, exportable to Rekordbox / Serato.",
                             zh: "每首曲目 8 个专业热 Cue · 可导出至 Rekordbox / Serato" },

  // ── Pro: Track ID detail ──────────────────────────────────────────
  "pro.trackid.input":     { en: "File path or library track id", zh: "文件路径或曲库 ID" },
  "pro.trackid.id":        { en: "IDENTIFY",         zh: "立即识别" },
  "pro.trackid.matches":   { en: "MATCHES",          zh: "匹配结果" },
  "pro.trackid.confidence":{ en: "Confidence",       zh: "置信度" },
  "pro.trackid.matched":   { en: "matched landmarks", zh: "匹配的指纹点" },
  "pro.trackid.discogs":   { en: "Discogs match",    zh: "Discogs 验证" },
  "pro.trackid.label":     { en: "Label",            zh: "厂牌" },
  "pro.trackid.year":      { en: "Year",             zh: "发行年份" },
  "pro.trackid.catno":     { en: "Catalog #",        zh: "唱片编号" },
  "pro.trackid.empty":     { en: "Enter a file path or click an analyzed track from the library.",
                             zh: "输入文件路径或在曲库中点选已分析的曲目" },

  // ── Pro: Live Mix ────────────────────────────────────────────────
  "pro.livemix.deck_a":    { en: "Deck A — playing now", zh: "Deck A · 当前播放" },
  "pro.livemix.deck_b":    { en: "Deck B candidates",     zh: "Deck B · 候选曲目" },
  "pro.livemix.mode":      { en: "Mode",                  zh: "模式" },
  "pro.livemix.steady":    { en: "Steady",                zh: "持平" },
  "pro.livemix.build":     { en: "Build",                 zh: "推升" },
  "pro.livemix.release":   { en: "Release",               zh: "释放" },
  "pro.livemix.score":     { en: "Mix Score",             zh: "混音分" },
  "pro.livemix.bpm_drift": { en: "BPM drift",             zh: "BPM 偏移" },
  "pro.livemix.mix_in":    { en: "Mix in @",              zh: "混入点 @" },
  "pro.livemix.mix_out":   { en: "Mix out @",             zh: "混出点 @" },
  "pro.livemix.no_track":  { en: "Pick a track from your library to start.",
                             zh: "请先在曲库中选择一首正在播放的曲目" },
  "pro.livemix.cue":       { en: "USE",                   zh: "采用" },
  "reason.perfect_bpm":    { en: "Perfect BPM",           zh: "BPM 完美吻合" },
  "reason.close_bpm":      { en: "Close BPM",             zh: "BPM 接近" },
  "reason.same_key":       { en: "Same key",              zh: "同调性" },
  "reason.harmonic":       { en: "Harmonic",              zh: "和声兼容" },
  "reason.energy_lift":    { en: "Energy lift",           zh: "能量推升" },
  "reason.energy_drop":    { en: "Energy drop",           zh: "能量下降" },
  "reason.smooth_continuation": { en: "Smooth continuation", zh: "平滑续接" },
  "reason.same_genre":     { en: "Same genre",            zh: "同风格" },
  "reason.you_like_this":  { en: "You like this",         zh: "你喜欢这首" },
  "reason.taste_match":    { en: "Taste match",           zh: "品味契合" },

  // ── Pro: Phrase Grid ─────────────────────────────────────────────
  "pro.phrasegrid.bars":   { en: "bars",                 zh: "小节" },
  "pro.phrasegrid.section":{ en: "Section",              zh: "段落" },
  "pro.phrasegrid.section.intro":     { en: "Intro",       zh: "前奏" },
  "pro.phrasegrid.section.main":      { en: "Main",        zh: "主歌" },
  "pro.phrasegrid.section.drop":      { en: "Drop",        zh: "Drop" },
  "pro.phrasegrid.section.breakdown": { en: "Breakdown",   zh: "Breakdown" },
  "pro.phrasegrid.section.outro":     { en: "Outro",       zh: "尾奏" },
  "pro.phrasegrid.section.outro_lead":{ en: "Outro lead",  zh: "渐入尾奏" },
  "pro.phrasegrid.mix_in_points":  { en: "Suggested mix-in points",  zh: "建议混入点" },
  "pro.phrasegrid.mix_out_points": { en: "Suggested mix-out points", zh: "建议混出点" },

  // ── Pro: Stems ───────────────────────────────────────────────────
  "pro.stems.run":         { en: "RUN SEPARATION",        zh: "开始分轨" },
  "pro.stems.no_track":    { en: "Select a track first.",  zh: "请先选择一首曲目" },
  "pro.stems.unavailable": { en: "No backend installed.",  zh: "未安装分轨引擎" },
  "pro.stems.install":     { en: "Install with: pip install demucs (≈2GB)",
                             zh: "请安装：pip install demucs（约 2GB 模型）" },
  "pro.stems.vocals":      { en: "Vocals",                  zh: "人声" },
  "pro.stems.drums":       { en: "Drums",                   zh: "鼓组" },
  "pro.stems.bass":        { en: "Bass",                    zh: "贝斯" },
  "pro.stems.other":       { en: "Other",                   zh: "其他" },
  "pro.stems.acapella":    { en: "Make Acapella",           zh: "生成纯人声" },
  "pro.stems.instrumental":{ en: "Make Instrumental",       zh: "生成伴奏" },

  // ── Pro: Gig Export ──────────────────────────────────────────────
  "pro.gig.out_dir":       { en: "Output folder (USB path)", zh: "输出文件夹（U 盘路径）" },
  "pro.gig.placeholder":   { en: "/Volumes/USB/Gig-Friday",  zh: "/Volumes/USB/Gig-Friday" },
  "pro.gig.playlist":      { en: "Playlist",                  zh: "歌单" },
  "pro.gig.normalize":     { en: "Normalize to (LUFS)",       zh: "响度归一化（LUFS）" },
  "pro.gig.covers":        { en: "Include covers",            zh: "包含封面" },
  "pro.gig.go":            { en: "PACK FOR GIG",              zh: "打包" },
  "pro.gig.success":       { en: "Pack ready",                zh: "打包完成" },
  "pro.gig.size":          { en: "Total size",                zh: "总大小" },
  "pro.gig.tracks":        { en: "Tracks",                    zh: "曲目数" },

  // ── Pro: Trends ──────────────────────────────────────────────────
  "pro.trends.refresh":    { en: "REFRESH",                   zh: "刷新榜单" },
  "pro.trends.have":       { en: "You have",                  zh: "已拥有" },
  "pro.trends.missing":    { en: "Missing",                   zh: "缺货" },
  "pro.trends.empty":      { en: "Charts unavailable. Check your network.",
                             zh: "暂无榜单数据 · 请检查网络" },

  // ── Pro: Quality ─────────────────────────────────────────────────
  "pro.quality.run":       { en: "AUDIT TRACK",               zh: "审计当前曲目" },
  "pro.quality.batch":     { en: "AUDIT WHOLE LIBRARY",       zh: "审计整个曲库" },
  "pro.quality.cutoff":    { en: "Spectral cutoff",           zh: "频谱截止" },
  "pro.quality.declared":  { en: "Declared bitrate",          zh: "声明码率" },
  "pro.quality.verdict":   { en: "Verdict",                   zh: "判定" },
  "pro.quality.score":     { en: "Score",                     zh: "得分" },
  "verdict.pristine":      { en: "Pristine",                  zh: "完美" },
  "verdict.lossless":      { en: "Lossless",                  zh: "无损" },
  "verdict.lossy_320":     { en: "True 320",                  zh: "真 320" },
  "verdict.lossy":         { en: "Lossy",                     zh: "有损" },
  "verdict.fake_320":      { en: "FAKE 320",                  zh: "冒牌 320" },
  "verdict.very_lossy":    { en: "Very lossy",                zh: "低质量" },
  "verdict.error":         { en: "Error",                     zh: "错误" },

  // ── Pro: Hot Cues ────────────────────────────────────────────────
  "pro.hotcues.generate":  { en: "GENERATE 8 HOT CUES",       zh: "生成 8 个热 Cue" },
  "pro.hotcues.export":    { en: "WRITE TO REKORDBOX XML",    zh: "写入 Rekordbox XML" },
  "pro.hotcues.no_track":  { en: "Pick a track from the library, then click Generate.",
                             zh: "在曲库中选中一首，然后点击生成" },
  "cue.intro_start":       { en: "Intro Start",               zh: "前奏起" },
  "cue.intro_end":         { en: "Intro End",                 zh: "前奏止" },
  "cue.build_up":          { en: "Build Up",                  zh: "推进" },
  "cue.drop_1":            { en: "Drop 1",                    zh: "Drop 1" },
  "cue.breakdown":         { en: "Breakdown",                 zh: "Breakdown" },
  "cue.drop_2":            { en: "Drop 2",                    zh: "Drop 2" },
  "cue.last_hit":          { en: "Last Hit",                  zh: "最后冲刺" },
  "cue.outro_start":       { en: "Outro Start",               zh: "尾奏起" },

  // ── Common ───────────────────────────────────────────────────────
  "common.loading":        { en: "Loading...",                zh: "加载中..." },
  "common.thinking":       { en: "Thinking...",               zh: "思考中..." },
  "common.error":          { en: "Error",                     zh: "错误" },
  "common.cancel":         { en: "CANCEL",                    zh: "取消" },
  "common.close":          { en: "CLOSE",                     zh: "关闭" },
  "common.ok":             { en: "OK",                        zh: "确认" },
  "common.unknown":        { en: "Unknown",                   zh: "未知" },
  "common.selected":       { en: "Selected",                  zh: "已选" },
  "common.no_track":       { en: "No track selected",         zh: "未选中曲目" },
};

export function translate(key: string, lang: Lang): string {
  const entry = TRANSLATIONS[key];
  if (!entry) return key;
  return entry[lang] ?? entry.en;
}

export const ALL_KEYS = Object.keys(TRANSLATIONS);
