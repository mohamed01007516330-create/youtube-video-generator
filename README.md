# YouTube Video Generator

AI-powered multilingual YouTube video generator using **DeepSeek AI**, **F5-TTS/Edge-TTS**, and **Remotion**.

## Features

- **Threads-to-Video Pipeline** — Search Threads, auto-generate narration, render Reddit-style videos
- **Pinterest Meme Integration** — Auto-fetch relevant memes from Pinterest and overlay them in videos
- **Web UI Dashboard** — Simple web interface to create videos without coding
- **Customizable Narration Styles** — Gen Z, professional, funny, dramatic, storytelling
- **AI Script Generation** — DeepSeek generates engaging video scripts in any language
- **Multi-Language TTS** — Support for Vietnamese, English, Chinese, Japanese, Korean, and more
- **5 Video Templates** — YouTubeVideo, TrueCrime, Reaction, ThreadsScroll, RedditStyle
- **Professional Video Rendering** — Remotion creates YouTube-optimized videos (1920x1080)
- **Animated Subtitles** — Auto-generated captions with smooth animations
- **Pipeline CLI** — One command from topic to finished video
- **REST API** — FastAPI backend for integration

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- FFmpeg
- DeepSeek API key ([Get one here](https://platform.deepseek.com/api_keys))
- Threads API token (optional, for auto-search — [Setup guide](https://developers.facebook.com/docs/threads/get-started))

### Installation

```bash
# Clone the repository
git clone https://github.com/mohamed01007516330-create/youtube-video-generator.git
cd youtube-video-generator

# Setup environment
cp .env.example .env
# Edit .env and add your DEEPSEEK_API_KEY (and optionally THREADS_ACCESS_TOKEN)

# Install Python dependencies
cd backend
pip install -e .
cd ..

# Install Node.js dependencies (for video rendering)
cd video
npm install
cd ..
```

### Usage

#### Web UI (Recommended)

```bash
cd backend
uvicorn app.main:app --reload --port 8000
# Open http://localhost:8000 in your browser
```

The web UI lets you:
1. Search Threads by keyword OR paste posts manually
2. Choose narration style (Gen Z, professional, funny, etc.)
3. Select voice and video template
4. Click "Tao Video" to generate

#### Threads-to-Video CLI

```bash
# Using manual posts (no API token needed)
python -c "
import asyncio
from backend.app.threads_pipeline import run_threads_pipeline
asyncio.run(run_threads_pipeline(
    manual_posts=[
        {'username': 'user1', 'content': 'Post content here', 'likes': 100},
        {'username': 'user2', 'content': 'Another post', 'likes': 200},
    ],
    style='genz',
    voice='vi_male',
))
"
```

#### Original CLI Pipeline

```bash
# Generate a short English video
python pipeline.py --topic "Introduction to Machine Learning" --language en

# Generate a Vietnamese video
python pipeline.py --topic "Huong dan lap trinh Python" --language vi --duration medium

# Generate script and audio only (skip video rendering)
python pipeline.py --topic "Your Topic" --language en --skip-video
```

#### API Server

```bash
cd backend
uvicorn app.main:app --reload --port 8000

# API endpoints:
# GET  /                          — Web UI Dashboard
# POST /api/threads-pipeline      — Threads-to-Video pipeline (NEW)
# POST /api/generate-script       — Generate video script
# POST /api/generate-tts          — Convert text to speech
# POST /api/generate-video        — Render video
# POST /api/pipeline              — Run full original pipeline
# GET  /api/download/{filename}   — Download output file
# GET  /health                    — Health check
```

## Architecture

```
Threads Search → Fetch Posts → Pinterest Memes (optional) → DeepSeek (Narration) → Edge-TTS (Audio) → Remotion (Video) → MP4
```

### Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Threads Scraper | Playwright / Manual | Fetch posts from Threads |
| Pinterest Scraper | Playwright | Fetch meme images from Pinterest |
| Narration Generator | DeepSeek API | Rewrite content in chosen style |
| TTS Engine | Edge-TTS / F5-TTS | Text-to-speech conversion |
| Video Engine | Remotion (React) | Programmatic video rendering |
| Web UI | HTML/CSS/JS | User-friendly dashboard |
| API Server | FastAPI | REST API endpoints |

### Video Templates

| Template | Description |
|----------|------------|
| `RedditStyleVideo` | Dark theme, Reddit-style post cards with narration (NEW) |
| `ThreadsScrollVideo` | Pastel background, Threads card scroll |
| `YouTubeVideo` | Standard YouTube video with scenes |
| `TrueCrimeVideo` | Crime documentary style with timeline |
| `ReactionVideo` | Review/reaction with emoji bars |

### Narration Styles

| Style | Description |
|-------|------------|
| `genz` | Gen Z Vietnamese slang, casual, humorous |
| `professional` | News anchor style, formal |
| `funny` | Comedian style, jokes and wordplay |
| `dramatic` | Strong emphasis, suspenseful |
| `storytelling` | Engaging narrative, vivid descriptions |

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DEEPSEEK_API_KEY` | Yes (for AI narration) | DeepSeek API key |
| `THREADS_ACCESS_TOKEN` | Optional | Meta Threads API token for auto-search |
| `TTS_ENGINE` | No (default: edge-tts) | TTS engine: "edge-tts" or "f5-tts" |

## Supported Languages

| Code | Language   | TTS Engine |
|------|-----------|------------|
| `en` | English   | Edge-TTS / F5-TTS |
| `vi` | Vietnamese| Edge-TTS / F5-TTS |
| `zh` | Chinese   | Edge-TTS / F5-TTS |
| `ja` | Japanese  | Edge-TTS / F5-TTS |
| `ko` | Korean    | Edge-TTS / F5-TTS |
| `fr` | French    | Edge-TTS |
| `de` | German    | Edge-TTS |
| `es` | Spanish   | Edge-TTS |
| `th` | Thai      | Edge-TTS |
| `id` | Indonesian| Edge-TTS |

## Output

After running the pipeline, you'll find in the `output/` directory:

- `scripts/` — Generated scripts (JSON)
- `audio/` — TTS audio files (MP3/WAV)
- `subtitles.srt` — Subtitle file for YouTube
- `threads_props.json` — Video props for Remotion
- `threads_video.mp4` — Rendered video file

## Development

```bash
# Run backend lint
cd backend && ruff check . && cd ..

# Run video typecheck
cd video && npm run typecheck && cd ..
```

## License

MIT
