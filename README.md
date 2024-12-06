# AIS2203 Rover Python Code
## Group 3

This is the final code of what is running on the Sphero RVR.
Everything is written in ``asyncio`` code and the pile of test files are not included.

It is divided into three main .py files
- ``run_robot.py``
- ``camera_sensors.py``
- ``TCP_flexbuffers.py``

### Run robot
In ``run_robot.py`` we have the `main()` function. So here lies both the initialization and the running of the sphero program.
This is where the rvr loop is, and all other functions are called.

### Camera & sensors
The camera class and sensor functions are in the `camera_sensors.py` file. Additionally, there is an ``IMUManager`` class here, that includes the IMU handlers for the RVR. 
``SimpleBroadcaster`` was not so simple by the end.

### TCP and flexbuffer
Flexbuffer and TCP transmission is mainly in the ``run_robot.py`` file.
So, the ``TCP_flexbuffers.py`` name is not a completely honest name. However, this file does include the whole process of receiving commands and running the robot.
