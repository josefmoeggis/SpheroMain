import camera_sensors as cam_sens
import TCP_flexbuffers as com
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

import asyncio
from sphero_sdk import SpheroRvrAsync
from sphero_sdk import SerialAsyncDal
import time
from sphero_sdk import RvrStreamingServices


loop = asyncio.get_event_loop()

rvr = SpheroRvrAsync(
    dal=SerialAsyncDal(
        loop
    )
)

HOST = '10.22.116.65'
PORT_TX = '5000'
PORT_RX = '5001'
mux, tof1, tof2 = cam_sens.dist_sensor_init()

async def initialize():
    print("Starting initialization...")
    await rvr.wake()
    await asyncio.sleep(2)

    # Initialize sensors
    mux, tof1, tof2 = await cam_sens.dist_sensor_init()
    cam = cam_sens.SimpleBroadcaster()
    await cam.start()

    return mux, tof1, tof2, cam

async def main():
    await rvr.wake()
    await asyncio.sleep(2)


    await rvr.sensor_control.start(interval=250)

    while True:

        task1 = asyncio.create_task(cam_sens.ToF_read(tof1))
        task2 = asyncio.create_task(cam_sens.ToF_read(tof2))
        task3 = asyncio.create_task(rvr.sensor_control.add_sensor_data_handler(
            service=RvrStreamingServices.imu,
            handler=cam_sens.imu_handler
        ))
        task4 = asyncio.create_task(rvr.sensor_control.add_sensor_data_handler(
            service=RvrStreamingServices.accelerometer,
            handler=cam_sens.accelerometer_handler
        ))

        distance1, distance2, rot, acc = await asyncio.gather(task1, task2, task3, task4)


        await com.run_tx_client(acc, rot, [distance1, distance2], HOST, PORT_TX)
        control_values = await com.run_rx_client(HOST, PORT_RX)
        await com.run_robot(control_values)

        await asyncio.sleep(0.25)


if __name__ == '__main__':
    try:
        mux, tof1, tof2, cam = loop.run_until_complete(initialize())

        loop.run_until_complete(main(mux, tof1, tof2, cam))


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