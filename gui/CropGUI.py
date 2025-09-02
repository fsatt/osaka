from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
)
from PIL import Image

from gui.ImageWithCropBox import ImageWithCropBox
from gui.ControlPanel import ControlPanel


class CropGUI(QWidget):
    def __init__(self, image_path, video_path, output_path, auto_close):
        super().__init__()
        self.image_path = image_path
        self.video_path = video_path
        self.output_path = output_path
        self.image = Image.open(self.image_path)
        self.auto_close = auto_close
        self.crop_thread = None  # Store crop thread reference
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Video Cropper")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(200, 200)

        # Main horizontal layout
        main_layout = QHBoxLayout()

        # Image with crop box widget
        self.image_with_cropbox = ImageWithCropBox(self.image, self)
        main_layout.addWidget(self.image_with_cropbox)

        # Control panel
        self.control_panel = ControlPanel(
            video_path=self.video_path, output_path=self.output_path
        )
        # Connect the control panel to the image widget
        self.control_panel.set_image_widget(self.image_with_cropbox)
        main_layout.addWidget(self.control_panel)

        self.setLayout(main_layout)

    def connect_crop_signals(self, crop_box):
        self.control_panel.connect_crop_signals(crop_box, self.image_with_cropbox)

    def set_crop_thread(self, thread):
        self.crop_thread = thread

    def get_crop_thread(self):
        return self.crop_thread
