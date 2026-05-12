"""
VieNeu-TTS Persistent Server
Models load once and stay in memory. Server runs until manually stopped.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import main function from gradio_main
from apps.gradio_main import main

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 VieNeu-TTS Persistent Server")
    print("=" * 60)
    print()
    print("💡 Mẹo:")
    print("   - Models sẽ load 1 lần và giữ trong RAM")
    print("   - Giữ cửa sổ này mở để server tiếp tục chạy")
    print("   - Đóng trình duyệt không ảnh hưởng - mở lại vẫn dùng được")
    print("   - Nhấn Ctrl+C để dừng server")
    print()
    print("=" * 60)
    print()

    # Run the main Gradio app
    main()
