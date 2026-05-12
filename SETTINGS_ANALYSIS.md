# 📊 Phân Tích Settings VieNeu-TTS

## ✅ Settings Hiện Tại (Đã Lưu)

### 1. Generation Parameters
- ✅ `temperature` (0.3) - Độ sáng tạo
- ✅ `max_chars_chunk` (128) - Độ dài mỗi chunk
- ✅ `top_p` (0.85) - Nucleus sampling
- ✅ `repetition_penalty` (1.05) - Tránh lặp

### 2. Processing Settings
- ✅ `spell_check_level` (Tắt) - Kiểm tra chính tả
- ✅ `generation_mode` (Sequential) - Chế độ generation
- ✅ `use_batch` (true) - Batch processing
- ✅ `max_batch_size` (16) - Batch size

### 3. Voice Settings
- ✅ `last_voice_id` (null) - Voice đã chọn
- ✅ `last_voice_name` (null) - Tên voice

### 4. Audiobook Settings
- ✅ `audiobook_split_mode` (Tự động) - Chế độ chia chapter
- ✅ `audiobook_output_mode` (Single file) - Output mode
- ✅ `audiobook_spell_check_level` (Tắt) - Spell check cho audiobook
- ✅ `audiobook_words_per_chunk` (100) - Số từ mỗi chunk

### 5. Model Settings
- ✅ `last_backbone` (null) - Model backbone đã load
- ✅ `last_codec` (null) - Codec đã load
- ✅ `last_device` (null) - Device đã chọn

---

## 🆕 Đề Xuất Settings Bổ Sung

### **Nhóm 1: Conversation/Hội thoại (Ưu tiên cao)**

#### 1.1. `conversation_silence_duration` (default: 0.1)
- **Mô tả:** Khoảng lặng giữa các câu thoại (giây)
- **Vị trí:** Tab Hội thoại → Slider "⏱️ Khoảng lặng"
- **Lý do:** User thường điều chỉnh để phù hợp với tốc độ đọc
- **Giá trị:** 0.0 - 3.0 giây

#### 1.2. `conversation_speaker_mappings` (default: {})
- **Mô tả:** Lưu mapping nhân vật → giọng đọc
- **Ví dụ:** `{"Phương": "Ly", "Dũng": "Binh", "Hùng": "Sơn"}`
- **Lý do:** Không phải setup lại mỗi lần
- **Quan trọng:** ⭐⭐⭐⭐⭐

#### 1.3. `conversation_auto_detect` (default: true)
- **Mô tả:** Tự động quét nhân vật khi paste script
- **Lý do:** Tiện lợi cho workflow

---

### **Nhóm 2: Audiobook (Ưu tiên cao)**

#### 2.1. `audiobook_default_voice` (default: "Ly")
- **Mô tả:** Giọng đọc mặc định cho audiobook
- **Vị trí:** Tab Audiobook → Voice dropdown
- **Lý do:** User có giọng yêu thích riêng
- **Quan trọng:** ⭐⭐⭐⭐⭐

#### 2.2. `audiobook_output_directory` (default: "audiobook_output")
- **Mô tả:** Thư mục lưu output mặc định
- **Lý do:** Không phải chọn lại mỗi lần
- **Quan trọng:** ⭐⭐⭐⭐

#### 2.3. `audiobook_chapter_keywords` (default: "Chương,Chapter,Chap")
- **Mô tả:** Keywords để detect chapters
- **Lý do:** Mỗi sách có format khác nhau
- **Quan trọng:** ⭐⭐⭐

#### 2.4. `audiobook_auto_export_text` (default: false)
- **Mô tả:** Tự động export text khi xử lý xong
- **Lý do:** Backup text đã xử lý

---

### **Nhóm 3: UI/UX (Ưu tiên trung bình)**

#### 3.1. `ui_theme` (default: "default")
- **Mô tả:** Theme giao diện (default/dark/light)
- **Lý do:** Preference cá nhân
- **Quan trọng:** ⭐⭐⭐

#### 3.2. `ui_default_tab` (default: "preset")
- **Mô tả:** Tab mở mặc định (preset/custom/conversation/audiobook)
- **Lý do:** User thường dùng 1 tab cố định
- **Quan trọng:** ⭐⭐⭐⭐

#### 3.3. `ui_auto_play` (default: true)
- **Mô tả:** Tự động play audio sau khi generate
- **Lý do:** Tiện lợi
- **Quan trọng:** ⭐⭐⭐

#### 3.4. `ui_show_advanced_settings` (default: false)
- **Mô tả:** Hiển thị advanced settings mặc định
- **Lý do:** Power users muốn access nhanh
- **Quan trọng:** ⭐⭐

---

### **Nhóm 4: Performance (Ưu tiên trung bình)**

#### 4.1. `cache_enabled` (default: true)
- **Mô tả:** Bật/tắt cache cho voices
- **Lý do:** Tăng tốc độ load
- **Quan trọng:** ⭐⭐⭐

#### 4.2. `cache_ttl_minutes` (default: 60)
- **Mô tả:** Thời gian cache tồn tại (phút)
- **Lý do:** Balance giữa memory và speed
- **Quan trọng:** ⭐⭐

#### 4.3. `auto_cleanup_temp_files` (default: true)
- **Mô tả:** Tự động xóa temp files sau khi xong
- **Lý do:** Tiết kiệm disk space
- **Quan trọng:** ⭐⭐⭐

---

### **Nhóm 5: History/Logging (Ưu tiên thấp)**

#### 5.1. `history_enabled` (default: true)
- **Mô tả:** Lưu lịch sử generation
- **Lý do:** Tracking và replay
- **Quan trọng:** ⭐⭐⭐

#### 5.2. `history_max_items` (default: 50)
- **Mô tả:** Số lượng history items tối đa
- **Lý do:** Giới hạn disk usage
- **Quan trọng:** ⭐⭐

#### 5.3. `logging_level` (default: "INFO")
- **Mô tả:** Mức độ logging (DEBUG/INFO/WARNING/ERROR)
- **Lý do:** Debug khi cần
- **Quan trọng:** ⭐⭐

---

### **Nhóm 6: Advanced (Ưu tiên thấp)**

#### 6.1. `custom_model_path` (default: null)
- **Mô tả:** Path đến custom model
- **Lý do:** Power users có fine-tuned models
- **Quan trọng:** ⭐⭐

#### 6.2. `gpu_memory_fraction` (default: 0.9)
- **Mô tả:** Phần trăm VRAM sử dụng
- **Lý do:** Multi-GPU hoặc shared GPU
- **Quan trọng:** ⭐⭐

#### 6.3. `enable_experimental_features` (default: false)
- **Mô tả:** Bật tính năng thử nghiệm
- **Lý do:** Early access cho beta testers
- **Quan trọng:** ⭐

---

## 📋 Tổng Kết Đề Xuất

### **Ưu tiên CAO (Nên thêm ngay):**
1. ✅ `conversation_silence_duration` - Khoảng lặng hội thoại
2. ✅ `conversation_speaker_mappings` - Mapping nhân vật → giọng
3. ✅ `audiobook_default_voice` - Giọng mặc định audiobook
4. ✅ `audiobook_output_directory` - Thư mục output
5. ✅ `ui_default_tab` - Tab mở mặc định

### **Ưu tiên TRUNG (Có thể thêm sau):**
6. `audiobook_chapter_keywords` - Keywords detect chapter
7. `ui_theme` - Theme giao diện
8. `ui_auto_play` - Auto play audio
9. `cache_enabled` - Bật/tắt cache
10. `auto_cleanup_temp_files` - Auto cleanup

### **Ưu tiên THẤP (Optional):**
11. `history_enabled` - Lưu lịch sử
12. `logging_level` - Mức độ logging
13. `custom_model_path` - Custom model path

---

## 🎯 Khuyến Nghị Implementation

### **Phase 1 (Ngay):**
- Thêm 5 settings ưu tiên cao
- Update UI để load/save các settings này
- Test persistence

### **Phase 2 (Tuần sau):**
- Thêm 5 settings ưu tiên trung
- Thêm UI cho theme switcher
- Thêm cache management

### **Phase 3 (Tương lai):**
- Thêm settings ưu tiên thấp
- Settings import/export UI
- Settings profile management (multiple profiles)

---

## 💡 Gợi Ý Thêm

### **Settings Categories UI:**
```
⚙️ Settings
├── 🎨 Generation (temperature, top_p, etc.)
├── 🎭 Conversation (silence, speaker mappings)
├── 📚 Audiobook (voice, output dir, keywords)
├── 🖥️ UI/UX (theme, default tab, auto play)
├── ⚡ Performance (cache, cleanup, batch)
└── 🔧 Advanced (logging, custom models)
```

### **Settings Profiles:**
- "Podcast Mode" - Optimized cho hội thoại
- "Audiobook Mode" - Optimized cho đọc sách
- "Quick Test" - Fast generation cho testing
- "High Quality" - Best quality, slower

---

**Tổng cộng:** 18 settings mới được đề xuất
**Đã có:** 17 settings
**Tổng sau khi thêm:** 35 settings (chuyên nghiệp!)
