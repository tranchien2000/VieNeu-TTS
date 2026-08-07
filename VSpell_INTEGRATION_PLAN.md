# VSpell Integration Plan - VieNeu-TTS

## Mục tiêu
Tích hợp VSpell làm spell checker chính cho audiobook batch processing, thay thế hoặc bổ sung cho spell check hiện tại.

---

## Phase 1: Research & Setup (1-2 ngày)

### 1.1 Cài đặt & Test
```bash
pip install vspell torch transformers
```
- Test basic functionality
- Benchmark tốc độ CPU vs GPU
- Kiểm tra VRAM usage

### 1.2 Đánh giá quality
- Test trên tập dữ liệu VN thực tế (news, story, conversation)
- So sánh với SymSpell + LanguageTool
- Đo false positive/negative rate

### 1.3 Model variants
- `vspell` default (PhoBERT-base)
- Có thể fine-tune trên domain TTS/audiobook nếu cần

---

## Phase 2: Architecture Design (1 ngày)

### 2.1 Interface abstraction
```python
# src/vieneu_utils/spell_checker.py
class SpellCheckerBase:
    def correct(self, text: str) -> str
    def correct_batch(self, texts: list[str]) -> list[str]

class VSpellChecker(SpellCheckerBase):
    # VSpell implementation

class SymSpellChecker(SpellCheckerBase):
    # SymSpell implementation (fallback)

class HybridSpellChecker(SpellCheckerBase):
    # Normalizer -> VSpell -> LanguageTool (optional)
```

### 2.2 Config options
```yaml
# config.yaml
spell_check:
  default: "vspell"  # vspell | symspell | hybrid | off
  vspell:
    device: "auto"  # auto | cpu | cuda
    batch_size: 16
  symspell:
    dict_path: "vn_dict.txt"
  hybrid:
    use_languagetool: false
    languagetool_url: "http://localhost:8081"
```

---

## Phase 3: Implementation (3-4 ngày)

### 3.1 Core module (`src/vieneu_utils/spell_checker.py`)
- [ ] Base class + implementations
- [ ] Lazy loading (load model khi đầu tiên dùng)
- [ ] Batch processing với progress
- [ ] Error handling (OOM, model missing)
- [ ] Caching cho texts lặp lại

### 3.2 Integration với phonemize pipeline
- Sửa `normalize_to_chunks*` để gọi spell checker trước
- Option `skip_spell_check` cho real-time

### 3.3 Audiobook integration
- Thêm spell check step trong audiobook processing
- Progress bar cho batch lớn
- Export report (số lỗi, từ đã sửa)

---

## Phase 4: UI Integration (2 ngày)

### 4.1 Settings
- Thêm dropdown "Spell Check Engine": Off / SymSpell / VSpell / Hybrid
- Device selector cho VSpell (Auto/CPU/CUDA)
- Batch size config

### 4.2 Audiobook tab
- Preview spell check trước khi generate
- Show diff (original vs corrected)
- Option apply/skip per chapter

---

## Phase 5: Testing & Optimization (2-3 ngày)

### 5.1 Unit tests
- Test từng checker riêng
- Test hybrid pipeline
- Edge cases: empty, chỉ số, emotion tags

### 5.2 Performance
- Benchmark các engine
- Memory profiling
- Optimize batch size

### 5.3 Quality validation
- Test trên 100+ samples thực tế
- Manual review kết quả
- A/B test với users

---

## Phase 6: Documentation & Release (1 ngày)

### 6.1 Docs
- README: Cài đặt VSpell, GPU setup
- Config guide
- Troubleshooting (OOM, slow)

### 6.2 Migration
- Default giữ SymSpell cho backward compat
- VSpell opt-in cho quality

---

## Rủi ro & Mitigation

| Rủi ro | Mitigation |
|--------|------------|
| VSpell OOM trên GPU nhỏ | Auto fallback CPU, config max_batch_size |
| Latency cao real-time | Chỉ bật cho audiobook batch, real-time dùng SymSpell |
| Model không load được | Graceful fallback về SymSpell, log warning |
| False positive trên tên riêng | Whitelist common names, proper nouns |

---

## Timeline tổng: ~10-12 ngày

### Milestones:
- **Day 2**: Phase 1 done - quyết định go/no-go
- **Day 5**: Phase 2-3 done - core working
- **Day 7**: Phase 4 done - UI integrated
- **Day 10**: Phase 5 done - tested
- **Day 12**: Phase 6 done - release ready