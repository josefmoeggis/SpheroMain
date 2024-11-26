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

#HOST = "10.22.119.215"
HOST = "10.22.20.251"
PORT_TX = 9090
PORT_RX = 9091

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

async def sensors(tof1, tof2, manager, host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((host, port))
            while True:
                try:
                    distance1, distance2, imu = await asyncio.gather(
                        ToF_read(tof1),
                        ToF_read(tof2),
                        asyncio.to_thread(manager.get_latest_imu_data),
                    )
                    await asyncio.sleep(0.1)
                    imu_rot_dict = imu['IMU']
                    imu_rot = [imu_rot_dict['Roll'], imu_rot_dict['Pitch'], imu_rot_dict['Yaw']]
                    imu_acc_dict = imu['Accelerometer']
                    imu_acc = [imu_acc_dict['X'], imu_acc_dict['Y'], imu_acc_dict['Z']]
                    distance = [distance1, distance2]
                    print(distance, imu_rot, imu_acc)
                    data_dict =  await com.pack_data(imu_rot, imu_acc, distance)
                    print('data is packed')
                    s.sendall(data_dict)
                    print('we got here')
                    await asyncio.sleep(0.1)
                except Exception as e:
                    print("Couldn't send or get sensorvals")
                    print(e)
                    await asyncio.sleep(0.5)
                    continue
        except Exception as e:
            s.shutdown(socket.SHUT_WR)
            print(f"Error unpacking response: {e}")



async def main():
    cam = camsen.SimpleBroadcaster(broadcast_ip=HOST)
    await rvr.wake()
    await asyncio.sleep(2)
    mux, tof1, tof2 = await camsen.dist_sensor_init()
    manager = camsen.IMUManager()
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

    tasks = [
        #asyncio.create_task(sensors(tof1, tof2, manager, HOST, PORT_TX)),
        asyncio.create_task(com.run_rx_client(rvr, HOST, PORT_RX)),
        asyncio.create_task(cam.start())
    ]
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        print("Tasks cancelled")
    await asyncio.sleep(0.1)




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