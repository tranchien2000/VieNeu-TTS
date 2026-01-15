# VieNeu-TTS SDK Examples

Bộ sưu tập các ví dụ hướng dẫn tích hợp VieNeu-TTS vào ứng dụng của bạn.

## Danh sách ví dụ

1.  **[Standard Mode](standard_mode.py)**: Chạy TTS trực tiếp trên máy (Local). Hỗ trợ GGUF (CPU) và PyTorch (GPU).
2.  **[Remote Mode](remote_mode.py)**: Kết nối tới server LMDeploy. Phù hợp cho ứng dụng Web/SaaS để đạt tốc độ tối đa và không cần phần cứng tại client.
3.  **[Voice Cloning](voice_cloning.py)**: Hướng dẫn Clone giọng nói bất kỳ từ một file âm thanh mẫu ngắn (Zero-shot).

## Cách chạy

Cài đặt SDK và các phụ kiện:

uv pip install -e .
# Hoặc
pip install -e .
```


## Yêu cầu

*   Python 3.10+
*   Server LMDeploy (cho ví dụ remote mode)
