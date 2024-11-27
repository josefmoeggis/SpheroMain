import asyncio
from sphero_sdk import SpheroRvrAsync
from sphero_sdk import SerialAsyncDal

rvr = SpheroRvrAsync(dal=SerialAsyncDal(asyncio.get_event_loop()))

async def main():
    await rvr.wake()
    await asyncio.sleep(2)
    await rvr.drive_with_heading(speed=100, heading=0)
    await asyncio.sleep(2)
    await rvr.drive_with_heading(speed=0, heading=0)
    await rvr.close()

if __name__ == '__main__':
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except KeyboardInterrupt:
        asyncio.get_event_loop().run_until_complete(rvr.close())
