#!/bin/bash
# VieNeu-TTS Persistent Server
# Models load once and stay in memory

echo "========================================"
echo "VieNeu-TTS Persistent Server"
echo "========================================"
echo ""
echo "Models sẽ được load 1 lần duy nhất."
echo "Server sẽ chạy cho đến khi bạn nhấn Ctrl+C."
echo ""
echo "Truy cập: http://127.0.0.1:7860"
echo ""
echo "========================================"
echo ""

# Run persistent server
uv run python apps/gradio_persistent.py
