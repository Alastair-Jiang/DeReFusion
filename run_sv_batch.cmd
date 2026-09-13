@echo off
REM Durable launcher for the structural-validation batch (idempotent; safe to re-run).
cd /d C:\Users\26843\Desktop\project\repos\DeReFusion
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\26843\Desktop\project\repos\DeReFusion\reproduction\batches\run_structural_validation.ps1" >> sv_batch_log.txt 2>&1
