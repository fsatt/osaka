import os
import threading

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QSpinBox,
)
from PyQt6.QtGui import QIcon

from config_loader import config
from utils import crop_video, crop_image, MediaType


class ControlPanel(QWidget):
    def __init__(self, media_path, media_type, output_path):
        super().__init__()
        self.media_path = media_path
        self.media_type = media_type
        self.video_path = media_path if media_type == MediaType.VIDEO else None
        self.output_path = output_path
        self.crop_box = None
        self.image_with_cropbox = None
        self.init_ui()

    def init_ui(self):
        # Main layout for controls
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Input fields for coordinates
        self.x_input = QSpinBox()
        self.x_input.setRange(0, 9999)  # Will be updated when image is set

        self.y_input = QSpinBox()
        self.y_input.setRange(0, 9999)  # Will be updated when image is set

        self.width_input = QSpinBox()
        self.width_input.setRange(1, 9999)  # Minimum 1 pixel width

        self.height_input = QSpinBox()
        self.height_input.setRange(1, 9999)  # Minimum 1 pixel height

        # Set fixed width for input fields
        input_width = 80
        self.x_input.setFixedWidth(input_width)
        self.y_input.setFixedWidth(input_width)
        self.width_input.setFixedWidth(input_width)
        self.height_input.setFixedWidth(input_width)

        # Add input fields with labels vertically
        x_layout = QHBoxLayout()
        x_label = QLabel("x")
        x_label.setToolTip("X of Top-Left Corner")
        x_layout.addWidget(x_label)
        x_layout.addWidget(self.x_input)
        layout.addLayout(x_layout)

        y_layout = QHBoxLayout()
        y_label = QLabel("y")
        y_label.setToolTip("Y of Top-Left Corner")
        y_layout.addWidget(y_label)
        y_layout.addWidget(self.y_input)
        layout.addLayout(y_layout)

        width_layout = QHBoxLayout()
        width_icon_label = QLabel()
        width_icon = QIcon(
            "assets/icons/arrow_range_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg"
        )
        width_icon_label.setPixmap(width_icon.pixmap(16, 16))
        width_icon_label.setToolTip("Width")
        width_layout.addWidget(width_icon_label)
        width_layout.addWidget(self.width_input)
        layout.addLayout(width_layout)

        height_layout = QHBoxLayout()
        height_icon_label = QLabel()
        height_icon = QIcon(
            "assets/icons/height_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg"
        )
        height_icon_label.setPixmap(height_icon.pixmap(16, 16))
        height_icon_label.setToolTip("Height")
        height_layout.addWidget(height_icon_label)
        height_layout.addWidget(self.height_input)
        layout.addLayout(height_layout)

        # Alignment buttons in horizontal layout
        alignment_layout = QHBoxLayout()
        alignment_layout.addStretch()

        self.align_vertical_button = QPushButton()
        self.align_vertical_button.setIcon(
            QIcon(
                "assets/icons/align_center_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg"
            )
        )
        self.align_vertical_button.setToolTip("Center Vertically")
        self.align_vertical_button.setFixedSize(28, 28)
        self.align_vertical_button.clicked.connect(self.align_vertical)
        alignment_layout.addWidget(self.align_vertical_button)

        self.align_horizontal_button = QPushButton()
        self.align_horizontal_button.setIcon(
            QIcon(
                "assets/icons/align_justify_center_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg"
            )
        )
        self.align_horizontal_button.setToolTip("Center Horizontally")
        self.align_horizontal_button.setFixedSize(28, 28)
        self.align_horizontal_button.clicked.connect(self.align_horizontal)
        alignment_layout.addWidget(self.align_horizontal_button)

        # Add the horizontal layout to the main vertical layout
        layout.addLayout(alignment_layout)

        # Portrait/Landscape switch for ratios that can be flipped
        orientation_layout = QHBoxLayout()
        orientation_layout.addStretch()

        self.orientation_portrait = QPushButton()
        self.orientation_portrait.setIcon(
            QIcon(
                "assets/icons/crop_portrait_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg"
            )
        )
        self.orientation_portrait.setCheckable(True)
        self.orientation_portrait.setChecked(True)  # Default to portrait
        self.orientation_portrait.setToolTip("Portrait orientation")
        self.orientation_portrait.setFixedSize(28, 28)
        self.orientation_portrait.clicked.connect(
            lambda: self.on_orientation_button_clicked("portrait")
        )
        orientation_layout.addWidget(self.orientation_portrait)

        self.orientation_landscape = QPushButton()
        self.orientation_landscape.setIcon(
            QIcon(
                "assets/icons/crop_landscape_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg"
            )
        )
        self.orientation_landscape.setCheckable(True)
        self.orientation_landscape.setToolTip("Landscape orientation")
        self.orientation_landscape.setFixedSize(28, 28)
        self.orientation_landscape.clicked.connect(
            lambda: self.on_orientation_button_clicked("landscape")
        )
        orientation_layout.addWidget(self.orientation_landscape)

        layout.addLayout(orientation_layout)

        # Aspect Ratio Controls
        aspect_layout = QHBoxLayout()

        # Create aspect ratio icon label
        aspect_icon_label = QLabel()
        aspect_icon = QIcon(
            "assets/icons/aspect_ratio_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg"
        )
        aspect_icon_label.setPixmap(aspect_icon.pixmap(20, 20))
        aspect_icon_label.setToolTip("Aspect Ratio")
        aspect_layout.addWidget(aspect_icon_label)

        self.aspect_ratio_combo = QComboBox()
        self.aspect_ratio_combo.setFixedWidth(input_width)
        self.aspect_ratio_combo.addItems(["Custom", "Original", "1:1", "3:4", "9:16"])
        self.aspect_ratio_combo.currentTextChanged.connect(self.on_aspect_ratio_changed)
        aspect_layout.addWidget(self.aspect_ratio_combo)
        layout.addLayout(aspect_layout)

        # Frame navigation controls for videos
        if self.media_type == MediaType.VIDEO:
            self.add_frame_navigation(layout)

        # Add some spacing
        layout.addStretch()

        # Cropping button - text depends on media type
        if self.media_type == MediaType.IMAGE:
            button_text = " Crop Image"
        elif self.media_type == MediaType.VIDEO:
            button_text = " Crop Video"
        else:
            button_text = " Crop Media"
            
        self.crop_button = QPushButton(button_text)
        self.crop_button.setIcon(
            QIcon("assets/icons/crop_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg")
        )
        self.crop_button.clicked.connect(self.start_crop_background)
        layout.addWidget(self.crop_button)

        # Set max width for the panel
        self.setMaximumWidth(130)
        self.setLayout(layout)

    def add_frame_navigation(self, layout):
        nav_layout = QHBoxLayout()

        self.frame_label = QLabel("1/1")
        self.frame_label.setToolTip("Current Frame")
        nav_layout.addWidget(self.frame_label)
        nav_layout.addStretch()

        self.prev_button = QPushButton()
        self.prev_button.setIcon(
            QIcon("assets/icons/arrow_back_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg")
        )
        self.prev_button.setFixedSize(28, 28)
        self.prev_button.setToolTip("Previous Frame")
        self.prev_button.clicked.connect(self.previous_frame)

        self.next_button = QPushButton()
        self.next_button.setIcon(
            QIcon(
                "assets/icons/arrow_forward_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg"
            )
        )
        self.next_button.setFixedSize(28, 28)
        self.next_button.setToolTip("Next Frame")
        self.next_button.clicked.connect(self.next_frame)

        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.next_button)

        layout.addLayout(nav_layout)

    def set_image_widget(self, image_with_cropbox):
        self.image_with_cropbox = image_with_cropbox

        # Initialize frame controls if this is a video
        if hasattr(image_with_cropbox, "frames") and len(image_with_cropbox.frames) > 1:
            self.update_frame_controls()

        # Check if crop box is already available
        if hasattr(image_with_cropbox, "crop_box") and image_with_cropbox.crop_box:
            self.connect_crop_signals(image_with_cropbox.crop_box, image_with_cropbox)
        else:
            # Connect when crop box becomes available (after widget is shown)
            def on_crop_box_ready():
                if (
                    hasattr(image_with_cropbox, "crop_box")
                    and image_with_cropbox.crop_box
                ):
                    self.connect_crop_signals(
                        image_with_cropbox.crop_box, image_with_cropbox
                    )

            # Use a timer to check periodically
            from PyQt6.QtCore import QTimer

            timer = QTimer()
            timer.timeout.connect(
                lambda: (on_crop_box_ready(), timer.stop())
                if hasattr(image_with_cropbox, "crop_box")
                and image_with_cropbox.crop_box
                else None
            )
            timer.start(100)  # Check every 100ms until crop box is ready

        # Update spinbox ranges based on image dimensions
        self.update_spinbox_ranges(image_with_cropbox)

    def update_spinbox_ranges(self, image_with_cropbox):
        if hasattr(image_with_cropbox, "pil_image") and image_with_cropbox.pil_image:
            image_width = image_with_cropbox.pil_image.width
            image_height = image_with_cropbox.pil_image.height

            # Update X and Width ranges
            self.x_input.setRange(0, image_width)
            self.width_input.setRange(1, image_width)

            # Update Y and Height ranges
            self.y_input.setRange(0, image_height)
            self.height_input.setRange(1, image_height)

    def connect_crop_signals(self, crop_box, image_with_cropbox):
        # Store references
        self.crop_box = crop_box
        self.image_with_cropbox = image_with_cropbox

        # Connect crop box changes to input fields
        crop_box.cropChanged.connect(self.update_crop_fields)

        # Connect input field changes to crop box
        self.x_input.valueChanged.connect(self.update_crop_from_fields)
        self.y_input.valueChanged.connect(self.update_crop_from_fields)
        self.width_input.valueChanged.connect(self.update_crop_from_fields)
        self.height_input.valueChanged.connect(self.update_crop_from_fields)

        # Initialize the input fields with current crop box values converted to original coordinates
        # Use a small delay to ensure the image area is properly calculated
        from PyQt6.QtCore import QTimer

        def initialize_fields():
            if (
                hasattr(image_with_cropbox, "display_to_original_coords")
                and not image_with_cropbox.image_area.isEmpty()
            ):
                try:
                    orig_x, orig_y, orig_width, orig_height = (
                        image_with_cropbox.display_to_original_coords(
                            crop_box.rect.x(),
                            crop_box.rect.y(),
                            crop_box.rect.width(),
                            crop_box.rect.height(),
                        )
                    )
                    self.update_crop_fields(orig_x, orig_y, orig_width, orig_height)
                except:
                    # Fallback to direct values if conversion fails
                    self.update_crop_fields(
                        crop_box.rect.x(),
                        crop_box.rect.y(),
                        crop_box.rect.width(),
                        crop_box.rect.height(),
                    )
            else:
                self.update_crop_fields(
                    crop_box.rect.x(),
                    crop_box.rect.y(),
                    crop_box.rect.width(),
                    crop_box.rect.height(),
                )

        # Try immediately, then with a small delay if needed
        initialize_fields()
        QTimer.singleShot(
            100, initialize_fields
        )  # Retry after 100ms to ensure proper sizing

    def update_crop_fields(self, x, y, width, height):
        # Temporarily disconnect signals to avoid infinite loop
        self.disconnect_input_signals()

        # Ensure we have integer values for the spinboxes
        self.x_input.setValue(int(round(x)))
        self.y_input.setValue(int(round(y)))
        self.width_input.setValue(int(round(width)))
        self.height_input.setValue(int(round(height)))

        # Reconnect signals
        self.connect_input_signals()

    def update_crop_from_fields(self):
        try:
            orig_x = self.x_input.value()
            orig_y = self.y_input.value()
            orig_width = self.width_input.value()
            orig_height = self.height_input.value()

            # Apply aspect ratio constraints first if locked
            adjusted_x, adjusted_y, adjusted_width, adjusted_height = (
                self.apply_aspect_ratio_constraints(
                    orig_x, orig_y, orig_width, orig_height
                )
            )

            # Then apply boundary constraints
            adjusted_x, adjusted_y, adjusted_width, adjusted_height = (
                self.apply_boundary_constraints(
                    adjusted_x, adjusted_y, adjusted_width, adjusted_height
                )
            )

            # Update spinboxes if values were adjusted
            if (
                adjusted_x != orig_x
                or adjusted_y != orig_y
                or adjusted_width != orig_width
                or adjusted_height != orig_height
            ):
                self.disconnect_input_signals()
                self.x_input.setValue(adjusted_x)
                self.y_input.setValue(adjusted_y)
                self.width_input.setValue(adjusted_width)
                self.height_input.setValue(adjusted_height)
                self.connect_input_signals()

            if self.crop_box and self.image_with_cropbox:
                # Convert from original image coordinates to display coordinates
                if hasattr(self.image_with_cropbox, "original_to_display_coords"):
                    x, y, width, height = (
                        self.image_with_cropbox.original_to_display_coords(
                            adjusted_x, adjusted_y, adjusted_width, adjusted_height
                        )
                    )
                else:
                    x, y, width, height = (
                        adjusted_x,
                        adjusted_y,
                        adjusted_width,
                        adjusted_height,
                    )

                self.crop_box.setCropRect(x, y, width, height)

        except ValueError:
            pass

    def apply_aspect_ratio_constraints(self, x, y, width, height):
        current_ratio_text = self.aspect_ratio_combo.currentText()

        # If custom mode or no crop box, return values unchanged
        if current_ratio_text == "Custom" or not self.crop_box:
            return x, y, width, height

        # Get the target aspect ratio
        aspect_ratio = self.get_aspect_ratio_value(current_ratio_text)
        if aspect_ratio is None:
            return x, y, width, height

        # Calculate what the other dimension should be to maintain aspect ratio
        expected_height_from_width = width / aspect_ratio
        expected_width_from_height = height * aspect_ratio

        # Get image dimensions for bounds checking
        if self.image_with_cropbox and hasattr(self.image_with_cropbox, "pil_image"):
            image_width = self.image_with_cropbox.pil_image.width
            image_height = self.image_with_cropbox.pil_image.height
        else:
            image_width = width * 2  # Fallback
            image_height = height * 2

        # Choose which dimension to constrain based on what fits better within bounds
        width_fits = (
            x + expected_width_from_height <= image_width
            and expected_width_from_height >= 20
        )
        height_fits = (
            y + expected_height_from_width <= image_height
            and expected_height_from_width >= 20
        )

        if width_fits and height_fits:
            # Both fit, choose the one that results in larger area (less constraining)
            area_from_width = width * expected_height_from_width
            area_from_height = expected_width_from_height * height

            if area_from_width >= area_from_height:
                # Width-driven constraint gives larger area
                height = round(expected_height_from_width)
            else:
                # Height-driven constraint gives larger area
                width = round(expected_width_from_height)
        elif width_fits:
            # Only width-constrained version fits
            width = round(expected_width_from_height)
        elif height_fits:
            # Only height-constrained version fits
            height = round(expected_height_from_width)
        else:
            # Neither fits perfectly, use width as driver (will be constrained by boundary function)
            height = round(expected_height_from_width)

        return x, y, width, height

    def apply_boundary_constraints(self, x, y, width, height):
        if not self.image_with_cropbox or not hasattr(
            self.image_with_cropbox, "pil_image"
        ):
            return x, y, width, height
        min_width, min_height = config.MIN_CROP_WIDTH, config.MIN_CROP_HEIGHT

        image_width = self.image_with_cropbox.pil_image.width
        image_height = self.image_with_cropbox.pil_image.height

        # Ensure minimum dimensions
        width = max(min_width, width)
        height = max(min_height, height)

        # Adjust width if x + width exceeds image bounds
        if x + width > image_width:
            width = image_width - x
            width = max(min_width, width)  # Ensure minimum width

        # Adjust height if y + height exceeds image bounds
        if y + height > image_height:
            height = image_height - y
            height = max(min_height, height)  # Ensure minimum height

        # If width is still too small, adjust x
        if width < min_width:
            x = max(0, image_width - min_width)
            width = min_width

        # If height is still too small, adjust y
        if height < min_height:
            y = max(0, image_height - min_height)
            height = min_height

        # Final bounds check
        x = max(0, min(x, image_width - width))
        y = max(0, min(y, image_height - height))

        return x, y, width, height

    def disconnect_input_signals(self):
        if self.crop_box:
            self.x_input.valueChanged.disconnect()
            self.y_input.valueChanged.disconnect()
            self.width_input.valueChanged.disconnect()
            self.height_input.valueChanged.disconnect()

    def connect_input_signals(self):
        if self.crop_box:
            self.x_input.valueChanged.connect(self.update_crop_from_fields)
            self.y_input.valueChanged.connect(self.update_crop_from_fields)
            self.width_input.valueChanged.connect(self.update_crop_from_fields)
            self.height_input.valueChanged.connect(self.update_crop_from_fields)

    def start_crop_background(self):
        # Extract all necessary data before starting the thread
        # This prevents issues with Qt objects being deleted
        try:
            x = self.x_input.value()
            y = self.y_input.value()
            width = self.width_input.value()
            height = self.height_input.value()
            media_path = self.media_path
            media_type = self.media_type
            output_path = self.output_path

            # Define a function that captures the data and calls appropriate crop function
            def crop_func():
                if media_type == MediaType.IMAGE:
                    crop_image(media_path, output_path, x, y, width, height)
                elif media_type == MediaType.VIDEO:
                    crop_video(media_path, output_path, x, y, width, height)
                else:
                    print(f"Unsupported media type: {media_type}")

            # Start the crop process in a separate thread
            crop_thread = threading.Thread(target=crop_func)
            crop_thread.start()

            # Store the thread reference in the parent GUI
            if self.parent() and hasattr(self.parent(), "set_crop_thread"):
                self.parent().set_crop_thread(crop_thread)

            # Only close the window if auto_close is True (--keep-gui flag not set)
            if (
                self.parent()
                and hasattr(self.parent(), "auto_close")
                and self.parent().auto_close
            ):
                self.parent().close()

        except Exception as e:
            print(f"Error starting crop process: {e}")

    def align_horizontal(self):
        if not self.crop_box or not self.image_with_cropbox:
            return

        try:
            # Get current crop dimensions
            current_width = (
                int(self.width_input.text()) if self.width_input.text() else 100
            )

            # Get original image dimensions
            image_width = self.image_with_cropbox.pil_image.width

            # Calculate centered X position
            centered_x = (image_width - current_width) // 2

            # Update the input fields
            self.x_input.setValue(centered_x)

        except ValueError:
            print("Please enter valid dimensions before aligning")

    def align_vertical(self):
        if not self.crop_box or not self.image_with_cropbox:
            return

        try:
            # Get current crop dimensions
            current_height = (
                int(self.height_input.text()) if self.height_input.text() else 100
            )

            # Get original image dimensions
            image_height = self.image_with_cropbox.pil_image.height

            # Calculate centered Y position
            centered_y = (image_height - current_height) // 2

            # Update the input fields
            self.y_input.setValue(centered_y)

        except ValueError:
            print("Please enter valid dimensions before aligning")

    def on_orientation_button_clicked(self, orientation):
        if orientation == "portrait":
            # Ensure portrait is checked and landscape is unchecked
            self.orientation_portrait.setChecked(True)
            self.orientation_landscape.setChecked(False)
        else:  # landscape
            # Ensure landscape is checked and portrait is unchecked
            self.orientation_landscape.setChecked(True)
            self.orientation_portrait.setChecked(False)

        # Trigger aspect ratio recalculation
        self.on_orientation_changed()

    def on_orientation_changed(self):
        current_ratio = self.aspect_ratio_combo.currentText()
        if current_ratio in ["3:4", "9:16"]:
            self.on_aspect_ratio_changed(current_ratio)

    def get_aspect_ratio_value(self, ratio_text):
        if not self.image_with_cropbox:
            return None

        if ratio_text == "Custom":
            return None  # No aspect ratio constraint
        elif ratio_text == "Original":
            # Use original image aspect ratio
            image_width = self.image_with_cropbox.pil_image.width
            image_height = self.image_with_cropbox.pil_image.height
            return image_width / image_height
        elif ratio_text == "1:1":
            return 1.0
        elif ratio_text == "3:4":
            if self.orientation_portrait.isChecked():  # Portrait
                return 3.0 / 4.0
            else:  # Landscape
                return 4.0 / 3.0
        elif ratio_text == "9:16":
            if self.orientation_portrait.isChecked():  # Portrait
                return 9.0 / 16.0
            else:  # Landscape
                return 16.0 / 9.0
        else:
            return None

    def on_aspect_ratio_changed(self, ratio_text):
        if not self.crop_box or not self.image_with_cropbox:
            return

        # Get the aspect ratio value and set it in the crop box
        aspect_ratio = self.get_aspect_ratio_value(ratio_text)
        if hasattr(self.crop_box, "aspect_ratio"):
            self.crop_box.aspect_ratio = aspect_ratio

        if ratio_text == "Custom":
            # No constraints for custom
            return

        # Get current crop dimensions
        current_width = int(self.width_input.text()) if self.width_input.text() else 100
        current_height = (
            int(self.height_input.text()) if self.height_input.text() else 100
        )

        # Calculate new dimensions based on aspect ratio
        new_width, new_height = self.calculate_aspect_ratio_dimensions(
            ratio_text, current_width, current_height
        )

        # Center the crop box
        image_width = self.image_with_cropbox.pil_image.width
        image_height = self.image_with_cropbox.pil_image.height

        new_x = (image_width - new_width) // 2
        new_y = (image_height - new_height) // 2

        # Update input fields
        self.x_input.setValue(new_x)
        self.y_input.setValue(new_y)
        self.width_input.setValue(new_width)
        self.height_input.setValue(new_height)

    def calculate_aspect_ratio_dimensions(
        self, ratio_text, current_width, current_height
    ):
        if not self.image_with_cropbox:
            return current_width, current_height

        image_width = self.image_with_cropbox.pil_image.width
        image_height = self.image_with_cropbox.pil_image.height

        # Get the aspect ratio value
        aspect_ratio = self.get_aspect_ratio_value(ratio_text)
        if aspect_ratio is None:
            return current_width, current_height

        # Calculate dimensions that fit within the image and maximize area
        if aspect_ratio >= 1:  # Wide aspect ratio
            # Width-limited
            new_width = min(image_width, round(image_height * aspect_ratio))
            new_height = round(new_width / aspect_ratio)
        else:  # Tall aspect ratio
            # Height-limited
            new_height = min(image_height, round(image_width / aspect_ratio))
            new_width = round(new_height * aspect_ratio)

        # Ensure dimensions don't exceed image bounds
        new_width = min(new_width, image_width)
        new_height = min(new_height, image_height)

        return new_width, new_height

    def previous_frame(self):
        if hasattr(self, "image_with_cropbox") and self.image_with_cropbox:
            self.image_with_cropbox.previous_frame()
            self.update_frame_controls()

    def next_frame(self):
        if hasattr(self, "image_with_cropbox") and self.image_with_cropbox:
            self.image_with_cropbox.next_frame()
            self.update_frame_controls()

    def update_frame_controls(self):
        # Update frame navigation controls state
        if not hasattr(self, "image_with_cropbox") or not self.image_with_cropbox:
            return

        if hasattr(self.image_with_cropbox, "frames") and hasattr(self, "frame_label"):
            current_frame = getattr(self.image_with_cropbox, "current_frame_index", 0)
            total_frames = len(self.image_with_cropbox.frames)

            # Update frame label
            self.frame_label.setText(f"{current_frame + 1}/{total_frames}")

            # Update button states
            if hasattr(self, "prev_button"):
                self.prev_button.setEnabled(current_frame > 0)
            if hasattr(self, "next_button"):
                self.next_button.setEnabled(current_frame < total_frames - 1)
