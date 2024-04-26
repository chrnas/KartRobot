from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
import socket
from keyPressed import *


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.connected = False  # Flagga för att hålla koll på om anslutningen är etablerad
        self.send_coord = True
        self.is_mapping = False
        self.paused_mapping = False
        self.auto_drive = None

        self.robot_x = 0
        self.robot_y = 0

        self.initMap()
        self.initTerminal()
        self.initButton()
        self.initLabels()
        self.initKeyPress()
        self.initTimer()
        self.initLayout()

        # Skapa en palett för bakgrundsfärg
        self.palette = self.palette()
        self.palette.setColor(self.backgroundRole(),
                              QColor.fromRgb(36, 36, 36))
        self.setPalette(self.palette)

    def initButton(self):
        self.connect_button = QPushButton("Connect to robot")
        self.connect_button.clicked.connect(self.connectToBT)
        self.connect_button.setStyleSheet("background-color: #E6E6E6;"
                                          "border-style: outset;"
                                          "color: #383838;"
                                          "border-radius: 10px;"
                                          "border-color: #BFBFBF;"
                                          "border-width: 3px;"
                                          "padding: 6px;"
                                          "font: bold 14px;"
                                          "height: 30px;")
        self.start_map_button = QPushButton("Start mapping")
        self.start_map_button.clicked.connect(self.start_mapping)
        self.start_map_button.setStyleSheet("background-color: #E6E6E6;"
                                            "border-style: outset;"
                                            "color: #383838;"
                                            "border-radius: 10px;"
                                            "border-color: #BFBFBF;"
                                            "border-width: 3px;"
                                            "padding: 6px;"
                                            "font: bold 14px;"
                                            "height: 30px;")
        self.pause_map_button = QPushButton("Pause mapping")
        self.pause_map_button.clicked.connect(self.pause_mapping)
        self.pause_map_button.setStyleSheet("background-color: #E6E6E6;"
                                            "border-style: outset;"
                                            "color: #383838;"
                                            "border-radius: 10px;"
                                            "border-color: #BFBFBF;"
                                            "border-width: 3px;"
                                            "padding: 6px;"
                                            "font: bold 14px;"
                                            "height: 30px;")

    def initTimer(self):
        # Skapa en timer för att periodiskt hämta väggkoordinater från Bluetooth-enhetens
        self.timer = QTimer()
        self.timer.timeout.connect(self.getCoords)
        self.timer.setInterval(500)

    def initKeyPress(self):
        # Skapa en nyckelpressfiltreringsinstans
        self.eventFilter = KeyPressFilter(parent=self)
        self.installEventFilter(self.eventFilter)

    def initTerminal(self):
        self.terminal = QTextEdit()
        self.terminal.setFixedHeight(200)
        self.terminal.setTextColor(QColor.fromRgb(114, 250, 48))
        self.terminal.setStyleSheet("background-color: #383838;"
                                    "border-color: none;"
                                    "border-radius: 7px;"
                                    "color: #72FA30;")

    def initRobot(self):
        robot = QGraphicsRectItem(800, 800, 20, 20)
        brush_robot = QBrush(QColor.fromRgb(0, 250, 225))
        robot.setBrush(brush_robot)
        self.map_scene.addItem(robot)

    def initMap(self):
        self.map_scene = QGraphicsScene(0, 0, 1600, 1600)

        self.map_view = QGraphicsView()
        self.map_view.setScene(self.map_scene)
        # self.map_view.setFixedSize(800, 400)
        self.map_view.setStyleSheet("background-color: #383838;"
                                    "border-color: none;"
                                    "border-radius: 7px;")

    def initLabels(self):
        self.user_drive_status = QLabel("User drive: ", self)
        self.user_drive_status.setStyleSheet("color : rgb(114,250,48);"
                                             "font: bold 14px;"
                                             "padding: 0px 15px 0 15px;"
                                             "background-color: #383838;"
                                             "border-radius: 5px;"
                                             "height: 30px;")

        self.pressedKey = QLabel("Key Pressed: ", self)
        self.pressedKey.setStyleSheet("color : rgb(114,250,48);"
                                      "font: bold 14px;"
                                      "padding: 0px 15px 0 15px;"
                                      "background-color: #383838;"
                                      "border-radius: 5px;"
                                      "height: 30px;")

        self.mapping_status = QLabel("Mapping: ")
        self.mapping_status.setStyleSheet("color : rgb(114,250,48);"
                                          "font: bold 14px;"
                                          "padding: 0px 15px 0 15px;"
                                          "background-color: #383838;"
                                          "border-radius: 5px;"
                                          "height: 30px;")

    def initLayout(self):
        self.layout_v = QVBoxLayout()
        self.layout_h = QHBoxLayout()

        self.layout_v.addWidget(self.map_view)
        self.layout_v.addWidget(self.terminal)
        self.layout_v.addLayout(self.layout_h)
        self.layout_h.addWidget(self.connect_button)
        self.layout_h.addWidget(self.start_map_button)
        self.layout_h.addWidget(self.pause_map_button)
        self.layout_h.addWidget(self.mapping_status)
        self.layout_h.addWidget(self.user_drive_status)
        self.layout_h.addWidget(self.pressedKey)

        container = QWidget()
        container.setLayout(self.layout_v)
        self.setCentralWidget(container)

    def drawMapEntity(self, type, x, y):
        # Rita en vägg på kartan
        rect = QGraphicsRectItem(0, 0, 20, 20)
        rect.setPos(x*20 + 800, y*20 + 800)
        if type == "w":
            brush = QBrush(QColor.fromRgb(214, 30, 48))
            rect.setBrush(brush)
            self.map_scene.addItem(rect)
        elif type == "e":
            brush = QBrush(QColor.fromRgb(30, 214, 55))
            rect.setBrush(brush)
            self.map_scene.addItem(rect)
        elif type == "u":
            brush = QBrush(QColor.fromRgb(214, 205, 30))
            rect.setBrush(brush)
            self.map_scene.addItem(rect)
        elif type == "r":
            self.terminal.append("ROBOT")
            brush = QBrush(QColor.fromRgb(0, 250, 225))
            rect.setBrush(brush)
            self.map_scene.addItem(rect)
        elif type == "p":
            brush = QBrush(QColor.fromRgb(255, 0, 255))
            rect.setBrush(brush)
            self.map_scene.addItem(rect)

    def moveRobot(self, x, y):
        # oldRobot = self.map_scene.itemAt(self.robot_x*20 + 800, self.robot_y*20 + 800, QTransform())
        # self.map_scene.removeItem(oldRobot)

        robot = QGraphicsRectItem(0, 0, 20, 20)
        robot.setPos((x*20 + 800), (y*20 + 800))
        self.robot_x = x
        self.robot_y = y

        brush_robot = QBrush(QColor.fromRgb(0, 250, 225))
        robot.setBrush(brush_robot)

        self.map_scene.addItem(robot)
        # self.map_view.centerOn(robot)

    def disconnect(self):
        self.terminal.append("Disconnecting...")
        self.client.close()
        self.timer.stop()
        self.connected = False
        self.connect_button.setText("Connect to robot")
        self.terminal.append("Disconnected")

    def connectToBT(self):
        # Försök ansluta till Bluetooth-enheten
        try:
            if not self.connected:
                self.terminal.append("Trying to connect...")
                self.client = socket.socket(
                    socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
                self.client.connect(("B8:27:EB:4E:FF:90", 4))
                self.connected = True

                self.timer.start()

                self.terminal.append("Succeeded to connect")
                self.connect_button.setText("Disconnect from robot")
            else:
                self.disconnect()
        except OSError:
            self.terminal.append("Failed to connect")
            pass

    def start_mapping(self):

        if self.connected and self.auto_drive:

            if not self.is_mapping:
                message = "start mapping"
                self.client.send(message.encode('utf-8'))
                self.map_scene.clear()
                self.map_view.viewport().update()
                self.terminal.append("Sent start mapping")

            elif self.is_mapping:
                message = "stop mapping"
                self.client.send(message.encode('utf-8'))
                self.terminal.append("Sent stop mapping")

    def pause_mapping(self):

        if self.is_mapping and self.connected and self.auto_drive:

            if not self.paused_mapping:
                message = "pause mapping"
                self.client.send(message.encode('utf-8'))

                self.terminal.append("Sent pause mapping")
            elif self.paused_mapping:

                self.terminal.append("Sent resume mapping")
                message = "unpause mapping"
                self.client.send(message.encode('utf-8'))

    def getCoords(self):
        # Skicka en förfrågan om koordinater och rita väggen baserat på svaret
        try:
            message = "send data"

            self.client.send(message.encode('utf-8'))

            data = self.client.recv(1024)

            decodedData = data.decode('utf-8')
            decodedData = decodedData.replace("\n", "")
            split_data = decodedData.split()

            sensor_data = split_data[:16]
            coord_data = split_data[16:]

            for i in range(0, len(coord_data), 3):

                if coord_data[0] != "no_coord_data" and decodedData != "":
                    self.drawMapEntity(coord_data[i], int(
                        coord_data[i+2]) - 7, int(coord_data[i+1]) - 7)

            if decodedData != "":
                self.terminal.append(decodedData)
                sensor_data = decodedData.split()
                if sensor_data[1] == "0":
                    self.auto_drive = False
                    self.user_drive_status.setText("User drive: Active")
                elif sensor_data[1] == "1":
                    self.auto_drive = True
                    self.user_drive_status.setText("User drive: Disabled")
                if sensor_data[13] == "0":
                    self.mapping_status.setText("Mapping: Disabled")
                    self.start_map_button.setText("Start mapping")
                    self.is_mapping = False
                    self.paused_mapping = False
                elif sensor_data[13] == "1":
                    self.mapping_status.setText("Mapping: Active")
                    self.start_map_button.setText("Stop mapping")
                    self.is_mapping = True
                if sensor_data[15] == "0":
                    self.pause_map_button.setText("Pause mapping")
                    self.paused_mapping = False
                elif sensor_data[15] == "1":
                    self.pause_map_button.setText("Resume mapping")
                    self.paused_mapping = True
        except ConnectionAbortedError as e:
            self.terminal.append("Lost connection.")
            self.disconnect()
