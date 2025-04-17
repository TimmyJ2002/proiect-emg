#include <WiFi.h>
#include <WebSocketsServer.h>
#define LED_PIN 13  // GPIO13 for LED

// Access Point credentials
const char* ssid = "ESP32_AP";
const char* password = "12345678";  // Minimum 8 characters

// Static IP configuration
IPAddress local_IP(192, 168, 0, 168); // Desired static IP address
IPAddress gateway(192, 168, 0, 1);    // Gateway (use ESP32's IP if standalone)
IPAddress subnet(255, 255, 255, 0);   // Subnet mask

// WebSocket server
WebSocketsServer webSocket = WebSocketsServer(81);

unsigned long previousMillis = 0;
const long interval = 5;  // 5ms interval for sending batches
const int samplesPerBatch = 5;  // 5 samples per batch
float sampleBuffer[samplesPerBatch];
int sampleIndex = 0;

bool isRecording = false;

void setup() {
    Serial.begin(921600);
    Serial.println("\n[SETUP] Initializing...");

    pinMode(LED_PIN, OUTPUT);
    Serial.println("[SETUP] LED pin set as OUTPUT");

    // Configure ESP32 as an Access Point with a static IP
    Serial.println("[SETUP] Starting ESP32 Access Point...");
    if (!WiFi.softAP(ssid, password)) {
        Serial.println("[ERROR] Failed to start AP");
        return;
    }
    Serial.println("[SETUP] Access Point started successfully");

    Serial.println("[SETUP] Configuring Static IP...");
    if (!WiFi.softAPConfig(local_IP, gateway, subnet)) {
        Serial.println("[ERROR] Failed to configure static IP");
        return;
    }
    Serial.println("[SETUP] Static IP configured successfully");

    IPAddress IP = WiFi.softAPIP();  // Get the AP IP address
    Serial.print("[SETUP] AP Static IP Address: ");
    Serial.println(IP);

    // Start WebSocket server
    Serial.println("[SETUP] Starting WebSocket server...");
    webSocket.begin();
    webSocket.onEvent(webSocketEvent);
    Serial.println("[SETUP] WebSocket server started successfully");
}

void loop() {
    webSocket.loop();

    // Serial.println("[LOOP] Blinking LED");
    // digitalWrite(LED_PIN, HIGH);  // Turn LED ON
    // delay(500);                   // Wait 500ms
    // digitalWrite(LED_PIN, LOW);   // Turn LED OFF
    // delay(500);                   // Wait 500ms

    if (webSocket.connectedClients() > 0) {
        Serial.print("[LOOP] Sending data to ");
        Serial.print(webSocket.connectedClients());
        Serial.println(" connected clients");

        String batchMessage = "";
        static int incrementNumber = 0; // Holds the current increment/decrement number
        static bool incrementing = true; // Direction flag: true for incrementing, false for decrementing

        // Collect 5 samples of increment/decrement values
        for (int i = 0; i < 5; i++) {
            // Update the incrementNumber
            if (incrementing) {
                incrementNumber++;
                if (incrementNumber >= 4095) {
                    incrementing = false; // Switch to decrementing when reaching 4095
                }
            } else {
                incrementNumber--;
                if (incrementNumber <= 0) {
                    incrementing = true; // Switch to incrementing when reaching 0
                }
            }

            // Append the value to the batchMessage
            if (i > 0) batchMessage += ",";
            batchMessage += String(incrementNumber);
        }

        // Send the batch
        webSocket.broadcastTXT(batchMessage);
        Serial.print("[LOOP] Sent message: ");
        Serial.println(batchMessage);
    }
}

void webSocketEvent(uint8_t num, WStype_t type, uint8_t* payload, size_t length) {
    switch (type) {
        case WStype_DISCONNECTED:
            Serial.printf("[WEBSOCKET] Client %u disconnected\n", num);
            if (webSocket.connectedClients() == 0) {
                isRecording = false;
                Serial.println("[WEBSOCKET] No clients connected. Recording stopped.");
            }
            break;

        case WStype_CONNECTED: {
            IPAddress ip = webSocket.remoteIP(num);
            Serial.printf("[WEBSOCKET] Client %u connected from %s\n", num, ip.toString().c_str());
            break;
        }

        case WStype_TEXT: {
            String message = String((char*)payload);
            Serial.printf("[WEBSOCKET] Received message from Client %u: %s\n", num, message.c_str());

            if (message == "TOGGLE_RECORDING") {
                isRecording = !isRecording;
                Serial.println(isRecording ? "[WEBSOCKET] Recording started" : "[WEBSOCKET] Recording stopped");
                webSocket.sendTXT(num, isRecording ? "Recording: ON" : "Recording: OFF");
            } 
            else if (message == "PING") {  // Handle PING message
                Serial.println("[WEBSOCKET] Received PING, sending PONG...");
                webSocket.sendTXT(num, "PONG");
            }
            break;
        }
    }
}

