// #include <WiFi.h>
// #include <WebSocketsServer.h>

// // Access Point credentials
// const char* ssid = "ESP32_AP";
// const char* password = "12345678";  // Minimum 8 characters

// // Static IP configuration
// IPAddress local_IP(192, 168, 0, 168); // Desired static IP address
// IPAddress gateway(192, 168, 0, 1);    // Gateway (use ESP32's IP if standalone)
// IPAddress subnet(255, 255, 255, 0);   // Subnet mask

// // WebSocket server
// WebSocketsServer webSocket = WebSocketsServer(81);

// unsigned long previousMillis = 0;
// const long interval = 5;  // 5ms interval for sending batches
// const int samplesPerBatch = 5;  // 5 samples per batch
// float sampleBuffer[samplesPerBatch];
// int sampleIndex = 0;

// bool isRecording = false;

// void setup() {
//     Serial.begin(921600);

//     // Configure ESP32 as an Access Point with a static IP
//     if (!WiFi.softAP(ssid, password)) {
//         Serial.println("Failed to start AP");
//         return;
//     }
//     if (!WiFi.softAPConfig(local_IP, gateway, subnet)) {
//         Serial.println("Failed to configure static IP");
//         return;
//     }

//     IPAddress IP = WiFi.softAPIP();  // Get the AP IP address
//     Serial.println("Access Point started");
//     Serial.print("AP Static IP Address: ");
//     Serial.println(IP);

//     // Start WebSocket server
//     webSocket.begin();
//     webSocket.onEvent(webSocketEvent);
// }

// void loop() {
//     webSocket.loop();

//     unsigned long currentMillis = millis();
//     if (currentMillis - previousMillis >= interval) {
//         previousMillis = currentMillis;

//         // Collect and send batch of samples
//         if (webSocket.connectedClients() > 0) {
//             String batchMessage = "";
//             for (int i = 0; i < samplesPerBatch; i++) {
//                 float sensorValue = analogRead(34);  // Replace with your analog pin
//                 if (i > 0) batchMessage += ",";
//                 batchMessage += String(sensorValue, 2);  // 2 decimal places
//             }

//             // Send the batch
//             webSocket.broadcastTXT(batchMessage);
//         }


//     // //increment-decrement
//     //     if (webSocket.connectedClients() > 0) {
//     // String batchMessage = "";
//     // static int incrementNumber = 0; // Holds the current increment/decrement number
//     // static bool incrementing = true; // Direction flag: true for incrementing, false for decrementing

//     // // Collect 5 samples of increment/decrement values
//     // for (int i = 0; i < 5; i++) {
//     //     // Update the incrementNumber
//     //     if (incrementing) {
//     //         incrementNumber++;
//     //         if (incrementNumber >= 4095) {
//     //             incrementing = false; // Switch to decrementing when reaching 4095
//     //         }
//     //     } else {
//     //         incrementNumber--;
//     //         if (incrementNumber <= 0) {
//     //             incrementing = true; // Switch to incrementing when reaching 0
//     //         }
//     //     }

//     //     // Append the value to the batchMessage
//     //     if (i > 0) batchMessage += ",";
//     //     batchMessage += String(incrementNumber);
//     // }
//     // //Send the batch
//      // webSocket.broadcastTXT(batchMessage);
//     //}


//     }
// }

// void webSocketEvent(uint8_t num, WStype_t type, uint8_t* payload, size_t length) {
//     switch (type) {
//         case WStype_DISCONNECTED:
//             Serial.printf("Client %u disconnected\n", num);
//             if (webSocket.connectedClients() == 0) {
//                 isRecording = false;
//                 Serial.println("No clients connected. Recording stopped.");
//             }
//             break;

//         case WStype_CONNECTED: {
//             IPAddress ip = webSocket.remoteIP(num);
//             Serial.printf("Client %u connected from %s\n", num, ip.toString().c_str());
//             break;
//         }

//         case WStype_TEXT: {
//             String message = String((char*)payload);
//             if (message == "TOGGLE_RECORDING") {
//                 isRecording = !isRecording;
//                 Serial.println(isRecording ? "Recording started" : "Recording stopped");
//                 webSocket.sendTXT(num, isRecording ? "Recording: ON" : "Recording: OFF");
//             }
//             break;
//         }
//     }
// }
