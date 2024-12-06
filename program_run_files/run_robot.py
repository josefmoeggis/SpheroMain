import os
import sys
import camera_sensors as camsen
import TCP_flexbuffers as com
import socket
import pi_servo_hat


# USE THIS FILE AS BASE FOR MAIN IN FUTURE JOSEF
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

import asyncio
from sphero_sdk import SpheroRvrAsync
from sphero_sdk import SerialAsyncDal
from sphero_sdk import RvrStreamingServices

HOST = "10.22.119.83"
#HOST = "10.22.20.251"
PORT_TX = 9090
PORT_RX = 9091

loop = asyncio.get_event_loop()

rvr = SpheroRvrAsync(
    dal=SerialAsyncDal(
        loop
    )
)

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
                await asyncio.sleep(0.01)  # Short delay between retries
            else:
                return 0

async def sensors(tof1, tof2, manager, host, port):
    while True:
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
                        imu_rot_dict = imu['IMU']
                        imu_rot = [imu_rot_dict['Roll'], imu_rot_dict['Pitch'], imu_rot_dict['Yaw']]
                        imu_acc_dict = imu['Accelerometer']
                        imu_acc = [imu_acc_dict['X'], imu_acc_dict['Y'], imu_acc_dict['Z']]
                        distance = [distance1, distance2]
                        data_dict =  await com.pack_data(imu_rot, imu_acc, distance)
                        s.sendall(data_dict)
                        await asyncio.sleep(0.05)
                    except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError) as e:
                        print(f"Sensors: Connection lost: {e}")
                        break  # Break inner loop to trigger reconnection

                    except Exception as e:
                        print(f"Sensors: Error reading or sending sensor data: {e}")
                        await asyncio.sleep(0.002)
                        continue  # Continue trying to read/send if it's a temporary error

            except (ConnectionRefusedError, socket.error) as e:
                print(f"Sensors: Connection failed: {e}, retrying in 1 second...")
                await asyncio.sleep(1)  # Wait before retrying connection

            except Exception as e:
                print(f"Sensors: Unexpected error: {e}, retrying in 1 second...")
                await asyncio.sleep(1)



async def main():
    while True:  # Add outer loop to keep restarting tasks
        try:
            cam = camsen.SimpleBroadcaster(broadcast_ip=HOST)
            await rvr.wake()
            await asyncio.sleep(2)
            mux, tof1, tof2 = await camsen.dist_sensor_init()
            manager = camsen.IMUManager()
            servo = pi_servo_hat.PiServoHat()
            servo.restart()
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
                asyncio.create_task(sensors(tof1, tof2, manager, HOST, PORT_TX)),
                asyncio.create_task(com.run_rx_client(servo, rvr, HOST, PORT_RX)),
                asyncio.create_task(cam.start())
            ]

            done, pending = await asyncio.wait(
                tasks,
                return_when=asyncio.FIRST_COMPLETED
            )

            # Cancel remaining tasks
            for task in pending:
                task.cancel()

            # Wait for cancellation to complete
            await asyncio.gather(*pending, return_exceptions=True)

            print("Tasks ended, restarting in 1 second...")
            await asyncio.sleep(1)

        except Exception as e:
            print(f"Main loop error: {e}")
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