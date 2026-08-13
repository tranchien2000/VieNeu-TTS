"""
Quick spell checker using SymSpell + Underthesea.
Replaces VSpell (requires Python 3.13+).
"""
from symspellpy import SymSpell, Verbosity
from underthesea import word_tokenize
from functools import lru_cache
import os

# Initialize SymSpell
_sym_spell = None
_dict_loaded = False

def _load_dictionary():
    """Load Vietnamese dictionary for SymSpell."""
    global _sym_spell, _dict_loaded
    if _dict_loaded:
        return

    _sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)

    # Try to load existing VN dict, or build a basic one
    dict_paths = [
        "vn_dict.txt",
        os.path.join(os.path.dirname(__file__), "vn_dict.txt"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "vn_dict.txt"),
    ]

    loaded = False
    for path in dict_paths:
        if os.path.exists(path):
            _sym_spell.load_dictionary(path, term_index=0, count_index=1)
            loaded = True
            break

    if not loaded:
        # Build minimal dict from underthesea's internal dict
        _build_basic_dict()

    _dict_loaded = True

def _build_basic_dict():
    """Build a basic VN dictionary from common words."""
    # Common Vietnamese words (top frequency)
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
        "bao", "gồm", "kể", "cả", "lẫn", "cùng", "theo", "về", "cho", "để",
        "học", "sinh", "viên", "giáo", "viên", "bác", "sĩ", "kỹ", "sư", "luật", "sư",
        "bán", "mua", "thuê", "cho thuê", "làm", "việc", "nghỉ", "việc", "tìm", "việc",
        "đọc", "viết", "nghe", "nói", "hiểu", "biết", "quên", "nhớ", "thích", "ghét",
        "yêu", "thương", "ghét", "bạn", "bè", "người", "yêu", "vợ", "chồng", "con", "cháu",
        "bố", "mẹ", "anh", "chị", "em", "rể", "dâu", "cô", "chú", "bác", "dì",
        "mày", "tao", "ta", "mình", "chúng", "ta", "họ", "nó", "cô ấy", "anh ấy",
        "cảm", "ơn", "xin", "lỗi", "chào", "tạm", "biệu", "hẹn", "gặp", "lại",
        "ngon", "ngọt", "mặn", "chua", "cay", "béo", "thơm", "hôi", "đẹp", "xấu",
        "sáng", "sủa", "trời", "mưa", "nắng", "gió", "mây", "sao", "trăng", "mặt trời",
        "nước", "lửa", "gió", "đất", "trời", "biển", "núi", "sông", "hồ", "suối",
        "xe", "cộ", "tàu", "bay", "đạp", "chạy", "đi", "đến", "về", "qua", "lại",
        "sách", "vở", "bút", "mực", "thước", "cây", "tính", "máy", "tính", "điện thoại",
        "máy", "tính", "bàn", "phím", "chuột", "màn", "hình", "loa", "tai", "nghe",
        "ngủ", "nghỉ", "ngồi", "đứng", "chạy", "nhảy", "bơi", "lướt", "leo", "xuống",
    ]

    for i, word in enumerate(common_words):
        # Higher frequency = higher priority
        freq = 1000000 - i * 1000
        _sym_spell.create_dictionary_entry(word, freq)

def get_sym_spell() -> SymSpell:
    """Get or create SymSpell instance."""
    _load_dictionary()
    return _sym_spell

@lru_cache(maxsize=2048)
def correct_text(text: str) -> str:
    """
    Correct Vietnamese text using SymSpell + Underthesea tokenization.

    Args:
        text: Input text (Vietnamese)

    Returns:
        Corrected text
    """
    if not text or not text.strip():
        return text

    _load_dictionary()

    # Tokenize with underthesea for proper VN word boundaries
    try:
        tokens = word_tokenize(text, format="text").split()
    except Exception:
        # Fallback: simple split
        tokens = text.split()

    corrected_tokens = []
    for token in tokens:
        # Skip tokens with numbers, punctuation, or already correct (has diacritics)
        if any(c.isdigit() for c in token) or len(token) <= 2:
            corrected_tokens.append(token)
            continue

        # Lookup in SymSpell
        suggestions = _sym_spell.lookup(token, Verbosity.CLOSEST, max_edit_distance=2)
        if suggestions and suggestions[0].distance > 0:
            corrected_tokens.append(suggestions[0].term)
        else:
            corrected_tokens.append(token)

    return " ".join(corrected_tokens)

def correct_batch(texts: list[str]) -> list[str]:
    """Correct multiple texts."""
    return [correct_text(t) for t in texts]

# Test
if __name__ == "__main__":
    tests = [
        "Toi di hoc o Ha Noi",
        "Hom nay troi dep qua",
        "Ban co muon an pho khong",
        "Tôi đi học ở Hà Nội",  # đã đúng
        "Em tên là Nam",
    ]

    for t in tests:
        result = correct_text(t)
        print(f"Input:  {t}")
        print(f"Output: {result}")
        print()