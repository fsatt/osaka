from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPixmap
from PyQt6.QtCore import Qt, QRect, QSize
from PIL.ImageQt import ImageQt
from gui.ResizableCropBox import ResizableCropBox


class ImageWithCropBox(QWidget):
    def __init__(self, pil_image, parent=None):
        super().__init__(parent)
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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update()  # Trigger paintEvent to recalculate image area

    def sizeHint(self):
        # Suggest a size with the same aspect ratio as the image
        w, h = self.pil_image.size
        aspect_ratio = w / h
        base_height = 300
        return QSize(int(base_height * aspect_ratio), base_height)

    def get_crop_coordinates(self):
        """Return crop coordinates in original image dimensions"""
        if not self.crop_box or self.image_area.isEmpty():
            return (0, 0, 100, 100)

        # Convert crop box coordinates from display to original image coordinates
        crop_rect = self.crop_box.rect

        # Calculate scaling factors
        scale_x = (
            self.pixmap.width() / self.image_area.width()
            if self.image_area.width() > 0
            else 1
        )
        scale_y = (
            self.pixmap.height() / self.image_area.height()
            if self.image_area.height() > 0
            else 1
        )

        # Convert to image coordinates
        img_x = int(crop_rect.x() * scale_x)
        img_y = int(crop_rect.y() * scale_y)
        img_w = int(crop_rect.width() * scale_x)
        img_h = int(crop_rect.height() * scale_y)

        return (img_x, img_y, img_w, img_h)
