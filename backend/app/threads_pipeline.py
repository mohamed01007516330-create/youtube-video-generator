"""
Threads-to-Video Pipeline — end-to-end flow:
Search Threads → Fetch Posts → Generate Narration → TTS → Render Video
"""

import json
import logging
import shutil
import subprocess
from dataclasses import asdict
from pathlib import Path

from .config import settings
from .narration_generator import generate_narrations
from .pinterest_scraper import scrape_pinterest_memes
from .threads_scraper import ThreadsPost, fetch_threads_posts
from .tts_service import synthesize_edge_tts

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
VIDEO_DIR = PROJECT_ROOT / "video"
OUTPUT_DIR = Path(settings.output_dir)

VOICE_MAP = {
    "vi_male": "vi-VN-NamMinhNeural",
    "vi_female": "vi-VN-HoaiMyNeural",
    "en_male": "en-US-GuyNeural",
    "en_female": "en-US-AriaNeural",
}


async def generate_audio_for_posts(
    narrations: list[str],
    language: str = "vi",
    voice_key: str = "vi_male",
) -> tuple[list[str], list[float]]:
    """Generate TTS audio for each narration."""
    public_audio_dir = VIDEO_DIR / "public" / "audio"
    public_audio_dir.mkdir(parents=True, exist_ok=True)

    voice = VOICE_MAP.get(voice_key, VOICE_MAP["vi_male"])
    audio_files: list[str] = []
    durations: list[float] = []

    for i, narration in enumerate(narrations):
        logger.info(f"  Generating audio {i+1}/{len(narrations)}...")
        audio_file, duration = await synthesize_edge_tts(
            text=narration,
            language=language,
            voice=voice,
        )
        filename = Path(audio_file).name
        public_path = public_audio_dir / filename
        shutil.copy2(audio_file, public_path)
        audio_files.append(f"audio/{filename}")
        durations.append(duration)
        logger.info(f"    Audio: {filename} ({duration:.1f}s)")

    return audio_files, durations


def render_threads_video(
    posts: list[ThreadsPost],
    narrations: list[str],
    audio_files: list[str],
    durations: list[float],
    composition: str = "RedditStyleVideo",
    background_music: str = "",
    background_music_volume: float = 0.12,
    output_filename: str = "threads_video.mp4",
) -> str:
    """Render video using Remotion."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    posts_data = []
    for i, post in enumerate(posts):
        post_data = {
            "username": post.username,
            "timeAgo": post.time_ago or f"{i+1} giờ",
            "content": post.content,
            "likes": post.likes,
            "comments": post.comments,
            "reposts": post.reposts,
            "avatarEmoji": post.avatar_emoji,
            "avatarColor": post.avatar_color,
            "narration": narrations[i] if i < len(narrations) else "",
            "audioFile": audio_files[i] if i < len(audio_files) else "",
            "durationInSeconds": max((durations[i] if i < len(durations) else 6.0) + 2.0, 6.0),
        }
        if post.media_url:
            post_data["postImage"] = post.media_url
        if post.meme_image:
            post_data["memeImage"] = post.meme_image
        posts_data.append(post_data)

    total_duration = sum(p["durationInSeconds"] for p in posts_data) + 5

    props = {
        "posts": posts_data,
        "totalDurationInSeconds": total_duration,
        "fps": settings.video_fps,
        "width": settings.video_width,
        "height": settings.video_height,
    }

    if background_music:
        props["backgroundMusic"] = background_music
        props["backgroundMusicVolume"] = background_music_volume

    props_file = str(OUTPUT_DIR / "threads_props.json")
    with open(props_file, "w", encoding="utf-8") as f:
        json.dump(props, f, ensure_ascii=False, indent=2)

    output_file = str(OUTPUT_DIR / output_filename)

    logger.info(f"Rendering {composition} with {len(posts_data)} posts...")
    logger.info(f"Total duration: {total_duration:.1f}s")

    result = subprocess.run(
        [
            "npx", "remotion", "render",
            composition,
            "--props", props_file,
            "--output", output_file,
            "--codec", "h264",
        ],
        cwd=str(VIDEO_DIR),
        capture_output=True,
        text=True,
        timeout=900,
    )

    if result.returncode != 0:
        logger.error(f"Render error: {result.stderr}")
        raise RuntimeError(f"Video rendering failed: {result.stderr}")

    logger.info(f"Video rendered: {output_file}")
    return output_file


async def run_threads_pipeline(
    query: str = "",
    limit: int = 7,
    style: str = "genz",
    voice: str = "vi_male",
    language: str = "vi",
    manual_posts: list[dict] | None = None,
    composition: str = "RedditStyleVideo",
    background_music: str = "",
    output_filename: str = "threads_video.mp4",
    skip_video: bool = False,
    include_memes: bool = False,
    meme_keyword: str = "",
) -> dict:
    """
    Run the full Threads-to-Video pipeline.

    Returns dict with: posts, narrations, audio_files, video_file
    """
    logger.info("=" * 60)
    logger.info("THREADS-TO-VIDEO PIPELINE")
    logger.info("=" * 60)

    # Step 1: Fetch posts
    logger.info("STEP 1: Fetching Threads posts...")
    posts = await fetch_threads_posts(
        query=query, limit=limit, manual_posts=manual_posts
    )
    logger.info(f"  Found {len(posts)} posts")

    # Step 1.5: Fetch memes from Pinterest (if enabled)
    if include_memes:
        meme_query = meme_keyword or query or "funny"
        logger.info(f"STEP 1.5: Fetching memes from Pinterest ('{meme_query}')...")
        meme_images = await scrape_pinterest_memes(
            query=meme_query, limit=len(posts)
        )
        logger.info(f"  Found {len(meme_images)} meme images")
        for i, post in enumerate(posts):
            if i < len(meme_images):
                post.meme_image = meme_images[i]
    else:
        logger.info("Memes: disabled")

    # Step 2: Generate narrations
    logger.info(f"STEP 2: Generating narrations (style: {style})...")
    narrations = await generate_narrations(posts, style=style, language=language)
    for i, n in enumerate(narrations):
        logger.info(f"  [{i+1}] {n[:80]}...")

    # Step 3: Generate audio
    logger.info("STEP 3: Generating TTS audio...")
    audio_files, durations = await generate_audio_for_posts(
        narrations, language=language, voice_key=voice
    )

    result = {
        "posts": [asdict(p) for p in posts],
        "narrations": narrations,
        "audio_files": audio_files,
        "durations": durations,
        "video_file": "",
    }

    # Step 4: Render video
    if skip_video:
        logger.info("STEP 4: Skipping video render (--skip-video)")
    else:
        logger.info("STEP 4: Rendering video...")
        video_file = render_threads_video(
            posts=posts,
            narrations=narrations,
            audio_files=audio_files,
            durations=durations,
            composition=composition,
            background_music=background_music,
            output_filename=output_filename,
        )
        result["video_file"] = video_file

    logger.info("=" * 60)
    logger.info("PIPELINE COMPLETE!")
    logger.info("=" * 60)

    return result
