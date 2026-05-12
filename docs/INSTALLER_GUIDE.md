# 📦 VieNeu-TTS Installer Guide

## 🎯 Tổng Quan

Hướng dẫn tạo installer để cài đặt VieNeu-TTS trên máy Windows khác.

---

## 🚀 Phương Án 1: Inno Setup (Khuyên dùng)

### **Đặc điểm:**
- ✅ Installer chuyên nghiệp với wizard
- ✅ Tự động tạo shortcuts
- ✅ Có uninstaller
- ✅ File size: ~500MB-1GB

### **Bước 1: Cài Inno Setup**

```bash
# Tải từ: https://jrsoftware.org/isdl.php
# Hoặc dùng winget:
winget install -e --id JRSoftware.InnoSetup
```

### **Bước 2: Chuẩn bị files**

```bash
# Chạy script chuẩn bị
build_installer.bat
# Chọn: 2 (Prepare for Inno Setup)
```

Script sẽ:
1. Tải Python Embedded
2. Cài dependencies
3. Copy models từ cache

### **Bước 3: Build installer**

```bash
# Cách 1: Dùng script
build_installer.bat
# Chọn: 3 (Build Full Installer)

# Cách 2: Thủ công
# - Mở Inno Setup Compiler
# - File → Open → installer.iss
# - Build → Compile
```

### **Kết quả:**
```
installer_output/VieNeu-TTS-Setup-2.5.0.exe
```

---

## 🚀 Phương Án 2: PyInstaller (Portable)

### **Đặc điểm:**
- ✅ Không cần cài đặt
- ✅ Portable (copy & run)
- ⚠️ File size lớn (~800MB-1.5GB)

### **Bước 1: Build executable**

```bash
# Chạy script
build_installer.bat
# Chọn: 1 (Build Portable EXE)
```

### **Bước 2: Test**

```bash
cd dist\VieNeu-TTS
VieNeu-TTS.exe
```

### **Kết quả:**
```
dist/VieNeu-TTS/
├── VieNeu-TTS.exe
├── _internal/
│   ├── Python DLLs
│   ├── Dependencies
│   └── Models
└── config.yaml
```

Copy toàn bộ thư mục này sang máy khác và chạy `VieNeu-TTS.exe`.

---

## 📊 So Sánh

| Tính năng | Inno Setup | PyInstaller |
|-----------|------------|-------------|
| **Có wizard cài đặt** | ✅ | ❌ |
| **Tạo shortcuts** | ✅ | ❌ |
| **Uninstaller** | ✅ | ❌ |
| **Portable** | ❌ | ✅ |
| **File size** | ~500MB-1GB | ~800MB-1.5GB |
| **Thời gian build** | ~5-10 phút | ~10-20 phút |

---

## 🎯 Khuyến Nghị

**Cho người dùng cuối:**
→ **Inno Setup** (installer chuyên nghiệp)

**Cho portable/testing:**
→ **PyInstaller** (không cần cài đặt)

---

## 📝 Nội Dung Installer

### **Inno Setup bao gồm:**
1. ✅ Python Embedded (~50MB)
2. ✅ VieNeu-TTS source code
3. ✅ Dependencies (đã cài sẵn)
4. ✅ Models (tùy chọn - có thể tải sau)
5. ✅ Scripts (persistent server, auto-start)
6. ✅ Documentation
7. ✅ Start Menu shortcuts
8. ✅ Desktop shortcut (tùy chọn)
9. ✅ Auto-start option (tùy chọn)

### **PyInstaller bao gồm:**
1. ✅ Python runtime (embedded)
2. ✅ VieNeu-TTS + dependencies
3. ✅ Tất cả trong 1 thư mục
4. ⚠️ Models phải tải riêng (lần đầu chạy)

---

## 🚀 Sau Khi Build

### **Inno Setup:**
```
installer_output/VieNeu-TTS-Setup-2.5.0.exe (~500MB-1GB)
```

**Người dùng chỉ cần:**
1. Chạy `VieNeu-TTS-Setup-2.5.0.exe`
2. Next → Next → Install
3. Chọn "Tu dong chay khi khoi dong Windows" (tùy chọn)
4. Finish
5. Mở "VieNeu-TTS" từ Start Menu
6. Dùng ngay!

### **PyInstaller:**
```
dist/VieNeu-TTS/ (~800MB-1.5GB)
```

**Người dùng chỉ cần:**
1. Copy thư mục `VieNeu-TTS` sang máy khác
2. Chạy `VieNeu-TTS.exe`
3. Lần đầu sẽ tải models (~1.8GB)
4. Dùng ngay!

---

## 🔧 Troubleshooting

### **Build thất bại?**

**Inno Setup:**
```bash
# Kiểm tra Python Embedded đã tải chưa
dir installer_temp\python-embed

# Kiểm tra dependencies
dir installer_temp\python-embed\Lib\site-packages

# Xem log
type installer_output\VieNeu-TTS-Setup-2.5.0.log
```

**PyInstaller:**
```bash
# Xóa cache và build lại
rmdir /s /q build dist
pyinstaller --clean vieneu_tts.spec

# Xem log
type build\VieNeu-TTS\warn-VieNeu-TTS.txt
```

### **File size quá lớn?**

**Giảm size:**
1. Không bao gồm models trong installer
2. Models sẽ tự động tải lần đầu chạy
3. Giảm từ ~1.5GB → ~500MB

**Cách làm:**
```bash
# Edit installer.iss, comment dòng:
; Source: "models\*"; DestDir: "{userappdata}\huggingface\hub"; ...
```

### **Thiếu DLL?**

```bash
# Cài Visual C++ Redistributable
# https://aka.ms/vs/17/release/vc_redist.x64.exe
```

---

## 📦 Phân Phối

### **Upload lên GitHub Releases:**
```bash
# Tag version
git tag v2.5.0
git push origin v2.5.0

# Upload file
# - VieNeu-TTS-Setup-2.5.0.exe (Inno Setup)
# - VieNeu-TTS-Portable-2.5.0.zip (PyInstaller)
```

### **Hướng dẫn người dùng:**
```markdown
## Cài đặt

### Phương án 1: Installer (Khuyên dùng)
1. Tải: VieNeu-TTS-Setup-2.5.0.exe
2. Chạy và làm theo wizard
3. Mở "VieNeu-TTS" từ Start Menu

### Phương án 2: Portable
1. Tải: VieNeu-TTS-Portable-2.5.0.zip
2. Giải nén
3. Chạy VieNeu-TTS.exe
```

---

## 💡 Tips

1. **Test trên máy sạch:**
   - Dùng VM hoặc máy không có Python
   - Đảm bảo installer chạy được

2. **Giảm file size:**
   - Không bao gồm models
   - Dùng UPX compression
   - Xóa debug symbols

3. **Code signing:**
   - Mua certificate để sign installer
   - Tránh Windows SmartScreen warning

4. **Auto-update:**
   - Thêm tính năng check updates
   - Download và cài đặt tự động

---

## 📚 Tài Liệu Tham Khảo

- [Inno Setup Documentation](https://jrsoftware.org/ishelp/)
- [PyInstaller Manual](https://pyinstaller.org/en/stable/)
- [Python Embedded](https://docs.python.org/3/using/windows.html#embedded-distribution)

---

## ✅ Checklist

Trước khi phân phối:
- [ ] Test installer trên máy sạch
- [ ] Kiểm tra auto-start hoạt động
- [ ] Kiểm tra uninstaller
- [ ] Test với Windows Defender
- [ ] Viết README cho người dùng
- [ ] Tạo video hướng dẫn (tùy chọn)

---

**Created:** 2026-05-07  
**Version:** 1.0
