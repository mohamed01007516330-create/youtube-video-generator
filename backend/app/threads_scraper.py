"""
Threads Scraper — fetch posts from Threads via official API or manual input.

Supports:
1. Official Meta Threads API (requires THREADS_ACCESS_TOKEN)
2. Manual input (user pastes post content directly)
"""

import logging
from dataclasses import dataclass

import httpx

from .config import settings

logger = logging.getLogger(__name__)


@dataclass
class ThreadsPost:
    username: str
    content: str
    likes: int = 0
    comments: int = 0
    reposts: int = 0
    time_ago: str = ""
    permalink: str = ""
    avatar_emoji: str = ""
    avatar_color: str = "#6366f1"
    media_url: str = ""


async def search_threads_api(
    query: str,
    limit: int = 7,
    search_type: str = "TOP",
) -> list[ThreadsPost]:
    """Search Threads using the official Meta Threads API."""
    access_token = settings.threads_access_token
    if not access_token:
        raise ValueError(
            "THREADS_ACCESS_TOKEN is required for Threads API search. "
            "Set it in your .env file or use manual input mode."
        )

    fields = "id,text,timestamp,username,permalink,like_count"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            "https://graph.threads.net/keyword_search",
            params={
                "q": query,
                "search_type": search_type,
                "fields": fields,
                "access_token": access_token,
                "limit": limit,
            },
        )
        response.raise_for_status()
        data = response.json()

    posts: list[ThreadsPost] = []
    avatars = ["🐸", "🔥", "💅", "🎨", "📚", "👒", "💪", "🎯", "✨", "🚀"]
    colors = [
        "#e94560", "#3b82f6", "#a855f7", "#f59e0b",
        "#06b6d4", "#ec4899", "#f97316", "#10b981",
    ]

    for i, item in enumerate(data.get("data", [])[:limit]):
        posts.append(
            ThreadsPost(
                username=item.get("username", f"user{i+1}"),
                content=item.get("text", ""),
                likes=item.get("like_count", 0),
                time_ago=_format_time_ago(item.get("timestamp", "")),
                permalink=item.get("permalink", ""),
                avatar_emoji=avatars[i % len(avatars)],
                avatar_color=colors[i % len(colors)],
            )
        )

    logger.info(f"Threads API: found {len(posts)} posts for query '{query}'")
    return posts


def parse_manual_posts(posts_data: list[dict]) -> list[ThreadsPost]:
    """Parse manually provided post data."""
    avatars = ["🐸", "🔥", "💅", "🎨", "📚", "👒", "💪", "🎯", "✨", "🚀"]
    colors = [
        "#e94560", "#3b82f6", "#a855f7", "#f59e0b",
        "#06b6d4", "#ec4899", "#f97316", "#10b981",
    ]

    posts: list[ThreadsPost] = []
    for i, p in enumerate(posts_data):
        posts.append(
            ThreadsPost(
                username=p.get("username", f"user{i+1}"),
                content=p.get("content", ""),
                likes=p.get("likes", 0),
                comments=p.get("comments", 0),
                reposts=p.get("reposts", 0),
                time_ago=p.get("time_ago", f"{i+1} giờ"),
                permalink=p.get("permalink", ""),
                avatar_emoji=p.get("avatar_emoji", avatars[i % len(avatars)]),
                avatar_color=p.get("avatar_color", colors[i % len(colors)]),
                media_url=p.get("media_url", ""),
            )
        )

    return posts


async def fetch_threads_posts(
    query: str = "",
    limit: int = 7,
    search_type: str = "TOP",
    manual_posts: list[dict] | None = None,
) -> list[ThreadsPost]:
    """
    Fetch Threads posts — tries API first, falls back to manual input.
    """
    if manual_posts:
        logger.info(f"Using {len(manual_posts)} manually provided posts")
        return parse_manual_posts(manual_posts)

    if settings.threads_access_token:
        try:
            return await search_threads_api(query, limit, search_type)
        except Exception as e:
            logger.warning(f"Threads API failed: {e}, no fallback available")
            raise

    raise ValueError(
        "No Threads data source available. Either:\n"
        "1. Set THREADS_ACCESS_TOKEN in .env for API access\n"
        "2. Provide posts manually via manual_posts parameter"
    )


def _format_time_ago(timestamp: str) -> str:
    """Convert ISO timestamp to Vietnamese time ago string."""
    if not timestamp:
        return ""
    try:
        from datetime import datetime, timezone

        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = now - dt
        hours = int(diff.total_seconds() / 3600)
        if hours < 1:
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes} phút"
        if hours < 24:
            return f"{hours} giờ"
        days = int(hours / 24)
        return f"{days} ngày"
    except (ValueError, TypeError):
        return ""
