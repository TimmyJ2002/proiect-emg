#include <WiFi.h>
#include <WebSocketsServer.h>

const char* ssid = "Leivis 2.4 GHz";
const char* password = "Levente.";

WebSocketsServer webSocket = WebSocketsServer(81);  // WebSocket port

unsigned long previousMillis = 0;
const long interval = 1;  // 5ms for 200Hz

//test 2

int incrementNumber = 0;
bool incrementing = true;


//

void setup() {
  Serial.begin(921600); // Set to 921600 or any higher rate the system can handle.

  
  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");

 Serial.println(WiFi.localIP());

  // Start WebSocket server
  webSocket.begin();
  webSocket.onEvent(webSocketEvent);
}

void loop() {
    webSocket.loop();  // Handle WebSocket events
    
    unsigned long currentMillis = millis();
    if (currentMillis - previousMillis >= interval) {
        previousMillis = currentMillis;

        //test

        // int randomNumber = random(0, 4096);  // Generates a random number between 0 and 4095.
        // String message = String(randomNumber);
        // Serial.println(message);
        
        // // Send to all connected clients
        // webSocket.broadcastTXT(message);

        //test 2

        //   // Create a string to send
        // String message = String(incrementNumber);
        // Serial.println(message);
        
        // // Send to all connected clients
        // webSocket.broadcastTXT(message);

        // // Update the incrementNumber based on whether we're incrementing or decrementing
        // if (incrementing) {
        //     incrementNumber++;
        //     if (incrementNumber >= 4095) {
        //         incrementing = false;  // Switch to decrementing once we reach 4095
        //     }
        // } else {
        //     incrementNumber--;
        //     if (incrementNumber <= 0) {
        //         incrementing = true;  // Switch to incrementing once we reach 0
        //     }
        // }

      

        //real

        //Read sensor data
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
