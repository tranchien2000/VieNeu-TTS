import pytest
from vieneu_utils.chapter_detector import detect_chapters, _split_by_char_count

def generate_text(length: int) -> str:
    """Generate dummy text of given character length with newline every 50 chars."""
    chunk = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    text = ""
    i = 0
    while len(text) < length:
        part = chunk[i % len(chunk)]
        text += part
        i += 1
        if i % 50 == 0:
            text += "\n"
    return text[:length]

@pytest.mark.parametrize("chars_per_chunk,expected_parts", [
    (2000, 3),  # 5500 chars => 3 parts (2000,2000,1500)
    (2500, 3),  # 5500 => 3 parts (2500,2500,500)
])
def test_split_by_char_count(chars_per_chunk, expected_parts):
    txt = generate_text(5500)
    chapters = _split_by_char_count(txt, chars_per_chunk=chars_per_chunk)
    assert len(chapters) == expected_parts
    # verify concatenated text equals original (ignoring trailing newline trims)
    reconstructed = "".join(ch["text"] for ch in chapters)
    assert reconstructed.replace("\n", "") == txt.replace("\n", "")

def test_detect_chapters_charcount_mode():
    txt = generate_text(4500)
    chapters = detect_chapters(
        txt,
        format="auto",
        custom_keywords=None,
        words_per_chunk=1000,
        split_mode="charcount",
        chars_per_chunk=2000,
    )
    # Expect 3 chapters (2000,2000,500)
    assert len(chapters) == 3
    assert chapters[0]["title"] == "Section 1"
    assert chapters[-1]["title"] == "Section 3"
    # Verify positions cover full text length
    assert chapters[-1]["end_pos"] == len(txt)

def test_detect_chapters_wordcount_mode():
    txt = "word " * 2500  # 2500 words (including trailing space)
    chapters = detect_chapters(
        txt,
        format="auto",
        custom_keywords=None,
        words_per_chunk=1000,
        split_mode="wordcount",
        chars_per_chunk=2000,
    )
    # 2500 words => 3 parts (1000,1000,500)
    assert len(chapters) == 3
    assert all("Part" in c["title"] for c in chapters)
