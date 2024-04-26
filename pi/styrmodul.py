import smbus
import time
import sensormodul
import json

GYRO_GAIN = 1/3
TURN_COEFF = 90*GYRO_GAIN
STOP_TURN_COEFF = 3.0
GYRO_OFFSET = 127
DRIVE_COEFF = 84
STOP_DRIVE_COEFF = 11
IR_FAIL_SAFE_COEFF = 15
MOTOR_ADDRESS = 0x7F
GYRO_INTERNAL_ADDRESS = 6
KP = -0.027
KD = -0.025
GYRO_REGULATION_FACTOR = 0.005
MAX_REGULATION_DIFF = 0.2
WANTED_WALL_DISTANCE = 11
REGULATOR_DISTANCE_THRESHOLD = 20
KD_TIME_DELTA = 0.5
PD_REGULATION = True
GYRO_REGULATION = True


class Motor:
    def __init__(self, bus, sensor):
        self.bus = bus
        self.sensor = sensor
        self.direction = None
        self.verbose = True

    def log(self, msg):
        if self.verbose:
            print("Styrmodul:")
            if isinstance(msg, dict):
                print(json.dumps(msg, indent=2))
            else:
                print(msg)
            print("\n")

    # Stop motors
    def stop(self):

        self.set_movement('stop')

    # Turn left 90*n degrees

    def turn_left(self, n):
        total_rotation = 0
        speed = 0.75
        max_reached = False
        slowed_down = False
        slowed_down_rotation = TURN_COEFF/2
        expected_rotation = TURN_COEFF*n-STOP_TURN_COEFF

        self.sensor.set_sensor(sensormodul.Internal_address.GYRO)

        self.set_movement('left', speed)

        start_time = time.time()
        speed_change_time = start_time

        while True:

            # Calculate the time passed since start of rotation
            new_time = time.time()
            time_passed = new_time - start_time
            total_rotation = total_rotation + time_passed * \
                (self.sensor.read_current_sensor() - GYRO_OFFSET)

            # Increase speed every 0.05 seconds
            if not max_reached and not slowed_down:
                if (new_time - speed_change_time) >= 0.05 and speed < 1:
                    speed = speed + 0.05
                    self.set_movement('left', speed)
                    speed_change_time = new_time
                elif speed == 1:
                    max_reached = True

            # Slow down, preparation for stop
            if total_rotation >= expected_rotation-slowed_down_rotation and not slowed_down:
                self.set_movement('left', 0.5)
                slowed_down = True

            # If turned 90*n degrees stop (cefficient calculated with tests)
            if (total_rotation >= expected_rotation):
                self.set_movement('stop')
                break

            start_time = new_time

    # Same as turn_left with different handling of the gyro value
    def turn_right(self, n):

        total_rotation = 0
        speed = 0.75
        expected_rotation = TURN_COEFF*n-STOP_TURN_COEFF
        slowed_down_rotation = TURN_COEFF/2
        max_reached = False
        slowed_down = False

        self.sensor.set_sensor(sensormodul.Internal_address.GYRO)

        self.set_movement('right', speed)

        start_time = time.time()
        speed_change_time = start_time

        while True:

            new_time = time.time()
            time_passed = new_time - start_time
            total_rotation = total_rotation + time_passed * \
                (GYRO_OFFSET - self.sensor.read_current_sensor())

            if not max_reached and not slowed_down:
                if (new_time - speed_change_time) >= 0.05 and speed < 1:
                    speed = speed + 0.05
                    self.set_movement('right', speed)
                    speed_change_time = new_time
                elif speed == 1:
                    max_reached = True

            if total_rotation >= expected_rotation-slowed_down_rotation and not slowed_down:
                self.set_movement('right', 0.5)
                slowed_down = True

            if total_rotation >= expected_rotation:
                self.set_movement('stop')
                break

            start_time = new_time

    def reg_value(self, distance, last_distance):
        reg_add = 0

        if distance < REGULATOR_DISTANCE_THRESHOLD:
            if PD_REGULATION:
                D_value = KD * (distance - last_distance) / KD_TIME_DELTA
                self.log("distance: " + str(distance) +
                         "\nlast_distance: " + str(last_distance))
            else:
                D_value = 0

            P_value = KP * (distance - WANTED_WALL_DISTANCE)

            reg_add = P_value + D_value
            self.log("KP: " + str(P_value) + "KD: " + str(D_value))
            # Make sure the resulting value not get overflow
            reg_add = reg_add if reg_add <= MAX_REGULATION_DIFF else MAX_REGULATION_DIFF
            reg_add = reg_add if reg_add >= -MAX_REGULATION_DIFF else -MAX_REGULATION_DIFF

            self.log(reg_add)
        return reg_add

    def reg_value_gyro(self, gyro, last_gyro):
        gyro = gyro - 127
        last_gyro = last_gyro - 127
        reg_add = 0

        if PD_REGULATION:
            D_value = KD * (gyro - last_gyro) / KD_TIME_DELTA
            self.log("distance: " + str(gyro) +
                     "\nlast_distance: " + str(last_gyro))
        else:
            D_value = 0

        P_value = KP * (gyro - 127)

        reg_add = (P_value + D_value) * GYRO_REGULATION_FACTOR
        self.log("KP: " + str(P_value) + "KD: " + str(D_value))
        # Make sure the resulting value not get overflow
        reg_add = reg_add if reg_add <= MAX_REGULATION_DIFF else MAX_REGULATION_DIFF
        reg_add = reg_add if reg_add >= -MAX_REGULATION_DIFF else -MAX_REGULATION_DIFF

        self.log(reg_add)
        return reg_add

    def drive_forward(self, n):

        # Get initial odometer value
        odometer_old = self.sensor.get_odometer()

        # Start driving forward
        self.set_movement('fwd', 0.7)

        # PD_REGULATION
        start_time = round(time.time(), 1)
        past_values = {}

        reg_left = False
        reg_right = False

        while True:
            now = round(time.time(), 1)

            ir_right = self.sensor.get_ir_right()
            ir_left = self.sensor.get_ir_left()
            gyro = self.sensor.get_gyro()

            # PD REGULATION
            past_values[str(now)] = (ir_right, ir_left, gyro)
            # wait until KD_TIME_DELTA has passed before first PD term can be added
            if now - start_time > KD_TIME_DELTA:
                past_val = past_values.get(str(now - KD_TIME_DELTA))
                last_ir_right = past_val[0] or ir_right
                last_ir_left = past_val[1] or ir_left
                last_gyro = past_val[2] or gyro
            else:
                last_ir_right = ir_right
                last_ir_left = ir_left
                last_gyro = gyro

            speed_left = 0.6
            speed_right = 0.6
            

            if ir_right < REGULATOR_DISTANCE_THRESHOLD and ir_right < ir_left and not reg_left:
                reg_right = True

                reg = self.reg_value(ir_right, last_ir_right)
                speed_right += reg
                speed_left -= reg
            elif ir_left < REGULATOR_DISTANCE_THRESHOLD and ir_left < ir_right and not reg_right:
                reg_left = True

                reg = self.reg_value(ir_left, last_ir_left)
                speed_left += reg
                speed_right -= reg
            else:  # gyro
                if GYRO_REGULATION:
                    reg = self.reg_value_gyro(gyro, last_gyro)
                    speed_left += reg
                    speed_right -= reg

                reg_right = False
                reg_left = False

            self.set_movement("fwd", speed_left, speed_right)

            # Get current odometer value
            odometer = self.sensor.get_odometer()

            # Get current ir_front value
            ir_front = self.sensor.get_ir_front()

            # Stop if driven 40*n cm (cefficient calculated with tests) or if about to drive into wall
            if ((odometer - odometer_old) >= (DRIVE_COEFF*n-STOP_DRIVE_COEFF)) or ir_front <= IR_FAIL_SAFE_COEFF:
                self.set_movement('stop')
                break

    # Same as drive_forward without IR fail safe and regulation
    def drive_backward(self, n):

        odometer_old = self.sensor.get_odometer()
        speed = 0.75

        self.set_movement('back', speed)

        while True:

            odometer = self.sensor.get_odometer()

            if (odometer - odometer_old) >= (DRIVE_COEFF*n-STOP_DRIVE_COEFF):
                self.set_movement('stop')
                break

    # Conver direction and speed to bytes and send to I2C

    def set_movement(self, direction, n=0, n1=0):

        speed = format(round(n*63), '06b')

        if direction == "fwd":
            # speed = 0b11111111 if regspeed == 0 else regspeed

            speed_left = int("01" + speed, 2)

            speed1 = format(round(n1*63), '06b') if n1 else speed
            speed_right = int("11" + speed1, 2)

            self.bus.write_byte(MOTOR_ADDRESS, speed_left)
            time.sleep(0.005)
            self.bus.write_byte(MOTOR_ADDRESS, speed_right)
            time.sleep(0.001)

        elif direction == "back":
            speed_left = int("00" + speed, 2)
            speed_right = int("10" + speed, 2)
            self.bus.write_byte(MOTOR_ADDRESS, speed_left)
            time.sleep(0.005)
            self.bus.write_byte(MOTOR_ADDRESS, speed_right)
            time.sleep(0.001)

        elif direction == "right":
            speed_left = int("01" + speed, 2)
            speed_right = int("10" + speed, 2)
            self.bus.write_byte(MOTOR_ADDRESS, speed_left)
            time.sleep(0.005)
            self.bus.write_byte(MOTOR_ADDRESS, speed_right)
            time.sleep(0.001)

        elif direction == "left":

            speed_left = int("00" + speed, 2)
            speed_right = int("11" + speed, 2)
            self.bus.write_byte(MOTOR_ADDRESS, speed_left)
            time.sleep(0.005)
            self.bus.write_byte(MOTOR_ADDRESS, speed_right)
            time.sleep(0.001)

        elif direction == "fwd_right":

            slower_wheel = format(int(speed, 2) >> 2, '06b')

            speed_left = int("01" + speed, 2)
            speed_right = int("11" + slower_wheel, 2)

            self.bus.write_byte(MOTOR_ADDRESS, speed_left)
            time.sleep(0.005)
            self.bus.write_byte(MOTOR_ADDRESS, speed_right)
            time.sleep(0.001)

        elif direction == "fwd_left":
            slower_wheel = format(int(speed, 2) >> 2, '06b')

            speed_left = int("01" + slower_wheel, 2)
            speed_right = int("11" + speed, 2)
            self.bus.write_byte(MOTOR_ADDRESS, speed_left)
            time.sleep(0.005)
            self.bus.write_byte(MOTOR_ADDRESS, speed_right)
            time.sleep(0.001)

        elif direction == "stop":

            speed_left = 0b00000000
            speed_right = 0b10000000
            self.bus.write_byte(MOTOR_ADDRESS, speed_left)
            time.sleep(0.005)
            self.bus.write_byte(MOTOR_ADDRESS, speed_right)
            time.sleep(0.001)

        self.direction = direction
