# 🔥 Hot Reload Development Plan

## ❌ Vấn Đề Hiện Tại

**Workflow hiện tại:**
```
1. Sửa code trong gradio_main.py
2. Ctrl+C để tắt app
3. Chạy lại: uv run vieneu-web
4. Đợi load model (~10-30 giây)
5. Test thay đổi
```

**Thời gian mất:**
- Load models: ~10-30 giây
- Restart Python: ~2-5 giây
- **Tổng:** ~15-35 giây mỗi lần thay đổi

**Vấn đề:**
- ❌ Mất thời gian load model mỗi lần
- ❌ Phải tắt/bật terminal
- ❌ Mất state/context đang test
- ❌ Workflow chậm, giảm productivity

---

## ✅ Giải Pháp Đề Xuất

### **Option 1: Gradio Auto-Reload (Khuyến nghị - Dễ nhất)**

**Cách hoạt động:**
- Gradio có built-in auto-reload khi detect file thay đổi
- Chỉ reload UI code, không reload models
- Models được cache trong memory

**Implementation:**

```python
# apps/gradio_main.py (cuối file)
if __name__ == "__main__":
    import os
    
    # Development mode: auto-reload
    dev_mode = os.getenv("VIENEU_DEV_MODE", "false").lower() == "true"
    
    if dev_mode:
        print("🔥 Development mode: Auto-reload enabled")
        demo.queue().launch(
            server_name="127.0.0.1",
            server_port=7860,
            share=False,
            debug=True,           # Enable debug mode
            show_error=True,      # Show detailed errors
            inbrowser=False       # Don't auto-open browser
        )
    else:
        main()
```

**Cách dùng:**
```bash
# Development mode (auto-reload)
VIENEU_DEV_MODE=true uv run vieneu-web

# Production mode (normal)
uv run vieneu-web
```

**Ưu điểm:**
- ✅ Đơn giản, chỉ thêm vài dòng code
- ✅ Gradio tự động detect file changes
- ✅ Không cần tool bên ngoài
- ✅ Models vẫn được cache

**Nhược điểm:**
- ⚠️ Chỉ reload UI code, không reload model code
- ⚠️ Một số thay đổi vẫn cần restart

---

### **Option 2: Watchdog + Auto-Restart (Nâng cao hơn)**

**Cách hoạt động:**
- Dùng `watchdog` để monitor file changes
- Tự động restart app khi detect thay đổi
- Có thể selective reload (chỉ reload phần cần thiết)

**Implementation:**

```python
# scripts/dev_server.py
import sys
import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class GradioReloader(FileSystemEventHandler):
    def __init__(self):
        self.process = None
        self.restart()
    
    def restart(self):
        if self.process:
            print("🔄 Restarting app...")
            self.process.terminate()
            self.process.wait()
        
        print("🚀 Starting app...")
        self.process = subprocess.Popen([
            sys.executable, "-m", "uvicorn",
            "apps.gradio_main:app",
            "--reload"
        ])
    
    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            print(f"📝 Detected change: {event.src_path}")
            time.sleep(0.5)  # Debounce
            self.restart()

if __name__ == "__main__":
    handler = GradioReloader()
    observer = Observer()
    observer.schedule(handler, path="apps/", recursive=True)
    observer.schedule(handler, path="src/", recursive=True)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        handler.process.terminate()
    observer.join()
```

**Cách dùng:**
```bash
# Install watchdog
uv add watchdog --dev

# Run dev server
uv run python scripts/dev_server.py
```

**Ưu điểm:**
- ✅ Auto-restart khi có thay đổi
- ✅ Có thể customize logic reload
- ✅ Monitor nhiều folders

**Nhược điểm:**
- ⚠️ Vẫn phải reload models
- ⚠️ Cần thêm dependency
- ⚠️ Phức tạp hơn Option 1

---

### **Option 3: Model Caching + Fast Reload (Tối ưu nhất)**

**Cách hoạt động:**
- Cache models trong shared memory hoặc Redis
- Chỉ reload UI code
- Models được load 1 lần duy nhất

**Implementation:**

```python
# src/vieneu_utils/model_cache.py
import pickle
import hashlib
from pathlib import Path

class ModelCache:
    """Cache models to avoid reloading on every restart."""
    
    def __init__(self, cache_dir=".vieneu/model_cache"):
        self.cache_dir = Path.home() / cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_cache_key(self, model_path, config):
        """Generate cache key from model path and config."""
        key_str = f"{model_path}_{str(config)}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def load(self, key):
        """Load cached model."""
        cache_file = self.cache_dir / f"{key}.pkl"
        if cache_file.exists():
            print(f"✅ Loading cached model: {key}")
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        return None
    
    def save(self, key, model):
        """Save model to cache."""
        cache_file = self.cache_dir / f"{key}.pkl"
        print(f"💾 Caching model: {key}")
        with open(cache_file, 'wb') as f:
            pickle.dump(model, f)

# apps/gradio_main.py
from vieneu_utils.model_cache import ModelCache

model_cache = ModelCache()

def load_model_with_cache(backbone_name, codec_name, device):
    """Load model with caching."""
    cache_key = model_cache.get_cache_key(
        f"{backbone_name}_{codec_name}",
        {"device": device}
    )
    
    # Try load from cache
    cached = model_cache.load(cache_key)
    if cached:
        return cached
    
    # Load fresh model
    print("⏳ Loading model from scratch...")
    model = Vieneu(
        backbone_name=backbone_name,
        codec_name=codec_name,
        device=device
    )
    
    # Cache for next time
    model_cache.save(cache_key, model)
    return model
```

**Ưu điểm:**
- ✅ Models chỉ load 1 lần
- ✅ Restart cực nhanh (~2-3 giây)
- ✅ Tiết kiệm thời gian development

**Nhược điểm:**
- ⚠️ Phức tạp nhất
- ⚠️ Cần quản lý cache
- ⚠️ Có thể gặp vấn đề với model updates

---

## 🎯 Khuyến Nghị

### **Cho Development (Ngay lập tức):**

**→ Dùng Option 1: Gradio Auto-Reload**

**Lý do:**
- Đơn giản nhất, chỉ thêm vài dòng code
- Không cần dependency mới
- Đủ tốt cho 90% trường hợp
- Gradio đã support sẵn

**Implementation ngay:**

```python
# apps/gradio_main.py - Thay thế phần cuối file

def main():
    server_name = os.getenv("GRADIO_SERVER_NAME", "127.0.0.1")
    server_port = int(os.getenv("GRADIO_SERVER_PORT", "7860"))
    is_on_colab = os.getenv("COLAB_RELEASE_TAG") is not None
    share = env_bool("GRADIO_SHARE", default=is_on_colab)
    
    if server_name == "0.0.0.0" and os.getenv("GRADIO_SHARE") is None:
        share = False
    
    # Development mode detection
    dev_mode = os.getenv("VIENEU_DEV_MODE", "false").lower() == "true"
    
    launch_kwargs = {
        "server_name": server_name,
        "server_port": server_port,
        "share": share,
    }
    
    if dev_mode:
        print("🔥 Development mode: Auto-reload enabled")
        launch_kwargs.update({
            "debug": True,
            "show_error": True,
            "inbrowser": False,
        })
    
    demo.queue().launch(**launch_kwargs)

if __name__ == "__main__":
    main()
```

**Cách dùng:**

```bash
# Development (auto-reload)
VIENEU_DEV_MODE=true uv run vieneu-web

# Hoặc tạo script shortcut
# scripts/dev.sh
export VIENEU_DEV_MODE=true
uv run vieneu-web
```

---

### **Cho Production:**

**→ Giữ nguyên như hiện tại**

Không cần auto-reload trong production để đảm bảo stability.

---

## 📊 So Sánh

| Feature | Option 1 (Gradio) | Option 2 (Watchdog) | Option 3 (Cache) |
|---------|-------------------|---------------------|------------------|
| **Độ phức tạp** | ⭐ Rất đơn giản | ⭐⭐ Trung bình | ⭐⭐⭐ Phức tạp |
| **Thời gian reload** | ~5-10s | ~15-20s | ~2-3s |
| **Dependencies** | Không cần | watchdog | pickle/redis |
| **Độ ổn định** | ⭐⭐⭐ Cao | ⭐⭐ Trung bình | ⭐⭐ Trung bình |
| **Khuyến nghị** | ✅ **Dùng ngay** | ⚠️ Nếu cần | ⚠️ Tương lai |

---

## 🚀 Action Items

### **Ngay lập tức (5 phút):**
1. ✅ Thêm dev mode vào `gradio_main.py`
2. ✅ Tạo script `scripts/dev.sh` hoặc `scripts/dev.bat`
3. ✅ Test auto-reload

### **Tuần sau (nếu cần):**
4. Implement Option 2 nếu Option 1 không đủ
5. Thêm model caching nếu load time vẫn chậm

### **Tương lai:**
6. Implement full model caching system
7. Add hot-reload cho model code

---

## 💡 Tips Thêm

### **1. Sử dụng Gradio Blocks.load() event:**

```python
# Reload settings khi UI load
def on_ui_load():
    """Reload settings when UI loads."""
    settings_mgr.load()
    return load_all_settings()

demo.load(fn=on_ui_load)
```

### **2. Separate UI và Logic:**

```python
# Tách UI code ra file riêng để reload nhanh hơn
# apps/ui_components.py - UI definitions
# apps/logic.py - Business logic
# apps/gradio_main.py - Glue code
```

### **3. Use Gradio's built-in reload:**

```bash
# Gradio có flag --reload (experimental)
gradio apps/gradio_main.py --reload
```

---

## 📝 Notes

- Gradio auto-reload chỉ work với UI changes
- Model changes vẫn cần full restart
- Cache models nếu load time > 10 giây
- Development mode không nên dùng trong production

---

**Tổng kết:** Implement Option 1 ngay, đơn giản và hiệu quả nhất cho development workflow.
