"""
Pinterest Meme Scraper — fetch meme images from Pinterest search.

Uses Playwright (headless browser) to scrape Pinterest image results
without requiring any API key or login.
"""

import hashlib
import logging
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
MEME_DIR = PROJECT_ROOT / "video" / "public" / "memes"


async def scrape_pinterest_memes(
    query: str,
    limit: int = 5,
) -> list[str]:
    """
    Scrape meme images from Pinterest search.

    Returns list of local file paths (relative to video/public/)
    that can be used as staticFile() in Remotion.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.warning("Playwright not installed, skipping meme scrape")
        return []

    MEME_DIR.mkdir(parents=True, exist_ok=True)

    search_query = f"{query} meme funny"
    logger.info(f"Scraping Pinterest for: '{search_query}' (limit={limit})")

    image_urls: list[str] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 900})

        try:
            url = f"https://www.pinterest.com/search/pins/?q={search_query}"
            await page.goto(url, timeout=30000)
            await page.wait_for_timeout(3000)

            # Close any signup modals
            try:
                close_btn = page.locator('[aria-label="close"], [data-test-id="close-button"]')
                if await close_btn.count() > 0:
                    await close_btn.first.click()
                    await page.wait_for_timeout(500)
            except Exception:
                pass

            # Scroll to load more images
            for _ in range(3):
                await page.mouse.wheel(0, 800)
                await page.wait_for_timeout(1500)

            # Extract image URLs from pins
            image_urls = await page.evaluate(
                """(maxImages) => {
                const urls = [];
                const seen = new Set();

                // Pinterest uses <img> tags inside pin containers
                const images = document.querySelectorAll('img[src*="pinimg.com"]');

                for (const img of images) {
                    if (urls.length >= maxImages) break;

                    let src = img.src || '';
                    // Skip tiny thumbnails
                    if (src.includes('/75x/') || src.includes('/60x/')) continue;

                    // Upgrade to higher resolution if possible
                    src = src.replace(/\\/\\d+x\\//g, '/564x/');

                    if (src && !seen.has(src)) {
                        seen.add(src);
                        urls.push(src);
                    }
                }

                return urls;
            }""",
                limit,
            )

            logger.info(f"Found {len(image_urls)} meme images from Pinterest")
        except Exception as e:
            logger.warning(f"Pinterest scrape failed: {e}")
        finally:
            await browser.close()

    # Download images locally
    local_paths: list[str] = []
    async with httpx.AsyncClient(timeout=15.0) as client:
        for i, img_url in enumerate(image_urls[:limit]):
            try:
                resp = await client.get(img_url)
                if resp.status_code != 200:
                    continue

                # Generate filename from URL hash
                url_hash = hashlib.md5(img_url.encode()).hexdigest()[:10]
                ext = ".jpg"
                if "png" in img_url:
                    ext = ".png"
                filename = f"meme_{url_hash}{ext}"
                filepath = MEME_DIR / filename

                filepath.write_bytes(resp.content)
                rel_path = f"memes/{filename}"
                local_paths.append(rel_path)
                logger.info(f"  Downloaded meme {i+1}: {filename}")
            except Exception as e:
                logger.warning(f"  Failed to download meme {i+1}: {e}")

    return local_paths
