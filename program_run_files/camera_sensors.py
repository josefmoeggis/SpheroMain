import qwiic_tca9548a
import qwiic_vl53l1x
import asyncio
from picamera2 import Picamera2
import socket
from PIL import Image
import io

class SimpleBroadcaster:
    def __init__(self, broadcast_ip='10.22.116.65', port=5000, width=320, height=240):
        # Setup UDP socket for broadcasting
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.address = (broadcast_ip, port)
        print('intialized camera')

        # Setup camera
        self.camera = Picamera2()
        self.camera.configure(self.camera.create_preview_configuration(
            main={"size": (width, height), "format": "RGB888"},  # Specify RGB format
            raw={"size": (width, height)}
        ))

    async def start(self):
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

                self.sock.sendto(len(jpeg_data).to_bytes(4, 'big'), self.address)

                chunk_size = 64000
                for i in range(0, len(jpeg_data), chunk_size):
                    chunk = jpeg_data[i:i + chunk_size]
                    self.sock.sendto(chunk, self.address)

                await asyncio.sleep(1/15)

        except KeyboardInterrupt:
            print("Stopping broadcast...")
        finally:
            self.camera.stop()
            self.sock.close()



async def dist_sensor_init():
    mux = qwiic_tca9548a.QwiicTCA9548A(address=0x70)
    await asyncio.sleep(.1)
    mux.disable_all()
    mux.enable_channels(1)
    await asyncio.sleep(.1)

    try:
        ToF = qwiic_vl53l1x.QwiicVL53L1X()
        ToF.set_i2c_address(0x20)
    except:
        ToF = qwiic_vl53l1x.QwiicVL53L1X(0x20)

    mux.enable_channels(7)
    await asyncio.sleep(.1)

    try:
        ToF2 = qwiic_vl53l1x.QwiicVL53L1X()
        ToF2.set_i2c_address(0x21)
    except:
        ToF2 = qwiic_vl53l1x.QwiicVL53L1X(0x21)

    if ToF.sensor_init() == 0:            # Begin returns 0 on a good init
        print("Sensor 1 online!\n")

    if ToF2.sensor_init() == 0:            # Begin returns 0 on a good init
        print("Sensor 2 online!\n")

    return mux, ToF, ToF2


async def ToF_read(tof):
    try:
        tof.start_ranging()
        await asyncio.sleep(.005)
        distance = tof.get_distance()    # Get the result of the measurement from the sensor
        await asyncio.sleep(.005)
        tof.stop_ranging()
        return distance
    except Exception as e:
        print(e)

class IMUManager:
    def __init__(self):
        self.latest_imu_data = None

    async def imu_handler(self, imu_data):
        self.latest_imu_data = imu_data
        return imu_data

    def get_latest_imu_data(self):
        return self.latest_imu_data