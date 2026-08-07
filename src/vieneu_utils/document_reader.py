"""
Document reader utility for extracting text from Word and text files.
"""

from docx import Document
from pathlib import Path
from typing import Tuple, Optional


def extract_text_from_txt(
    file_path: str,
    max_chars: Optional[int] = None
) -> Tuple[str, int, bool, Optional[str]]:
    """
    Extract text from .txt file with auto-detect encoding.

    Args:
        file_path: Path to the .txt file
        max_chars: Maximum characters to extract (default: None = no limit)

    Returns:
        Tuple of (text, char_count, truncated, error_message)
        - text: Extracted text content
        - char_count: Total character count
        - truncated: Whether text was truncated
        - error_message: Error message if failed, None if successful
    """
    try:
        # Validate file
        path = Path(file_path)
        if not path.exists():
            return "", 0, False, "File không tồn tại"
        if path.suffix.lower() != '.txt':
            return "", 0, False, "Chỉ hỗ trợ file .txt"

        # Auto-detect encoding using charset-normalizer
        from charset_normalizer import from_path
        results = from_path(file_path)
        best_result = results.best()

        if best_result is None:
            # Fallback to UTF-8
            encoding = 'utf-8'
        else:
            encoding = best_result.encoding

        # Read with detected encoding
        with open(file_path, 'r', encoding=encoding, errors='replace') as f:
            full_text = f.read()

        char_count = len(full_text)

        # Truncate if needed
        truncated = False
        if max_chars is not None and char_count > max_chars:
            truncated = True
            full_text = full_text[:max_chars]

        return full_text, char_count, truncated, None

    except Exception as e:
        return "", 0, False, f"Lỗi đọc file: {str(e)}"


def extract_text_from_docx(
    file_path: str,
    max_chars: Optional[int] = None
) -> Tuple[str, int, bool, Optional[str]]:
    """
    Extract text from .docx file.

    Args:
        file_path: Path to the .docx file
        max_chars: Maximum characters to extract (default: None = no limit)

    Returns:
        Tuple of (text, char_count, truncated, error_message)
        - text: Extracted text content
        - char_count: Total character count
        - truncated: Whether text was truncated
        - error_message: Error message if failed, None if successful
    """
    try:
        # Validate file
        path = Path(file_path)
        if not path.exists():
            return "", 0, False, "File không tồn tại"
        if path.suffix.lower() != '.docx':
            return "", 0, False, "Chỉ hỗ trợ file .docx"

        # Read document
        doc = Document(file_path)

        # Extract text from paragraphs
        paragraphs = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:  # Skip empty paragraphs
                paragraphs.append(text)

        # Join with double newline
        full_text = "\n\n".join(paragraphs)
        char_count = len(full_text)

        # Truncate if needed
        truncated = False
        if max_chars is not None and char_count > max_chars:
            truncated = True
            full_text = full_text[:max_chars]

        return full_text, char_count, truncated, None

    except Exception as e:
        return "", 0, False, f"Lỗi đọc file: {str(e)}"
