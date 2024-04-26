import smbus
import time
from enum import Enum
from ir_conversion import linearize_ir_data

SENSOR_ADDRESS = 0x24
IR_LEFT_ERROR = 1.5


class Internal_address(Enum):
    AUTOMATIC_DRIVE = 0
    IR_FRONT = 1
    IR_LEFT = 2
    IR_RIGHT = 3
    ODOMETER_H = 4
    ODOMETER_L = 5
    GYRO = 6
    START_DRIVE = 7


class Sensor:
    def __init__(self, bus):
        self.bus = bus

    def get_automatic_drive(self):
        self.set_sensor(Internal_address.AUTOMATIC_DRIVE)

        return self.read_current_sensor()

    def get_ir_front(self):
        self.set_sensor(Internal_address.IR_FRONT)

        return linearize_ir_data(self.read_current_sensor())

    def get_ir_left(self):
        self.set_sensor(Internal_address.IR_LEFT)

        data = linearize_ir_data(self.read_current_sensor())
        
        if 0 < data < 255:
            return data + IR_LEFT_ERROR
        else:
            return data
        
    def get_ir_right(self):
        self.set_sensor(Internal_address.IR_RIGHT)

        return linearize_ir_data(self.read_current_sensor())

    def get_odometer_h(self):
        self.set_sensor(Internal_address.ODOMETER_H)

        return self.read_current_sensor()

    def get_odometer_l(self):
        self.set_sensor(Internal_address.ODOMETER_L)

        return self.read_current_sensor()

    def get_odometer(self):
        odometer_h = self.get_odometer_h()
        odometer_l = self.get_odometer_l()

        return (odometer_h << 8) | odometer_l

    def get_gyro(self):
        self.set_sensor(Internal_address.GYRO)

        return self.read_current_sensor()

    def get_start_drive(self):
        self.set_sensor(Internal_address.START_DRIVE)

        return self.read_current_sensor()

    def set_sensor(self, sensor):
        self.bus.write_byte(SENSOR_ADDRESS, sensor.value)
        time.sleep(0.01)

    def read_current_sensor(self):
        result = self.bus.read_byte(SENSOR_ADDRESS)

        return result

    # Read all sensors
    def read_sensors(self):

        automatic_drive = self.get_automatic_drive()
        ir_front = self.get_ir_front()
        ir_left = self.get_ir_left()
        ir_right = self.get_ir_right()
        odometer = self.get_odometer()
        gyro = self.get_gyro()
        start_drive = self.get_start_drive()

        return [automatic_drive, ir_front, ir_left, ir_right, odometer, gyro, start_drive]
