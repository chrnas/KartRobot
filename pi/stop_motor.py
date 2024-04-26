import smbus
import styrmodul
import time

MOTOR_ADDRESS = 0x7F
bus1 = smbus.SMBus(1)
bus1.write_byte(MOTOR_ADDRESS, 0b00000000)
time.sleep(0.001)
bus1.write_byte(MOTOR_ADDRESS, 0b10000000)
