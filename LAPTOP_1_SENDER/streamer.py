import csv, time, serial
from datetime import datetime

CSV_FILE      = "ai4i2020.csv"
COM_PORT      = "COM5"       # ← check your port
BAUD_RATE     = 115200
DELAY_SECONDS = 1.0

def main():
    ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=2, write_timeout=None)
    time.sleep(2)
    ser.reset_input_buffer()
    print("[INIT] Connected to Arduino!\n")

    print("[WAIT] Giving Arduino 5 seconds to connect to WiFi + MQTT...")
    for i in range(5, 0, -1):
        print(f"       Starting in {i}s..."); time.sleep(1)
    print("[START] Streaming!\n")

    try:
        with open(CSV_FILE, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                air_temp  = float(row["Air temperature [K]"])
                proc_temp = float(row["Process temperature [K]"])
                rpm       = int(row["Rotational speed [rpm]"])
                torque    = float(row["Torque [Nm]"])
                tool_wear = int(row["Tool wear [min]"])
                failure   = int(row["Machine failure"])

                packet = f"{air_temp},{proc_temp},{rpm},{torque},{tool_wear},{failure}\n"
                ts = datetime.now().strftime("%H:%M:%S")
                print(f"[{ts}] Row #{i+1:04d}: {packet.strip()}")
                ser.write(packet.encode("utf-8"))

                if ser.in_waiting > 0:
                    ack = ser.readline().decode("utf-8", errors="ignore").strip()
                    if ack: print(f"         ACK: {ack}")

                time.sleep(DELAY_SECONDS)
    except KeyboardInterrupt:
        print("\n[STOPPED]")
    finally:
        ser.close()

if __name__ == "__main__":
    main()