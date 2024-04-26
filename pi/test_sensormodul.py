'''
 main.py
 
 Created: 2023-10-31 09:51:57
 Author : G07
'''

import smbus
import time
import sensormodul


def main() -> int:

    bus1 = smbus.SMBus(1)
    time.sleep(1)

    sensor = sensormodul.Sensor(bus1)

    while True:
        automatic_drive, ir_front, ir_left, ir_right, odometer, gyro, start_drive = sensor.read_sensors()
        print("atuomatic_drive", automatic_drive, "\tIR-fr:", ir_front, "\tIR-le:", ir_left,
              "\tIR-ri:", ir_right, "\tOdometer:", odometer, "\tGyro:", gyro, "\tstart:", start_drive)

    return 0


if __name__ == '__main__':
    main()
