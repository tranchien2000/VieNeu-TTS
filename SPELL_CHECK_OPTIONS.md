# Spell‑Check Options for VieNeu‑TTS

## Overview
VieNeu‑TTS now supports a **pluggable spell‑check system** that can run **offline** on the local machine or **online** via external APIs. The UI exposes the engine, device and batch‑size controls, and the core code routes all calls through a unified interface.

---

## 1. Architecture
- **`SpellCheckerBase`** – abstract class defining `correct(text: str) -> Tuple[str, str]`.
- Each concrete implementation lives in `src/vieneu_utils/spell_checkers/` and registers itself via `get_spell_checker(engine, device, batch_size)`.
- A small cache (`functools.lru_cache`) keeps recent results, and a batch mode can process many sentences at once when the engine supports it.

---

## 2. Available Engines
### Offline (no internet required)
| Engine | Device | Batch support | Remarks |
|--------|--------|--------------|---------|
| **SymSpell** | CPU | ✅ (any size) | Fast, dictionary‑based. Good for bulk processing on low‑end hardware. |
| **VSpell** | CPU / GPU | ✅ (up to 16) | Transformer‑based, higher accuracy. GPU gives ~2‑3× speedup. |
| **Hybrid** | CPU / GPU | ✅ (mixed) | Combines SymSpell, VSpell and optional LanguageTool for the best of both worlds. |
| **Hùn‑Spell** | CPU | ❌ | n‑gram based C++ implementation, needs compilation. |

### Online (requires internet/API key)
| Engine | Service | Device | Batch support | Remarks |
|--------|---------|--------|--------------|---------|
| **LanguageTool** | `https://languagetool.org/api` | CPU | ✅ (up to 100) | Open‑source, multilingual. Free tier limited requests per hour. |
| **Microsoft Word Proofing** | Azure Cognitive Services | CPU | ✅ (up to 50) | High‑quality Vietnamese models, requires Azure subscription. |
| **Custom REST API** | User‑provided | CPU | ✅ (depends) | Can plug any third‑party spell‑checker that follows a simple JSON contract. |

---

## 3. UI Controls (in **Xử lý văn bản** tab)
- **Engine** – dropdown listing all offline + online options.
- **Device** – `Auto`, `CPU`, `CUDA` (GPU) – only shown for GPU‑capable engines.
- **Batch size** – numeric slider; default `16`. Larger values reduce API round‑trips for online services.
- **Select / Deselect all** – checkbox column in the chapter table to apply the chosen engine per‑chapter.

---

## 4. Configuration (`config.yaml`)
```yaml
spell_check:
  engine: "off"          # off | symspell | vspell | hybrid | languagetool | ms_word
  device: "auto"        # auto | cpu | cuda
  batch_size: 16
  use_languagetool: false # keep for backward compatibility
```
- The UI automatically writes back any changes via `save_setting`.
- When `engine` is set to `off` the pipeline skips spell‑checking entirely.

---

## 5. How the Pipeline Calls Spell‑Check
1. **`phonemize_text.py`** receives `spell_check_engine`, `spell_check_device` and `spell_check_batch_size` from the UI.
2. It calls `get_spell_checker()` which returns an instance of the selected engine.
3. The text (or each chapter chunk) is passed to `clean_vietnamese_text(text, level)` → the engine’s `correct` method.
4. The cleaned text proceeds to the normalizer → phonemizer → TTS.

---

## 6. Adding a New Engine (Developer Guide)
1. Create a file `src/vieneu_utils/spell_checkers/<name>_checker.py`.
2. Subclass `SpellCheckerBase` and implement:
   ```python
   class MyChecker(SpellCheckerBase):
       def __init__(self, device="cpu"):
           ...
       def correct(self, text: str) -> Tuple[str, str]:
           # return cleaned_text, status_message
   ```
3. Register it in `spell_checker.py` inside `ENGINE_MAP`.
4. Add UI entries (dropdown value and optional device choices).
5. Update `config.yaml` documentation.

---

## 7. Testing
- Unit tests live in `test_spell_*.py`.
- Mock online services with `responses` library to avoid real calls.
- Run `pytest -k spell` to ensure all engines return a tuple and respect batch size.

---

## 8. References
- SymSpell original repo: https://github.com/wolfgarbe/SymSpell
- VSpell model: https://github.com/vnspelling/vspell
- LanguageTool API docs: https://languagetool.org/http-api/swagger
- Azure Proofing API: https://learn.microsoft.com/azure/cognitive-services/spell-check/

---

*This file is generated for developers and users to understand all spell‑check options available in VieNeu‑TTS.*