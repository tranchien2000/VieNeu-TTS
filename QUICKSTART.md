# Quick Start Scripts

## 🚀 Persistent Server (Khuyên dùng - Models load 1 lần)

### Windows:
```bash
run_server_persistent.bat
```

### Linux/Mac:
```bash
./run_server_persistent.sh
```

**Lợi ích:**
- Models load 1 lần duy nhất
- Server chạy liên tục
- Đóng browser vẫn giữ server
- Mở lại http://127.0.0.1:7860 → dùng ngay

---

## 📦 Standard Mode (Load mỗi lần)

```bash
uv run vieneu-web
```

---

## ⚡ Offline Mode (Không check updates)

### Windows:
```bash
set HF_HUB_OFFLINE=1
uv run vieneu-web
```

### Linux/Mac:
```bash
export HF_HUB_OFFLINE=1
uv run vieneu-web
```

---

Xem thêm: [docs/SPEED_OPTIMIZATION.md](docs/SPEED_OPTIMIZATION.md)
