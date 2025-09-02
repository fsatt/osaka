import cv2
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPixmap
from PyQt6.QtCore import Qt, QRect, QSize
from PIL.ImageQt import ImageQt
from PIL import Image

from gui.ResizableCropBox import ResizableCropBox


class ImageWithCropBox(QWidget):
    def __init__(self, pil_image, parent=None, video_path=None):
        super().__init__(parent)

        # If video_path is provided, extract frames from video
        if video_path:
            self.frames = self.extract_frames_from_video(video_path)
            self.current_frame_index = 0
            self.pil_image = self.frames[0] if self.frames else pil_image
        else:
            self.frames = [pil_image] if pil_image else []
            self.current_frame_index = 0
            self.pil_image = pil_image

        self.qimage = ImageQt(self.pil_image)
        self.pixmap = QPixmap.fromImage(self.qimage)

        # Image display area (calculated in paintEvent)
        self.image_area = QRect()

        # Create the crop box overlay (will be positioned in resizeEvent)
        self.crop_box = None

    def showEvent(self, event):
        super().showEvent(event)
        if self.crop_box is None:
            self.crop_box = ResizableCropBox(self)
            # Give the crop box a reference to get image boundaries
            self.crop_box.get_image_bounds = lambda: self.image_area
            self.crop_box.show()

            # Emit a signal or call parent method to connect the crop box signal
            if hasattr(self.parent(), "connect_crop_signals"):
                self.parent().connect_crop_signals(self.crop_box)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Calculate image display area maintaining aspect ratio
        widget_rect = self.rect()
        pixmap_size = self.pixmap.size()

        # Scale to fit while maintaining aspect ratio
        scaled_size = pixmap_size.scaled(
            widget_rect.size(), Qt.AspectRatioMode.KeepAspectRatio
        )

        # Center the image
        x = (widget_rect.width() - scaled_size.width()) // 2
        y = (widget_rect.height() - scaled_size.height()) // 2

        # Update image area
        self.image_area = QRect(x, y, scaled_size.width(), scaled_size.height())

        # Draw the image
        scaled_pixmap = self.pixmap.scaled(
            scaled_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        painter.drawPixmap(x, y, scaled_pixmap)

        # Update crop box to only cover the image area
        if self.crop_box:
            self.crop_box.setGeometry(self.image_area)

    def display_to_original_coords(self, x, y, width, height):
        if self.image_area.isEmpty():
            return x, y, width, height

        # Convert from display coordinates to original image coordinates
        scale_x = self.pil_image.width / self.image_area.width()
        scale_y = self.pil_image.height / self.image_area.height()

        orig_x = round(x * scale_x)
        orig_y = round(y * scale_y)
        orig_width = round(width * scale_x)
        orig_height = round(height * scale_y)

        return orig_x, orig_y, orig_width, orig_height

    def original_to_display_coords(self, orig_x, orig_y, orig_width, orig_height):
        if self.image_area.isEmpty():
            return orig_x, orig_y, orig_width, orig_height

        # Convert from original image coordinates to display coordinates
        scale_x = self.image_area.width() / self.pil_image.width
        scale_y = self.image_area.height() / self.pil_image.height

        x = round(orig_x * scale_x)
        y = round(orig_y * scale_y)
        width = round(orig_width * scale_x)
        height = round(orig_height * scale_y)

        return x, y, width, height

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update()  # Trigger paintEvent to recalculate image area

    def sizeHint(self):
        # Suggest a size with the same aspect ratio as the image
        w, h = self.pil_image.size
        aspect_ratio = w / h
        base_height = 300
        return QSize(round(base_height * aspect_ratio), base_height)

    def get_crop_coordinates(self):
        if not self.crop_box or self.image_area.isEmpty():
            return (0, 0, 100, 100)

        # Convert crop box coordinates from display to original image coordinates
        crop_rect = self.crop_box.rect

        # Use consistent scaling factors with display_to_original_coords method
        scale_x = self.pil_image.width / self.image_area.width()
        scale_y = self.pil_image.height / self.image_area.height()

        # Convert to image coordinates (round to avoid precision loss)
        img_x = round(crop_rect.x() * scale_x)
        img_y = round(crop_rect.y() * scale_y)
        img_w = round(crop_rect.width() * scale_x)
        img_h = round(crop_rect.height() * scale_y)

        return (img_x, img_y, img_w, img_h)

    def extract_frames_from_video(self, video_path, num_frames=10):
        frames = []
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                print(f"Error opening video: {video_path}")
                return frames

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            if total_frames <= num_frames:
                # If video has fewer frames than requested, get all frames
                frame_indices = list(range(total_frames))
            else:
                # Extract evenly spaced frames
                frame_indices = [
                    int(i * total_frames / num_frames) for i in range(num_frames)
                ]

            for frame_idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if ret:
                    # Convert BGR to RGB
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    # Convert to PIL Image
                    pil_image = Image.fromarray(frame)
                    frames.append(pil_image)

            cap.release()
            print(f"Extracted {len(frames)} frames from video")

        except Exception as e:
            print(f"Error extracting frames: {e}")

        return frames

    def previous_frame(self):
        if hasattr(self, "frames") and self.current_frame_index > 0:
            self.current_frame_index -= 1
            self.update_current_frame()

    def next_frame(self):
        if hasattr(self, "frames") and self.current_frame_index < len(self.frames) - 1:
            self.current_frame_index += 1
            self.update_current_frame()

    def update_current_frame(self):
        if not hasattr(self, "frames") or not self.frames:
            return

        self.pil_image = self.frames[self.current_frame_index]
        self.qimage = ImageQt(self.pil_image)
        self.pixmap = QPixmap.fromImage(self.qimage)

        # Trigger repaint
        self.update()
