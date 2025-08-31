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

    def connect_crop_signals(self, crop_box):
        # Store reference to crop box
        self.crop_box = crop_box
        
        # Connect crop box changes to input fields
        crop_box.cropChanged.connect(self.update_crop_fields)
        
        # Connect input field changes to crop box
        self.x_input.textChanged.connect(self.update_crop_from_fields)
        self.y_input.textChanged.connect(self.update_crop_from_fields)
        self.width_input.textChanged.connect(self.update_crop_from_fields)
        self.height_input.textChanged.connect(self.update_crop_from_fields)
        
        # Initialize the input fields with current crop box values
        self.update_crop_fields(crop_box.rect.x(), crop_box.rect.y(), crop_box.rect.width(), crop_box.rect.height())

    def showEvent(self, event):
        super().showEvent(event)
        # Connect the crop box signal after it's created
        if hasattr(self.image_with_cropbox, 'crop_box') and self.image_with_cropbox.crop_box:
            self.image_with_cropbox.crop_box.cropChanged.connect(self.update_crop_fields)

    def update_crop_fields(self, x, y, width, height):
        # Temporarily disconnect signals to avoid infinite loop
        self.disconnect_input_signals()
        
        self.x_input.setText(str(x))
        self.y_input.setText(str(y))
        self.width_input.setText(str(width))
        self.height_input.setText(str(height))
        
        # Reconnect signals
        self.connect_input_signals()

    def update_crop_from_fields(self):
        try:
            orig_x = int(self.x_input.text()) if self.x_input.text() else 0
            orig_y = int(self.y_input.text()) if self.y_input.text() else 0
            orig_width = int(self.width_input.text()) if self.width_input.text() else 100
            orig_height = int(self.height_input.text()) if self.height_input.text() else 100
            
            if hasattr(self, 'crop_box') and self.crop_box:
                # Convert from original image coordinates to display coordinates
                if hasattr(self.image_with_cropbox, 'original_to_display_coords'):
                    x, y, width, height = self.image_with_cropbox.original_to_display_coords(
                        orig_x, orig_y, orig_width, orig_height
                    )
                else:
                    x, y, width, height = orig_x, orig_y, orig_width, orig_height
                
                self.crop_box.setCropRect(x, y, width, height, apply_constraints=True)
                
        except ValueError:
            pass

    def disconnect_input_signals(self):
        if hasattr(self, 'crop_box'):
            self.x_input.textChanged.disconnect()
            self.y_input.textChanged.disconnect()
            self.width_input.textChanged.disconnect()
            self.height_input.textChanged.disconnect()

    def connect_input_signals(self):
        if hasattr(self, 'crop_box'):
            self.x_input.textChanged.connect(self.update_crop_from_fields)
            self.y_input.textChanged.connect(self.update_crop_from_fields)
            self.width_input.textChanged.connect(self.update_crop_from_fields)
            self.height_input.textChanged.connect(self.update_crop_from_fields)

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
