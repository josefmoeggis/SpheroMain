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

HOST = '0.0.0.0'
PORT_TX = '5000'
PORT_RX = '5001'
rvr.wake()
time.sleep(2)
cam = cam_sens.SimpleBroadcaster()
mux, tof1, tof2 = cam_sens.dist_sensor_init()

async def main():
    await cam.start()

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

    distance1, distance2, rot, acc  = await asyncio.gather(task1, task2, task3, task4)

    await com.run_tx_client(acc, rot, [distance1, distance2], HOST, PORT_TX)

    control_values = await com.run_rx_client(HOST, PORT_RX)
    await com.run_robot(control_values)

    await rvr.sensor_control.start(interval=250)


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