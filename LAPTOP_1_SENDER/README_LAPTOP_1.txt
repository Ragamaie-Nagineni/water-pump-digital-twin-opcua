==============================================================
  LAPTOP 1 INSTRUCTIONS (SENDER TO ARDUINO VIA USB)
==============================================================

WHAT THIS LAPTOP DOES:
- Feeds data from the dataset (ai4i2020.csv) into the Arduino UNO R4 WiFi via USB cable.
- The Arduino acts as the physical sensor node, broadcasts data over WiFi via MQTT.

STEPS TO RUN:
1. Connect Arduino UNO R4 WiFi to Laptop 1 with USB cable.
2. In Arduino IDE:
   - Open pump_emulator.ino
   - Set your WiFi SSID and Password in the code (e.g., your phone hotspot)
   - Select Board: "Arduino UNO R4 WiFi" and Port: "COM5"
   - Click "Upload"
   - Close Arduino IDE (so COM port is free).
3. Double-click "run_laptop_1.bat"
   - Data will begin streaming to Arduino!
   - Arduino receives each row and broadcasts it over WiFi via MQTT to Laptop 2.
==============================================================
