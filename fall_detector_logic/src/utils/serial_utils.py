import queue
import threading
import time
import serial
import serial.tools.list_ports

class AsyncSerialReader:
    """
    A threaded serial reader to prevent main thread blocking while collecting high-speed CSI data.
    """
    def __init__(self, port, baud_rate=921600, timeout=1):
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.serial_conn = None
        self.is_running = False
        self.thread = None
        self.data_queue = queue.Queue(maxsize=10000)
    
    @staticmethod
    def get_available_ports():
        return [port.device for port in serial.tools.list_ports.comports()]
    
    def connect(self):
        try:
            self.serial_conn = serial.Serial(self.port, self.baud_rate, timeout=self.timeout)
            # Increase RX buffer size to 1MB to prevent overflow during CSI bursts
            self.serial_conn.set_buffer_size(rx_size=1048576, tx_size=1048576)
            # Clear buffers
            self.serial_conn.reset_input_buffer()
            self.serial_conn.reset_output_buffer()
            return True
        except serial.SerialException as e:
            print(f"Error connecting to {self.port}: {e}")
            return False

    def _read_loop(self):
        while self.is_running and self.serial_conn and self.serial_conn.is_open:
            try:
                line = self.serial_conn.readline()
                if line:
                    decoded = line.decode('utf-8', errors='ignore').strip()
                    if decoded.startswith("CSI_DATA"):
                        if not self.data_queue.full():
                            self.data_queue.put_nowait(decoded)
            except Exception as e:
                print(f"Serial read error: {e}")
                time.sleep(0.1)

    def start(self):
        if not self.serial_conn and not self.connect():
            raise ConnectionError(f"Could not open serial port {self.port}")
        
        self.is_running = True
        self.thread = threading.Thread(target=self._read_loop, daemon=True)
        self.thread.start()
        print(f"Started reading from {self.port} at {self.baud_rate} baud")

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        print("Serial reader stopped.")

    def get_lines(self, max_lines=None):
        """Get accumulated lines from the queue"""
        lines = []
        count = 0
        while not self.data_queue.empty():
            if max_lines and count >= max_lines:
                break
            try:
                lines.append(self.data_queue.get_nowait())
                count += 1
            except queue.Empty:
                break
        return lines

    def clear(self):
        with self.data_queue.mutex:
            self.data_queue.queue.clear()
