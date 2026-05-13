@echo off
REM Development mode script for VieNeu-TTS
REM Auto-reload enabled for faster development

echo.
echo ========================================
echo   VieNeu-TTS Development Mode
echo ========================================
echo.
echo Features:
echo   - Auto-reload on file changes
echo   - Debug mode enabled
echo   - Detailed error messages
echo.

set VIENEU_DEV_MODE=true
uv run vieneu-web
