import serial
import time

class SerialManager:
    def __init__(self, port='/dev/ttyACM0', baudrate=115200):
        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=0.1
            )
            
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            
            time.sleep(0.1)
            print(f"Serial port {port} initialized at {baudrate} baud.")
            
        except serial.SerialException as e:
            print(f"Error: Could not open serial port {port}. {e}")
            self.ser = None

    def is_active(self):
        return self.ser is not None and self.ser.is_open

    def send_packet(self, running, detected, direction, clicking, fps, latency):
        if not self.is_active():
            return

        packet = f"#{int(running)},{int(detected)},{int(direction)},{int(clicking)},{int(fps)},{int(latency)}!\n"
        
        try:
            self.ser.write(packet.encode('ascii'))
        except Exception as e:
            print(f"Serial write error: {e}")

    def read_command(self):
        if not self.is_active():
            return None
        try:
            if self.ser.in_waiting > 0:
                line = self.ser.readline().decode('ascii').strip()
                return line
        except Exception as e:
            print(f"Serial read error: {e}")
        
        return None

    def close(self):
        if self.ser:
            self.ser.close()
