import re
from settings import SUPPORTED_CONTENT_TYPES


class TelegramParser:
    @staticmethod
    def extract_content(text, content_type="images"):
        if content_type not in SUPPORTED_CONTENT_TYPES:
            raise ValueError(f"Unsupported content type: {content_type}")

        extensions = "|".join(SUPPORTED_CONTENT_TYPES[content_type])
        pattern = rf'https?://[^\s]+?\.(?:{extensions})(?:\?[^\s]*)?'
        return re.findall(pattern, text, re.IGNORECASE)

    @staticmethod
    def extract_text(text):
        # Simple text extraction - can be enhanced for Telegram-specific formatting
        text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags
        text = re.sub(r'\s+', ' ', text).strip()
        return text