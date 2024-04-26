from typing import Optional
import PySide6.QtCore
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *


# Skapa en Bluetooth-socket

class KeyPressFilter(QObject):

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

    def eventFilter(self, widget, event):
        # Filtrera tangenttryckningar och skicka kommandon till Bluetooth-enheten

        if event.type() == QEvent.KeyRelease and not event.isAutoRepeat():
            key = event.key()
            if key == 87 or key == 83 or key == 65 or key == 68 or key == 81 or key == 69:
                if widget.connected:
                    dir = "stop"
                    widget.client.send(dir.encode('utf-8'))

        if event.type() == QEvent.KeyPress and not event.isAutoRepeat():
            key = event.key()
            if widget.connected:
                if key == 87:
                    dir = "fwd"  # W
                    widget.client.send(dir.encode('utf-8'))
                elif key == 83:
                    dir = "back"  # S
                    widget.client.send(dir.encode('utf-8'))
                elif key == 65:
                    dir = "left"  # A
                    widget.client.send(dir.encode('utf-8'))
                elif key == 68:
                    dir = "right"  # D
                    widget.client.send(dir.encode('utf-8'))
                elif key == 88:
                    dir = "stop"  # X
                    widget.client.send(dir.encode('utf-8'))
                elif key == 81:
                    dir = "fwd_left"
                    widget.client.send(dir.encode('utf-8'))
                elif key == 69:
                    dir = "fwd_right"
                    widget.client.send(dir.encode('utf-8'))

                widget.pressedKey.setText("Key Pressed: " + dir)

        return False
