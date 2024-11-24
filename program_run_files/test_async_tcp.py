import os
import sys
import camera_sensors as camsen
import TCP_flexbuffers as com

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
async def imu_handler(imu_data):
    return imu_data

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

async def sensors(tof1, tof2, manager):
    distance1, distance2, imu = await asyncio.gather(
        ToF_read(tof1),
        ToF_read(tof2),
        asyncio.to_thread(manager.get_latest_imu_data),
    )
    return distance1, distance2, imu

async def main():
    await rvr.wake()
    await asyncio.sleep(2)
    mux, tof1, tof2 = await camsen.dist_sensor_init()
    manager = camsen.IMUManager()
    await rvr.sensor_control.add_sensor_data_handler(
        service=RvrStreamingServices.imu,
        handler=manager.imu_handler
    )
    await rvr.sensor_control.start(interval=250)

    while True:
        distance1, distance2, imu = await sensors(tof1, tof2, manager)
        print(distance1, distance2, imu)
        await com.run_tx_client(imu, imu, [distance1, distance2], HOST, PORT)

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