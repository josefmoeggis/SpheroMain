import qwiic_tca9548a
import qwiic_vl53l1x
import asyncio
from picamera2 import Picamera2
import socket
from PIL import Image
import io

#------------------------------------------ Camera class used through run_robot -----------------------------------
class SimpleBroadcaster:
    def __init__(self, broadcast_ip='10.22.119.215', port=5000, width=640, height=480):
        # Setup UDP socket for broadcasting
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.address = (broadcast_ip, port)
        print('intialized camera')

        # Setup camera
        self.camera = Picamera2()
        self.camera.configure(self.camera.create_preview_configuration(
            main={"size": (width, height), "format": "RGB888"},
            raw={"size": (width, height)}
        ))

    async def start(self):
        self.camera.start()
        print(f"Broadcasting to {self.address}")

        try:
            while True:
                frame = self.camera.capture_array()

                img = Image.fromarray(frame, 'RGB')  # Specify RGB mode problematic if not

                # Convert to JPEG
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=40)
                jpeg_data = buffer.getvalue()

                self.sock.sendto(len(jpeg_data).to_bytes(4, 'big'), self.address)

                chunk_size = 64000
                for i in range(0, len(jpeg_data), chunk_size):
                    chunk = jpeg_data[i:i + chunk_size]
                    self.sock.sendto(chunk, self.address)

                await asyncio.sleep(1/15)

        except asyncio.CancelledError:
           print("Camera broadcast cancelled")
        except Exception as e:
            print(f"Camera broadcast error: {e}")
        finally:
            self.camera.stop()
            self.sock.close()


#--------------------------------------------- ToF sensor stuff -----------------------------------------------------
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

    if ToF2.sensor_init() == 0:
        print("Sensor 2 online!\n")

    return mux, ToF, ToF2


async def ToF_read(tof):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            tof.start_ranging()
            await asyncio.sleep(.005)
            distance = tof.get_distance()
            await asyncio.sleep(.005)
            tof.stop_ranging()
            return distance
        except Exception as e:
            print(f"ToF read error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(0.01)
            else:
                return 0


#------------------------------------------ Handler to get values from IMU ----------------------------------------
class IMUManager:
    def __init__(self):
        self.latest_imu_data = {'IMU': {'Pitch': 0.0, 'Roll': 0.0, 'Yaw': 0.0}}
        self.latest_acc_data = {'Accelerometer': {'X': 0.0, 'Y': 0.0, 'Z': 0.0}}

    async def imu_handler(self, imu_data):
        self.latest_imu_data = imu_data

    async def accelerometer_handler(self, acc_data):
        self.latest_acc_data = acc_data

    def get_latest_imu_data(self):
        return self.latest_imu_data if self.latest_imu_data else {'IMU': {'Pitch': 0.0, 'Roll': 0.0, 'Yaw': 0.0}}

    def get_latest_acc_data(self):
        return self.latest_acc_data if self.latest_acc_data else {'Accelerometer': {'X': 0.0, 'Y': 0.0, 'Z': 0.0}}