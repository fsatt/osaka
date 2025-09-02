import sys

from PyQt6.QtWidgets import QApplication

from gui.CropGUI import CropGUI


def run_gui(image_path, video_path=None, output_path="temp", keep_open=False):
    app = QApplication(sys.argv)
    gui = CropGUI(image_path, video_path, output_path, auto_close=(not keep_open))
    gui.show()
    exit_code = app.exec()  # Get the exit code
    return exit_code, gui  # Return both exit code and GUI instance
