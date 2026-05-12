@echo off
chcp 65001 >nul
REM VieNeu-TTS Persistent Server (Updated)
REM Models chi load 1 lan, server chay mai mai

echo ========================================
echo VieNeu-TTS Persistent Server
echo ========================================
echo.
echo Models se duoc load 1 lan duy nhat.
echo Server se chay cho den khi ban dong cua so nay.
echo.
echo Truy cap: http://127.0.0.1:7860
echo.
echo Nhan Ctrl+C de dung server.
echo ========================================
echo.

REM Chay persistent server
uv run python apps/gradio_persistent.py

pause
