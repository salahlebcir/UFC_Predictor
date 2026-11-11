@echo off
title MMA Vision - 2h Auto-Sync Worker
echo ==============================================================================
echo  MMA VISION — BACKGROUND WORKER (AUTO SYNC EVERY 2 HOURS)
echo ==============================================================================
cd /d "%~dp0"
python warmup.py --daemon --interval 7200
pause
