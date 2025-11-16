import re
import unicodedata
from pypinyin import slug, Style

def slugify(text: str) -> str:
    """
    Converts text into a URL-friendly slug.
    Handles ASCII text, accented characters, and Chinese characters (converts to pinyin).

    Examples:
    - "My Python Course" -> "my-python-course"
    - "Learn Python!" -> "learn-python"
    - "数据结构与算法" -> "shu-ju-jie-gou-yu-suan-fa"
    """
    if text is None:
        raise ValueError("text cannot be None")

    # Convert Chinese characters to pinyin first
    text = slug(text, separator="-", style=Style.NORMAL)

    # Normalize unicode characters (handles accented characters)
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')

    # Convert to lowercase and replace non-alphanumeric characters with hyphens
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)

    # Remove leading/trailing hyphens
    text = text.strip('-')

    # Limit length to 100 characters
    if len(text) > 100:
        text = text[:100].rstrip('-')

    return text or 'untitled'
