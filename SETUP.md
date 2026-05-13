# 🎧 MixMind DJ — Complete Setup & Test Guide

[English](#english) · [中文](#中文)

---

## 中文

### 🚀 一键启动（推荐）

#### Windows
1. 安装 **Python 3.11+**：https://www.python.org/downloads/ （安装时勾选 "Add to PATH"）
2. 安装 **Node.js 20+**：https://nodejs.org/
3. 在仓库根目录双击 **`start.bat`**

#### macOS / Linux
1. 安装 **Python 3.11+** 和 **Node.js 20+**
   - macOS: `brew install python@3.11 node`
   - Ubuntu/Debian: `sudo apt install python3.11 python3.11-venv nodejs npm`
2. 在仓库根目录运行 **`./start.sh`**

启动脚本会自动：
- 创建 Python 虚拟环境
- 安装所有依赖
- 运行健康检查
- 自动播种 60 首演示曲目（首次启动时）
- 同时启动后端 API 和前端，打开浏览器到 http://localhost:5173

---

### 🧪 测试流程（看完整 8 个 Pro 模块的最快路径）

启动后浏览器自动打开 → 左侧导航点 **"Pro Tools / 专业工具"** → 按以下顺序试每个模块：

#### 1️⃣ 🎯 **Track ID Studio**（曲目识别）
- 在曲目选择器中点选任意一首演示曲目
- 点 "IDENTIFY / 立即识别"
- 看 **置信度大数字**（绿色）+ **匹配条** + **Discogs 元数据条**
- ⏱️ 约 1-2 秒

#### 2️⃣ 🎚️ **Live Mix Assistant**（实时混音）
- 选一首做 Deck A
- 点击 **Steady / Build / Release** 切换模式（每次切换会重新计算）
- 看 **3 个候选卡片** 滑入，**Mix Score 数字会从 0 增长到目标值**
- 每张卡片有 **5+ 个推荐理由标签**（同调性 / BPM 完美 / 能量推升...）
- 点 "USE #1" 把它推到 Deck A，立即看下一组推荐
- ⏱️ 约 0.5 秒

#### 3️⃣ 📐 **Phrase Grid**（乐句网格）
- 选一首已分析的曲目
- 看 **彩色结构带**（Intro 蓝 → Drop 粉 → Breakdown 紫 → Outro 黄）
- 看 **小节刻度线**（每 32 小节带粗粉线 + 小节号）
- 看下方 **建议混入点 / 混出点**
- ⏱️ 立即

#### 4️⃣ 🔥 **Auto Hot Cues**（自动热 Cue）
- 选一首曲目，点 "GENERATE 8 HOT CUES"
- 看 **8 个发光圆点** 在波形上**逐个弹入并持续脉冲发光**
- 下方 **8 张卡片** 错落入场，每个卡片左侧色条对应 Rekordbox 颜色
- ⏱️ 约 1 秒（动画时间）

#### 5️⃣ 🎵 **Quality Audit**（音质审计）
- 选一首演示曲目（演示数据都标的是 320 kbps）
- 点 "AUDIT TRACK"
- 看 **判定徽标** 弹出（绿色 = True 320 / 红色 = FAKE 320）
- 看 **频谱图** 一根一根从下往上长出来，到截止点的位置出现 **黄色虚线 + 频率标注**
- ⏱️ 约 1 秒（动画 + 计算）

#### 6️⃣ 📡 **Trend Radar**（潮流雷达）
- 点 "REFRESH" 刷新 Beatport 榜单
- 看每个风格 section 的 **绿/黄双进度条**（已有 vs 缺货）
- 离线/沙箱环境下榜单为空，但本地匹配逻辑可正常运行

#### 7️⃣ 💎 **AI Stems**（AI 分轨）
- 选一首曲目，点 "RUN SEPARATION"
- ⚠️ **需要先安装 Demucs**（约 2GB 模型）：
  ```bash
  pip install demucs
  ```
- 演示数据是 1 秒静默 WAV，所以分轨会瞬间完成但内容为空 — 这是预期的，用真实音乐文件即可看到效果

#### 8️⃣ 📦 **Gig USB Export**（演出包导出）
- 先去 **Playlist Builder / 歌单生成器** 生成一个歌单（"GENERATE"）
- 回到 Pro Tools → Gig USB Export
- 选刚生成的歌单 + 输入输出路径（如 `/tmp/test-gig`）
- 点 "PACK FOR GIG"
- 看 **打包成功** 反馈：曲目数 + 总大小
- 在输出文件夹会有 `rekordbox.xml` / `serato_playlist.txt` / `playlist.m3u8` / `metadata.json` / `README.txt`

---

### 🌐 双语切换测试

- 任何视图都可以点 **侧边栏右上角 "EN / 中文"** 切换
- 切换后 170+ 处文本立即变化
- 选择会保存到 `localStorage`，刷新后保留

---

### 🔍 命令行验证（无浏览器）

```bash
# 进入 backend 目录并激活 venv
cd backend
source venv/bin/activate          # mac/linux
# 或 venv\Scripts\activate         # Windows

# 检查环境
python -m mixmind health

# 看曲库统计
python -m mixmind stats

# 列出所有曲目
python -m mixmind list --limit 10

# 用真实音乐扫描
python -m mixmind scan "/path/to/your/music"

# 标记喜欢的歌
python -m mixmind like "Artist - Track"

# AI 推荐
python -m mixmind recommend --limit 20

# 生成 60 分钟 Peak Time 歌单
python -m mixmind playlist --duration 60 --style peak-time --out peak.m3u8

# 重新生成演示数据（先清空再播种）
python -m mixmind demo --clear --count 60
```

---

### 🛠️ 故障排查

| 症状 | 解决方法 |
|------|---------|
| `python: command not found` | 安装 Python 3.11+，确保 PATH 中有 python |
| `npm: command not found` | 安装 Node.js 20+ |
| `pip install` 卡住 / 报 SSL 错 | `pip install --upgrade pip` 然后重试，或用 `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt`（中国大陆） |
| `npm install` 慢 | 用 `npm install --registry=https://registry.npmmirror.com` |
| `librosa` 安装失败（缺 ffmpeg / soundfile）| macOS: `brew install libsndfile ffmpeg`；Ubuntu: `sudo apt install libsndfile1 ffmpeg`；Windows 通常 `pip install soundfile` 即可 |
| 端口 8000 被占用 | `uvicorn mixmind.api:app --port 8001`，前端 `vite.config.ts` 也改 proxy 端口 |
| 端口 5173 被占用 | `npm run dev -- --port 5174` |
| Pro 视图空白 / 3D 报错 | 确认浏览器支持 WebGL：在地址栏输入 `chrome://gpu` 检查；若旧机器，关闭 3D 仍可用所有功能 |
| 切换语言后某处仍是英文 | 强制刷新（Ctrl+F5），i18n 偶尔需要重载 |
| `音频流 404` | 演示数据生成的 WAV 在 `~/.mixmind/cache/demo_audio/` — 确保此目录可读 |
| Demucs 报 OOM | CPU 模式 fallback：`python -m demucs --device cpu ...` |
| Rekordbox 导入 XML 失败 | 仅支持 Pioneer rekordbox **6.x+**；菜单：偏好设置 → 高级 → rekordbox xml |

---

### 🧪 跑测试套件

```bash
cd backend
source venv/bin/activate

# 用 pytest 跑后端冒烟测试
pip install pytest pytest-asyncio httpx
pytest tests/ -v
```

---

### 📂 演示数据是什么？

`python -m mixmind demo` 生成的 60 首：
- ✅ **真实算法值**：BPM / Camelot / 能量 / LUFS 等都是按风格分布合理生成（不是随机数）
- ✅ **真实节拍网格**：beat_times 是按 BPM 严格生成的 4/4 网格
- ✅ **真实结构点**：intro/drop/breakdown/outro 按 16/32 小节对齐
- ⚠️ **音频文件是 1 秒静默 WAV** — 用于让流接口不报 404，但试听不会有声音
- 📁 默认在 `~/.mixmind/cache/demo_audio/`
- 🗑️ `python -m mixmind demo --clear` 可清除

要听真实音乐 + 看真实分析，就用 `python -m mixmind scan "你的音乐文件夹"`。

---

## English

### 🚀 One-Click Start

#### Windows
1. Install **Python 3.11+**: https://www.python.org/downloads/ (check "Add to PATH")
2. Install **Node.js 20+**: https://nodejs.org/
3. Double-click **`start.bat`** in the repo root

#### macOS / Linux
1. Install **Python 3.11+** and **Node.js 20+**
   - macOS: `brew install python@3.11 node`
   - Ubuntu/Debian: `sudo apt install python3.11 python3.11-venv nodejs npm`
2. Run **`./start.sh`** in the repo root

The launcher will:
- Create a Python virtualenv
- Install all dependencies
- Run a health check
- Seed 60 demo tracks (on first start)
- Start backend API + frontend, open your browser to http://localhost:5173

---

### 🧪 Test Path — fastest route through all 8 Pro modules

Open the app, navigate to **Pro Tools** in the sidebar, then try each module
in this order for maximum demo impact:

1. **🎯 Track ID** — pick a track, click IDENTIFY → see big confidence number + Discogs row
2. **🎚️ Live Mix** — pick a Deck A track → 3 candidate cards slide in, Mix Score counts up, reasons appear as tag pills
3. **📐 Phrase Grid** — pick a track → instantly see colored section ribbon + 32-bar tick marks + suggested mix points
4. **🔥 Hot Cues** — click GENERATE 8 → 8 colored dots animate in along the timeline, each pulsing in its Rekordbox color
5. **🎵 Quality Audit** — click AUDIT TRACK → verdict pill, spectrum bars sweep in, dashed cutoff line + label appear
6. **📡 Trend Radar** — click REFRESH → Beatport charts vs your library; have/missing dual progress bars
7. **💎 AI Stems** — needs `pip install demucs` (~2GB) for real separation
8. **📦 Gig USB Export** — generate a playlist first (in Playlist Builder), then pack to a USB folder

Switch language any time with the **EN / 中文** button at the top of the sidebar — 170+ strings update instantly, choice is persisted in localStorage.

---

### 🛠️ Troubleshooting (English)

| Symptom | Fix |
|---------|-----|
| `python: command not found` | Install Python 3.11+ and add to PATH |
| `pip install` SSL/timeout errors | `pip install --upgrade pip`, retry; or use a closer mirror |
| `librosa` install fails | macOS: `brew install libsndfile ffmpeg`; Ubuntu: `sudo apt install libsndfile1 ffmpeg` |
| Port 8000 in use | `uvicorn mixmind.api:app --port 8001` and edit frontend `vite.config.ts` proxy |
| Port 5173 in use | `npm run dev -- --port 5174` |
| Blank Pro view / 3D errors | Verify WebGL: visit `chrome://gpu` |
| Audio stream 404 | Demo WAVs live under `~/.mixmind/cache/demo_audio/` — ensure that directory is readable |
| Rekordbox import fails | Pioneer rekordbox **6.x+** only; menu: Preferences → Advanced → rekordbox xml |

---

### 📂 What is the demo data?

`python -m mixmind demo` generates 60 tracks with:
- ✅ Real algorithmic values (BPM / Camelot / energy / LUFS in genre-typical ranges)
- ✅ Real 4/4 beat grids generated from BPM
- ✅ Real structural cue points snapped to 16/32-bar boundaries
- ⚠️ 1-second silent WAVs (so audio streaming endpoints work; nothing audible)
- 📁 Stored under `~/.mixmind/cache/demo_audio/`
- 🗑️ Clear with `python -m mixmind demo --clear`

To use real music, run `python -m mixmind scan "/path/to/your/music"`.
