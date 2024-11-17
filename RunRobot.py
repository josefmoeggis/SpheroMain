import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

import asyncio
from sphero_sdk import SpheroRvrAsync
from sphero_sdk import SerialAsyncDal
from sphero_sdk import RvrStreamingServices

loop = asyncio.get_event_loop()

try:
    rvr = SpheroRvrAsync(
        dal=SerialAsyncDal(
            loop
        )
    )
    print("RVR initialized successfully")
except Exception as e:
    print(f"Error initializing RVR: {e}")
    sys.exit(1)

async def imu_handler(imu_data):
    print('IMU data response: ', imu_data)

async def color_detected_handler(color_detected_data):
    print('Color detection data response: ', color_detected_data)

async def accelerometer_handler(accelerometer_data):
    print('Accelerometer data response: ', accelerometer_data)

async def ambient_light_handler(ambient_light_data):
    print('Ambient light data response: ', ambient_light_data)

async def encoder_handler(encoder_data):
    print('Encoder data response: ', encoder_data)

async def main():
    try:
        print("Starting main routine...")
        await rvr.wake()
        print("RVR awakened")

        # Give RVR time to wake up
        await asyncio.sleep(2)

        print("Setting up sensor handlers...")

        # Enable each sensor with error handling
        try:
            await rvr.sensor_control.add_sensor_data_handler(
                service=RvrStreamingServices.imu,
                handler=imu_handler
            )
            print("IMU sensor handler added")

            await rvr.sensor_control.add_sensor_data_handler(
                service=RvrStreamingServices.color_detection,
                handler=color_detected_handler
            )
            print("Color detection handler added")

            await rvr.sensor_control.add_sensor_data_handler(
                service=RvrStreamingServices.accelerometer,
                handler=accelerometer_handler
            )
            print("Accelerometer handler added")

            await rvr.sensor_control.add_sensor_data_handler(
                service=RvrStreamingServices.ambient_light,
                handler=ambient_light_handler
            )
            print("Ambient light handler added")

            await rvr.sensor_control.add_sensor_data_handler(
                service=RvrStreamingServices.encoders,
                handler=encoder_handler
            )
            print("Encoder handler added")

            print("Starting sensor streaming...")
            await rvr.sensor_control.start(interval=250)
            print("Sensor streaming started")

            # Let's also add a simple drive command to make sure the RVR is responsive
            await rvr.drive_control.roll_start(speed=0, heading=0)
            print("Drive control initialized")

        except Exception as e:
            print(f"Error setting up sensors: {e}")
            return

    except Exception as e:
        print(f"Error in main routine: {e}")

if __name__ == '__main__':
    try:
        print("Starting program...")
        asyncio.ensure_future(
            main()
        )
        print("Entering main loop...")
        loop.run_forever()

    except KeyboardInterrupt:
        print('\nProgram terminated with keyboard interrupt.')
        loop.run_until_complete(
            asyncio.gather(
                rvr.sensor_control.clear(),
                rvr.close()
            )
        )

    except Exception as e:
        print(f"Unexpected error: {e}")

    finally:
        if loop.is_running():
            loop.close()