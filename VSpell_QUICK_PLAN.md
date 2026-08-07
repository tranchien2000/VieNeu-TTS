# VSpell Quick Integration - Minimal

## 1. Cài & Test (30 phút)
```bash
pip install vspell
python -c "from vspell import VSpell; s=VSpell(); print(s.correct('Tôi đi hocc'))"
```

## 2. Tạo wrapper đơn giản (1 file)
`src/vieneu_utils/vspell_checker.py`:
```python
from vspell import VSpell
from functools import lru_cache

_vspell = None

def get_vspell():
    global _vspell
    if _vspell is None:
        _vspell = VSpell()  # auto CPU/CUDA
    return _vspell

@lru_cache(maxsize=1024)
def correct_text(text: str) -> str:
    return get_vspell().correct(text)

def correct_batch(texts: list[str]) -> list[str]:
    return [correct_text(t) for t in texts]
```

## 3. Hook vào audiobook pipeline (1 chỗ)
Trong `phonemize_text.py` - thêm option `use_vspell=False` vào `normalize_to_chunks*`:

```python
def normalize_to_chunks(text, max_chars=256, use_vspell=False, ...):
    if use_vspell:
        from vieneu_utils.vspell_checker import correct_text
        text = correct_text(text)
    # ... existing code
```

## 4. UI: Thêm 1 checkbox "Use VSpell (slow, accurate)" trong Audiobook tab

## 5. Done

---

**Total: ~2-3 giờ code, 0 abstraction layer, 0 config file, 0 migration.**

Chạy được → ship. Sau đó mới optimize (batch, cache, fallback) nếu cần.