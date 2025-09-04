import sys

from PyQt6.QtWidgets import QApplication

from gui.CropGUI import CropGUI


def run_gui(media_path, media_type, output_path, keep_open):
    app = QApplication(sys.argv)

    gui = CropGUI(
        media_path=media_path,
        media_type=media_type,
        output_path=output_path,
        auto_close=(not keep_open),
    )
    
    gui.show()
    exit_code = app.exec()  # Get the exit code
    return exit_code, gui  # Return both exit code and GUI instance
