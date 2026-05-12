# 🚀 Tối Ưu Tốc Độ Khởi Động VieNeu-TTS

## Vấn đề: Models tải lại mỗi lần chạy

Khi chạy `uv run vieneu-web`, models được load vào RAM mỗi lần → chậm (30s-2 phút).

---

## ✅ Giải pháp 1: Persistent Server (Khuyên dùng)

**Chạy server 1 lần, giữ models trong RAM:**

### Windows:
```bash
# Double-click file này
run_server_persistent.bat

# Hoặc chạy trực tiếp:
uv run python apps/gradio_persistent.py
```

### Linux/Mac:
```bash
chmod +x run_server_persistent.sh
./run_server_persistent.sh
```

**Lợi ích:**
- ✅ Models load **1 lần duy nhất**
- ✅ Đóng browser vẫn giữ server chạy
- ✅ Mở lại `http://127.0.0.1:7860` → dùng ngay
- ✅ Không cần load lại cho đến khi tắt server

---

## ✅ Giải pháp 2: Offline Mode (Không check updates)

Nếu vẫn muốn chạy mỗi lần, tắt network check:

```bash
# Windows
set HF_HUB_OFFLINE=1
uv run vieneu-web

# Linux/Mac
export HF_HUB_OFFLINE=1
uv run vieneu-web
```

**Lợi ích:**
- ✅ Không check updates từ HuggingFace
- ✅ Dùng cache local → nhanh hơn ~5-10s
- ⚠️ Vẫn phải load models vào RAM mỗi lần

---

## ✅ Giải pháp 3: Windows Service (Advanced)

Chạy VieNeu-TTS như Windows Service, tự động khởi động cùng máy:

```bash
# Cài NSSM (Non-Sucking Service Manager)
# Download: https://nssm.cc/download

# Tạo service
nssm install VieNeuTTS "C:\Users\Chien\VieNeu-TTS\.venv\Scripts\python.exe" "C:\Users\Chien\VieNeu-TTS\apps\gradio_persistent.py"
nssm set VieNeuTTS AppDirectory "C:\Users\Chien\VieNeu-TTS"
nssm start VieNeuTTS
```

**Lợi ích:**
- ✅ Tự động chạy khi khởi động Windows
- ✅ Chạy nền, không cần cửa sổ console
- ✅ Models luôn sẵn sàng

---

## ✅ Giải pháp 4: Docker Persistent Container

```bash
# Chạy container và giữ nó chạy
docker run -d --name vieneu-server \
  --gpus all \
  -p 7860:7860 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  pnnbao/vieneu-tts:latest

# Truy cập: http://localhost:7860
```

---

## 📊 So sánh

| Phương án | Tốc độ khởi động | Dễ dùng | Persistent |
|-----------|------------------|---------|------------|
| **Persistent Server** | ⚡ 30s (1 lần) | ⭐⭐⭐⭐⭐ | ✅ |
| Offline Mode | 🐢 25s (mỗi lần) | ⭐⭐⭐⭐ | ❌ |
| Windows Service | ⚡ 0s (luôn chạy) | ⭐⭐⭐ | ✅ |
| Docker | ⚡ 0s (luôn chạy) | ⭐⭐⭐⭐ | ✅ |

---

## 🎯 Khuyến nghị

**Cho người dùng thông thường:**
→ Dùng **Persistent Server** (`run_server_persistent.bat`)

**Cho developer:**
→ Dùng **Offline Mode** khi test

**Cho production:**
→ Dùng **Docker** hoặc **Windows Service**

---

## 🔧 Troubleshooting

### Models vẫn tải lại?
```bash
# Kiểm tra cache
ls ~/.cache/huggingface/hub/

# Nếu rỗng, tải lại 1 lần:
uv run vieneu-web
# Sau đó dùng persistent server
```

### Port 7860 đã được dùng?
```bash
# Windows: Tìm process đang dùng port
netstat -ano | findstr :7860
taskkill /PID <PID> /F

# Linux/Mac:
lsof -ti:7860 | xargs kill -9
```

### RAM không đủ?
- Turbo mode: ~2GB RAM
- Standard mode: ~4GB RAM
- GPU mode: ~6GB VRAM

Nếu thiếu RAM, dùng Turbo mode hoặc đóng app khác.
