from PyQt6.QtCore import (
    Qt, QSize, QPoint, QPointF, QRectF,
    QEasingCurve, QPropertyAnimation, QSequentialAnimationGroup,QEvent,
    pyqtSlot, pyqtProperty)

from PyQt6.QtWidgets import QCheckBox, QLabel, QSlider, QVBoxLayout, QWidget
from PyQt6.QtGui import QColor, QBrush, QPaintEvent, QPen, QPainter


class AnimatedToggle(QCheckBox):

    _transparent_pen = QPen(Qt.GlobalColor.transparent)
    _light_grey_pen = QPen(Qt.GlobalColor.lightGray)

    def __init__(self,
        parent=None,
        bar_color=Qt.GlobalColor.gray,
        checked_color="#00B0FF",
        handle_color=Qt.GlobalColor.white,
        pulse_unchecked_color="#44999999",
        pulse_checked_color="#4400B0EE"
        ):
        super().__init__(parent)

        # Save our properties on the object via self, so we can access them later
        # in the paintEvent.
        self._bar_brush = QBrush(bar_color)
        self._bar_checked_brush = QBrush(QColor(checked_color).lighter())

        self._handle_brush = QBrush(handle_color)
        self._handle_checked_brush = QBrush(QColor(checked_color))

        self._pulse_unchecked_animation = QBrush(QColor(pulse_unchecked_color))
        self._pulse_checked_animation = QBrush(QColor(pulse_checked_color))

        # Setup the rest of the widget.
        self.setContentsMargins(8, 0, 8, 0)
        self._handle_position = 0

        self._pulse_radius = 0

        self.animation = QPropertyAnimation(self, b"handle_position", self)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.animation.setDuration(200)  # time in ms

        self.pulse_anim = QPropertyAnimation(self, b"pulse_radius", self)
        self.pulse_anim.setDuration(350)  # time in ms
        self.pulse_anim.setStartValue(10)
        self.pulse_anim.setEndValue(20)

        self.animations_group = QSequentialAnimationGroup()
        self.animations_group.addAnimation(self.animation)
        self.animations_group.addAnimation(self.pulse_anim)

        self.stateChanged.connect(self.setup_animation)

    def sizeHint(self):
        return QSize(58, 45)

    def hitButton(self, pos: QPoint):
        return self.contentsRect().contains(pos)

    @pyqtSlot(int)
    def setup_animation(self, value):
        self.animations_group.stop()
        if value:
            self.animation.setEndValue(1)
        else:
            self.animation.setEndValue(0)
        self.animations_group.start()

    def paintEvent(self, e: QPaintEvent):

        contRect = self.contentsRect()
        handleRadius = round(0.24 * contRect.height())

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        p.setPen(self._transparent_pen)
        barRect = QRectF(
            0, 0,
            contRect.width() - handleRadius, 0.40 * contRect.height()
        )
        barRect.moveCenter(QPointF(contRect.center()))
        rounding = barRect.height() / 2

        # the handle will move along this line
        trailLength = contRect.width() - 2 * handleRadius

        xPos = contRect.x() + handleRadius + trailLength * self._handle_position

        if self.pulse_anim.state() == QPropertyAnimation.State.Running:
            p.setBrush(
                self._pulse_checked_animation if
                self.isChecked() else self._pulse_unchecked_animation)
            p.drawEllipse(QPointF(xPos, barRect.center().y()),
                          self._pulse_radius, self._pulse_radius)

        if self.isChecked():
            p.setBrush(self._bar_checked_brush)
            p.drawRoundedRect(barRect, rounding, rounding)
            p.setBrush(self._handle_checked_brush)

        else:
            p.setBrush(self._bar_brush)
            p.drawRoundedRect(barRect, rounding, rounding)
            p.setPen(self._light_grey_pen)
            p.setBrush(self._handle_brush)

        p.drawEllipse(
            QPointF(xPos, barRect.center().y()),
            handleRadius, handleRadius)

        p.end()

    @pyqtProperty(float)
    def handle_position(self):
        return self._handle_position

    @handle_position.setter
    def handle_position(self, pos):
        """change the property
        we need to trigger QWidget.update() method, either by:
            1- calling it here [ what we doing ].
            2- connecting the QPropertyAnimation.valueChanged() signal to it.
        """
        self._handle_position = pos
        self.update()

    @pyqtProperty(float)
    def pulse_radius(self):
        return self._pulse_radius

    @pulse_radius.setter
    def pulse_radius(self, pos):
        self._pulse_radius = pos
        self.update()
        
    def changeEvent(self, event):
        if event.type() == QEvent.Type.EnabledChange:
            # Change colors based on whether the widget is enabled or disabled
            if self.isEnabled():
                # Widget is enabled, set the colors to enabled state
                self._bar_brush = QBrush(Qt.GlobalColor.gray)
                self._bar_checked_brush = QBrush(QColor("#00B0FF").lighter())
                self._handle_brush = QBrush(Qt.GlobalColor.white)
                self._handle_checked_brush = QBrush(QColor("#00B0FF"))
            else:
                # Widget is disabled, set the colors to disabled state
                self._bar_brush = QBrush(Qt.GlobalColor.lightGray)
                self._bar_checked_brush = QBrush(Qt.GlobalColor.gray)
                self._handle_brush = QBrush(Qt.GlobalColor.gray)
                self._handle_checked_brush = QBrush(Qt.GlobalColor.gray)
            self.update()
        super().changeEvent(event)




class CustomSlider(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Create a layout with margins on the sides
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 10, 20, 0)  # Left, Top, Right, Bottom margins

        # Create and style the slider
        self.slider = QSlider(Qt.Orientation.Horizontal, self)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider.setTickInterval(5)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 4px;
                background: #b0c4de;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #FF8C00;
                border: 1px solid #5c5c5c;
                width: 18px;
                height: 18px;
                margin: -8px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #FF8C00;
            }
            QSlider::sub-page:horizontal {
                background: #FFA500;
                border: 1px solid #777;
                height: 10px;
                border-radius: 4px;
            }
            QSlider::add-page:horizontal {
                background: #e0e0e0;
                border: 1px solid #777;
                height: 10px;
                border-radius: 4px;
            }
        """)
        self.slider.setValue(5)
        self.layout.addWidget(self.slider)

        # Create a QLabel to display the slider's value
        self.value_label = QLabel('α = 0.05', self)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setStyleSheet("font-size: 14px; color: #333;")
        self.layout.addWidget(self.value_label)

        # Connect the slider's valueChanged signal to the update_label function
        self.slider.valueChanged.connect(self.update_label)

    def update_label(self, value):
        # Update the label with the value divided by 100 and prefixed with "α = "
        self.value_label.setText(f"α = {value / 100:.2f}")