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

HOST = '10.22.185.93'
PORT_TX = '5001'
PORT_RX = '5002'

async def initialize():
    print("Starting initialization...")
    await rvr.wake()
    await asyncio.sleep(2)

    # Initialize sensors
    mux, tof1, tof2 = await cam_sens.dist_sensor_init()
    cam = cam_sens.SimpleBroadcaster()
    await cam.start()

    return tof1, tof2, cam

async def run_sensor_stream(tof1, tof2):
    print('sensor stream')
    while True:
        distance1, distance2, rot, acc = await asyncio.gather(
            cam_sens.ToF_read(tof1),
            cam_sens.ToF_read(tof2),
            rvr.sensor_control.add_sensor_data_handler(
                service=RvrStreamingServices.imu,
                handler=cam_sens.imu_handler),
            rvr.sensor_control.add_sensor_data_handler(
                service=RvrStreamingServices.accelerometer,
                handler=cam_sens.accelerometer_handler)
        )
        await com.run_tx_client(acc, rot, [distance1, distance2], HOST, PORT_TX)


async def run_commands(rvr):
    print('running program')
    while True:
        control_values = await com.run_rx_client(HOST, PORT_RX)
        await com.run_robot(control_values, rvr)
        await asyncio.sleep(0.25)


async def main(tof1, tof2, cam):
    await rvr.sensor_control.start(interval=250)
    tasks = [
        asyncio.create_task(cam.start(), name="camera"),
        asyncio.create_task(run_sensor_stream(rvr, tof1, tof2), name="sensors"),
        asyncio.create_task(run_commands(rvr), name="commands")
    ]
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    try:
        tof1, tof2, cam = loop.run_until_complete(initialize())

        loop.run_until_complete(main(tof1, tof2, cam))


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