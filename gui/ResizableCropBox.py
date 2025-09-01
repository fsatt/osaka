from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QBrush, QColor, QPen
from PyQt6.QtCore import Qt, QRect, pyqtSignal


class ResizableCropBox(QWidget):
    # Signal to emit when crop rectangle changes
    cropChanged = pyqtSignal(int, int, int, int)  # x, y, width, height

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setGeometry(0, 0, parent.width(), parent.height())
        self.rect = QRect(0, 0, parent.width(), parent.height())
        # Store the original floating-point rectangle for precise scaling
        self.float_rect = [0.0, 0.0, float(parent.width()), float(parent.height())]
        # Store previous size for proportional scaling
        self.previous_size = self.size()
        self.handle_size = 10
        self.min_height = 20
        self.min_width = 20
        self.drag_handle = None
        self.drag_start = None
        self.drag_rect_initial = None

    def resizeEvent(self, event):
        old_size = event.oldSize()
        new_size = event.size()

        # Only scale if we have a valid old size
        if old_size.isValid() and old_size.width() > 0 and old_size.height() > 0:
            # Calculate scaling factors
            scale_x = new_size.width() / old_size.width()
            scale_y = new_size.height() / old_size.height()

            # Scale the floating-point rectangle for better precision
            self.float_rect[0] *= scale_x  # x
            self.float_rect[1] *= scale_y  # y
            self.float_rect[2] *= scale_x  # width
            self.float_rect[3] *= scale_y  # height

            # Convert to integer rectangle
            new_rect = QRect(
                int(self.float_rect[0]),
                int(self.float_rect[1]),
                int(self.float_rect[2]),
                int(self.float_rect[3]),
            )

            self.rect = new_rect

        super().resizeEvent(event)

    def _get_bounds_rect(self):
        if hasattr(self, "get_image_bounds") and callable(self.get_image_bounds):
            bounds = self.get_image_bounds()
            if bounds.isEmpty():
                bounds = QRect(0, 0, self.parent().width(), self.parent().height())
        else:
            bounds = QRect(0, 0, self.parent().width(), self.parent().height())

        return bounds

    def apply_aspect_ratio(self, rect, delta, aspect_ratio="1:1"):
        
        if aspect_ratio == "original":
            return rect

        # Calculate the new dimensions based on the aspect ratio
        if aspect_ratio == "1:1":
            new_size = min(self.drag_rect_initial.width() + delta.x(), self.drag_rect_initial.height() + delta.y())
            return QRect(rect.x(), rect.y(), new_size, new_size)
        elif aspect_ratio == "3:4":
            new_height = rect.width() * 4 / 3
            return QRect(rect.x(), rect.y(), rect.width(), new_height)
        elif aspect_ratio == "9:16":
            new_height = rect.width() * 16 / 9
            return QRect(rect.x(), rect.y(), rect.width(), new_height)

    def paintEvent(self, event):
        painter = QPainter(self)

        # Draw semi-transparent overlay in four regions around the crop box
        painter.setBrush(QBrush(QColor(0, 0, 0, 100)))  # Semi-transparent black
        painter.setPen(Qt.PenStyle.NoPen)  # No border for the overlay

        # Top region
        if self.rect.top() > 0:
            painter.drawRect(0, 0, self.width(), self.rect.top())

        # Bottom region
        if self.rect.bottom() < self.height():
            painter.drawRect(
                0,
                self.rect.bottom() + 1,
                self.width(),
                self.height() - self.rect.bottom(),
            )

        # Left region
        painter.drawRect(0, self.rect.top(), self.rect.left(), self.rect.height())

        # Right region
        if self.rect.right() < self.width():
            painter.drawRect(
                self.rect.right(),
                self.rect.top(),
                self.width() - self.rect.right(),
                self.rect.height(),
            )

        # Draw the crop box border (the inside should be clear/transparent now)
        painter.setPen(QPen(QColor(255, 255, 255), 2, Qt.PenStyle.SolidLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)  # No fill, just border
        painter.drawRect(self.rect)

        # Draw resize handles
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        for x in [self.rect.left(), self.rect.right() - self.handle_size]:
            for y in [self.rect.top(), self.rect.bottom() - self.handle_size]:
                painter.drawRect(x, y, self.handle_size, self.handle_size)

    def mousePressEvent(self, event):
        # Check if a handle is clicked
        if self.rect.contains(event.pos()):
            self.drag_start = event.pos()
            self.drag_rect_initial = QRect(self.rect)  # Store initial rect
            # Check corners
            for x, y, handle in [
                (self.rect.left(), self.rect.top(), "top_left"),
                (self.rect.right() - self.handle_size, self.rect.top(), "top_right"),
                (
                    self.rect.left(),
                    self.rect.bottom() - self.handle_size,
                    "bottom_left",
                ),
                (
                    self.rect.right() - self.handle_size,
                    self.rect.bottom() - self.handle_size,
                    "bottom_right",
                ),
            ]:
                handle_rect = QRect(x, y, self.handle_size, self.handle_size)
                if handle_rect.contains(event.pos()):
                    self.drag_handle = handle
                    return
            self.drag_handle = "move"

    def mouseMoveEvent(self, event):
        if self.drag_handle:
            big_delta = event.pos() - self.drag_start
            bounds = self._get_bounds_rect()
            bounds.adjust(0, 0, -1, -1)  # Adjust bounds to prevent overflow

            if self.drag_handle == "move":
                # For move operations, just translate without changing size
                new_rect = self.drag_rect_initial.translated(big_delta)

                # Ensure the rectangle stays within bounds
                if new_rect.left() < 0:
                    new_rect.moveLeft(0)
                if new_rect.top() < 0:
                    new_rect.moveTop(0)
                if new_rect.right() >= bounds.width():
                    new_rect.moveRight(bounds.width())
                if new_rect.bottom() >= bounds.height():
                    new_rect.moveBottom(bounds.height())

                self.setCropRect(
                    new_rect.x(),
                    new_rect.y(),
                    new_rect.width(),
                    new_rect.height(),
                )

            else:
                # Handle resize operations
                new_rect = QRect(self.rect)

                # bind top
                if self.drag_handle == "top_left" or self.drag_handle == "top_right":
                    if (new_top := self.drag_rect_initial.top() + big_delta.y()) < self.drag_rect_initial.bottom() - self.min_height:
                        new_rect.setTop(max(0, new_top))
                    else:
                        new_rect.setTop(self.drag_rect_initial.bottom() - self.min_height)
                # bind bottom
                if self.drag_handle == "bottom_left" or self.drag_handle == "bottom_right":
                    if (new_bottom := self.drag_rect_initial.bottom() + big_delta.y()) > self.drag_rect_initial.top() + self.min_height:
                        new_rect.setBottom(min(bounds.height(), new_bottom))
                    else:
                        new_rect.setBottom(self.drag_rect_initial.top() + self.min_height)
                # bind left
                if self.drag_handle == "top_left" or self.drag_handle == "bottom_left":
                    if (new_left := self.drag_rect_initial.left() + big_delta.x()) < self.drag_rect_initial.right() - self.min_width:
                        new_rect.setLeft(max(0, new_left))
                    else:
                        new_rect.setLeft(self.drag_rect_initial.right() - self.min_width)
                # bind right
                if self.drag_handle == "bottom_right" or self.drag_handle == "top_right":
                    if (new_right := self.drag_rect_initial.right() + big_delta.x()) > self.drag_rect_initial.left() + self.min_width:
                        new_rect.setRight(min(bounds.width(), new_right))
                    else:
                        new_rect.setRight(self.drag_rect_initial.left() + self.min_width)

                self.setCropRect(
                    new_rect.x(),
                    new_rect.y(),
                    new_rect.width(),
                    new_rect.height(),
                )

    def mouseReleaseEvent(self, event):
        self.drag_handle = None
        # Emit signal with original image coordinates if conversion is available
        if hasattr(self.parent(), "display_to_original_coords"):
            orig_x, orig_y, orig_width, orig_height = (
                self.parent().display_to_original_coords(
                    self.rect.x(), self.rect.y(), self.rect.width(), self.rect.height()
                )
            )
            self.cropChanged.emit(orig_x, orig_y, orig_width, orig_height)
        else:
            self.cropChanged.emit(
                self.rect.x(), self.rect.y(), self.rect.width(), self.rect.height()
            )

    def setCropRect(self, x, y, width, height):
        self.rect = QRect(x, y, width, height)
        self.float_rect[0] = float(x)
        self.float_rect[1] = float(y)
        self.float_rect[2] = float(width)
        self.float_rect[3] = float(height)
        self.update()
