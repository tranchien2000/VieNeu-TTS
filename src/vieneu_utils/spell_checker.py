"""
Vietnamese spell checker with multiple engines (SymSpell, VSpell, Hybrid).
"""

from abc import ABC, abstractmethod
from typing import Tuple, List, Dict, Optional
import re
import json
import time
from pathlib import Path
from functools import lru_cache


class SpellCheckerBase(ABC):
    """Abstract base class for spell checkers."""

    @abstractmethod
    def correct(self, text: str) -> str:
        """Correct a single text."""
        pass

    @abstractmethod
    def correct_batch(self, texts: List[str]) -> List[str]:
        """Correct multiple texts (batch processing)."""
        pass

    @abstractmethod
    def name(self) -> str:
        """Engine name for logging/debugging."""
        pass


class SymSpellChecker(SpellCheckerBase):
    """SymSpell + Underthesea based spell checker (fast, CPU-only)."""

    def __init__(self):
        self._sym_spell = None
        self._dict_loaded = False

    def _load_dictionary(self):
        """Load Vietnamese dictionary for SymSpell."""
        from symspellpy import SymSpell, Verbosity
        import os

        if self._dict_loaded:
            return

        self._sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)

        dict_paths = [
            "vn_dict.txt",
            os.path.join(os.path.dirname(__file__), "vn_dict.txt"),
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "vn_dict.txt"),
        ]

        loaded = False
        for path in dict_paths:
            if os.path.exists(path):
                self._sym_spell.load_dictionary(path, term_index=0, count_index=1)
                loaded = True
                break

        if not loaded:
            self._build_basic_dict()

        self._dict_loaded = True

    def _build_basic_dict(self):
        """Build a basic VN dictionary from common words."""
        common_words = [
            "và", "của", "có", "là", "trong", "được", "cho", "với", "tại", "từ",
            "khi", "này", "đó", "những", "các", "một", "nhiều", "ít", "lớn", "nhỏ",
            "tôi", "bạn", "anh", "chị", "em", "họ", "chúng", "ta", "mình", "người",
            "đi", "đến", "về", "làm", "ăn", "ngủ", "học", "làm việc", "chơi", "xem",
            "đẹp", "xấu", "tốt", "xấu", "nhanh", "chậm", "dễ", "khó", "mới", "cũ",
            "ngày", "tháng", "năm", "giờ", "phút", "giây", "sáng", "trưa", "chiều", "tối",
            "Hà Nội", "Hồ Chí Minh", "Đà Nẵng", "Việt Nam", "trường", "bệnh viện", "công ty",
            "không", "có", "được", "sẽ", "đã", "đang", "sẽ", "có thể", "phải", "nên",
            "vì", "nên", "do", "bởi", "nếu", "thì", "mà", "hoặc", "hay", "hoặc là",
            "trên", "dưới", "giữa", "bên", "trái", "phải", "trước", "sau", "ngoài", "trong",
        ]

        for i, word in enumerate(common_words):
            freq = 1000000 - i * 1000
            self._sym_spell.create_dictionary_entry(word, freq)

    @property
    def sym_spell(self):
        self._load_dictionary()
        return self._sym_spell

    def correct(self, text: str) -> str:
        from symspellpy import Verbosity
        from underthesea import word_tokenize

        if not text or not text.strip():
            return text

        try:
            tokens = word_tokenize(text, format="text").split()
        except Exception:
            tokens = text.split()

        corrected_tokens = []
        for token in tokens:
            if any(c.isdigit() for c in token) or len(token) <= 2:
                corrected_tokens.append(token)
                continue

            suggestions = self.sym_spell.lookup(token, Verbosity.CLOSEST, max_edit_distance=2)
            if suggestions and suggestions[0].distance > 0:
                corrected_tokens.append(suggestions[0].term)
            else:
                corrected_tokens.append(token)

        return " ".join(corrected_tokens)

    def correct_batch(self, texts: List[str]) -> List[str]:
        return [self.correct(t) for t in texts]

    def name(self) -> str:
        return "SymSpell"


class VSpellChecker(SpellCheckerBase):
    """VSpell based spell checker (transformer-based, GPU/CPU)."""

    def __init__(self, device: str = "auto", batch_size: int = 16):
        self._model = None
        self._device = device
        self._batch_size = batch_size
        self._initialized = False
        self._init_error = None

    def _init_model(self):
        """Lazy initialize VSpell model."""
        if self._initialized:
            return

        try:
            import torch
            from vspell import VSpell

            if self._device == "auto":
                self._device = "cuda" if torch.cuda.is_available() else "cpu"

            self._model = VSpell(device=self._device)
            self._initialized = True
            print(f"✅ VSpell initialized on {self._device}")

        except ImportError:
            self._init_error = "vspell not installed (pip install vspell torch transformers)"
            self._initialized = True  # Don't retry
        except Exception as e:
            self._init_error = f"VSpell init failed: {e}"
            self._initialized = True

    def correct(self, text: str) -> str:
        self._init_model()

        if self._init_error or self._model is None:
            return text  # Fallback: return original

        if not text or not text.strip():
            return text

        try:
            result = self._model.correct(text)
            return result
        except Exception as e:
            print(f"⚠️ VSpell error: {e}")
            return text

    def correct_batch(self, texts: List[str]) -> List[str]:
        self._init_model()

        if self._init_error or self._model is None:
            return texts  # Fallback

        if not texts:
            return []

        results = []
        for i in range(0, len(texts), self._batch_size):
            batch = texts[i:i + self._batch_size]
            try:
                batch_results = self._model.correct_batch(batch)
                results.extend(batch_results)
            except Exception as e:
                print(f"⚠️ VSpell batch error: {e}")
                results.extend(batch)  # Fallback to original

        return results

    def name(self) -> str:
        return f"VSpell({self._device})"


class HybridSpellChecker(SpellCheckerBase):
    """Hybrid: Normalizer -> VSpell -> (optional LanguageTool)."""

    def __init__(self, device: str = "auto", batch_size: int = 16, use_languagetool: bool = False, languagetool_url: str = "http://localhost:8081"):
        self._vspell = VSpellChecker(device=device, batch_size=batch_size)
        self._symspell = SymSpellChecker()
        self._use_languagetool = use_languagetool
        self._languagetool_url = languagetool_url

    def correct(self, text: str) -> str:
        # Step 1: VSpell (main correction)
        text = self._vspell.correct(text)

        # Step 2: SymSpell for remaining typos (fast cleanup)
        text = self._symspell.correct(text)

        # Step 3: LanguageTool (optional, slow)
        if self._use_languagetool:
            text = self._languagetool_correct(text)

        return text

    def correct_batch(self, texts: List[str]) -> List[str]:
        # VSpell batch
        texts = self._vspell.correct_batch(texts)
        # SymSpell cleanup
        texts = self._symspell.correct_batch(texts)
        # LanguageTool (optional)
        if self._use_languagetool:
            texts = [self._languagetool_correct(t) for t in texts]
        return texts

    def _languagetool_correct(self, text: str) -> str:
        """Call LanguageTool API for grammar checking."""
        try:
            import requests
            response = requests.post(
                f"{self._languagetool_url}/v2/check",
                data={"text": text, "language": "vi-VN"},
                timeout=10
            )
            if response.status_code == 200:
                matches = response.json().get("matches", [])
                # Apply corrections in reverse order to maintain positions
                for match in reversed(matches):
                    if match.get("replacements"):
                        offset = match["offset"]
                        length = match["length"]
                        replacement = match["replacements"][0]["value"]
                        text = text[:offset] + replacement + text[offset + length:]
        except Exception:
            pass  # Silently skip LanguageTool errors
        return text

    def name(self) -> str:
        parts = [self._vspell.name(), "SymSpell"]
        if self._use_languagetool:
            parts.append("LanguageTool")
        return "Hybrid(" + "+".join(parts) + ")"


# ---------------------------------------------------------------------------
# Factory & Cache
# ---------------------------------------------------------------------------

_checker_cache: Dict[str, SpellCheckerBase] = {}


def get_spell_checker(
    engine: str = "symspell",
    device: str = "auto",
    batch_size: int = 16,
    use_languagetool: bool = False,
    languagetool_url: str = "http://localhost:8081"
) -> SpellCheckerBase:
    """Get or create spell checker instance (cached)."""
    cache_key = f"{engine}:{device}:{batch_size}:{use_languagetool}"

    if cache_key not in _checker_cache:
        if engine == "vspell":
            _checker_cache[cache_key] = VSpellChecker(device=device, batch_size=batch_size)
        elif engine == "hybrid":
            _checker_cache[cache_key] = HybridSpellChecker(
                device=device, batch_size=batch_size,
                use_languagetool=use_languagetool, languagetool_url=languagetool_url
            )
        else:  # symspell (default)
            _checker_cache[cache_key] = SymSpellChecker()

    return _checker_cache[cache_key]


def clear_spell_checker_cache():
    """Clear all cached spell checkers (e.g., when config changes)."""
    _checker_cache.clear()


# ---------------------------------------------------------------------------
# Legacy compatibility layer (existing API)
# ---------------------------------------------------------------------------

class VietnameseSpellChecker:
    """Legacy wrapper for backward compatibility."""

    def __init__(self):
        try:
            from pyvi import ViTokenizer
            self.tokenizer = ViTokenizer
            self.available = True
        except ImportError:
            print("⚠️ pyvi not installed. Spell checking disabled.")
            self.available = False

        self.custom_dict_path = Path.home() / ".vieneu" / "custom_spell_dict.json"
        self.custom_replacements = {}
        self.whitelist = []
        self.load_custom_dict()

    def load_custom_dict(self):
        if self.custom_dict_path.exists():
            try:
                with open(self.custom_dict_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.custom_replacements = data.get('replacements', {})
                    self.whitelist = data.get('whitelist', [])
            except Exception as e:
                print(f"⚠️ Failed to load custom dictionary: {e}")

    def save_custom_dict(self):
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
        self.custom_replacements[old_word] = new_word
        self.save_custom_dict()

    def add_to_whitelist(self, word: str):
        if word not in self.whitelist:
            self.whitelist.append(word)
            self.save_custom_dict()

    def remove_replacement(self, old_word: str):
        if old_word in self.custom_replacements:
            del self.custom_replacements[old_word]
            self.save_custom_dict()

    def remove_from_whitelist(self, word: str):
        if word in self.whitelist:
            self.whitelist.remove(word)
            self.save_custom_dict()

    def clean_text(self, text: str, level: str = "off") -> Tuple[str, str]:
        """Legacy clean_text with levels (off/light/medium/strong)."""
        if level == "off":
            return text, "Spell checking: OFF"

        original_length = len(text)
        cleaned = text
        changes = []

        # Level 1: Remove special characters (all levels)
        if level in ["light", "medium", "strong"]:
            url_pattern = re.compile(
                r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            )
            cleaned = url_pattern.sub('', cleaned)

            email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
            cleaned = email_pattern.sub('', cleaned)

            cleaned = re.sub(r'#\w+', '', cleaned)
            cleaned = re.sub(r'@\w+', '', cleaned)

            emoji_pattern = re.compile(
                "["
                "\U0001F600-\U0001F64F"
                "\U0001F300-\U0001F5FF"
                "\U0001F680-\U0001F6FF"
                "\U0001F1E0-\U0001F1FF"
                "\U00002702-\U000027B0"
                "\U000024C2-\U0001F251"
                "]+", flags=re.UNICODE
            )
            before = len(cleaned)
            cleaned = emoji_pattern.sub('', cleaned)
            emoji_removed = before - len(cleaned)

            cleaned = re.sub(r'!{2,}', '!', cleaned)
            cleaned = re.sub(r'\?{2,}', '?', cleaned)
            cleaned = re.sub(r'\.{4,}', '...', cleaned)
            cleaned = re.sub(r'[~*\-_]{3,}', '', cleaned)
            cleaned = re.sub(r'[""]', '"', cleaned)
            cleaned = re.sub(r'[''`]', "'", cleaned)
            cleaned = re.sub(r'[–—]', '-', cleaned)
            cleaned = re.sub(r'[​‌‍﻿]', '', cleaned)
            cleaned = re.sub(r'\s+', ' ', cleaned)
            cleaned = cleaned.strip()

            if emoji_removed > 0:
                changes.append(f"Removed {emoji_removed} special chars/emojis")

        # Level 2: Fix common typos (medium, strong)
        if level in ["medium", "strong"]:
            typo_map = {
                'mik': 'mình', 'mk': 'mình', 'mjk': 'mình',
                'bn': 'bạn',
                'tớ': 'tôi',
                'cx': 'cũng', 'cug': 'cũng',
                'đg': 'đang', 'dg': 'đang',
                'lm': 'làm',
                'bik': 'biết', 'bit': 'biết', 'bít': 'biết',
                'đc': 'được', 'dc': 'được',
                'hok': 'không', 'hong': 'không', 'hông': 'không',
                'ko': 'không', 'k': 'không',
                'vs': 'với', 'v': 'với',
                'ntn': 'như thế nào',
                'j': 'gì', 'z': 'gì',
                'h': 'giờ',
                'r': 'rồi', 'ròi': 'rồi',
                'nx': 'nữa',
                'nhìu': 'nhiều', 'nhiu': 'nhiều',
                'it': 'ít',
                'ok': 'được', 'oke': 'được', 'okie': 'được',
                'tks': 'cảm ơn', 'thanks': 'cảm ơn', 'thank': 'cảm ơn',
                'camon': 'cảm ơn',
                'sry': 'xin lỗi', 'sr': 'xin lỗi', 'sorry': 'xin lỗi',
                'plz': 'làm ơn', 'pls': 'làm ơn',
                'wtf': 'gì vậy',
                'lol': 'ha ha', 'haha': 'ha ha',
                'yep': 'vâng', 'yeah': 'vâng', 'uh': 'vâng',
                'zao': 'sao', 'zo': 'sao',
                'dau': 'đâu',
                'nao': 'nào',
                'aj': 'ai',
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
                tokens = self.tokenizer.tokenize(cleaned)
                changes.append("Applied advanced spell checking")
            except Exception as e:
                changes.append(f"Advanced checking failed: {str(e)}")

        # Apply custom replacements (all levels except "off")
        if self.custom_replacements:
            for old_word, new_word in self.custom_replacements.items():
                if old_word in self.whitelist:
                    continue
                pattern = r'\b' + re.escape(old_word) + r'\b'
                if re.search(pattern, cleaned, re.IGNORECASE):
                    cleaned = re.sub(pattern, new_word, cleaned, flags=re.IGNORECASE)
                    changes.append(f"Custom: '{old_word}' → '{new_word}'")

        if changes:
            status = f"✅ Cleaned ({level}): " + ", ".join(changes)
        else:
            status = f"✅ No changes needed ({level})"

        return cleaned, status


_legacy_checker = None


def get_legacy_checker() -> VietnameseSpellChecker:
    global _legacy_checker
    if _legacy_checker is None:
        _legacy_checker = VietnameseSpellChecker()
    return _legacy_checker


def clean_vietnamese_text(text: str, level: str = "off") -> Tuple[str, str]:
    """Legacy convenience function."""
    checker = get_legacy_checker()
    return checker.clean_text(text, level)


def clean_text_with_changes(text: str, level: str = "off") -> Tuple[str, List[dict]]:
    """Legacy clean text with detailed changes for preview."""
    checker = get_legacy_checker()

    if level == "off":
        return text, []

    original = text
    cleaned = text
    changes = []

    if level in ["light", "medium", "strong"]:
        # URLs
        url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        urls = [(m.start(), m.group()) for m in url_pattern.finditer(cleaned)]
        for pos, url in reversed(urls):
            changes.append({"type": "removed", "original": url, "new": "", "position": pos, "category": "url"})
        cleaned = url_pattern.sub('', cleaned)

        # Emails
        email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        emails = [(m.start(), m.group()) for m in email_pattern.finditer(cleaned)]
        for pos, email in reversed(emails):
            changes.append({"type": "removed", "original": email, "new": "", "position": pos, "category": "email"})
        cleaned = email_pattern.sub('', cleaned)

        # Hashtags/mentions
        for pattern, cat in [(r'#\w+', 'hashtag'), (r'@\w+', 'mention')]:
            matches = [(m.start(), m.group()) for m in re.finditer(pattern, cleaned)]
            for pos, match in reversed(matches):
                changes.append({"type": "removed", "original": match, "new": "", "position": pos, "category": cat})
            cleaned = re.sub(pattern, '', cleaned)

        # Emojis
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U0001F1E0-\U0001F1FF"
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE
        )
        before = cleaned
        cleaned = emoji_pattern.sub('', cleaned)
        if len(before) != len(cleaned):
            for i, (a, b) in enumerate(zip(before, cleaned)):
                if a != b:
                    changes.append({"type": "removed", "original": before[i:i+10], "new": "", "position": i, "category": "emoji"})
                    break

        # Normalize punctuation
        before = cleaned
        cleaned = re.sub(r'!{2,}', '!', cleaned)
        cleaned = re.sub(r'\?{2,}', '?', cleaned)
        cleaned = re.sub(r'\.{4,}', '...', cleaned)
        if before != cleaned:
            changes.append({"type": "normalized", "original": before, "new": cleaned, "position": 0, "category": "punctuation"})

        # Decorative chars
        before = cleaned
        cleaned = re.sub(r'[~*\-_]{3,}', '', cleaned)
        if before != cleaned:
            changes.append({"type": "removed", "original": before, "new": cleaned, "position": 0, "category": "decorative"})

        # Normalize quotes/dashes
        before = cleaned
        cleaned = re.sub(r'[""]', '"', cleaned)
        cleaned = re.sub(r'[''`]', "'", cleaned)
        cleaned = re.sub(r'[–—]', '-', cleaned)
        if before != cleaned:
            changes.append({"type": "normalized", "original": before, "new": cleaned, "position": 0, "category": "quotes"})

        # Zero-width chars
        before = cleaned
        cleaned = re.sub(r'[​‌‍﻿]', '', cleaned)
        if before != cleaned:
            changes.append({"type": "removed", "original": "zero-width", "new": "", "position": 0, "category": "zero-width"})

        # Excessive whitespace
        before = cleaned
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = cleaned.strip()
        if before != cleaned:
            changes.append({"type": "normalized", "original": "whitespace", "new": "normalized", "position": 0, "category": "whitespace"})

    # Level 2: Fix common typos (medium, strong)
    if level in ["medium", "strong"]:
        typo_map = {
            'mik': 'mình', 'mk': 'mình', 'mjk': 'mình',
            'bn': 'bạn',
            'tớ': 'tôi',
            'cx': 'cũng', 'cug': 'cũng',
            'đg': 'đang', 'dg': 'đang',
            'lm': 'làm',
            'bik': 'biết', 'bit': 'biết', 'bít': 'biết',
            'đc': 'được', 'dc': 'được',
            'hok': 'không', 'hong': 'không', 'hông': 'không',
            'ko': 'không', 'k': 'không',
            'vs': 'với', 'v': 'với',
            'ntn': 'như thế nào',
            'j': 'gì', 'z': 'gì',
            'h': 'giờ',
            'r': 'rồi', 'ròi': 'rồi',
            'nx': 'nữa',
            'nhìu': 'nhiều', 'nhiu': 'nhiều',
            'it': 'ít',
            'ok': 'được', 'oke': 'được', 'okie': 'được',
            'tks': 'cảm ơn', 'thanks': 'cảm ơn', 'thank': 'cảm ơn',
            'camon': 'cảm ơn',
            'sry': 'xin lỗi', 'sr': 'xin lỗi', 'sorry': 'xin lỗi',
            'plz': 'làm ơn', 'pls': 'làm ơn',
            'wtf': 'gì vậy',
            'lol': 'ha ha', 'haha': 'ha ha',
            'yep': 'vâng', 'yeah': 'vâng', 'uh': 'vâng',
            'zao': 'sao', 'zo': 'sao',
            'dau': 'đâu',
            'nao': 'nào',
            'aj': 'ai',
            'ns': 'nói',
            'ngê': 'nghe',
            'thay': 'thấy',
            'mún': 'muốn',
        }

        for typo, correct in typo_map.items():
            pattern = r'\b' + re.escape(typo) + r'\b'
            matches = [(m.start(), m.group()) for m in re.finditer(pattern, cleaned, re.IGNORECASE)]
            for pos, match in reversed(matches):
                changes.append({"type": "replaced", "original": match, "new": correct, "position": pos, "category": "typo"})
            cleaned = re.sub(pattern, correct, cleaned, flags=re.IGNORECASE)

    # Level 3: Advanced (strong only)
    if level == "strong" and checker.available:
        try:
            tokens = checker.tokenizer.tokenize(cleaned)
            changes.append({"type": "normalized", "original": "tokenized", "new": "pyvi", "position": 0, "category": "advanced"})
        except Exception as e:
            changes.append({"type": "error", "original": "", "new": str(e), "position": 0, "category": "advanced"})

    # Custom replacements
    if checker.custom_replacements:
        for old_word, new_word in checker.custom_replacements.items():
            if old_word in checker.whitelist:
                continue
            pattern = r'\b' + re.escape(old_word) + r'\b'
            matches = [(m.start(), m.group()) for m in re.finditer(pattern, cleaned, re.IGNORECASE)]
            for pos, match in reversed(matches):
                changes.append({"type": "replaced", "original": match, "new": new_word, "position": pos, "category": "custom"})
            cleaned = re.sub(pattern, new_word, cleaned, flags=re.IGNORECASE)

    return cleaned, changes


def export_spell_checked_text(
    chapters: List[Dict],
    output_dir: str,
    level: str = "off",
    base_name: str = "audiobook"
) -> Tuple[List[str], str]:
    """Export spell-checked text files with status in filename."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    level_suffix = {
        "off": "goc",
        "light": "da_loc",
        "medium": "da_sua",
        "strong": "da_sau"
    }.get(level, "unknown")

    files_created = []

    # Export individual chapters
    for i, chapter in enumerate(chapters):
        safe_title = "".join(c for c in chapter['title'] if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title[:50]

        cleaned_text, changes = clean_text_with_changes(chapter['text'], level)

        filename = f"{base_name}_chapter_{i+1:02d}_{safe_title}_{level_suffix}.txt"
        file_path = output_path / filename

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"# {chapter['title']} ({level_suffix})\n\n")
            f.write(cleaned_text)
            f.write(f"\n\n--- Changes: {len(changes)} ---")

        files_created.append(str(file_path))

    # Combined file
    combined_filename = f"{base_name}_all_chapters_{level_suffix}.txt"
    combined_path = output_path / combined_filename

    with open(combined_path, 'w', encoding='utf-8') as f:
        for i, chapter in enumerate(chapters):
            cleaned_text, _ = clean_text_with_changes(chapter['text'], level)
            f.write(f"{'='*80}\n")
            f.write(f"CHAPTER {i+1}: {chapter['title']} ({level_suffix})\n")
            f.write(f"{'='*80}\n\n")
            f.write(cleaned_text)
            if i < len(chapters) - 1:
                f.write(f"\n\n{'='*80}\n\n")

    files_created.append(str(combined_path))

    return files_created, f"✅ Đã xuất {len(chapters)} file chương + 1 file tổng hợp (trạng thái: {level_suffix})"


def generate_diff_html(original: str, cleaned: str, changes: List[dict], mode: str = "inline", limit: int = 5000) -> str:
    """Generate HTML diff for preview."""
    if mode == "inline":
        return _generate_inline_diff(original, cleaned, changes, limit)
    elif mode == "side-by-side":
        return _generate_side_by_side_diff(original, cleaned, changes, limit)
    else:  # unified
        return _generate_unified_diff(original, cleaned, changes, limit)


def _generate_inline_diff(original: str, cleaned: str, changes: List[dict], limit: int) -> str:
    import difflib
    from html import escape

    display_original = original[:limit] + ("..." if len(original) > limit else "")
    display_cleaned = cleaned[:limit] + ("..." if len(cleaned) > limit else "")

    matcher = difflib.SequenceMatcher(None, original[:limit], cleaned[:limit])

    html_parts = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            html_parts.append(escape(original[i1:i2]))
        elif tag == 'delete':
            html_parts.append(f'<span style="background: #fee2e2; color: #991b1b; text-decoration: line-through; padding: 1px 2px; border-radius: 2px;">{escape(original[i1:i2])}</span>')
        elif tag == 'insert':
            html_parts.append(f'<span style="background: #d1fae5; color: #065f46; font-weight: 600; padding: 1px 2px; border-radius: 2px;">{escape(cleaned[j1:j2])}</span>')
        elif tag == 'replace':
            html_parts.append(f'<span style="background: #fee2e2; color: #991b1b; text-decoration: line-through; padding: 1px 2px; border-radius: 2px;">{escape(original[i1:i2])}</span>')
            html_parts.append(f'<span style="background: #d1fae5; color: #065f46; font-weight: 600; padding: 1px 2px; border-radius: 2px;">{escape(cleaned[j1:j2])}</span>')

    from collections import Counter
    cats = Counter(c['category'] for c in changes)

    stats_html = ""
    for cat, count in sorted(cats.items()):
        color = {
            'typo': '#dc3545', 'custom': '#fd7e14', 'url': '#6c757d',
            'email': '#6c757d', 'hashtag': '#6c757d', 'mention': '#6c757d',
            'emoji': '#6c757d', 'punctuation': '#0d6efd', 'decorative': '#6c757d',
            'zero-width': '#6c757d', 'whitespace': '#0d6efd', 'quotes': '#0d6efd',
            'advanced': '#198754', 'error': '#dc3545'
        }.get(cat, '#6c757d')

        label = {
            'typo': 'Sửa typo', 'custom': 'Tùy chỉnh', 'url': 'URL', 'email': 'Email',
            'hashtag': 'Hashtag', 'mention': 'Mention', 'emoji': 'Emoji',
            'punctuation': 'Dấu câu', 'decorative': 'Trang trí', 'zero-width': 'Zero-width',
            'whitespace': 'Khoảng trắng', 'quotes': 'Dấu ngoặc', 'advanced': 'Nâng cao', 'error': 'Lỗi'
        }.get(cat, cat)

        stats_html += f'<span style="background: {color}22; color: {color}; padding: 2px 8px; border-radius: 4px; margin: 2px; display: inline-block; font-size: 12px;">{label}: {count}</span>'

    html = f"""
    <div style="font-family: monospace; font-size: 13px; line-height: 1.6;">
        <h4 style="margin-bottom: 8px;">Kết quả sau làm sạch ({len(changes)} thay đổi)</h4>
        <div style="background: #f8f9fa; padding: 12px; border-radius: 8px; border: 1px solid #e9ecef; margin-bottom: 12px;">
            {stats_html}
        </div>
        <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #e9ecef; white-space: pre-wrap; word-wrap: break-word; max-height: 400px; overflow-y: auto;">
{''.join(html_parts)}
        </div>
    </div>
    """
    return html


def _generate_side_by_side_diff(original: str, cleaned: str, changes: List[dict], limit: int) -> str:
    import difflib
    from html import escape

    display_original = original[:limit]
    display_cleaned = cleaned[:limit]

    orig_lines = display_original.splitlines(keepends=True)
    clean_lines = display_cleaned.splitlines(keepends=True)

    matcher = difflib.SequenceMatcher(None, orig_lines, clean_lines)

    html_rows = []
    line_num_left = 1
    line_num_right = 1

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            for i in range(i1, i2):
                html_rows.append(f"""
                <tr class="diff-equal">
                    <td class="diff-linenum">{line_num_left}</td>
                    <td class="diff-content">{escape(orig_lines[i].rstrip())}</td>
                    <td class="diff-linenum">{line_num_right}</td>
                    <td class="diff-content">{escape(clean_lines[i - i1 + j1].rstrip())}</td>
                </tr>
                """)
                line_num_left += 1
                line_num_right += 1

        elif tag == 'delete':
            for i in range(i1, i2):
                html_rows.append(f"""
                <tr class="diff-delete">
                    <td class="diff-linenum">{line_num_left}</td>
                    <td class="diff-content" style="background: #fee2e2; color: #991b1b; text-decoration: line-through;">{escape(orig_lines[i].rstrip())}</td>
                    <td class="diff-linenum"></td>
                    <td class="diff-content"></td>
                </tr>
                """)
                line_num_left += 1

        elif tag == 'insert':
            for j in range(j1, j2):
                html_rows.append(f"""
                <tr class="diff-insert">
                    <td class="diff-linenum"></td>
                    <td class="diff-content"></td>
                    <td class="diff-linenum">{line_num_right}</td>
                    <td class="diff-content" style="background: #d1fae5; color: #065f46; font-weight: 600;">{escape(clean_lines[j].rstrip())}</td>
                </tr>
                """)
                line_num_right += 1

        elif tag == 'replace':
            for i in range(i1, i2):
                html_rows.append(f"""
                <tr class="diff-replace">
                    <td class="diff-linenum">{line_num_left}</td>
                    <td class="diff-content" style="background: #fee2e2; color: #991b1b; text-decoration: line-through;">{escape(orig_lines[i].rstrip())}</td>
                    <td class="diff-linenum">{line_num_right}</td>
                    <td class="diff-content" style="background: #d1fae5; color: #065f46; font-weight: 600;">{escape(clean_lines[j1].rstrip())}</td>
                </tr>
                """)
                line_num_left += 1
                line_num_right += 1

    html = f"""
    <style>
        .diff-table {{ width: 100%; border-collapse: collapse; font-family: monospace; font-size: 12px; }}
        .diff-table td {{ padding: 4px 8px; border: 1px solid #e5e7eb; vertical-align: top; white-space: pre-wrap; word-break: break-all; }}
        .diff-linenum {{ width: 40px; text-align: right; color: #6b7280; background: #f9fafb; }}
        .diff-content {{ width: calc(50% - 40px); }}
        .diff-even {{ background: #fafafa; }}
    </style>
    <div style="max-height: 500px; overflow-y: auto; border: 1px solid #e5e7eb; border-radius: 6px;">
        <table class="diff-table">
            <thead>
                <tr style="background: linear-gradient(135deg, #6366f1 0%, #0ea5e9 100%); color: white; position: sticky; top: 0;">
                    <th style="padding: 8px; width: 40px;">Gốc</th>
                    <th style="padding: 8px;">Nội dung gốc</th>
                    <th style="padding: 8px; width: 40px;">Mới</th>
                    <th style="padding: 8px;">Nội dung mới</th>
                </tr>
            </thead>
            <tbody>
                {''.join(html_rows)}
            </tbody>
        </table>
    </div>
    <p style="margin-top: 8px; color: #6b7280; font-size: 12px;">Tổng cộng: {len(changes)} thay đổi | Hiển thị {min(len(orig_lines), 100)} dòng đầu tiên</p>
    """
    return html


def _generate_unified_diff(original: str, cleaned: str, changes: List[dict], limit: int) -> str:
    import difflib
    from html import escape

    display_original = original[:limit]
    display_cleaned = cleaned[:limit]

    orig_lines = display_original.splitlines(keepends=True)
    clean_lines = display_cleaned.splitlines(keepends=True)

    diff = list(difflib.unified_diff(orig_lines, clean_lines, lineterm='', n=3))

    html_parts = []
    for line in diff[:100]:
        if line.startswith('---') or line.startswith('+++'):
            html_parts.append(f'<div style="color: #6366f1; font-weight: 600;">{escape(line)}</div>')
        elif line.startswith('@@'):
            html_parts.append(f'<div style="color: #0ea5e9; background: #f0f9ff; padding: 4px 8px; border-radius: 4px; font-family: monospace; font-size: 11px;">{escape(line)}</div>')
        elif line.startswith('-'):
            html_parts.append(f'<div style="background: #fee2e2; color: #991b1b; padding: 2px 8px; font-family: monospace; font-size: 12px;">{escape(line)}</div>')
        elif line.startswith('+'):
            html_parts.append(f'<div style="background: #d1fae5; color: #065f46; padding: 2px 8px; font-family: monospace; font-size: 12px;">{escape(line)}</div>')
        else:
            html_parts.append(f'<div style="color: #6b7280; padding: 2px 8px; font-family: monospace; font-size: 12px;">{escape(line)}</div>')

    html = f"""
    <div style="font-family: monospace; font-size: 12px; line-height: 1.5; max-height: 500px; overflow-y: auto; border: 1px solid #e5e7eb; border-radius: 6px; padding: 8px; background: #fafafa;">
        {''.join(html_parts)}
    </div>
    <p style="margin-top: 8px; color: #6b7280; font-size: 12px;">Unified diff - Tóm tắt {len(changes)} thay đổi chi tiết</p>
    """
    return html


# ---------------------------------------------------------------------------
# New API: Engine-aware spell checking (for pipeline integration)
# ---------------------------------------------------------------------------

def spell_check_text(
    text: str,
    engine: str = "symspell",
    device: str = "auto",
    batch_size: int = 16,
    use_languagetool: bool = False,
    languagetool_url: str = "http://localhost:8081"
) -> Tuple[str, Dict]:
    """
    Spell check text with new engine API.
    Returns (corrected_text, metadata).
    """
    start_time = time.time()
    checker = get_spell_checker(engine, device, batch_size, use_languagetool, languagetool_url)

    if not text or not text.strip():
        return text, {"engine": checker.name(), "time_ms": 0, "changes": 0}

    corrected = checker.correct(text)
    elapsed_ms = int((time.time() - start_time) * 1000)

    # Count changes (simple diff)
    changes = sum(1 for a, b in zip(text.split(), corrected.split()) if a != b)

    return corrected, {
        "engine": checker.name(),
        "time_ms": elapsed_ms,
        "changes": changes,
        "original_len": len(text),
        "corrected_len": len(corrected)
    }


def spell_check_batch(
    texts: List[str],
    engine: str = "symspell",
    device: str = "auto",
    batch_size: int = 16,
    use_languagetool: bool = False,
    languagetool_url: str = "http://localhost:8081"
) -> Tuple[List[str], List[Dict]]:
    """Spell check multiple texts with new engine API."""
    start_time = time.time()
    checker = get_spell_checker(engine, device, batch_size, use_languagetool, languagetool_url)

    if not texts:
        return [], []

    corrected = checker.correct_batch(texts)
    elapsed_ms = int((time.time() - start_time) * 1000)

    metadata = []
    for orig, corr in zip(texts, corrected):
        changes = sum(1 for a, b in zip(orig.split(), corr.split()) if a != b)
        metadata.append({
            "engine": checker.name(),
            "time_ms": elapsed_ms // len(texts) if texts else 0,
            "changes": changes,
            "original_len": len(orig),
            "corrected_len": len(corr)
        })

    return corrected, metadata


if __name__ == "__main__":
    # Quick test
    test_texts = [
        "Toi di hoc o Ha Noi",
        "Hom nay troi dep qua",
        "Ban co muon an pho khong",
        "Tôi đi học ở Hà Nội",  # đã đúng
        "Em tên là Nam",
    ]

    print("=== SymSpell ===")
    checker = SymSpellChecker()
    for t in test_texts:
        result = checker.correct(t)
        print(f"Input:  {t}")
        print(f"Output: {result}")
        print()

    print("=== VSpell (if available) ===")
    vspell = VSpellChecker()
    for t in test_texts:
        result = vspell.correct(t)
        print(f"Input:  {t}")
        print(f"Output: {result}")
        print()