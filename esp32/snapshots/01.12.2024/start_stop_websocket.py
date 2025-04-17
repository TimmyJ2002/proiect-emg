import asyncio
import websockets
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import messagebox
from time import time
import threading
import os
import matlab.engine
import threading
from time import perf_counter


class DataRecorder:
    """Manages data recording from a WebSocket connection."""

    def __init__(self, uri):
        self.uri = uri
        self.time_data = []
        self.sensor_data = []
        self.live_time_data = []
        self.live_sensor_data = []
        self.recording = False
        self.start_time = None
        self.live_start_time = perf_counter()

    async def receive_data(self):
        """Continuously receives data from the WebSocket server and updates live data."""
        while True:
            try:
                async with websockets.connect(self.uri) as websocket:
                    print("Connected to WebSocket server.")
                    while True:
                        data = await websocket.recv()
                        try:
                            sensor_value = float(data)
                            current_time = perf_counter()
                            elapsed_time_live = current_time - self.live_start_time

                            self.live_time_data.append(elapsed_time_live)
                            self.live_sensor_data.append(sensor_value)

                            while self.live_time_data and self.live_time_data[0] < elapsed_time_live - 10:
                                self.live_time_data.pop(0)
                                self.live_sensor_data.pop(0)

                            if self.recording:
                                if self.start_time is None:
                                    self.start_time = current_time

                                elapsed_time_record = current_time - self.start_time
                                self.time_data.append(elapsed_time_record)
                                self.sensor_data.append(sensor_value)

                                while self.time_data and self.time_data[0] < elapsed_time_record - 10:
                                    self.time_data.pop(0)
                                    self.sensor_data.pop(0)

                        except ValueError:
                            print("Received malformed data, skipping...")
            except (websockets.ConnectionClosedError, OSError):
                print("Connection lost, attempting to reconnect...")
                await asyncio.sleep(1)

    def start_recording(self):
        """Starts recording data."""
        self.time_data.clear()
        self.sensor_data.clear()
        self.start_time = None
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
            script_path = r"C:\Users\janost\Desktop\uni\proiect-emg\01.12.2024\test_plot_python_matlab.m"
        
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

        # Create the buttons
        self.record_button = tk.Button(root, text="Start Recording", command=self.toggle_recording, height=3, width=25, font=("Arial", 16))
        self.record_button.pack(pady=20)

        self.export_button = tk.Button(root, text="Export Data", command=self.recorder.export_data, height=3, width=25, font=("Arial", 16))
        self.export_button.pack(pady=20)
        self.export_button.config(state=tk.DISABLED)  # Initially disable the export button

        # Set up Matplotlib figure and embed it in Tkinter
        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.ax.set_title("Live Sensor Data")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Sensor Value")
        self.ax.set_xlim(0, 10)
        self.ax.set_ylim(0, 4100)  # Adjust based on your sensor's range
        self.line, = self.ax.plot([], [], color='blue')

        # Embed the Matplotlib graph in the Tkinter GUI
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().pack(pady=20)

        # Start live graph update
        self.update_live_graph()

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

    def update_live_graph(self):
        """Updates the live graph with the latest 10 seconds of live data."""
        if self.recorder.live_time_data and self.recorder.live_sensor_data:
            # Update graph data
            self.line.set_data(self.recorder.live_time_data, self.recorder.live_sensor_data)
            self.ax.set_xlim(max(0, self.recorder.live_time_data[0]), max(10, self.recorder.live_time_data[-1]))

        # Redraw the canvas
        self.canvas.draw()

        # Schedule the next update
        root.after(100, self.update_live_graph)  # Update every 100 ms


def run_event_loop(recorder):
    """Runs the WebSocket connection in a separate event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(recorder.receive_data())


# Main Application
if __name__ == "__main__":
    # Initialize the data recorder with the WebSocket URI
    uri = "ws://192.168.4.1:81"  # Use your ESP32's IP address Field
   # uri = "ws://192.168.0.168:81"  # Home
    recorder = DataRecorder(uri)

    # Start the Tkinter GUI
    root = tk.Tk()
    root.title("EMG Data Recorder")
    root.geometry("800x600")  # Larger window size to fit the graph

    # Initialize the graphical interface with the recorder
    gui = GraphicalInterface(root, recorder)

    # Run the WebSocket client in a separate thread
    threading.Thread(target=run_event_loop, args=(recorder,), daemon=True).start()

    # Start the Tkinter main loop
    root.mainloop()