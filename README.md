# 🎧 MixMind DJ

**AI-Powered Music Management for DJs** — Stop wasting hours sorting music. Let AI learn your taste.

[English](#english) | [中文](#中文)

---

## 中文

### 🎯 解决什么问题？

作为DJ，你是否经常：
- 下载了几百首新歌，却要花几小时一首一首试听
- 曲库几千首，按风格/能量分类混乱
- 每次演出前花很久准备歌单
- 不同版本的同一首歌塞满硬盘
- Rekordbox / Serato 标签各自为政，数据不通

**MixMind DJ** 是为DJ量身打造的本地AI音乐管家，运行在你的电脑上，不需要上传云端。

### ✨ 核心功能

| 功能 | 说明 |
|------|------|
| 🔍 **批量扫描** | 一键扫描硬盘/云盘本地目录，支持 MP3/WAV/FLAC/AIFF/M4A |
| 🎵 **音频分析** | 自动提取 BPM、调性(Camelot Key)、能量值、响度、频谱特征 |
| 🤖 **AI风格分类** | House / Techno / Trance / Hip-Hop / Drum&Bass 等自动归类 |
| ⚡ **能量/情绪标签** | Warm-up / Peak Time / Chill / Afterhours 自动打标 |
| 💖 **AI学习你的喜好** | 标记几首"喜欢"，AI 找出曲库里相似的歌 |
| 🔁 **智能去重** | 识别同一首歌的 Original / Extended / Remix 版本 |
| 📁 **自动归档** | 按你的规则自动整理到文件夹 |
| 🎬 **高潮预览** | 自动提取每首歌最精彩的 30 秒 |
| 🎚️ **AI智能排歌** | 按能量曲线 + 和声兼容 + 你的品味自动生成歌单 |
| 🔄 **导出兼容** | 导出 Rekordbox XML / Serato crates |

### 🖥️ 炫酷 3D Web UI

- 赛博朋克霓虹风格，3D 音乐可视化
- 实时波形 + 频谱 + Camelot 轮盘
- 拖拽式歌单编辑器
- 本地运行，浏览器访问

### 🚀 快速开始（Windows）

#### 步骤 1: 安装依赖

```powershell
# 安装 Python 3.11+ : https://www.python.org/downloads/
# 安装 Node.js 20+ : https://nodejs.org/

# 克隆仓库
git clone https://github.com/30254537/-.git mixmind-dj
cd mixmind-dj

# 后端
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 前端
cd ..\frontend
npm install
```

#### 步骤 2: 扫描你的曲库

```powershell
cd backend
venv\Scripts\activate

# 扫描并分析音乐文件夹
python -m mixmind scan "D:\Music\NewDownloads"

# 查看曲库统计
python -m mixmind stats

# 查找重复曲目
python -m mixmind dedupe

# 标记喜欢的歌
python -m mixmind like "Artist - Track Name"

# 让 AI 推荐相似的
python -m mixmind recommend --limit 20

# 生成一个 90 分钟的 Peak Time 歌单
python -m mixmind playlist --duration 90 --style peak-time --out peak.m3u8
```

#### 步骤 3: 启动 Web UI（炫酷 3D 界面）

```powershell
# 终端 1: 启动后端 API
cd backend
venv\Scripts\activate
uvicorn mixmind.api:app --reload

# 终端 2: 启动前端
cd frontend
npm run dev

# 浏览器打开 http://localhost:5173
```

### 📁 目录结构

```
mixmind-dj/
├── backend/              # Python 后端
│   ├── mixmind/
│   │   ├── __main__.py       # CLI 入口
│   │   ├── cli.py            # 命令行界面
│   │   ├── api.py            # FastAPI Web 服务
│   │   ├── database.py       # SQLite 数据层
│   │   ├── scanner.py        # 文件扫描
│   │   ├── analyzer.py       # 音频分析 (BPM/Key/Energy)
│   │   ├── classifier.py     # AI 风格分类
│   │   ├── dedupe.py         # 智能去重
│   │   ├── preferences.py    # AI 喜好学习
│   │   ├── playlist.py       # 智能排歌
│   │   └── exporter.py       # Rekordbox/Serato 导出
│   └── requirements.txt
├── frontend/             # React + Three.js 3D UI
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── Scene3D.tsx       # 3D 场景
│   │   │   ├── CamelotWheel.tsx  # Camelot 轮盘
│   │   │   ├── TrackList.tsx
│   │   │   ├── Waveform.tsx
│   │   │   └── PlaylistBuilder.tsx
│   │   └── api/
│   └── package.json
└── docs/
```

### 🛠️ 技术栈

- **音频分析**: librosa, mutagen, numpy
- **AI 分类**: scikit-learn (KNN + 自训练模型)
- **后端**: Python 3.11 + FastAPI + SQLite
- **前端**: React 18 + TypeScript + Three.js + React Three Fiber + Tailwind
- **可视化**: WebGL 3D + WaveSurfer.js

### 🗺️ 路线图

- [x] **v0.1** - CLI 工具：扫描 / 分析 / 去重 / 归类
- [x] **v0.2** - AI 喜好学习 + 智能排歌
- [x] **v0.3** - 3D Web UI
- [ ] **v0.4** - Rekordbox XML / Serato crates 导出
- [ ] **v0.5** - Electron 打包成 Windows 桌面应用
- [ ] **v1.0** - 深度学习风格识别（替换启发式分类器）

---

## English

### What is MixMind DJ?

A local, privacy-first AI music manager built for DJs. Scan your music library, let AI classify by genre and energy, learn your taste, and auto-generate DJ-ready playlists.

### Key Features

- 🔍 Batch scan local folders (MP3/WAV/FLAC/AIFF/M4A)
- 🎵 Auto-extract BPM, Key (Camelot), Energy, Loudness
- 🤖 AI genre classification
- 💖 Learn your preferences from like/dislike feedback
- 🔁 Smart duplicate detection (Original/Extended/Remix aware)
- 🎚️ Auto-playlist generation with energy curves + harmonic mixing
- 🎨 Cool cyberpunk 3D Web UI

See [中文](#中文) section above for full installation and usage instructions.

### License

MIT

---

Built with ❤️ for DJs who'd rather spin than sort.
