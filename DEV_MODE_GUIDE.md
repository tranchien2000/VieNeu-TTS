# 🔥 Development Mode Guide

## Giới Thiệu

Development mode giúp bạn phát triển nhanh hơn bằng cách tự động reload UI khi có thay đổi code, không cần restart lại app.

## Cách Sử Dụng

### **Windows:**

```bash
# Cách 1: Dùng script
scripts\dev.bat

# Cách 2: Set biến môi trường
set VIENEU_DEV_MODE=true
uv run vieneu-web
```

### **Linux/Mac:**

```bash
# Cách 1: Dùng script
chmod +x scripts/dev.sh
./scripts/dev.sh

# Cách 2: Set biến môi trường
export VIENEU_DEV_MODE=true
uv run vieneu-web
```

### **Hoặc inline:**

```bash
# Windows
set VIENEU_DEV_MODE=true && uv run vieneu-web

# Linux/Mac
VIENEU_DEV_MODE=true uv run vieneu-web
```

## Tính Năng

Khi chạy dev mode, bạn sẽ có:

✅ **Auto-reload:** UI tự động reload khi save file  
✅ **Debug mode:** Hiển thị thông tin debug chi tiết  
✅ **Error details:** Thông báo lỗi rõ ràng hơn  
✅ **No auto-open:** Không tự động mở browser (giữ tab hiện tại)  

## Workflow Development

### **Trước đây:**
```
1. Sửa code
2. Ctrl+C tắt app
3. Chạy lại: uv run vieneu-web
4. Đợi load model (~15-30s)
5. Test
```

### **Bây giờ:**
```
1. Chạy: scripts\dev.bat (1 lần duy nhất)
2. Sửa code
3. Save file (Ctrl+S)
4. Refresh browser (F5)
5. Test ngay lập tức
```

## Lưu Ý

⚠️ **Chỉ dùng cho development:**
- Không dùng dev mode trong production
- Dev mode có thể chậm hơn một chút do debug overhead

⚠️ **Một số thay đổi vẫn cần restart:**
- Thay đổi model code (src/vieneu/)
- Thay đổi dependencies
- Thay đổi config.yaml

⚠️ **Models vẫn được cache:**
- Models chỉ load 1 lần khi khởi động
- Không cần reload models mỗi lần sửa UI

## Tips

### **1. Sử dụng với VS Code:**

Thêm vào `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "VieNeu Dev Mode",
      "type": "python",
      "request": "launch",
      "module": "vieneu_web",
      "env": {
        "VIENEU_DEV_MODE": "true"
      },
      "console": "integratedTerminal"
    }
  ]
}
```

### **2. Tắt auto-reload tạm thời:**

```bash
# Chỉ cần không set VIENEU_DEV_MODE
uv run vieneu-web
```

### **3. Kết hợp với hot-reload browser:**

Cài extension "Live Server" hoặc "Auto Refresh" trong browser để tự động refresh khi Gradio reload.

## Troubleshooting

### **Vấn đề: UI không reload sau khi save**

**Giải pháp:**
1. Kiểm tra console có thông báo "🔥 Development mode" không
2. Thử refresh browser (F5)
3. Kiểm tra file có lỗi syntax không

### **Vấn đề: App crash khi reload**

**Giải pháp:**
1. Kiểm tra lỗi trong console
2. Fix lỗi syntax/import
3. Restart app nếu cần

### **Vấn đề: Thay đổi không có hiệu lực**

**Giải pháp:**
1. Một số thay đổi cần full restart (model code, config)
2. Clear browser cache (Ctrl+Shift+R)
3. Restart app với dev mode

## So Sánh

| Mode | Reload Time | Use Case |
|------|-------------|----------|
| **Normal** | ~15-30s | Production, stable testing |
| **Dev Mode** | ~2-5s | Development, rapid iteration |

## Kết Luận

Development mode giúp tăng tốc độ phát triển đáng kể. Sử dụng nó khi đang code và test UI, chuyển về normal mode khi deploy production.

**Happy coding! 🚀**
