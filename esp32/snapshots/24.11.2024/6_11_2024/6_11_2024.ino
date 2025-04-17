#include <WiFi.h>
#include <WebSocketsServer.h>

// Set up access point credentials
const char* ssid = "ESP32_EMG";
const char* password = "12345678";  // Set this to whatever you'd like

// Set a fixed IP for the ESP32
IPAddress local_IP(192, 168, 4, 1);     // This will be the IP address of the ESP32
IPAddress gateway(192, 168, 4, 1);      // The gateway is the same as the ESP32's IP
IPAddress subnet(255, 255, 255, 0);     // Standard subnet mask

WebSocketsServer webSocket = WebSocketsServer(81);  // WebSocket port

unsigned long previousMillis = 0;
const long interval = 5;  // 5ms for 200Hz

void setup() {
  Serial.begin(921600);  // Set to 921600 or any higher rate the system can handle.

  // Configure the ESP32 as an Access Point
  if (!WiFi.softAP(ssid, password)) {
    Serial.println("Failed to start AP");
    return;
  }

  // Set the IP address for the AP
  if (!WiFi.softAPConfig(local_IP, gateway, subnet)) {
    Serial.println("Failed to configure AP IP");
    return;
  }

  Serial.println("Access Point started");
  Serial.print("IP Address: ");
  Serial.println(WiFi.softAPIP());  // Print the IP address to connect to

  // Start WebSocket server
  webSocket.begin();
  webSocket.onEvent(webSocketEvent);
}

void loop() {
  webSocket.loop();  // Handle WebSocket events

  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;

    // Read sensor data
    float sensorValue = analogRead(34);  // Replace with actual sensor reading
    String message = String(sensorValue);
    Serial.println(message);
    
    // Send to all connected clients
    webSocket.broadcastTXT(message);
  }
}

void webSocketEvent(uint8_t num, WStype_t type, uint8_t * payload, size_t length) {
  // Handle WebSocket events (not needed for sending data)
}
