@echo off
REM Script khoi chay nhanh Hermex tren Windows.
REM Gia dinh venv da duoc tao va cai dat thu vien (xem README.md).

call venv\Scripts\activate.bat
python -m src.main
pause
