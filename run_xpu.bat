@echo off
cd /d "%~dp0"
.xpu_venv\Scripts\python.exe gradio_app_xpu.py

pause