from picamera2 import Picamera2
import socket
import time
from PIL import Image
import io

class SimpleBroadcaster:
    def __init__(self, broadcast_ip='10.22.116.65', port=5000, width=640, height=480):
        # Setup UDP socket for broadcasting
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.address = (broadcast_ip, port)

        # Setup camera
        self.camera = Picamera2()
        self.camera.configure(self.camera.create_preview_configuration(
            main={"size": (width, height), "format": "RGB888"},  # Specify RGB format
            raw={"size": (width, height)}
        ))

    def start(self):
        self.camera.start()
        print(f"Broadcasting to {self.address}")

        try:
            while True:
                # Capture frame
                frame = self.camera.capture_array()

                # Convert to PIL Image and ensure RGB mode
                img = Image.fromarray(frame, 'RGB')  # Specify RGB mode

                # Convert to JPEG
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=50)
                jpeg_data = buffer.getvalue()

                # Send frame size first
                self.sock.sendto(len(jpeg_data).to_bytes(4, 'big'), self.address)

                chunk_size = 64000
                for i in range(0, len(jpeg_data), chunk_size):
                    chunk = jpeg_data[i:i + chunk_size]
                    self.sock.sendto(chunk, self.address)

                time.sleep(1/30)

        except KeyboardInterrupt:
            print("Stopping broadcast...")
        finally:
            self.camera.stop()
            self.sock.close()

if __name__ == "__main__":
    broadcaster = SimpleBroadcaster()
    broadcaster.start()