from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QBrush, QColor, QPen
from PyQt6.QtCore import Qt, QRect


class ResizableCropBox(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setGeometry(0, 0, parent.width(), parent.height())
        self.rect = QRect(0, 0, parent.width(), parent.height())
        # Store the original floating-point rectangle for precise scaling
        self.float_rect = [0.0, 0.0, float(parent.width()), float(parent.height())]
        self.handle_size = 10
        self.drag_handle = None
        self.drag_position = None
        # Store previous size for proportional scaling
        self.previous_size = self.size()

    def resizeEvent(self, event):
        """Scale the crop rectangle proportionally when the widget is resized"""
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
            self.drag_position = event.pos()
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
            delta = event.pos() - self.drag_position
            new_rect = self.rect

            if self.drag_handle == "move":
                # For move operations, just translate without changing size
                new_rect = self.rect.translated(delta)

                # Constrain movement to bounds
                if hasattr(self, "get_image_bounds") and callable(
                    self.get_image_bounds
                ):
                    bounds = self.get_image_bounds()
                    if bounds.isEmpty():
                        bounds = QRect(
                            0, 0, self.parent().width(), self.parent().height()
                        )
                else:
                    bounds = QRect(0, 0, self.parent().width(), self.parent().height())

                relative_bounds = QRect(0, 0, bounds.width(), bounds.height())

                # Ensure the rectangle stays within bounds
                if new_rect.left() < 0:
                    new_rect.moveLeft(0)
                if new_rect.top() < 0:
                    new_rect.moveTop(0)
                if new_rect.right() >= relative_bounds.width():
                    new_rect.moveRight(relative_bounds.width() - 1)
                if new_rect.bottom() >= relative_bounds.height():
                    new_rect.moveBottom(relative_bounds.height() - 1)

                self.setCropRect(
                    new_rect.x(), new_rect.y(), new_rect.width(), new_rect.height()
                )
                self.drag_position = event.pos()

            else:
                # Handle resize operations
                if self.drag_handle == "top_left":
                    new_rect = QRect(
                        self.rect.topLeft() + delta, self.rect.bottomRight()
                    )
                elif self.drag_handle == "top_right":
                    # Move top edge and right edge
                    new_rect = QRect(
                        self.rect.left(),
                        self.rect.top() + delta.y(),
                        self.rect.width() + delta.x(),
                        self.rect.height() - delta.y(),
                    )
                elif self.drag_handle == "bottom_left":
                    # Move bottom edge and left edge
                    new_rect = QRect(
                        self.rect.left() + delta.x(),
                        self.rect.top(),
                        self.rect.width() - delta.x(),
                        self.rect.height() + delta.y(),
                    )
                elif self.drag_handle == "bottom_right":
                    new_rect = QRect(
                        self.rect.topLeft(), self.rect.bottomRight() + delta
                    )

                # Normalize the rectangle to ensure positive dimensions
                new_rect = new_rect.normalized()

                # Constrain to parent bounds more carefully
                if hasattr(self, "get_image_bounds") and callable(
                    self.get_image_bounds
                ):
                    bounds = self.get_image_bounds()
                    if bounds.isEmpty():
                        bounds = QRect(
                            0, 0, self.parent().width(), self.parent().height()
                        )
                else:
                    bounds = QRect(0, 0, self.parent().width(), self.parent().height())

                relative_bounds = QRect(0, 0, bounds.width(), bounds.height())

                clamped_rect = QRect(
                    max(0, new_rect.left()),
                    max(0, new_rect.top()),
                    min(
                        new_rect.width(),
                        relative_bounds.width() - max(0, new_rect.left()),
                    ),
                    min(
                        new_rect.height(),
                        relative_bounds.height() - max(0, new_rect.top()),
                    ),
                )

                # Only update if the clamped rectangle is valid (positive dimensions)
                if clamped_rect.width() > 20 and clamped_rect.height() > 20:
                    self.setCropRect(
                        clamped_rect.x(),
                        clamped_rect.y(),
                        clamped_rect.width(),
                        clamped_rect.height(),
                    )
                    self.drag_position = event.pos()

    def mouseReleaseEvent(self, event):
        self.drag_handle = None
        # You'll emit a signal here to update the QLineEdit widgets in the main GUI
        print(
            f"Final crop: {self.rect.x()}, {self.rect.y()}, {self.rect.width()}, {self.rect.height()}"
        )

    def setCropRect(self, x, y, width, height):
        self.rect = QRect(x, y, width, height)
        self.float_rect[0] = float(x)
        self.float_rect[1] = float(y)
        self.float_rect[2] = float(width)
        self.float_rect[3] = float(height)
        self.update()
