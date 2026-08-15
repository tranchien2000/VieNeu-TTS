"""
Chapter detection utility for audiobook processing.
"""

import re
from typing import List, Dict, Optional


def detect_chapters(text: str, format: str = "auto", custom_keywords: Optional[List[str]] = None, words_per_chunk: int = 1000, split_mode: str = "auto", chars_per_chunk: int = 2000) -> List[Dict]:
    """
    Detect chapters from text structure.

    Args:
        text: Full text content
        format: "auto", "markdown", "numbered", "wordcount"
        custom_keywords: Custom keywords for numbered detection (e.g., ["Chương", "Chapter", "Chap"])
        words_per_chunk: Number of words per chunk for wordcount mode

    Returns:
        List of chapters with metadata:
        [
            {
                "title": "Chapter 1: Introduction",
                "start_pos": 0,
                "end_pos": 5000,
                "text": "...",
                "level": 1
            },
            ...
        ]
    """
    chapters = []

    if split_mode == "charcount":
        chapters = _split_by_char_count(text, chars_per_chunk)
    elif split_mode == "wordcount":
        chapters = _split_by_word_count(text, words_per_chunk=words_per_chunk)
    elif split_mode == "numbered":
        chapters = _detect_numbered_chapters(text, custom_keywords=custom_keywords)
    else:
        # Existing format handling (for backward compatibility with format param)
        if format == "auto":
            # Try markdown first
            chapters = _detect_markdown_chapters(text)
            if not chapters:
                # Try numbered chapters
                chapters = _detect_numbered_chapters(text)
            if not chapters:
                # Fallback: split by blank lines
                chapters = _detect_blank_line_chapters(text)
        elif format == "markdown":
            chapters = _detect_markdown_chapters(text)
        elif format == "numbered":
            chapters = _detect_numbered_chapters(text, custom_keywords=custom_keywords)
        elif format == "wordcount":
            chapters = _split_by_word_count(text, words_per_chunk=words_per_chunk)

    # If no chapters detected, treat entire text as one chapter
    if not chapters:
        chapters = [{
            "title": "Full Text",
            "start_pos": 0,
            "end_pos": len(text),
            "text": text,
            "level": 1
        }]

    return chapters


def _detect_markdown_chapters(text: str) -> List[Dict]:
    """Detect chapters from markdown headings (# Chapter, ## Section)."""
    chapters = []

    # Pattern: # Heading or ## Heading at start of line
    pattern = r'^(#{1,3})\s+(.+)$'

    lines = text.split('\n')
    current_chapter = None
    current_text = []

    for i, line in enumerate(lines):
        match = re.match(pattern, line)
        if match:
            # Save previous chapter
            if current_chapter:
                current_chapter['text'] = '\n'.join(current_text).strip()
                current_chapter['end_pos'] = current_chapter['start_pos'] + len(current_chapter['text'])
                chapters.append(current_chapter)

            # Start new chapter
            level = len(match.group(1))  # Number of #
            title = match.group(2).strip()
            start_pos = sum(len(l) + 1 for l in lines[:i])

            current_chapter = {
                "title": title,
                "start_pos": start_pos,
                "end_pos": 0,  # Will be set later
                "text": "",
                "level": level
            }
            current_text = []
        else:
            if current_chapter:
                current_text.append(line)

    # Save last chapter
    if current_chapter:
        current_chapter['text'] = '\n'.join(current_text).strip()
        current_chapter['end_pos'] = current_chapter['start_pos'] + len(current_chapter['text'])
        chapters.append(current_chapter)

    return chapters


def _detect_numbered_chapters(text: str, custom_keywords: Optional[List[str]] = None) -> List[Dict]:
    """Detect numbered chapters (Chapter 1, Chương 1, PHẦN I)."""
    chapters = []

    # Default patterns
    default_keywords = ["Chapter", "CHAPTER", "Chương", "CHƯƠNG", "Phần", "PHẦN", "Chap", "CHAP"]

    # Use custom keywords if provided
    keywords = custom_keywords if custom_keywords else default_keywords

    # Build pattern from keywords
    keyword_pattern = "|".join(re.escape(k) for k in keywords)

    # Patterns for various chapter formats
    patterns = [
        rf'^({keyword_pattern})\s+(\d+|[IVX]+)[\s:.\-]*(.*)$',
        r'^(\d+)[\.\)]\s+(.+)$',  # 1. Title or 1) Title
    ]

    lines = text.split('\n')
    current_chapter = None
    current_text = []

    for i, line in enumerate(lines):
        matched = False
        for pattern in patterns:
            match = re.match(pattern, line.strip())
            if match:
                # Save previous chapter
                if current_chapter:
                    current_chapter['text'] = '\n'.join(current_text).strip()
                    current_chapter['end_pos'] = current_chapter['start_pos'] + len(current_chapter['text'])
                    chapters.append(current_chapter)

                # Extract title
                if len(match.groups()) == 3:
                    title = f"{match.group(1)} {match.group(2)}: {match.group(3)}".strip()
                else:
                    title = f"{match.group(1)}: {match.group(2)}".strip()

                start_pos = sum(len(l) + 1 for l in lines[:i])

                current_chapter = {
                    "title": title,
                    "start_pos": start_pos,
                    "end_pos": 0,
                    "text": "",
                    "level": 1
                }
                current_text = []
                matched = True
                break

        if not matched and current_chapter:
            current_text.append(line)

    # Save last chapter
    if current_chapter:
        current_chapter['text'] = '\n'.join(current_text).strip()
        current_chapter['end_pos'] = current_chapter['start_pos'] + len(current_chapter['text'])
        chapters.append(current_chapter)

    return chapters


def _split_by_char_count(text: str, chars_per_chunk: int = 2000) -> List[Dict]:
    """Split text into chunks by character count.

    Args:
        text: Full text content.
        chars_per_chunk: Number of characters per chapter.
    """
    chapters = []
    total_len = len(text)
    start = 0
    idx = 1
    while start < total_len:
        end = min(start + chars_per_chunk, total_len)
        # Prefer split at newline boundary
        slice_ = text[start:end]
        newline = slice_.rfind('\n')
        if newline != -1 and end != total_len:
            end = start + newline
        chapter_text = text[start:end].strip()
        title = f"Section {idx}"
        chapters.append({
            "title": title,
            "start_pos": start,
            "end_pos": end,
            "text": chapter_text,
            "level": 1
        })
        start = end
        idx += 1
    return chapters


def _detect_blank_line_chapters(text: str, min_blank_lines: int = 3) -> List[Dict]:
    """Split by multiple consecutive blank lines."""
    chapters = []

    # Split by 3+ consecutive newlines
    pattern = r'\n{' + str(min_blank_lines) + r',}'
    sections = re.split(pattern, text)

    current_pos = 0
    for i, section in enumerate(sections):
        section = section.strip()
        if not section:
            continue

        # Use first line as title (truncated)
        first_line = section.split('\n')[0][:50]
        title = f"Section {i+1}: {first_line}..."

        chapters.append({
            "title": title,
            "start_pos": current_pos,
            "end_pos": current_pos + len(section),
            "text": section,
            "level": 1
        })

        current_pos += len(section) + min_blank_lines

    return chapters


def _split_by_word_count(text: str, words_per_chunk: int = 1000) -> List[Dict]:
    """Split text into chunks by word count."""
    chapters = []

    # Split text into words (simple whitespace split)
    words = text.split()
    total_words = len(words)

    if total_words == 0:
        return chapters

    current_pos = 0
    chunk_num = 1

    for i in range(0, total_words, words_per_chunk):
        chunk_words = words[i:i + words_per_chunk]
        chunk_text = ' '.join(chunk_words)

        # Find actual position in original text
        start_pos = text.find(chunk_words[0], current_pos)
        if start_pos == -1:
            start_pos = current_pos

        end_pos = start_pos + len(chunk_text)

        # Create title with word count info
        actual_word_count = len(chunk_words)
        title = f"Part {chunk_num} ({actual_word_count} words)"

        chapters.append({
            "title": title,
            "start_pos": start_pos,
            "end_pos": end_pos,
            "text": chunk_text,
            "level": 1
        })

        current_pos = end_pos
        chunk_num += 1

    return chapters


def split_text_by_chapters(text: str, chapters: List[Dict]) -> List[Dict]:
    """
    Split text into chapter chunks (already done in detect_chapters).
    This is a convenience function that returns the same chapters.
    """
    return chapters


def estimate_chapter_duration(chapter_text: str, chars_per_second: float = 50) -> float:
    """
    Estimate audio duration for a chapter.

    Args:
        chapter_text: Chapter text content
        chars_per_second: Average speaking speed (default: 50 chars/s)

    Returns:
        Estimated duration in seconds
    """
    char_count = len(chapter_text)
    return char_count / chars_per_second
