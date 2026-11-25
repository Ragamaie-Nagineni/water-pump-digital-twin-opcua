@echo off
echo.
echo ========================================================
echo   LAPTOP 1: INDUSTRIAL SENSOR TRANSMITTER (DATA FEEDER)
echo ========================================================
echo.
echo Verifying pyserial library...
pip install pyserial --quiet
echo.
echo Starting CSV to Arduino streamer...
echo Make sure Arduino UNO R4 is plugged into USB (COM5)!
echo.
python streamer.py
pause
