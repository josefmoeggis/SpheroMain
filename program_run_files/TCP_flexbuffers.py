from flatbuffers import flexbuffers as flex
import socket
import asyncio

async def run_tx_client(acc_data, rot_data, dist_data, HOST, PORT):
    print('running tx')
    builder = flex.Builder()

    with builder.Map():
        builder.Key('acc')
        builder.TypedVectorFromElements(acc_data, flex.Type.FLOAT)
        builder.Key('rot')
        builder.TypedVectorFromElements(rot_data, flex.Type.FLOAT)
        builder.Key('dist')
        builder.TypedVectorFromElements(dist_data, flex.Type.FLOAT)

    packed_dict = builder.Finish()

    try:
        reader, writer = await asyncio.open_connection(HOST, PORT)
        writer.write(packed_dict)
        await writer.drain()
        writer.close()
        await writer.wait_closed()
    except Exception as e:
        print(f"Error sending data: {e}")

async def run_robot(response_dict, rvr):
    print('running robot')
    try:
        left_mode = response_dict['leftMode']
        left_speed = response_dict['leftSpeed']
        right_mode = response_dict['rightMode']
        right_speed = response_dict['rightSpeed']
        servo1 = response_dict['cameraYaw']
        servo2 = response_dict['cameraPitch']
        heading_mode = response_dict['headingMode']
        speed = response_dict['speed']
        heading = response_dict['heading']
        flags = response_dict['flags']

        if heading_mode:
            rvr.drive_with_heading(speed, heading, flags)
            print('true')
        else:
            rvr.raw_motors(
                left_mode=left_mode,
                left_duty_cycle=left_speed,
                right_mode=right_mode,
                right_duty_cycle=right_speed
            )

        print(f'Right: {right_speed}, Left: {left_speed}, servo1: {servo1}, servo2: {servo2}, '
              f'left_mode: {left_mode}, right_mode: {right_mode}, headingMode: {heading_mode}, '
              f'speed: {speed}, heading: {heading}')

    except Exception as e:
        print(f"Error processing command: {e}")



async def run_rx_client(HOST, PORT):
    print('running rx')
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))

            # Set a timeout to avoid hanging
            await asyncio.sleep(.1)

            buffer = b''
            while True:
                try:
                    chunk = s.recv(1024)
                    if not chunk:
                        break
                    buffer += chunk

                    # Process complete messages
                    if len(buffer) >= 4:  # Min størrlse msg
                        root = flex.GetRoot(buffer)
                        response_dict = root.Value

                        buffer = b''
                        return response_dict

                except socket.timeout:
                    # No data received, continue listening
                    continue
                except Exception as e:
                    print(f"Error receiving data: {e}")
                    break

    except Exception as e:
        print(f"Connection error: {e}")
        await asyncio.sleep(1)  # Wait before retrying connection