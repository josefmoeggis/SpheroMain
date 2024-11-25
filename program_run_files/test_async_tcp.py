import os
import sys
import camera_sensors as camsen
import TCP_flexbuffers as com
import socket

# USE THIS FILE AS BASE FOR MAIN IN FUTURE JOSEF
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

import asyncio
from sphero_sdk import SpheroRvrAsync
from sphero_sdk import SerialAsyncDal
from sphero_sdk import RvrStreamingServices

HOST = "10.22.119.215"
PORT = 5001

loop = asyncio.get_event_loop()

rvr = SpheroRvrAsync(
    dal=SerialAsyncDal(
        loop
    )
)

async def ToF_read(tof):
    try:
        tof.start_ranging()
        await asyncio.sleep(.005)
        distance = tof.get_distance()
        await asyncio.sleep(.005)
        tof.stop_ranging()
        return distance
    except Exception as e:
        print(e)

async def sensors_tx(tof1, tof2, manager):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, PORT))
            print('connected')
            while True:
                distance1, distance2, imu = await asyncio.gather(
                    ToF_read(tof1),
                    ToF_read(tof2),
                    asyncio.to_thread(manager.get_latest_imu_data),
                )
                imu_rot_dict = imu['IMU']
                imu_rot = [imu_rot_dict['Roll'], imu_rot_dict['Pitch'], imu_rot_dict['Yaw']]
                imu_acc_dict = imu['Accelerometer']
                imu_acc = [imu_acc_dict['X'], imu_acc_dict['Y'], imu_acc_dict['Z']]
                print(imu_rot)
                await com.run_tx_client(imu_rot, imu_acc, [distance1, distance2], s)
                await asyncio.sleep(0.2)

        except Exception as e:
            print(f"Error in tx_client: {e}")

        finally:
            s.shutdown(socket.SHUT_WR)


async def main():
    #cam = camsen.SimpleBroadcaster(broadcast_ip=HOST)
    await rvr.wake()
    await asyncio.sleep(2)
    mux, tof1, tof2 = await camsen.dist_sensor_init()
    manager = camsen.IMUManager()
    #camera_task = asyncio.create_task(cam.start())
    await rvr.sensor_control.add_sensor_data_handler(
        service=RvrStreamingServices.imu,
        handler=manager.imu_handler
    )
    await asyncio.sleep(0.1)
    await rvr.sensor_control.add_sensor_data_handler(
        service=RvrStreamingServices.accelerometer,
        handler=manager.accelerometer_handler
    )
    await asyncio.sleep(0.1)
    await rvr.sensor_control.start(interval=250)
    # await cam.start()

    try:
        print('i got here')
        sensor_task = asyncio.create_task(sensors_tx(tof1, tof2, manager))
        print('i got here 2')
    except Exception as e:
        print(f"Error in main loop: {e}")
        await asyncio.sleep(1)


if __name__ == '__main__':
    try:
        asyncio.ensure_future(
            main()
        )
        loop.run_forever()


    except KeyboardInterrupt:
        print('\nProgram terminated with keyboard interrupt.')

        loop.run_until_complete(
            asyncio.gather(
                rvr.sensor_control.clear(),
                rvr.close()
            )
        )

    finally:
        if loop.is_running():
            loop.close()