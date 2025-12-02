import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QGridLayout, QLabel,
                             QPushButton, QSizePolicy, QGraphicsOpacityEffect)
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QPoint, QRect, QSize, QVariantAnimation, QTimer, Qt
from PyQt6.QtGui import QColor, QPalette, QMouseEvent, QFont


class AnimatedButton(QPushButton):
    def __init__(self, text, animation_type='fade', animation_time=0.5, font_size=18):
        super().__init__("")

        self.label = QLabel(text, self)
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("QLabel { background-color: transparent; color: white; }")
        self.label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)

        # Setup Font
        font = QFont()
        font.setPointSize(font_size)
        self.label.setFont(font)


        self.animation_type = animation_type
        # Every Animation time in milliseconds
        self.animation_time = int(animation_time * 1000)

        self.setFlat(True)

        self.full_static_style = f"""
                QPushButton {{ 
                    border: 2px solid gray; 
                    border-radius: 5px; 
                    color: white;
                    background-color: transparent; 
                    white-space: normal;
                    min-height: 40px; 
                    padding: 5px;
                    text-align: center;
                }}

                QPushButton:hover {{
                    border-color: yellow;
                    background-color: rgba(100, 100, 100, 50);
                }}

                QPushButton:pressed {{
                    background-color: rgba(50, 50, 50, 255);
                    border-style: inset;
                }}

                QPushButton:checked {{
                    background-color: #55aaff;
                }}
            """

        self.setStyleSheet(self.full_static_style)

        self.base_css = "border: 2px solid gray; border-radius: 5px; color: white; white-space: normal; min-height: 40px; padding: 5px; text-align: center;"

        self.setCheckable(True)

        self.setAutoFillBackground(True)

        self._original_palette = self.palette()

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)


    # Overwrite event, for label always fulfill button
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.label.setGeometry(self.rect().adjusted(5, 5, -5, -5))

    # Redirect setText to Label
    def setText(self, text):
        self.label.setText(text)

    # Redirect get Text from Label
    def text(self):
        return self.label.text()

    # Catch mouse event to disable button automatic change state pressed/unpressed
    def mousePressEvent(self, event: QMouseEvent):
        if self.isCheckable():
            if event.button() == Qt.MouseButton.LeftButton:
                # emit left mouse button - for working normally in matching_ui.py
                self.clicked.emit(self.isChecked())

                # I dont' want call super().mousePressEvent to prevent button change state (toggle)
                return

        # If this is other type of buttons or other click - call super...
        super().mousePressEvent(event)

    def start_disappearing(self):
        if self.animation_type == 'fade':
            self.animate_fade()
        elif self.animation_type == 'shrink':
            self.animate_shrink_centered()
        elif self.animation_type == 'fly':      # don't use currently, need to repair the code
            self.animate_fly()

    def animate_fade(self):
        # create transparent effect
        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)

        # create animation based on opacity
        self.anim = QPropertyAnimation(effect, b"opacity")
        self.anim.setDuration(self.animation_time)
        self.anim.setStartValue(1.0)    # fully visible
        self.anim.setEndValue(0.0)      # hidden
        self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self.anim.start()

    def animate_shrink_centered(self):
        # original X,Y
        start_rect = self.geometry()

        center_point = start_rect.center()

        # End geometry, center position with zero size
        end_rect = QRect(center_point.x(), center_point.y(), 0, 0)

        # animate geometry (not size!)
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(self.animation_time)
        self.anim.setStartValue(start_rect)
        self.anim.setEndValue(end_rect)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

        # Use timer to avoid flicker in last frame
        self.anim.finished.connect(lambda: QTimer.singleShot(0, self.set_permanent_transparent ))

        self.anim.start()

    def set_permanent_transparent(self):
        # Create and setup 100% Transparency on button
        effect = QGraphicsOpacityEffect(self)
        effect.setOpacity(0.0)
        self.setGraphicsEffect(effect)

    def animate_fly(self):
        # fly up and fade
        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)

        self.anim_fade = QPropertyAnimation(effect, b"opacity")
        self.anim_fade.setDuration(self.animation_time)
        self.anim_fade.setStartValue(1.0)
        self.anim_fade.setEndValue(0.0)

        self.anim_pos = QPropertyAnimation(self, b"pos")
        self.anim_pos.setDuration(self.animation_time)
        self.anim_pos.setStartValue(self.pos())
        self.anim_pos.setEndValue(self.pos() - QPoint(0, 50))   # 50 px up

        self.anim_fade.finished.connect(self.hide)

        self.anim_fade.start()
        self.anim_pos.start()


    # Threshold for alpha in animation to finish it.
    # this is the only way I found to avoid last frame 100% opacity flash
    # below the threshold animation is finished
    ALPHA_THRESHOLD = 15

    def _generate_flash_style(self, color):

        # Cut animation when threshold is achieved
        a = color.alpha()

        if a <= self.ALPHA_THRESHOLD:
            if self.color_anim.state() == self.color_anim.State.Running:
                self.force_finish_flash()
                return ""

        # Generate CSS in current frame
        r, g, b, a = color.red(), color.green(), color.blue(), color.alpha()

        # I remove hover, to disable it during animation
        background_style = f"background-color: rgba({r}, {g}, {b}, {a});"

        # Original Style + dynamic background
        qpushbutton_style = f"QPushButton {{ {self.base_css} {background_style} }}"

        # chcked style must be setup if button is in setChecked
        checked_style = f"""
            QPushButton:checked {{
                background-color: #55aaff; 
                border: 2px solid white; 
            }}
        """

        return qpushbutton_style + checked_style

    def flash_color_overlay_two(self, color_name="red"):
        base_color = QColor(color_name)

        start_color = QColor(base_color)
        start_color.setAlpha(255)

        end_color = QColor(base_color)
        end_color.setAlpha(0)

        # setup 100% color
        self.update_overlay_color(start_color)

        # create and run fade animation (from 255 to 0 alpha)
        self.color_anim = QVariantAnimation(self)
        self.color_anim.setDuration(self.animation_time)
        self.color_anim.setStartValue(start_color)
        self.color_anim.setEndValue(end_color)
        self.color_anim.setEasingCurve(QEasingCurve.Type.OutQuad)

        try:
            self.color_anim.finished.disconnect()
        except TypeError:
            pass

        ### Poniżej kod wywalenia hover podczas animacji

        # First frame of Flash
        self.setStyleSheet(self._generate_flash_style(start_color))

        # connect to fade method
        self.color_anim.valueChanged.connect(lambda color: self.setStyleSheet(self._generate_flash_style(color)))

        self.color_anim.start()

    # When fade reach alpha_threshold, this method kill animation before it's normally finish
    # to avoid last frame 100% opacity flash
    def force_finish_flash(self):

        # Stop Animation
        if self.color_anim.state() == QVariantAnimation.State.Running:
            self.color_anim.stop()

        # Clear CSS
        QTimer.singleShot(0, self.restore_default_style)

    def update_overlay_color(self, color):
        r, g, b, a = color.red(), color.green(), color.blue(), color.alpha()

        ALPHA_THRESHOLD = 15
        if a <= ALPHA_THRESHOLD and self.color_anim.state() == self.color_anim.State.Running:
            self.force_finish_flash()
            return

        dynamic_style = f"""
            QPushButton {{ 
                {self.base_css} 
                background-color: rgba({r}, {g}, {b}, {a}); 
            }}

            /* Keep static :hover and :pressed without changes! */
            QPushButton:hover {{
                border-color: yellow;
                background-color: rgba(100, 100, 100, 50);
            }}
            QPushButton:pressed {{
                background-color: rgba(50, 50, 50, 255);
                border-style: inset;
            }}
        """

        self.setStyleSheet(dynamic_style)

    def restore_default_style(self):
        self.setStyleSheet(self.full_static_style)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Animowane Siatka")
        self.resize(400, 300)

        layout = QGridLayout()
        self.setLayout(layout)

        # create grid 3x3
        for row in range(3):
            for col in range(3):
                # create contener (QLabel)
                container_label = QLabel()
                container_label.setStyleSheet("QLabel { background-color: #eee; border: 1px solid #ccc; }")

                container_label.setFixedSize(120, 60)

                # create button inside (diffrent animation for different column)
                if col == 0:
                    btn = AnimatedButton(f"Fade {row},{col}", 'fade')
                elif col == 1:
                    btn = AnimatedButton(f"Shrink {row},{col}", 'shrink')
                else:
                    btn = AnimatedButton(f"Fly {row},{col}", 'fly')

                btn.setParent(container_label)
                btn.move(10, 10)
                layout.addWidget(container_label, row, col)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exec()
