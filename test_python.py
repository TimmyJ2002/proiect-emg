import websocket

ws = websocket.WebSocket()
ws.connect("ws://192.168.0.168:81")  # Replace with your ESP32's WebSocket IP
ws.send("PING")
print(ws.recv())  # Should print "PONG"
