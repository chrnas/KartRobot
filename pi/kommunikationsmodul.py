# förts biten, höger hjul, 1 för fram, 0 för bak
# andra, (0) 000  -  (0) 000

# 1111, 1111 fram
# 1100, 1001, höger
# 1001, 1100, vänster
# 0111, 0111, bak


import smbus
import socket
import time
from io import StringIO
import numpy as np
import queue
from auto import Block_type

instr_set = ['fwd', 'back', 'left', 'right', 'fwd_right', 'fwd_left', 'stop']


class Server:
    def __init__(self, motor):
        self.motor = motor
        self.connection = None
        self.client = None
        self.coord_data_queue = None
        self.active = False
        self.start_mapping = False
        self.pause_mapping = False
        self.stop_mapping = False
        self.unpause_mapping = False

    def init_map(self, map, pos):

        # Send start map to external computer
        for y, row in enumerate(map):
            for x, block in enumerate(row):
                if (x, y) == pos:
                    self.put_robot(x, y)
                elif block == Block_type.EMPTY:
                    self.put_empty(x, y)
                elif block == Block_type.WALL:
                    self.put_wall(x, y)
                # elif block == Block_type.UNKNOWN:
                    # self.put_unknown(x,y)

    def start_server(self, map, pos):

        # Start server
        self.connection = socket.socket(
            socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        self.connection.bind(("B8:27:EB:4E:FF:90", 4))
        self.connection.listen(1)

        print("Waiting for connection...")

        # Wait for connection
        self.client, addr = self.connection.accept()
        print(f"Accepted connection from {addr}")

        # Set active to true
        self.active = True

        # Init data queue
        self.coord_data_queue = queue.Queue()

        self.init_map(map, pos)

    # Format sdata

    def format_data(self, data):
        return "auto_drive: " + str(data[0]) + " ir_front: " + str(data[1]) + " ir_left " \
            + str(data[2]) + " ir_right: " + str(data[3]) + " odometer: " + str(data[4]) \
            + " gyro: " + str(data[5]) + " is_mapping: " + \
            str(data[6]) + " is_paused: " + str(data[7])

    def cycle_server(self, data_out):
        # Get data from external
        data_in = self.client.recv(1024)
        print(data_in)

        print(data_in.decode('utf-8'))

        # Check if data in
        if data_in:

            print(" in if")

            message_in = data_in.decode('utf-8')

            if message_in == "send data":
                message_out = self.format_data(data_out)

                # Check if something in data queue
                if not self.coord_data_queue.empty():
                    while not self.coord_data_queue.empty():
                        message_out = message_out + " " + self.coord_data_queue.get()

                 # Send data out
                self.client.send(message_out.encode('utf-8'))

            # If autodrive is off and message in instruction set, do instruction
            auto_drive = data_out[0]
            if auto_drive == 0 and message_in in instr_set:
                print(f"Received: {message_in}")
                self.motor.set_movement(message_in, 1)

            # If autodrive is on and message is 'start mapping', then start mapping
            elif auto_drive == 1:
                if message_in == 'start mapping':
                    message_out = ""
                    self.client.send(message_out.encode('utf-8'))
                    self.start_mapping = True
                elif message_in == 'pause mapping':
                    message_out = ""
                    self.client.send(message_out.encode('utf-8'))
                    self.pause_mapping = True
                elif message_in == 'stop mapping':
                    message_out = ""
                    self.client.send(message_out.encode('utf-8'))
                    self.stop_mapping = True
                elif message_in == "unpause mapping":
                    message_out = ""
                    self.client.send(message_out.encode('utf-8'))
                    self.unpause_mapping = True

    def mapping_started(self):
        return self.start_mapping

    def mapping_paused(self):

        return self.pause_mapping

    def mapping_stopped(self):

        return self.stop_mapping

    def mapping_unpaused(self):

        return self.unpause_mapping

    def reset_mapping_started(self):
        self.start_mapping = False

    def reset_mapping_stopped(self):
        self.stop_mapping = False

    def reset_mapping_paused(self):
        self.pause_mapping = False

    def reset_mapping_unpaused(self):
        self.unpause_mapping = False

    def close_server(self):

        print("Disconnected")

        self.client.close()
        self.connection.close()
        self.active = False

    def put_wall(self, x, y=-1):

        if not self.active:
            return

        if y == -1:
            x, y = x[0], x[1]

        message = "w " + str(x) + " " + str(y) + " "

        self.coord_data_queue.put(message)

    def put_robot(self, x, y=-1):

        if not self.active:
            return

        if y == -1:
            x, y = x[0], x[1]

        message = "r " + str(x) + " " + str(y) + " "

        self.coord_data_queue.put(message)

    def put_empty(self, x, y=-1):

        if not self.active:
            return

        if y == -1:
            x, y = x[0], x[1]

        message = "e " + str(x) + " " + str(y) + " "

        self.coord_data_queue.put(message)

    def put_unknown(self, x, y=-1):

        if not self.active:
            return

        if y == -1:
            x, y = x[0], x[1]

        message = "u " + str(x) + " " + str(y) + " "

        self.coord_data_queue.put(message)

    def put_path(self, x, y=-1):
        if not self.active:
            return

        if y == -1:
            x, y = x[0], x[1]

        message = "p " + str(x) + " " + str(y) + " "

        self.coord_data_queue.put(message)
