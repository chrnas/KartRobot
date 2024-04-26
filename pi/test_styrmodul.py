import smbus
import time
import sensormodul
import styrmodul
import statistics


def main() -> int:

    bus1 = smbus.SMBus(1)

    sensor = sensormodul.Sensor(bus1)
    motor = styrmodul.Motor(bus1, sensor)

    while True:

        try:
            motor.drive_forward(8)
            print(sensor.get_gyro())
            time.sleep(0.1)

        except KeyboardInterrupt:
            motor.stop()
            break

    return 0


if __name__ == '__main__':
    main()
