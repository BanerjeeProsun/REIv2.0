import re

class ContentSanitiser:
    def sanitize(self, text: str) -> str:
        # Strip system XML tags that could be used for prompt injection escape
        text = re.sub(r"</?UNTRUSTED_CONTENT[^>]*>", "", text, flags=re.IGNORECASE)
        text = re.sub(r"</?SYSTEM[^>]*>", "", text, flags=re.IGNORECASE)
        
        # Replace unicode directional formatting characters (Right-to-Left Override etc)
        directional_chars = r"[\u202A-\u202E\u2066-\u2069]"
        text = re.sub(directional_chars, "", text)
        
        return text.strip()
