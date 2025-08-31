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

    def _get_bounds_rect(self):
        if hasattr(self, "get_image_bounds") and callable(self.get_image_bounds):
            bounds = self.get_image_bounds()
            if bounds.isEmpty():
                bounds = QRect(0, 0, self.parent().width(), self.parent().height())
        else:
            bounds = QRect(0, 0, self.parent().width(), self.parent().height())
        
        return bounds

    def _constrain_movement(self, rect):
        bounds = self._get_bounds_rect()
        
        # Ensure the rectangle stays within bounds
        if rect.left() < 0:
            rect.moveLeft(0)
        if rect.top() < 0:
            rect.moveTop(0)
        if rect.right() >= bounds.width():
            rect.moveRight(bounds.width() - 1)
        if rect.bottom() >= bounds.height():
            rect.moveBottom(bounds.height() - 1)
        
        return rect

    def _constrain_resize(self, rect, min_width=20, min_height=20):
        bounds = self._get_bounds_rect()
        
        # Normalize the rectangle to ensure positive dimensions
        rect = rect.normalized()
        
        # Clamp to bounds with careful dimension calculations
        clamped_rect = QRect(
            max(0, rect.left()),
            max(0, rect.top()),
            min(rect.width(), bounds.width() - max(0, rect.left())),
            min(rect.height(), bounds.height() - max(0, rect.top())),
        )
        
        # Ensure minimum dimensions
        if clamped_rect.width() >= min_width and clamped_rect.height() >= min_height:
            return clamped_rect
        else:
            return None  # Invalid rectangle

    def constrain_crop_rect(self, x, y, width, height, min_width=20, min_height=20):
        rect = QRect(x, y, width, height)
        constrained = self._constrain_resize(rect, min_width, min_height)
        
        if constrained is not None:
            return constrained.x(), constrained.y(), constrained.width(), constrained.height()
        else:
            # Return current rect if the new one is invalid
            return self.rect.x(), self.rect.y(), self.rect.width(), self.rect.height()

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
                
                # Constrain movement to bounds using helper function
                new_rect = self._constrain_movement(new_rect)

                self.setCropRect(
                    new_rect.x(), new_rect.y(), new_rect.width(), new_rect.height(), apply_constraints=False
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

                # Constrain to bounds using helper function
                constrained_rect = self._constrain_resize(new_rect)

                # Only update if the constrained rectangle is valid
                if constrained_rect is not None:
                    self.setCropRect(
                        constrained_rect.x(),
                        constrained_rect.y(),
                        constrained_rect.width(),
                        constrained_rect.height(),
                        apply_constraints=False
                    )
                    self.drag_position = event.pos()

    def mouseReleaseEvent(self, event):
        self.drag_handle = None
        # Emit signal to update the QLineEdit widgets in the main GUI
        self.cropChanged.emit(self.rect.x(), self.rect.y(), self.rect.width(), self.rect.height())
        print(
            f"Crop: {self.rect.x()}, {self.rect.y()}, {self.rect.width()}, {self.rect.height()}"
        )

    def setCropRect(self, x, y, width, height, apply_constraints=True):
        if apply_constraints:
            # Apply constraints to the input coordinates
            x, y, width, height = self.constrain_crop_rect(x, y, width, height)
        
        self.rect = QRect(x, y, width, height)
        self.float_rect[0] = float(x)
        self.float_rect[1] = float(y)
        self.float_rect[2] = float(width)
        self.float_rect[3] = float(height)
        self.update()
