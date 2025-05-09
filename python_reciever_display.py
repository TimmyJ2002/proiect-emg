import asyncio
import websockets
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import messagebox
from time import time
import threading
import os
#import matlab.engine
import threading
from time import perf_counter

class DataRecorder:
    """Manages data recording from a WebSocket connection with different sampling rates for display and storage."""
    def __init__(self, uri):
        self.uri = uri
        self.time_data = []        # Full resolution time data (1000Hz)
        self.sensor_data = []      # Full resolution sensor data (1000Hz)
        self.live_time_data = []   # Display rate time data (200Hz)
        self.live_sensor_data = [] # Display rate sensor data (200Hz)
        self.recording = False
        self.start_time = None
        self.live_start_time = None
        self.last_display_time = 0
        self.display_interval = 0.005  # 5ms display interval
        self.sample_interval = 0.001   # 1ms between samples
        self.last_sample_time = 0

    async def receive_data(self):
        """Continuously receives data from the WebSocket server and updates data arrays."""
        while True:
            try:
                async with websockets.connect(self.uri) as websocket:
                    print("Connected to WebSocket server.")
                    while True:
                        data = await websocket.recv()
                        
                        if isinstance(data, str):
                            try:
                                # Split the batch of values
                                values = [float(x) for x in data.split(',')]
                                current_time = perf_counter()
                                
                                if self.live_start_time is None:
                                    self.live_start_time = current_time
                                    self.last_sample_time = current_time
                                
                                # Process each value in the batch
                                for i, sensor_value in enumerate(values):
                                    # Calculate precise time based on fixed sample interval
                                    sample_time = self.last_sample_time + self.sample_interval
                                    self.last_sample_time = sample_time
                                    
                                    # Handle recording data (full resolution)
                                    if self.recording:
                                        if self.start_time is None:
                                            self.start_time = sample_time
                                        elapsed_time_record = sample_time - self.start_time
                                        self.time_data.append(elapsed_time_record)
                                        self.sensor_data.append(sensor_value)
                                    
                                    # Handle live display data (200Hz)
                                    elapsed_time_live = sample_time - self.live_start_time
                                    if elapsed_time_live >= self.last_display_time + self.display_interval:
                                        self.live_time_data.append(elapsed_time_live)
                                        self.live_sensor_data.append(sensor_value)
                                        self.last_display_time = elapsed_time_live
                                        
                                        # Keep only last 10 seconds for live display
                                        while self.live_time_data and self.live_time_data[0] < elapsed_time_live - 10:
                                            self.live_time_data.pop(0)
                                            self.live_sensor_data.pop(0)
                                            
                            except ValueError as e:
                                print(f"Failed to parse data: {e}")
                                print(f"Raw data: {data}")
                        else:
                            print(f"Received non-text data of type {type(data)}")
                            
            except (websockets.ConnectionClosedError, OSError) as e:
                print(f"Connection error: {str(e)}, attempting to reconnect...")
                await asyncio.sleep(1)

    def start_recording(self):
        """Start recording data."""
        self.recording = True
        self.start_time = None
        print("Recording started")

    def stop_recording(self):
        """Stop recording data."""
        self.recording = False
        print("Recording stopped")


                
    async def send_message(self, message):
        """Sends a message to the WebSocket server."""
        try:
            async with websockets.connect(self.uri) as websocket:
                await websocket.send(message)
        except Exception as e:
            print(f"Error sending message: {e}")
            
    async def close_connection(self):
        """Closes the WebSocket connection."""
        try:
            async with websockets.connect(self.uri) as websocket:
                await websocket.close()
                print("WebSocket connection closed.")
        except Exception as e:
            print(f"Error closing connection: {e}")
        

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
        
        plt.close('all')
            
            
        max_sensor_value = max(self.sensor_data) if self.sensor_data else 0
        max_value_index = self.sensor_data.index(max_sensor_value) if max_sensor_value > 0 else -1
        sixty_percent = 0.6 * max_sensor_value
        seventy_percent = 0.7 * max_sensor_value

        plt.figure(figsize=(10, 6))
        plt.plot(self.time_data, self.sensor_data, color='blue', label='Recording RMS')
        plt.axhline(y=sixty_percent, color='red', linestyle='--', label=f'60% of Max ({sixty_percent:.2f})')
        plt.axhline(y=seventy_percent, color='orange', linestyle='--', label=f'70% of Max ({seventy_percent:.2f})')
        
        # Highlight the maximum value on the graph
        if max_value_index != -1:
            plt.scatter(self.time_data[max_value_index], max_sensor_value, color='magenta', s=20, zorder=5, label='Max Value')
            plt.annotate(f'Max ({max_sensor_value:.2f})',
                        (self.time_data[max_value_index], max_sensor_value),
                        textcoords="offset points",
                        xytext=(10, 10),
                        ha='center',
                        fontsize=10,
                        color='magenta')
        
        plt.title("Recorded Sensor Data 2")
        plt.xlabel("Time (s)")
        plt.ylabel("Sensor Value")
        plt.ylim(0, 4100)  # Adjust this according to your sensor value range
        plt.xlim(max(0, self.time_data[0]), self.time_data[-1])  # Show the full time range
        plt.legend()
        plt.show()

    def export_data(self):
        """Exports the recorded data to a .txt file and calls the MATLAB script."""
        if len(self.time_data) == 0:
            messagebox.showinfo("No Data", "No data to export.")
            return

        filename = "EXPORTED.txt"
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
            script_path = r"C:\Users\janost\Desktop\uni\proiect-emg\31.03.2025\matlab_script.m"
        
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
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Start live graph update
        self.update_live_graph()
        
        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)


    def toggle_recording(self):
        
        asyncio.run(self.recorder.send_message("TOGGLE_RECORDING"))
        """Toggles between starting and stopping the recording."""
        if self.recorder.recording:
            self.recorder.stop_recording()
            self.record_button.config(text="Start Recording")
            self.export_button.config(state=tk.NORMAL)  # Enable the export button when recording stops
            self.recorder.plot_data()

            # Send a message to the ESP32 to stop recording
            
        else:
            self.recorder.start_recording()
            self.record_button.config(text="Stop Recording")
            self.export_button.config(state=tk.DISABLED)  # Disable the export button while recording

            #Send a message to the ESP32 to start recording
            #asyncio.run(self.recorder.send_message("TOGGLE_RECORDING"))

    def update_live_graph(self):
        """Updates the live graph with the latest 10 seconds of live data."""
        if self.recorder.live_time_data and self.recorder.live_sensor_data:
            # Update graph data
            self.line.set_data(self.recorder.live_time_data, self.recorder.live_sensor_data)
            self.ax.set_xlim(max(0, self.recorder.live_time_data[0]), max(10, self.recorder.live_time_data[-1]))

        # Redraw the canvas
        self.canvas.draw()

        # Schedule the next update
        root.after(5, self.update_live_graph)  # Update every 100 ms


def run_event_loop(recorder):
    """Runs the WebSocket connection in a separate event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(recorder.receive_data())


# Main Application
if __name__ == "__main__":
    # Initialize the data recorder with the WebSocket URI
    #uri = "ws://192.168.0.168:81"  # Use your ESP32's IP address Field
    uri = "ws://192.168.0.168:81"  # Home
    recorder = DataRecorder(uri)

    # Start the Tkinter GUI
    root = tk.Tk()
    root.title("EMG Data Recorder")
    root.geometry("800x600")  # Larger window size to fit the graph

    # Initialize the graphical interface with the recorder
    gui = GraphicalInterface(root, recorder)
    
    # Ensure WebSocket connection closes on window exit
    root.protocol("WM_DELETE_WINDOW", lambda: [asyncio.run(recorder.close_connection()), root.destroy()])

    # Run the WebSocket client in a separate thread
    threading.Thread(target=run_event_loop, args=(recorder,), daemon=True).start()

    # Start the Tkinter main loop
    root.mainloop()
