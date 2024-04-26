import sys
import os
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from mainWindow import *

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()

    # Flytta fönstret till övre vänstra hörnet
    screenRect = app.primaryScreen().geometry()
    window.move(screenRect.top(), screenRect.left())

    window.show()

    script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in
    rel_path = "style.qss"
    abs_file_path = os.path.join(script_dir, rel_path)

    with open(abs_file_path, "r") as f:
        _style = f.read()
        app.setStyleSheet(_style)

    app.exec()
