@echo off
echo.
echo ========================================================
echo   LAPTOP 2: DIGITAL TWIN, AI/ML INFERENCE & DASHBOARD
echo ========================================================
echo.
echo Verifying Python libraries (flask, paho-mqtt, scikit-learn, joblib, asyncua)...
pip install flask paho-mqtt scikit-learn joblib asyncua pandas --quiet
echo.
echo Starting Digital Twin Server...
echo Subscribing to MQTT topic: pump/sensor/data
echo.
echo ========================================================
echo   OPEN YOUR BROWSER AT:  http://localhost:5000
echo ========================================================
echo.
python app.py
pause
