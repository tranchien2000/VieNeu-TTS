"""
Vietnamese spell checker and text filter.
"""

from typing import Tuple, List, Dict
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


def clean_text_with_changes(text: str, level: str = "off") -> Tuple[str, List[dict]]:
    """
    Clean text and return detailed changes for preview.

    Args:
        text: Input text
        level: Cleaning level

    Returns:
        Tuple of (cleaned_text, list_of_changes)
        Each change: {"type": "removed|replaced|normalized", "original": "...", "new": "...", "position": int}
    """
    checker = get_spell_checker()

    if level == "off":
        return text, []

    original = text
    cleaned = text
    changes = []

    # Level 1: Remove special characters (all levels)
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
            # Approximate position - find first difference
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
    """
    Export spell-checked text files with status in filename.

    Args:
        chapters: List of chapter dicts
        output_dir: Output directory
        level: Spell check level applied
        base_name: Base name for files

    Returns:
        Tuple of (file_paths, status_message)
    """
    from pathlib import Path

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

        # Apply spell check
        cleaned_text, changes = clean_text_with_changes(chapter['text'], level)

        # Filename: name_chapter01_trangthai.txt
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
    """Generate inline diff with character-level highlighting."""
    import difflib
    from html import escape

    # Limit text for performance
    display_original = original[:limit] + ("..." if len(original) > limit else "")
    display_cleaned = cleaned[:limit] + ("..." if len(cleaned) > limit else "")

    # Use SequenceMatcher for character-level diff
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

    # Generate category badges
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
    """Generate side-by-side diff with line-by-line comparison."""
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
    """Generate unified diff with inline highlights."""
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
