"""
Threads Scraper — automatically fetch posts from Threads search.

Priority order:
1. Playwright web scraping (default, no token needed)
2. Official Meta Threads API (if THREADS_ACCESS_TOKEN is set)
3. Manual input (user pastes post content)
"""

import logging
from dataclasses import dataclass

import httpx

from .config import settings

logger = logging.getLogger(__name__)

AVATARS = ["🐸", "🔥", "💅", "🎨", "📚", "👒", "💪", "🎯", "✨", "🚀"]
COLORS = [
    "#e94560", "#3b82f6", "#a855f7", "#f59e0b",
    "#06b6d4", "#ec4899", "#f97316", "#10b981",
]


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


async def scrape_threads_playwright(
    query: str,
    limit: int = 10,
) -> list[ThreadsPost]:
    """Scrape Threads search results using Playwright (headless browser)."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise RuntimeError(
            "Playwright is required for auto-scraping. "
            "Install: pip install playwright && playwright install chromium"
        )

    logger.info(f"Scraping Threads for: '{query}' (limit={limit})")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 900})

        try:
            url = f"https://www.threads.com/search?q={query}&serp_type=default"
            await page.goto(url, timeout=30000)
            await page.wait_for_timeout(3000)

            # Dismiss login modal
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(500)

            # Scroll to load more posts
            scroll_count = max(2, limit // 4)
            for _ in range(scroll_count):
                await page.mouse.wheel(0, 800)
                await page.wait_for_timeout(1500)

            # Extract posts from DOM
            raw_posts = await page.evaluate(
                """(maxPosts) => {
                const results = [];
                const containers = document.querySelectorAll(
                    'div[data-pressable-container="true"]'
                );

                for (const container of containers) {
                    if (results.length >= maxPosts) break;

                    const userLinks = container.querySelectorAll('a[href*="/@"]');
                    let username = '';
                    let timeAgo = '';
                    let permalink = '';

                    for (const link of userLinks) {
                        const text = link.textContent?.trim();
                        const href = link.getAttribute('href') || '';

                        if (text && !username && /\\/@[^/]+$/.test(href)) {
                            username = text;
                        }
                        if (href.includes('/post/')) {
                            permalink = 'https://www.threads.com' + href;
                            timeAgo = link.textContent?.trim() || '';
                        }
                    }

                    if (!username) continue;

                    // Extract post text content
                    const allSpans = container.querySelectorAll('span');
                    let content = '';
                    for (const span of allSpans) {
                        const text = span.textContent?.trim();
                        if (
                            text &&
                            text !== username &&
                            text !== timeAgo &&
                            !/^\\d+$/.test(text) &&
                            text !== 'Translate' &&
                            text !== 'Verified' &&
                            text.length > 10
                        ) {
                            if (!content || text.length > content.length) {
                                content = text;
                            }
                        }
                    }

                    // Extract engagement numbers
                    const nums = [];
                    for (const s of allSpans) {
                        const t = s.textContent?.trim();
                        if (t && /^[\\d,.]+[KkMm]?$/.test(t)) {
                            let val = parseFloat(t.replace(/,/g, ''));
                            if (/[Kk]$/.test(t)) val *= 1000;
                            if (/[Mm]$/.test(t)) val *= 1000000;
                            if (val > 0) nums.push(Math.round(val));
                        }
                    }

                    if (content) {
                        results.push({
                            username,
                            content,
                            timeAgo,
                            permalink,
                            likes: nums[0] || 0,
                            comments: nums[1] || 0,
                            reposts: nums[2] || 0,
                        });
                    }
                }

                return results;
            }""",
                limit,
            )

        finally:
            await browser.close()

    posts: list[ThreadsPost] = []
    for i, raw in enumerate(raw_posts[:limit]):
        posts.append(
            ThreadsPost(
                username=raw["username"],
                content=raw["content"],
                likes=raw.get("likes", 0),
                comments=raw.get("comments", 0),
                reposts=raw.get("reposts", 0),
                time_ago=raw.get("timeAgo", ""),
                permalink=raw.get("permalink", ""),
                avatar_emoji=AVATARS[i % len(AVATARS)],
                avatar_color=COLORS[i % len(COLORS)],
            )
        )

    logger.info(f"Playwright scraper: found {len(posts)} posts for '{query}'")
    return posts


async def search_threads_api(
    query: str,
    limit: int = 10,
    search_type: str = "TOP",
) -> list[ThreadsPost]:
    """Search Threads using the official Meta Threads API."""
    access_token = settings.threads_access_token
    if not access_token:
        raise ValueError("THREADS_ACCESS_TOKEN is required for API search.")

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
    for i, item in enumerate(data.get("data", [])[:limit]):
        posts.append(
            ThreadsPost(
                username=item.get("username", f"user{i+1}"),
                content=item.get("text", ""),
                likes=item.get("like_count", 0),
                time_ago=_format_time_ago(item.get("timestamp", "")),
                permalink=item.get("permalink", ""),
                avatar_emoji=AVATARS[i % len(AVATARS)],
                avatar_color=COLORS[i % len(COLORS)],
            )
        )

    logger.info(f"Threads API: found {len(posts)} posts for '{query}'")
    return posts


def parse_manual_posts(posts_data: list[dict]) -> list[ThreadsPost]:
    """Parse manually provided post data."""
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
                avatar_emoji=p.get("avatar_emoji", AVATARS[i % len(AVATARS)]),
                avatar_color=p.get("avatar_color", COLORS[i % len(COLORS)]),
                media_url=p.get("media_url", ""),
            )
        )
    return posts


async def fetch_threads_posts(
    query: str = "",
    limit: int = 10,
    search_type: str = "TOP",
    manual_posts: list[dict] | None = None,
) -> list[ThreadsPost]:
    """
    Fetch Threads posts — auto-scrape by default.

    Priority:
    1. Manual posts (if provided)
    2. Playwright web scraper (default, no token needed)
    3. Threads API (if THREADS_ACCESS_TOKEN is set)
    """
    if manual_posts:
        logger.info(f"Using {len(manual_posts)} manually provided posts")
        return parse_manual_posts(manual_posts)

    if not query:
        raise ValueError("Search query is required for auto-scraping.")

    # Try Playwright scraping first (no token needed)
    try:
        return await scrape_threads_playwright(query, limit)
    except RuntimeError as e:
        logger.warning(f"Playwright not available: {e}")
    except Exception as e:
        logger.warning(f"Playwright scraping failed: {e}")

    # Fallback to Threads API if token available
    if settings.threads_access_token:
        try:
            return await search_threads_api(query, limit, search_type)
        except Exception as e:
            logger.warning(f"Threads API also failed: {e}")

    raise RuntimeError(
        "Could not fetch Threads posts. Ensure Playwright is installed: "
        "pip install playwright && playwright install chromium"
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
