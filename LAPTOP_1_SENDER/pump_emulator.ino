#include <WiFiS3.h>
#include <PubSubClient.h>

const char* ssid     = "SSID;      // ← change this
const char* password = "PSWD";   // ← change this

const char* mqtt_server = "broker.hivemq.com";
const int   mqtt_port   = 1883;
const char* mqtt_topic  = "pump/sensor/data";
const int   ALERT_LED   = 13;

WiFiClient   wifiClient;
PubSubClient mqtt(wifiClient);

void setup() {
  Serial.begin(115200);
  pinMode(ALERT_LED, OUTPUT);
  digitalWrite(ALERT_LED, LOW);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) { delay(500); }
  mqtt.setServer(mqtt_server, mqtt_port);
  delay(500);
  Serial.println(">>> ARDUINO UNO R4 IS ONLINE & READY <<<");
  Serial.println(ssid);
}

void reconnectMQTT() {
  while (!mqtt.connected()) {
    mqtt.connect("PumpArduinoR4");
    delay(2000);
  }
}

void loop() {
  if (!mqtt.connected()) reconnectMQTT();
  mqtt.loop();

  if (Serial.available() > 0) {
    String packet = Serial.readStringUntil('\n');
    packet.trim();
    if (packet.length() == 0) return;

    char buf[128];
    packet.toCharArray(buf, sizeof(buf));
    char* token = strtok(buf, ",");
    if (token == NULL) return;

    float airTemp  = atof(token);
    token = strtok(NULL, ","); float procTemp = token ? atof(token) : 0;
    token = strtok(NULL, ","); int speed      = token ? atoi(token) : 0;
    token = strtok(NULL, ","); float torque   = token ? atof(token) : 0;
    token = strtok(NULL, ","); int toolWear   = token ? atoi(token) : 0;
    token = strtok(NULL, ","); int failure    = token ? atoi(token) : 0;

    digitalWrite(ALERT_LED, failure == 1 ? HIGH : LOW);

    String payload = "{";
    payload += "\"air_temp\":"        + String(airTemp, 1)  + ",";
    payload += "\"process_temp\":"    + String(procTemp, 1) + ",";
    payload += "\"rpm\":"             + String(speed)       + ",";
    payload += "\"torque\":"          + String(torque, 1)   + ",";
    payload += "\"tool_wear\":"       + String(toolWear)    + ",";
    payload += "\"machine_failure\":" + String(failure);
    payload += "}";
    mqtt.publish(mqtt_topic, payload.c_str());

    Serial.print("ACK -> RPM:"); Serial.print(speed);
    Serial.print(" | Torque:"); Serial.print(torque);
    //Serial.print(" | Status:"); Serial.println(failure ? "!! FAULT !!" : "NORMAL");
  }
}