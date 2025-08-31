from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt
from PIL.ImageQt import ImageQt
from PIL import Image

from gui.ImageWithCropBox import ImageWithCropBox


class CropGUI(QWidget):
    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path
        self.image = Image.open(self.image_path)
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Video Cropper")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(200, 200)

        # Main layout
        main_layout = QVBoxLayout()

        # Image with crop box widget
        self.image_with_cropbox = ImageWithCropBox(self.image, self)
        main_layout.addWidget(self.image_with_cropbox)

        # Input fields for coordinates
        input_layout = QHBoxLayout()

        self.x_input = QLineEdit()
        self.y_input = QLineEdit()
        self.width_input = QLineEdit()
        self.height_input = QLineEdit()

        input_layout.addWidget(QLabel("X:"))
        input_layout.addWidget(self.x_input)
        input_layout.addWidget(QLabel("Y:"))
        input_layout.addWidget(self.y_input)
        input_layout.addWidget(QLabel("Width:"))
        input_layout.addWidget(self.width_input)
        input_layout.addWidget(QLabel("Height:"))
        input_layout.addWidget(self.height_input)

        main_layout.addLayout(input_layout)

        # Cropping button
        self.crop_button = QPushButton("Crop Video")
        self.crop_button.clicked.connect(self.start_crop_process)
        main_layout.addWidget(self.crop_button)

        self.setLayout(main_layout)

    def start_crop_process(self):
        try:
            x = int(self.x_input.text())
            y = int(self.y_input.text())
            width = int(self.width_input.text())
            height = int(self.height_input.text())

            print(
                f"Cropping with coordinates: X={x}, Y={y}, Width={width}, Height={height}"
            )
        except ValueError:
            print("Please enter valid integer values for cropping coordinates.")
