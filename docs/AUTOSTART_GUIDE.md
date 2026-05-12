# 🚀 VieNeu-TTS Auto-start trên Windows

## 📋 Tổng quan

Script `setup_autostart.bat` giúp bạn cấu hình VieNeu-TTS tự động chạy khi khởi động Windows.

---

## 🎯 3 Phương Án

### **1. Startup Folder (Đơn giản - Khuyên dùng)**

**Cách dùng:**
```bash
setup_autostart.bat
# Chọn: 1
```

**Đặc điểm:**
- ✅ Đơn giản nhất
- ✅ Tự động chạy khi login Windows
- ✅ Hiện cửa sổ console (có thể đóng)
- ✅ Dễ tắt (xóa shortcut hoặc chạy `remove_autostart.bat`)

**Cách hoạt động:**
- Tạo shortcut trong `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\`
- Windows tự động chạy khi login

---

### **2. Task Scheduler (Nâng cao)**

**Cách dùng:**
```bash
setup_autostart.bat
# Chọn: 2
```

**Đặc điểm:**
- ✅ Chạy với quyền cao (highest privilege)
- ✅ Có thể cấu hình restart tự động nếu crash
- ⚠️ Vẫn hiện cửa sổ console
- ⚠️ Cần quyền Administrator

**Quản lý:**
```bash
# Mở Task Scheduler
taskschd.msc

# Hoặc xóa bằng command
schtasks /delete /tn "VieNeuTTS-AutoStart" /f
```

---

### **3. Windows Service (Professional)**

**Cách dùng:**
```bash
# Bước 1: Tải NSSM
# https://nssm.cc/download
# Giải nén và copy nssm.exe vào thư mục VieNeu-TTS

# Bước 2: Chạy setup
setup_autostart.bat
# Chọn: 3
```

**Đặc điểm:**
- ✅ Chạy như Windows Service
- ✅ Không hiện cửa sổ console
- ✅ Tự động restart nếu crash
- ✅ Chạy ngay khi Windows boot (trước khi login)
- ⚠️ Cần NSSM tool
- ⚠️ Cần quyền Administrator

**Quản lý:**
```bash
# Mở Services Manager
services.msc

# Hoặc dùng NSSM
nssm stop VieNeuTTS
nssm start VieNeuTTS
nssm restart VieNeuTTS
nssm remove VieNeuTTS confirm
```

---

## 🔇 Chạy Silent (Không hiện cửa sổ)

Nếu dùng **Startup Folder** hoặc **Task Scheduler** nhưng không muốn hiện console:

```bash
# Sửa trong setup_autostart.bat, thay:
# run_server_persistent.bat
# Thành:
# run_server_silent.bat
```

File `run_server_silent.bat` đã được tạo sẵn - chạy server ẩn console.

---

## 🛑 Tắt Auto-start

```bash
# Xóa tất cả auto-start methods
remove_autostart.bat
```

Hoặc thủ công:

**Startup Folder:**
```bash
# Xóa file:
%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\VieNeu-TTS.lnk
```

**Task Scheduler:**
```bash
schtasks /delete /tn "VieNeuTTS-AutoStart" /f
```

**Windows Service:**
```bash
nssm stop VieNeuTTS
nssm remove VieNeuTTS confirm
```

---

## 📊 So Sánh

| Tính năng | Startup Folder | Task Scheduler | Windows Service |
|-----------|----------------|----------------|-----------------|
| **Dễ setup** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Không cần tool** | ✅ | ✅ | ❌ (cần NSSM) |
| **Chạy nền** | ❌ | ❌ | ✅ |
| **Auto restart** | ❌ | ✅ (config) | ✅ |
| **Chạy trước login** | ❌ | ❌ | ✅ |
| **Dễ tắt** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |

---

## 🎯 Khuyến Nghị

**Người dùng thông thường:**
→ Dùng **Startup Folder** (Phương án 1)

**Developer/Power User:**
→ Dùng **Task Scheduler** (Phương án 2)

**Production/Server:**
→ Dùng **Windows Service** (Phương án 3)

---

## 🐛 Troubleshooting

### Server không chạy sau khi login?

**Kiểm tra:**
```bash
# 1. Kiểm tra shortcut có tồn tại?
dir "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\VieNeu-TTS.lnk"

# 2. Kiểm tra task scheduler
schtasks /query /tn "VieNeuTTS-AutoStart"

# 3. Kiểm tra service
sc query VieNeuTTS
```

**Chạy thử thủ công:**
```bash
run_server_persistent.bat
```

Nếu có lỗi, fix lỗi đó trước khi setup auto-start.

---

### Port 7860 đã được dùng?

```bash
# Tìm process đang dùng port
netstat -ano | findstr :7860

# Kill process
taskkill /PID <PID> /F
```

---

### Muốn đổi port?

**Cách 1: Environment Variable**
```bash
# Thêm vào System Environment Variables
GRADIO_SERVER_PORT=8080
```

**Cách 2: Sửa code**
```python
# Edit apps/gradio_persistent.py
# Hoặc apps/gradio_main.py, dòng ~2022:
server_port = int(os.getenv("GRADIO_SERVER_PORT", "8080"))  # Đổi 7860 → 8080
```

---

### RAM không đủ?

VieNeu-TTS cần:
- **Turbo mode:** ~2GB RAM
- **Standard mode:** ~4GB RAM  
- **GPU mode:** ~6GB VRAM

Nếu thiếu RAM:
1. Đóng app khác
2. Dùng Turbo mode (nhẹ hơn)
3. Không dùng auto-start, chỉ chạy khi cần

---

## 📝 Files Đã Tạo

```
VieNeu-TTS/
├── setup_autostart.bat          # Setup auto-start (3 phương án)
├── remove_autostart.bat         # Xóa auto-start
├── run_server_silent.bat        # Chạy server ẩn console
└── docs/
    └── AUTOSTART_GUIDE.md       # Hướng dẫn này
```

---

## 🚀 Quick Start

```bash
# 1. Setup auto-start (chọn phương án 1)
setup_autostart.bat

# 2. Restart Windows để test

# 3. Sau khi login, mở browser:
http://127.0.0.1:7860

# 4. Nếu muốn tắt:
remove_autostart.bat
```

---

## 💡 Tips

1. **Test trước khi setup auto-start:**
   ```bash
   run_server_persistent.bat
   # Đảm bảo chạy OK, không có lỗi
   ```

2. **Dùng silent mode cho trải nghiệm tốt hơn:**
   - Không hiện cửa sổ console
   - Server chạy nền
   - Chỉ mở browser khi cần

3. **Monitor server:**
   ```bash
   # Kiểm tra server có chạy không
   curl http://127.0.0.1:7860
   
   # Hoặc mở Task Manager → tìm python.exe
   ```

4. **Logs:**
   - Nếu dùng Service, logs ở: `C:\Windows\System32\config\systemprofile\AppData\Local\Temp\`
   - Hoặc redirect logs trong `apps/gradio_persistent.py`

---

Xem thêm:
- [OPTIMIZATION_SUMMARY.md](../OPTIMIZATION_SUMMARY.md) - Tối ưu tốc độ
- [SPEED_OPTIMIZATION.md](SPEED_OPTIMIZATION.md) - Chi tiết về caching
