"""
Narration Generator — rewrite Threads posts into video narration
using DeepSeek AI with customizable writing styles.
"""

import json
import logging

import httpx

from .config import settings
from .threads_scraper import ThreadsPost

logger = logging.getLogger(__name__)

STYLE_PROMPTS = {
    "genz": (
        "Bạn là một content creator Gen Z Việt Nam, "
        "nói chuyện rất tự nhiên, hay dùng tiếng lóng, "
        "ngắn gọn, hài hước, đôi khi châm biếm nhẹ. "
        "Hay dùng từ như: vãi, ủa, nè, á, kìa, chill, vibe, slay, "
        "real, bro, bestie, cap, no cap, gì đâu, hông, hông biết. "
        "Dùng cảm xúc mạnh, hay reaction kiểu Gen Z."
    ),
    "professional": (
        "Bạn là một MC tin tức chuyên nghiệp, "
        "giọng điệu nghiêm túc, rõ ràng, khách quan. "
        "Sử dụng ngôn ngữ chuẩn mực, tránh tiếng lóng."
    ),
    "funny": (
        "Bạn là một comedian Việt Nam, "
        "hay nói đùa, chơi chữ, châm biếm hài hước. "
        "Tạo sự bất ngờ và cười cho người xem."
    ),
    "storytelling": (
        "Bạn là một người kể chuyện cuốn hút, "
        "tạo sự hồi hộp, dùng ngôn ngữ miêu tả sinh động, "
        "dẫn dắt người xem qua từng chi tiết."
    ),
    "dramatic": (
        "Bạn là một narrator phong cách dramatic, "
        "giọng điệu mạnh mẽ, nhấn mạnh, tạo kịch tính. "
        "Dùng ngôn ngữ gây ấn tượng mạnh."
    ),
}


def _build_narration_prompt(
    posts: list[ThreadsPost],
    style: str,
    language: str = "vi",
) -> tuple[str, str]:
    """Build system and user prompts for narration generation."""
    style_desc = STYLE_PROMPTS.get(style, STYLE_PROMPTS["genz"])

    system_prompt = f"""{style_desc}

NHIỆM VỤ: Viết narration (lời bình) cho từng bài đăng Threads dưới đây.
Mỗi bài cần 1 đoạn narration ngắn (2-3 câu) để đọc cho video.

QUY TẮC:
- Narration phải tự nhiên như đang nói chuyện, phù hợp để đọc thành giọng nói (TTS)
- Nhắc đến số liệu tương tác (likes, comments) để tạo sự hấp dẫn
- Nhắc đến username để credit tác giả
- Mỗi narration khoảng 15-25 từ, đủ cho 5-8 giây audio
- Viết bằng tiếng Việt
- KHÔNG dùng emoji trong narration (vì TTS sẽ đọc)
- Kết nối các bài viết một cách tự nhiên

OUTPUT FORMAT: Trả về JSON array, mỗi phần tử là một object:
[
    {{
        "post_index": 0,
        "narration": "Lời bình cho bài đăng..."
    }}
]
Chỉ trả về JSON, không thêm text nào khác."""

    posts_text = ""
    for i, post in enumerate(posts):
        posts_text += f"\n--- Bài {i+1} ---\n"
        posts_text += f"Username: @{post.username}\n"
        posts_text += f"Nội dung: {post.content}\n"
        posts_text += f"Likes: {post.likes}, Comments: {post.comments}, Reposts: {post.reposts}\n"

    user_prompt = f"Viết narration cho {len(posts)} bài đăng Threads sau:{posts_text}"

    return system_prompt, user_prompt


async def generate_narrations(
    posts: list[ThreadsPost],
    style: str = "genz",
    language: str = "vi",
) -> list[str]:
    """Generate narration text for each post using DeepSeek AI."""
    if not settings.deepseek_api_key:
        logger.warning("No DeepSeek API key, generating simple narrations")
        return _generate_simple_narrations(posts, style)

    system_prompt, user_prompt = _build_narration_prompt(posts, style, language)

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.deepseek_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.deepseek_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.deepseek_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.8,
                    "max_tokens": 2048,
                    "response_format": {"type": "json_object"},
                },
            )
            response.raise_for_status()
            result = response.json()

        content = result["choices"][0]["message"]["content"]
        narration_data = json.loads(content)

        if isinstance(narration_data, dict) and "narrations" in narration_data:
            narration_data = narration_data["narrations"]
        elif isinstance(narration_data, dict):
            for key in narration_data:
                if isinstance(narration_data[key], list):
                    narration_data = narration_data[key]
                    break

        if isinstance(narration_data, list):
            narrations = []
            for item in narration_data:
                if isinstance(item, dict):
                    narrations.append(item.get("narration", ""))
                elif isinstance(item, str):
                    narrations.append(item)
            while len(narrations) < len(posts):
                idx = len(narrations)
                narrations.append(
                    f"Bài đăng từ {posts[idx].username}, "
                    f"nhận được {posts[idx].likes} lượt thích."
                )
            return narrations[:len(posts)]

    except Exception as e:
        logger.error(f"DeepSeek narration generation failed: {e}")

    return _generate_simple_narrations(posts, style)


def _generate_simple_narrations(
    posts: list[ThreadsPost],
    style: str = "genz",
) -> list[str]:
    """Fallback: generate simple narrations without AI."""
    narrations = []
    for post in posts:
        if style == "genz":
            narration = (
                f"Ủa bài này từ {post.username} viral dữ luôn á! "
                f"{post.likes} likes, {post.comments} bình luận kìa."
            )
        elif style == "professional":
            narration = (
                f"Bài đăng từ tài khoản {post.username} "
                f"đã nhận được {post.likes} lượt thích "
                f"và {post.comments} bình luận."
            )
        elif style == "funny":
            narration = (
                f"Ê xem bài của {post.username} nè, "
                f"{post.likes} người thích cái này luôn!"
            )
        else:
            narration = (
                f"Bài đăng của {post.username} "
                f"với {post.likes} lượt thích."
            )
        narrations.append(narration)

    return narrations
