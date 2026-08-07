"""
Text exporter for audiobook chapters.
"""

from pathlib import Path
from typing import List, Dict, Tuple, Optional
from vieneu_utils.spell_checker import export_spell_checked_text


def export_chapters_to_text(
    chapters: List[Dict],
    output_dir: str,
    export_mode: str = "both",
    spell_check_level: str = "off",
    base_name: str = "audiobook"
) -> Tuple[List[str], Optional[str], str]:
    """
    Export chapters to text files.

    Args:
        chapters: List of chapter dicts with 'title' and 'text'
        output_dir: Directory to save text files
        export_mode: "individual", "combined", or "both"
        spell_check_level: "off", "light", "medium", "strong" - applies spell check and adds status to filename
        base_name: Base name for files (used when spell_check_level != "off")

    Returns:
        Tuple of (individual_files, combined_file, status_message)
        - individual_files: List of paths to individual chapter files
        - combined_file: Path to combined file (or None)
        - status_message: Success/error message
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # If spell check requested, use enhanced exporter
    if spell_check_level != "off":
        from vieneu_utils.spell_checker import export_spell_checked_text
        files_created, status_msg = export_spell_checked_text(chapters, output_dir, spell_check_level, base_name)
        # export_spell_checked_text returns (files, status_msg)
        # Separate into individual and combined for compatibility
        individual_files = files_created[:-1] if len(files_created) > 1 else files_created
        combined_file = files_created[-1] if len(files_created) > 1 else None
        return individual_files, combined_file, status_msg

    individual_files = []
    combined_file = None

    try:
        # Export individual chapter files
        if export_mode in ["individual", "both"]:
            for i, chapter in enumerate(chapters):
                # Sanitize filename
                safe_title = "".join(c for c in chapter['title'] if c.isalnum() or c in (' ', '-', '_')).strip()
                safe_title = safe_title[:50]  # Limit length

                filename = f"chapter_{i+1:02d}_{safe_title}.txt"
                file_path = output_path / filename

                # Write chapter text
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"# {chapter['title']}\n\n")
                    f.write(chapter['text'])

                individual_files.append(str(file_path))

        # Export combined file
        if export_mode in ["combined", "both"]:
            combined_file = str(output_path / "all_chapters.txt")

            with open(combined_file, 'w', encoding='utf-8') as f:
                for i, chapter in enumerate(chapters):
                    # Chapter header
                    f.write(f"{'='*80}\n")
                    f.write(f"CHAPTER {i+1}: {chapter['title']}\n")
                    f.write(f"{'='*80}\n\n")

                    # Chapter text
                    f.write(chapter['text'])

                    # Separator between chapters
                    if i < len(chapters) - 1:
                        f.write(f"\n\n{'='*80}\n\n")

        # Success message
        if export_mode == "both":
            msg = f"✅ Đã xuất {len(individual_files)} file riêng lẻ và 1 file tổng hợp"
        elif export_mode == "individual":
            msg = f"✅ Đã xuất {len(individual_files)} file riêng lẻ"
        else:
            msg = f"✅ Đã xuất file tổng hợp"

        return individual_files, combined_file, msg

    except Exception as e:
        return [], None, f"❌ Lỗi xuất text: {str(e)}"


def get_export_summary(
    chapters: List[Dict],
    output_dir: str
) -> str:
    """
    Get summary of what will be exported.

    Args:
        chapters: List of chapters
        output_dir: Output directory

    Returns:
        Summary markdown string
    """
    total_chars = sum(len(ch['text']) for ch in chapters)

    summary = f"""
### Export Summary
- **Chapters:** {len(chapters)}
- **Total characters:** {total_chars:,}
- **Output directory:** `{output_dir}`
- **Files to create:**
  - {len(chapters)} individual files (chapter_01.txt, chapter_02.txt, ...)
  - 1 combined file (all_chapters.txt)
    """

    return summary
