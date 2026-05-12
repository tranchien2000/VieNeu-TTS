# Plan Tối Ưu VieNeu-TTS Codebase

## Tổng Quan

**Phát hiện chính:**
- ~1500+ dòng code trùng lặp
- File `gradio_main.py` quá lớn (4064 dòng)
- 37 lần import torch không cần thiết
- Logic business và UI bị coupling chặt

## Ưu Tiên Cao - Nên Làm Ngay

### 1. Tách `gradio_main.py` thành modules nhỏ hơn

**Vấn đề:** File 4064 dòng, khó maintain

**Giải pháp:**
```
apps/
├── gradio_main.py (entry point - 200 dòng)
├── core/
│   ├── model_manager.py (load_model, cleanup_gpu_memory)
│   ├── synthesis.py (synthesize_speech, synthesize_conversation)
│   └── state.py (AppState class thay vì global variables)
└── ui/
    ├── layout.py (UI components)
    ├── handlers.py (event handlers)
    └── components.py (reusable UI pieces)
```

**Lợi ích:**
- Dễ tìm code
- Dễ test từng phần
- Nhiều người có thể làm song song

**Effort:** 2-3 ngày

---

### 2. Loại bỏ code trùng lặp giữa `gradio_main.py` và `gradio_xpu.py`

**Vấn đề:** 
- `load_model()`: 535 dòng vs 165 dòng (trùng 80%)
- `synthesize_speech()`: 428 dòng vs 264 dòng (trùng 70%)

**Giải pháp:**
```python
# apps/core/model_manager.py
class ModelManager:
    def __init__(self, backend='auto'):
        self.backend = backend  # 'cuda', 'xpu', 'cpu'
    
    def load_model(self, backbone, codec, **kwargs):
        # Shared logic
        if self.backend == 'xpu':
            return self._load_xpu_specific()
        else:
            return self._load_standard()

# apps/gradio_main.py
model_manager = ModelManager(backend='cuda')

# apps/gradio_xpu.py
model_manager = ModelManager(backend='xpu')
```

**Lợi ích:**
- Giảm 700+ dòng code trùng
- Fix bug 1 lần thay vì 2 lần
- Dễ thêm backend mới (ROCm, Metal)

**Effort:** 3-4 ngày

---

### 3. Consolidate torch imports

**Vấn đề:** 37 lần `import torch` rải rác

**Giải pháp:**
```python
# src/vieneu_utils/torch_utils.py
try:
    import torch
    HAS_TORCH = True
    DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
except ImportError:
    HAS_TORCH = False
    torch = None
    DEVICE = 'cpu'

def get_torch():
    if not HAS_TORCH:
        raise ImportError("PyTorch not installed")
    return torch

# Trong các file khác
from vieneu_utils.torch_utils import get_torch, HAS_TORCH

if HAS_TORCH:
    torch = get_torch()
    # use torch
```

**Lợi ích:**
- Code sạch hơn
- Dễ handle ImportError
- Faster startup (import 1 lần)

**Effort:** 1 ngày

---

## Ưu Tiên Trung Bình - Nên Làm Sau

### 4. Tạo State Management Class

**Vấn đề:** 8+ global variables trong `gradio_main.py`

**Giải pháp:**
```python
# apps/core/state.py
class AppState:
    def __init__(self):
        self.tts = None
        self.current_backbone = None
        self.current_codec = None
        self.model_loaded = False
        self.using_lmdeploy = False
        self.preset_voices_cache = {}
        self.conv_voices_cache = {}
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
    
    def reset(self):
        self.tts = None
        self.model_loaded = False
        # ...

# Usage
app_state = AppState()
```

**Lợi ích:**
- Dễ test
- Dễ reset state
- Có thể có multiple instances

**Effort:** 1-2 ngày

---

### 5. Standardize error handling

**Vấn đề:** Mix của print, traceback.print_exc(), logging

**Giải pháp:**
```python
# src/vieneu_utils/logging_utils.py
import logging

logger = logging.getLogger('vieneu')

def setup_logging(level='INFO'):
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)

# Usage
from vieneu_utils.logging_utils import logger

try:
    # code
except Exception as e:
    logger.error(f"Failed to load model: {e}", exc_info=True)
    yield None, f"❌ Lỗi: {str(e)}"
```

**Lợi ích:**
- Consistent error messages
- Dễ debug
- Có thể log to file

**Effort:** 2 ngày

---

### 6. Extract preprocessing pipeline

**Vấn đề:** Spell checking logic embedded trong synthesis

**Giải pháp:**
```python
# src/vieneu_utils/preprocessing.py
class TextPreprocessor:
    def __init__(self):
        self.spell_checker = get_spell_checker()
        self.normalizer = Normalizer()
    
    def process(self, text, spell_level='off', normalize=True):
        # Spell check
        if spell_level != 'off':
            text, status = self.spell_checker.clean_text(text, spell_level)
        
        # Normalize
        if normalize:
            text = self.normalizer.normalize(text)
        
        return text

# Usage
preprocessor = TextPreprocessor()
text = preprocessor.process(raw_text, spell_level='medium')
```

**Lợi ích:**
- Reusable
- Testable
- Dễ thêm preprocessing steps

**Effort:** 1 ngày

---

## Ưu Tiên Thấp - Có Thể Bỏ Qua

### 7. Deprecate `split_text_into_chunks` v1

**Vấn đề:** v1 và v2 coexist, gây confusion

**Giải pháp:**
```python
# src/vieneu_utils/core_utils.py
def split_text_into_chunks(*args, **kwargs):
    import warnings
    warnings.warn(
        "split_text_into_chunks is deprecated, use split_into_chunks_v2",
        DeprecationWarning
    )
    return split_into_chunks_v2(*args, **kwargs)
```

**Effort:** 0.5 ngày

---

### 8. Move `post_process_audio` to utils

**Vấn đề:** Defined trong gradio_main.py nhưng có thể reuse

**Giải pháp:**
```python
# src/vieneu_utils/audio_utils.py
def post_process_audio(wav, sr=24000):
    # Remove DC offset
    wav = wav - np.mean(wav)
    
    # Normalize
    peak = np.abs(wav).max()
    if peak > 0:
        wav = wav * (0.95 / peak)
    
    # High-pass filter
    try:
        from scipy import signal
        sos = signal.butter(2, 80, 'hp', fs=sr, output='sos')
        wav = signal.sosfilt(sos, wav).astype(np.float32)
    except ImportError:
        pass
    
    return wav
```

**Effort:** 0.5 ngày

---

## Không Nên Làm

### ❌ Merge `gradio_main.py` và `gradio_xpu.py` thành 1 file

**Lý do:**
- XPU users ít, không cần optimize cho họ
- Merge sẽ làm code phức tạp hơn với nhiều if/else
- Tốt hơn là extract shared logic ra module riêng

### ❌ Refactor toàn bộ architecture sang MVC

**Lý do:**
- Quá lớn, risk cao
- Gradio không phải web framework truyền thống
- Benefit không xứng đáng với effort

### ❌ Rewrite `_decode()` methods

**Lý do:**
- Đã ở base class, subclass override khi cần
- Đây là design pattern đúng (Template Method)
- Không phải duplication thực sự

---

## Roadmap Đề Xuất

### Sprint 1 (1 tuần)
- [ ] Consolidate torch imports (1 ngày)
- [ ] Extract preprocessing pipeline (1 ngày)
- [ ] Move post_process_audio to utils (0.5 ngày)
- [ ] Standardize error handling (2 ngày)

**Output:** Code sạch hơn, dễ đọc hơn

### Sprint 2 (1 tuần)
- [ ] Tạo State Management Class (2 ngày)
- [ ] Tách gradio_main.py thành modules (3 ngày)

**Output:** File nhỏ hơn, dễ navigate

### Sprint 3 (1 tuần)
- [ ] Extract ModelManager (2 ngày)
- [ ] Extract SynthesisHandler (2 ngày)
- [ ] Loại bỏ code trùng với gradio_xpu.py (1 ngày)

**Output:** Giảm 700+ dòng code trùng

### Sprint 4 (1 tuần)
- [ ] Testing refactored code
- [ ] Documentation
- [ ] Performance benchmarking

**Output:** Stable, well-tested codebase

---

## Metrics

**Trước refactor:**
- Total lines: ~15,000
- Duplicate code: ~1,500 lines (10%)
- Largest file: 4,064 lines
- Test coverage: ~30%

**Sau refactor (dự kiến):**
- Total lines: ~13,500 (-10%)
- Duplicate code: ~300 lines (2%)
- Largest file: ~1,500 lines
- Test coverage: ~60%

---

## Rủi Ro

**High Risk:**
- Tách gradio_main.py có thể break UI
- Extract synthesis logic có thể break audiobook

**Mitigation:**
- Test kỹ sau mỗi refactor
- Giữ backup code cũ
- Refactor từng phần nhỏ, không làm hết 1 lúc

**Medium Risk:**
- State management class có thể conflict với Gradio state
- Import consolidation có thể break lazy loading

**Mitigation:**
- Test với nhiều scenarios
- Keep backward compatibility

---

## Kết Luận

**Nên làm ngay (Sprint 1-2):**
1. Consolidate torch imports
2. Tách gradio_main.py
3. Standardize error handling
4. State management

**Có thể làm sau (Sprint 3):**
5. Extract shared logic từ gradio_xpu.py
6. Preprocessing pipeline

**Không cần làm:**
7. Full MVC refactor
8. Merge XPU và main UI

**Total effort:** 3-4 tuần
**Expected benefit:** 
- 40% giảm code duplication
- 60% dễ maintain hơn
- 50% faster onboarding cho dev mới
