import os

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
from moviepy import VideoFileClip
from moviepy.video.fx.Crop import Crop


class ControlPanel(QWidget):
    def __init__(self, video_path=None, output_path="temp"):
        super().__init__()
        self.video_path = video_path
        self.output_path = output_path
        self.crop_box = None
        self.image_with_cropbox = None
        self.init_ui()

    def init_ui(self):
        # Main layout for controls
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Input fields for coordinates
        self.x_input = QLineEdit()
        self.y_input = QLineEdit()
        self.width_input = QLineEdit()
        self.height_input = QLineEdit()

        # Set fixed width for input fields
        input_width = 80
        self.x_input.setFixedWidth(input_width)
        self.y_input.setFixedWidth(input_width)
        self.width_input.setFixedWidth(input_width)
        self.height_input.setFixedWidth(input_width)

        # Add input fields with labels vertically
        x_layout = QHBoxLayout()
        x_layout.addWidget(QLabel("X:"))
        x_layout.addWidget(self.x_input)
        layout.addLayout(x_layout)

        y_layout = QHBoxLayout()
        y_layout.addWidget(QLabel("Y:"))
        y_layout.addWidget(self.y_input)
        layout.addLayout(y_layout)

        width_layout = QHBoxLayout()
        width_layout.addWidget(QLabel("Width:"))
        width_layout.addWidget(self.width_input)
        layout.addLayout(width_layout)

        height_layout = QHBoxLayout()
        height_layout.addWidget(QLabel("Height:"))
        height_layout.addWidget(self.height_input)
        layout.addLayout(height_layout)

        # Add some spacing
        layout.addStretch()

        # Cropping button
        self.crop_button = QPushButton("Crop Video")
        self.crop_button.clicked.connect(self.start_crop_process)
        layout.addWidget(self.crop_button)

        # Set max width for the panel
        self.setMaximumWidth(150)
        self.setLayout(layout)

    def set_image_widget(self, image_with_cropbox):
        self.image_with_cropbox = image_with_cropbox
        
        # Check if crop box is already available
        if hasattr(image_with_cropbox, 'crop_box') and image_with_cropbox.crop_box:
            self.connect_crop_signals(image_with_cropbox.crop_box, image_with_cropbox)
        else:
            # Connect when crop box becomes available (after widget is shown)
            def on_crop_box_ready():
                if hasattr(image_with_cropbox, 'crop_box') and image_with_cropbox.crop_box:
                    self.connect_crop_signals(image_with_cropbox.crop_box, image_with_cropbox)
            
            # Use a timer to check periodically
            from PyQt6.QtCore import QTimer
            timer = QTimer()
            timer.timeout.connect(lambda: (
                on_crop_box_ready(),
                timer.stop()
            ) if hasattr(image_with_cropbox, 'crop_box') and image_with_cropbox.crop_box else None)
            timer.start(100)  # Check every 100ms until crop box is ready

    def connect_crop_signals(self, crop_box, image_with_cropbox):
        # Store references
        self.crop_box = crop_box
        self.image_with_cropbox = image_with_cropbox

        # Connect crop box changes to input fields
        crop_box.cropChanged.connect(self.update_crop_fields)

        # Connect input field changes to crop box
        self.x_input.textChanged.connect(self.update_crop_from_fields)
        self.y_input.textChanged.connect(self.update_crop_from_fields)
        self.width_input.textChanged.connect(self.update_crop_from_fields)
        self.height_input.textChanged.connect(self.update_crop_from_fields)

        # Initialize the input fields with current crop box values
        self.update_crop_fields(
            crop_box.rect.x(),
            crop_box.rect.y(),
            crop_box.rect.width(),
            crop_box.rect.height(),
        )

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

            if self.crop_box and self.image_with_cropbox:
                # Convert from original image coordinates to display coordinates
                if hasattr(self.image_with_cropbox, "original_to_display_coords"):
                    x, y, width, height = self.image_with_cropbox.original_to_display_coords(
                        orig_x, orig_y, orig_width, orig_height
                    )
                else:
                    x, y, width, height = orig_x, orig_y, orig_width, orig_height

                self.crop_box.setCropRect(x, y, width, height, apply_constraints=True)

        except ValueError:
            pass

    def disconnect_input_signals(self):
        if self.crop_box:
            self.x_input.textChanged.disconnect()
            self.y_input.textChanged.disconnect()
            self.width_input.textChanged.disconnect()
            self.height_input.textChanged.disconnect()

    def connect_input_signals(self):
        if self.crop_box:
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

            # Ensure dimensions are even numbers (required for H.264)
            if width % 2 == 1:
                width -= 1
                print(f"Adjusted width to {width} (must be even for H.264)")
            if height % 2 == 1:
                height -= 1
                print(f"Adjusted height to {height} (must be even for H.264)")

            print(f"Cropping video with coordinates: X={x}, Y={y}, Width={width}, Height={height}")

            if not self.video_path:
                print("No video path provided - cannot crop video")
                return

            # Load the video
            clip = VideoFileClip(self.video_path)

            # Crop the video
            crop_effect = Crop(x1=x, y1=y, x2=x + width, y2=y + height)
            cropped_clip = clip.with_effects([crop_effect])

            # Generate output filename
            base_name = os.path.splitext(os.path.basename(self.video_path))[0]
            cropped_video_path = f"{self.output_path}/{base_name}_cropped.mp4"

            print(f"Saving cropped video to: {cropped_video_path}")

            # Write the cropped video with Windows-compatible settings
            cropped_clip.write_videofile(
                cropped_video_path,
                codec="libx264",
                audio_codec="aac",
                temp_audiofile="temp-audio.m4a",
                remove_temp=True,
            )

            # Clean up
            cropped_clip.close()
            clip.close()

            print(f"Video cropping completed! Output saved to: {cropped_video_path}")

        except ValueError:
            print("Please enter valid integer values for cropping coordinates.")
        except Exception as e:
            print(f"Error during video cropping: {e}")
