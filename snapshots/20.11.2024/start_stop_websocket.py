import asyncio
import websockets
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import messagebox
from time import time
import threading
import os
import matlab.engine
import threading


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
        while True:  # Keep trying to connect indefinitely
            try:
                async with websockets.connect(self.uri) as websocket:
                    print("Connected to WebSocket server.")
                    while True:
                        data = await websocket.recv()  # Receive data from the ESP32
                        # print(f"Received: {data}")  # Uncomment if you want to see each data point

                        try:
                            sensor_value = float(data)  # Parse the received data as a float

                            if self.recording:
                                if self.start_time is None:
                                    self.start_time = time()  # Set start time on recording start

                                current_time = time() - self.start_time  # Calculate elapsed time
                                self.time_data.append(current_time)  # Store elapsed time
                                self.sensor_data.append(sensor_value)  # Store sensor value

                                # Keep only the last 10 seconds of data
                                if current_time > 10:
                                    while self.time_data and self.time_data[0] < current_time - 10:
                                        self.time_data.pop(0)
                                        self.sensor_data.pop(0)

                        except ValueError:
                            print("Received malformed data, skipping...")

            except (websockets.ConnectionClosedError, OSError) as e:
                print("Connection lost, attempting to reconnect...")
                await asyncio.sleep(1)  # Wait 1 second before trying to reconnect


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
        """Exports the recorded data to a .txt file and calls the MATLAB script."""
        if len(self.time_data) == 0:
            messagebox.showinfo("No Data", "No data to export.")
            return

        filename = "EMG4.txt"
        with open(filename, "w") as file:
            for t, value in zip(self.time_data, self.sensor_data):
                file.write(f"{t:.3f}\t{value}\n")

        messagebox.showinfo("Export Complete", f"Data exported to {os.path.abspath(filename)}")

        # Call the MATLAB script to process the data
        self.run_matlab_script()
        
    def run_matlab_script(self):
        """Starts the MATLAB engine in a separate thread and runs the script."""
        threading.Thread(target=self._run_matlab_and_monitor).start()

    def _run_matlab_and_monitor(self):
        """Runs the MATLAB script and monitors for the flag in a separate thread."""
        try:
            eng = matlab.engine.start_matlab()
            print("MATLAB engine started successfully.")
        
            # Define the path to your MATLAB script
            script_path = r"C:\Users\janost\Desktop\uni\proiect-emg\20.11.2024\test_plot_python_matlab.m"
        
            # Run the MATLAB script
            eng.run(script_path, nargout=0)  # Use 'nargout=0' if the script does not return any output
        
            print("MATLAB script executed successfully.")
        
            # Monitor for the close_flag.txt file
            print("Waiting for the MATLAB figure window to close...")
            while not os.path.exists('close_flag.txt'):
                time.sleep(0.5)  # Wait for a short period before checking again
        
            # If the flag is detected, proceed to clean up
            print("MATLAB figure closed, shutting down the MATLAB engine.")
            eng.quit()  # Close the MATLAB engine
        
            # Remove the flag file after quitting MATLAB
            os.remove('close_flag.txt')
        
        except Exception as e:
            print(f"An error occurred while running the MATLAB script: {e}")


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
    uri = "ws://192.168.4.1:81"  # Use your ESP32's IP address
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
