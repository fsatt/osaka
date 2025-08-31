import sys

from PyQt6.QtWidgets import QApplication

from gui.CropGUI import CropGUI


def run_gui(image_path):
    app = QApplication(sys.argv)
    gui = CropGUI(image_path)
    gui.show()
    sys.exit(app.exec())
