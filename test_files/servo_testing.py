
import pi_servo_hat
import time
test = pi_servo_hat.PiServoHat()
test.restart()


# Moves servo position to 0 degrees (1ms), Channel 0
test.move_servo_position(0, 0)

# Pause 1 sec
time.sleep(1)

# Moves servo position to 90 degrees (2ms), Channel 0
test.move_servo_position(0, 30)

# Pause 1 sec
time.sleep(1)
