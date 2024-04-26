'''
 main.py
 
 Created: 2023-10-31 09:51:57
 Author : G07
'''

import smbus
import time
import sensormodul
import styrmodul
import kommunikationsmodul
import auto

USING_BLUETOOTH = False


def main() -> int:

    # Init bus for I2C
    bus1 = smbus.SMBus(1)
    time.sleep(1)

    # Init sensors, motors, server and autopilot
    sensor = sensormodul.Sensor(bus1)
    motor = styrmodul.Motor(bus1, sensor)
    server = kommunikationsmodul.Server(motor)
    autopilot = auto.Autopilot(motor, server)

    old_start_drive = None
    start_flag_manual = False

    # If using bluetooth start server
    if USING_BLUETOOTH:
        print("Using bluetooth, starting server...")
        server.start_server(autopilot.map, autopilot.pos)

    # Main loop
    while True:
        try:
            try:
                data = sensor.read_sensors()  # Read sensors
            except Exception as e:
                print("Sensor error: ", e)
            else:

                auto_drive = data[0]  # Get auto drive status

                if USING_BLUETOOTH:

                    data.pop()  # Get rid of start_drive, not needed

                    # Add if currently mapping to data to sent to external computer
                    if autopilot.is_mapping():
                        data.append(1)
                    else:
                        data.append(0)

                    # Add if currently paused to data to sent to external computer
                    if autopilot.is_paused():
                        data.append(1)
                    else:
                        data.append(0)

                    try:
                        print("Performing bluetooth cycle...")
                        server.cycle_server(data)  # Perform bluetooth cycle
                        print("Bluetooth cycle done.")
                    except Exception as e:  # Lost connection
                        print("Bluetooth error: ", e)
                        motor.stop()
                        print("Restarting server...")
                        server.close_server()  # Close and restart server
                        server.start_server(autopilot.map, autopilot.pos)
                else:
                    # If not using bluetooth, get start drive button status
                    start_drive = data[6]

                    # If was none before just update status
                    if old_start_drive == None:
                        old_start_drive = start_drive

                    # If status changed and auto_drive is enabled raise start-flag
                    elif not (start_drive == old_start_drive):
                        old_start_drive = start_drive
                        if auto_drive == 1:
                            start_flag_manual = True

                # If auto drive enabled
                if auto_drive == 1:

                    # Got pause mapping from bt
                    if server.mapping_paused() and not autopilot.is_paused():
                        autopilot.pause_mapping()

                    # Got unpause mapping from bt
                    elif server.mapping_unpaused() and autopilot.is_paused():
                        autopilot.unpause_mapping()

                    # Got stop mapping from bt
                    elif server.mapping_stopped() and autopilot.is_mapping():
                        autopilot.stop_mapping()

                    # Got start mapping from bt
                    elif not autopilot.is_mapping() and server.mapping_started():  # External computer sent start mapping
                        autopilot.start_mapping()

                    # Got stop mapping from manual button
                    elif autopilot.is_mapping() and start_flag_manual:
                        autopilot.stop_mapping()
                        start_flag_manual = False

                    # Got start mapping from manual button
                    elif not autopilot.is_mapping() and start_flag_manual:
                        autopilot.start_mapping()
                        start_flag_manual = False

                    # Else perfrom autopilot cycle if mapping and not paused
                    elif autopilot.is_mapping() and not autopilot.is_paused():
                        print("Performing autopilot cycle...")
                        ir_data = data[1], data[2], data[3]
                        autopilot.cycle_autopilot(ir_data)
                        print("Autopilot cycle done.")

        # Stop program with Ctrl + C
        except KeyboardInterrupt:
            motor.stop()
            print("Keyboard interrupt: ", e)
            break

        # Other exceptions
        except Exception as e:
            motor.stop()
            print("Exception: ", e)
            raise TypeError("Error")

    return 0


if __name__ == '__main__':
    main()
