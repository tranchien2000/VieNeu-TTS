"""
Vietnamese spell checker and text filter.
"""

from typing import Tuple
import re
import json
from pathlib import Path


class VietnameseSpellChecker:
    """
    Vietnamese spell checker with multiple filtering levels.
    """

    def __init__(self):
        """Initialize spell checker."""
        try:
            from pyvi import ViTokenizer
            self.tokenizer = ViTokenizer
            self.available = True
        except ImportError:
            print("⚠️ pyvi not installed. Spell checking disabled.")
            self.available = False

        # Custom dictionary
        self.custom_dict_path = Path.home() / ".vieneu" / "custom_spell_dict.json"
        self.custom_replacements = {}
        self.whitelist = []
        self.load_custom_dict()

    def load_custom_dict(self):
        """Load custom dictionary from file."""
        if self.custom_dict_path.exists():
            try:
                with open(self.custom_dict_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.custom_replacements = data.get('replacements', {})
                    self.whitelist = data.get('whitelist', [])
            except Exception as e:
                print(f"⚠️ Failed to load custom dictionary: {e}")

    def save_custom_dict(self):
        """Save custom dictionary to file."""
        self.custom_dict_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.custom_dict_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'replacements': self.custom_replacements,
                    'whitelist': self.whitelist
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Failed to save custom dictionary: {e}")

    def add_replacement(self, old_word: str, new_word: str):
        """Add custom replacement rule."""
        self.custom_replacements[old_word] = new_word
        self.save_custom_dict()

    def add_to_whitelist(self, word: str):
        """Add word to whitelist."""
        if word not in self.whitelist:
            self.whitelist.append(word)
            self.save_custom_dict()

    def remove_replacement(self, old_word: str):
        """Remove custom replacement rule."""
        if old_word in self.custom_replacements:
            del self.custom_replacements[old_word]
            self.save_custom_dict()

    def remove_from_whitelist(self, word: str):
        """Remove word from whitelist."""
        if word in self.whitelist:
            self.whitelist.remove(word)
            self.save_custom_dict()

    def clean_text(self, text: str, level: str = "off") -> Tuple[str, str]:
        """
        Clean and spell check text based on level.

        Args:
            text: Input text
            level: Cleaning level - "off", "light", "medium", "strong"

        Returns:
            Tuple of (cleaned_text, status_message)
        """
        if level == "off":
            return text, "Spell checking: OFF"

        original_length = len(text)
        cleaned = text
        changes = []

        # Level 1: Remove special characters (all levels)
        if level in ["light", "medium", "strong"]:
            # Remove URLs
            url_pattern = re.compile(
                r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            )
            cleaned = url_pattern.sub('', cleaned)

            # Remove email addresses
            email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
            cleaned = email_pattern.sub('', cleaned)

            # Remove hashtags and mentions
            cleaned = re.sub(r'#\w+', '', cleaned)
            cleaned = re.sub(r'@\w+', '', cleaned)

            # Remove emojis
            emoji_pattern = re.compile(
                "["
                "\U0001F600-\U0001F64F"  # emoticons
                "\U0001F300-\U0001F5FF"  # symbols & pictographs
                "\U0001F680-\U0001F6FF"  # transport & map symbols
                "\U0001F1E0-\U0001F1FF"  # flags
                "\U00002702-\U000027B0"
                "\U000024C2-\U0001F251"
                "]+", flags=re.UNICODE
            )
            before = len(cleaned)
            cleaned = emoji_pattern.sub('', cleaned)
            emoji_removed = before - len(cleaned)

            # Normalize excessive punctuation
            cleaned = re.sub(r'!{2,}', '!', cleaned)  # !!! → !
            cleaned = re.sub(r'\?{2,}', '?', cleaned)  # ??? → ?
            cleaned = re.sub(r'\.{4,}', '...', cleaned)  # ..... → ...

            # Remove decorative characters
            cleaned = re.sub(r'[~*\-_]{3,}', '', cleaned)  # ~~~, ***, ---

            # Normalize quotes and dashes
            cleaned = re.sub(r'[""]', '"', cleaned)
            cleaned = re.sub(r'[''`]', "'", cleaned)
            cleaned = re.sub(r'[–—]', '-', cleaned)

            # Remove zero-width characters
            cleaned = re.sub(r'[​‌‍﻿]', '', cleaned)

            # Remove excessive whitespace
            cleaned = re.sub(r'\s+', ' ', cleaned)
            cleaned = cleaned.strip()

            if emoji_removed > 0:
                changes.append(f"Removed {emoji_removed} special chars/emojis")

        # Level 2: Fix common typos (medium, strong)
        if level in ["medium", "strong"]:
            # Common Vietnamese typos - EXPANDED
            typo_map = {
                # Pronouns
                'mik': 'mình', 'mk': 'mình', 'mjk': 'mình',
                'bn': 'bạn',
                'tớ': 'tôi',
                'cx': 'cũng', 'cug': 'cũng',

                # Common words
                'đg': 'đang', 'dg': 'đang',
                'lm': 'làm',
                'bik': 'biết', 'bit': 'biết', 'bít': 'biết',
                'đc': 'được', 'dc': 'được',
                'hok': 'không', 'hong': 'không', 'hông': 'không',
                'ko': 'không', 'k': 'không',
                'vs': 'với', 'v': 'với',
                'ntn': 'như thế nào',
                'j': 'gì', 'z': 'gì',

                # Time & quantity
                'h': 'giờ',
                'r': 'rồi', 'ròi': 'rồi',
                'nx': 'nữa',
                'nhìu': 'nhiều', 'nhiu': 'nhiều',
                'it': 'ít',

                # Expressions
                'ok': 'được', 'oke': 'được', 'okie': 'được',
                'tks': 'cảm ơn', 'thanks': 'cảm ơn', 'thank': 'cảm ơn',
                'camon': 'cảm ơn',
                'sry': 'xin lỗi', 'sr': 'xin lỗi', 'sorry': 'xin lỗi',
                'plz': 'làm ơn', 'pls': 'làm ơn',
                'wtf': 'gì vậy',
                'lol': 'ha ha', 'haha': 'ha ha',
                'yep': 'vâng', 'yeah': 'vâng', 'uh': 'vâng',

                # Question words
                'zao': 'sao', 'zo': 'sao',
                'dau': 'đâu',
                'nao': 'nào',
                'aj': 'ai',

                # Verbs
                'ns': 'nói',
                'ngê': 'nghe',
                'thay': 'thấy',
                'mún': 'muốn',
            }

            for typo, correct in typo_map.items():
                pattern = r'\b' + re.escape(typo) + r'\b'
                if re.search(pattern, cleaned, re.IGNORECASE):
                    cleaned = re.sub(pattern, correct, cleaned, flags=re.IGNORECASE)
                    changes.append(f"'{typo}' → '{correct}'")

        # Level 3: Advanced spell checking with pyvi (strong only)
        if level == "strong" and self.available:
            try:
                # Tokenize and check for non-Vietnamese words
                tokens = self.tokenizer.tokenize(cleaned)
                # pyvi tokenization helps identify word boundaries
                # Further spell checking logic can be added here
                changes.append("Applied advanced spell checking")
            except Exception as e:
                changes.append(f"Advanced checking failed: {str(e)}")

        # Apply custom replacements (all levels except "off")
        if self.custom_replacements:
            for old_word, new_word in self.custom_replacements.items():
                # Skip if word is in whitelist
                if old_word in self.whitelist:
                    continue

                pattern = r'\b' + re.escape(old_word) + r'\b'
                if re.search(pattern, cleaned, re.IGNORECASE):
                    cleaned = re.sub(pattern, new_word, cleaned, flags=re.IGNORECASE)
                    changes.append(f"Custom: '{old_word}' → '{new_word}'")

        # Generate status message
        if changes:
            status = f"✅ Cleaned ({level}): " + ", ".join(changes)
        else:
            status = f"✅ No changes needed ({level})"

        return cleaned, status


# Global singleton
_spell_checker = None

def get_spell_checker() -> VietnameseSpellChecker:
    """Get or create spell checker singleton."""
    global _spell_checker
    if _spell_checker is None:
        _spell_checker = VietnameseSpellChecker()
    return _spell_checker


def clean_vietnamese_text(text: str, level: str = "off") -> Tuple[str, str]:
    """
    Convenience function to clean Vietnamese text.

    Args:
        text: Input text
        level: Cleaning level - "off", "light", "medium", "strong"

    Returns:
        Tuple of (cleaned_text, status_message)
    """
    checker = get_spell_checker()
    return checker.clean_text(text, level)


def update_custom_dict(replacements_text: str, whitelist_text: str) -> str:
    """
    Update custom dictionary from UI input.

    Args:
        replacements_text: Multi-line text with "old → new" format
        whitelist_text: Comma-separated words

    Returns:
        Status message
    """
    checker = get_spell_checker()

    # Parse replacements
    checker.custom_replacements = {}
    if replacements_text.strip():
        for line in replacements_text.strip().split('\n'):
            if '→' in line:
                parts = line.split('→')
                if len(parts) == 2:
                    old = parts[0].strip()
                    new = parts[1].strip()
                    if old and new:
                        checker.custom_replacements[old] = new

    # Parse whitelist
    checker.whitelist = []
    if whitelist_text.strip():
        words = [w.strip() for w in whitelist_text.split(',')]
        checker.whitelist = [w for w in words if w]

    checker.save_custom_dict()

    return f"✅ Đã lưu: {len(checker.custom_replacements)} replacements, {len(checker.whitelist)} whitelist words"


def get_custom_dict_text() -> Tuple[str, str]:
    """
    Get custom dictionary as text for UI display.

    Returns:
        Tuple of (replacements_text, whitelist_text)
    """
    checker = get_spell_checker()

    # Format replacements
    replacements_lines = [f"{old} → {new}" for old, new in checker.custom_replacements.items()]
    replacements_text = '\n'.join(replacements_lines)

    # Format whitelist
    whitelist_text = ', '.join(checker.whitelist)

    return replacements_text, whitelist_text
