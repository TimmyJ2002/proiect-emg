import asyncio
import websockets
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import messagebox
from time import time
import threading
import os

class DataRecorder:
    """Manages data recording from a WebSocket connection."""

    def __init__(self, uri):
        self.uri = uri
        self.time_data = []
        self.sensor_data = []
        self.recording = False
        self.start_time = None

    async def receive_data(self):
        """Continuously receives data from the WebSocket server and stores it during recording."""
        async with websockets.connect(self.uri) as websocket:
            print("Connected to WebSocket server.")
            while True:
                data = await websocket.recv()  # Receive data from the ESP32
                print(f"Received: {data}")     # Print received data

                try:
                    sensor_value = float(data)  # Directly parse the received data as a float

                    if self.recording:
                        if self.start_time is None:
                            self.start_time = time()  # Set the start time when recording begins

                        current_time = time() - self.start_time  # Calculate elapsed time
                        self.time_data.append(current_time)  # Store elapsed time
                        self.sensor_data.append(sensor_value)  # Store sensor value

                        # Ensure the list keeps only the last 10 seconds of data
                        if current_time > 10:
                            while self.time_data and self.time_data[0] < current_time - 10:
                                self.time_data.pop(0)
                                self.sensor_data.pop(0)

                except ValueError:
                    print("Received malformed data, skipping...")

    def start_recording(self):
        """Starts recording data."""
        self.time_data.clear()
        self.sensor_data.clear()
        self.start_time = None  # Reset the start time
        self.recording = True
        print("Recording started...")

    def stop_recording(self):
        """Stops recording data."""
        self.recording = False
        print("Recording stopped.")

    def plot_data(self):
        """Plots the recorded data."""
        if len(self.time_data) == 0:
            messagebox.showinfo("No Data", "No data recorded.")
            return

        plt.figure(figsize=(10, 6))
        plt.plot(self.time_data, self.sensor_data, color='blue')
        plt.title("Recorded Sensor Data")
        plt.xlabel("Time (s)")
        plt.ylabel("Sensor Value")
        plt.ylim(0, 4100)  # Adjust this according to your sensor value range
        plt.xlim(max(0, self.time_data[0]), self.time_data[-1])  # Show the full time range
        plt.show()

    def export_data(self):
        """Exports the recorded data to a .txt file."""
        if len(self.time_data) == 0:
            messagebox.showinfo("No Data", "No data to export.")
            return

        filename = "EMG4.txt"
        with open(filename, "w") as file:
            for t, value in zip(self.time_data, self.sensor_data):
                file.write(f"{t:.3f}\t{value}\n")

        messagebox.showinfo("Export Complete", f"Data exported to {os.path.abspath(filename)}")


class GraphicalInterface:
    """Manages the graphical interface for starting/stopping recording and plotting."""

    def __init__(self, root, recorder):
        self.recorder = recorder
        # Create the buttons with more padding and larger font
        self.record_button = tk.Button(root, text="Start Recording", command=self.toggle_recording, height=3, width=25, font=("Arial", 16))
        self.record_button.pack(pady=20)

        self.export_button = tk.Button(root, text="Export Data", command=self.recorder.export_data, height=3, width=25, font=("Arial", 16))
        self.export_button.pack(pady=20)
        self.export_button.config(state=tk.DISABLED)  # Initially disable the export button

    def toggle_recording(self):
        """Toggles between starting and stopping the recording."""
        if self.recorder.recording:
            self.recorder.stop_recording()
            self.record_button.config(text="Start Recording")
            self.export_button.config(state=tk.NORMAL)  # Enable the export button when recording stops
            self.recorder.plot_data()  # Plot the data after stopping the recording
        else:
            self.recorder.start_recording()
            self.record_button.config(text="Stop Recording")
            self.export_button.config(state=tk.DISABLED)  # Disable the export button while recording


def run_event_loop(recorder):
    """Runs the WebSocket connection in a separate event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(recorder.receive_data())


# Main Application
if __name__ == "__main__":
    # Initialize the data recorder with the WebSocket URI
    uri = "ws://192.168.0.168:81"  # Use your ESP32's IP address
    recorder = DataRecorder(uri)

    # Start the Tkinter GUI
    root = tk.Tk()
    root.title("EMG Data Recorder")

    # Set the window size to a larger fixed size
    root.geometry("400x400")  # Set window size (Width x Height)

    # Initialize the graphical interface with the recorder
    gui = GraphicalInterface(root, recorder)

    # Run the WebSocket client in a separate thread
    threading.Thread(target=run_event_loop, args=(recorder,), daemon=True).start()

    # Start the Tkinter main loop
    root.mainloop()
