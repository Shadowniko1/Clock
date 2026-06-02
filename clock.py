import sys
import os
import random
import ctypes
from PyQt6.QtCore import Qt, QTimer, QTime, QUrl, QPropertyAnimation, QRect
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtWidgets import QApplication, QLabel, QHBoxLayout, QSlider, QPushButton, QWidget, QVBoxLayout

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

if sys.platform == "win32":
    myappid = "lofi.desktop.clock.system.v3" 
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)


class DesktopClock(QWidget):
    def __init__(self):
        super().__init__()
        
        # Keep it completely frameless and clean
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Geometry configurations
        self.normal_width = 350
        self.normal_height = 160
        self.resize(self.normal_width, self.normal_height)
        self.setMinimumSize(250, 110)
        
        self.apply_my_icon()
        self.setWindowTitle("Lofi Desktop Clock")
        self.setMouseTracking(True)

        # Main Layout Setup
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 12, 15, 12)

        # ─── TOP CONTROL BUTTONS ROW ───────────────────────────────────────
        self.top_row_widget = QWidget(self)
        self.top_row_layout = QHBoxLayout(self.top_row_widget)
        self.top_row_layout.setContentsMargins(0, 0, 5, 0)
        self.top_row_layout.setSpacing(6)
        self.top_row_layout.addStretch()
        
        self.minimize_button = QPushButton("–", self)
        self.minimize_button.setFixedSize(24, 24)
        self.minimize_button.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.minimize_button.setStyleSheet("""
            QPushButton { background: rgba(255, 255, 255, 0.15); color: white; border-radius: 12px; border: none; padding-bottom: 2px; }
            QPushButton:hover { background: rgba(255, 255, 255, 0.3); }
        """)
        self.minimize_button.clicked.connect(self.animate_minimize)
        self.top_row_layout.addWidget(self.minimize_button)

        self.close_button = QPushButton("×", self)
        self.close_button.setFixedSize(24, 24)
        self.close_button.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.close_button.setStyleSheet("""
            QPushButton { background: rgba(255, 255, 255, 0.15); color: white; border-radius: 12px; border: none; padding-bottom: 2px; }
            QPushButton:hover { background: rgba(232, 17, 35, 0.9); }
        """)
        self.close_button.clicked.connect(self.close_app)
        self.top_row_layout.addWidget(self.close_button)
        self.layout.addWidget(self.top_row_widget)

        # ─── TIME DISPLAY ──────────────────────────────────────────────────
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setFont(QFont("Arial", 44, QFont.Weight.Bold))
        self.label.setStyleSheet("color: white; background: transparent;")
        self.layout.addWidget(self.label)

        # ─── MODERN STREAMING CONTAINER PANEL ──────────────────────────────
        # Matches your screenshot layout: Pill structure with volume on left, toggle on right
        self.controller_widget = QWidget(self)
        self.controller_widget.setObjectName("ControllerPill")
        self.controller_widget.setStyleSheet("""
            QWidget #ControllerPill {
                background-color: rgba(0, 0, 0, 0.4);
                border-radius: 20px;
            }
        """)
        
        self.control_layout = QHBoxLayout(self.controller_widget)
        self.control_layout.setContentsMargins(15, 5, 10, 5)
        self.control_layout.setSpacing(10)

        # Left: Tracking Volume Slider
        self.volume_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 4px; background: rgba(255, 255, 255, 0.2); border-radius: 2px; }
            QSlider::sub-page:horizontal { background: white; border-radius: 2px; }
            QSlider::handle:horizontal { background: white; width: 10px; height: 10px; margin: -3px 0; border-radius: 5px; }
        """)
        self.volume_slider.valueChanged.connect(self.change_volume)
        self.control_layout.addWidget(self.volume_slider, stretch=1)

        # Right: Circular Media Button
        self.play_button = QPushButton("⏺", self)
        self.play_button.setFixedSize(30, 30)
        self.play_button.setStyleSheet("""
            QPushButton { 
                background: white; 
                color: black; 
                border-radius: 15px; 
                border: none; 
                font-size: 11pt;
                font-weight: bold;
                padding-left: 1px;
            }
            QPushButton:hover { background: rgba(240, 240, 240, 1); }
        """)
        self.play_button.clicked.connect(self.toggle_audio)
        self.control_layout.addWidget(self.play_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.layout.addWidget(self.controller_widget)

        # Initial visibility configurations
        self.top_row_widget.setVisible(False)
        self.controller_widget.setVisible(False)

        # Mechanics & Audio Architecture Setup
        self._drag_position = None
        self.border_margin = 10
        self.is_minimizing = False

        self.color1 = self.get_random_color()
        self.color2 = self.get_random_color()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)

        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        
        music_path = resource_path("lofi_music.mp3")
        self.media_player.setSource(QUrl.fromLocalFile(music_path))
        self.audio_output.setVolume(0.5) 
        self.media_player.setLoops(QMediaPlayer.Loops.Infinite)
        self.media_player.play()

        self.update_clock()

    # ─── SMOOTH CUSTOM MINIMIZE ANIMATION ──────────────────────────────────
    def animate_minimize(self):
        if self.is_minimizing:
            return
        self.is_minimizing = True
        
        # Save our actual current layout bounds
        self.saved_geometry = self.geometry()
        
        # Build the shrinking property interpolator
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(220) # 220ms matches native Windows transitions cleanly
        self.anim.setStartValue(self.saved_geometry)
        
        # Animate toward the bottom screen edge (simulating sliding to taskbar)
        target_rect = QRect(
            self.saved_geometry.x() + int(self.saved_geometry.width() / 2) - 25,
            self.saved_geometry.y() + self.saved_geometry.height(),
            50, 
            0
        )
        self.anim.setEndValue(target_rect)
        self.anim.finished.connect(self.finalize_minimize)
        self.anim.start()

    def finalize_minimize(self):
        self.showMinimized()
        # Restore full design canvas scale dimensions layout once hidden
        self.setGeometry(self.saved_geometry)
        self.is_minimizing = False

    def changeEvent(self, event):
        """ Ensure the UI graphics render properly if minimized window states change """
        if event.type() == event.Type.WindowStateChange:
            if not self.isMinimized() and hasattr(self, 'saved_geometry'):
                self.setGeometry(self.saved_geometry)
        super().changeEvent(event)

    # ─── NATIVE APP MECHANICS ──────────────────────────────────────────────
    def apply_my_icon(self):
        icon_path = resource_path("app_icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    def get_random_color(self):
        return QColor(random.randint(40, 180), random.randint(40, 180), random.randint(40, 180))

    def update_clock(self):
        if not self.is_minimizing:
            self.label.setText(QTime.currentTime().toString("hh:mm:ss"))
            self.color1 = self.color2
            self.color2 = self.get_random_color()
            self.update() 

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        from PyQt6.QtGui import QLinearGradient
        grad = QLinearGradient(0, 0, rect.width(), rect.height())
        grad.setColorAt(0.0, self.color1)
        grad.setColorAt(1.0, self.color2)
        p.setBrush(grad)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(rect, 16, 16)

    def toggle_audio(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.play_button.setText("▶")
        else:
            self.media_player.play()
            self.play_button.setText("⏸")

    def change_volume(self, value):
        self.audio_output.setVolume(value / 100.0)

    def enterEvent(self, event):
        if not self.is_minimizing:
            self.top_row_widget.setVisible(True)
            self.controller_widget.setVisible(True)

    def leaveEvent(self, event):
        self.top_row_widget.setVisible(False)
        self.controller_widget.setVisible(False)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            rect = self.rect()
            left = pos.x() < self.border_margin
            right = pos.x() > rect.width() - self.border_margin
            top = pos.y() < self.border_margin
            bottom = pos.y() > rect.height() - self.border_margin

            edge = None
            if left and top: edge = Qt.Edge.LeftEdge | Qt.Edge.TopEdge
            elif right and top: edge = Qt.Edge.RightEdge | Qt.Edge.TopEdge
            elif left and bottom: edge = Qt.Edge.LeftEdge | Qt.Edge.BottomEdge
            elif right and bottom: edge = Qt.Edge.RightEdge | Qt.Edge.BottomEdge
            elif left: edge = Qt.Edge.LeftEdge
            elif right: edge = Qt.Edge.RightEdge
            elif top: edge = Qt.Edge.TopEdge
            elif bottom: edge = Qt.Edge.BottomEdge

            if edge is not None:
                self.windowHandle().startSystemResize(edge)
            else:
                self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        rect = self.rect()
        left = pos.x() < self.border_margin
        right = pos.x() > rect.width() - self.border_margin
        top = pos.y() < self.border_margin
        bottom = pos.y() > rect.height() - self.border_margin

        if (left and top) or (right and bottom): self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif (right and top) or (left and bottom): self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif left or right: self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif top or bottom: self.setCursor(Qt.CursorShape.SizeVerCursor)
        else: self.setCursor(Qt.CursorShape.ArrowCursor)

        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_position is not None:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_position = None

    def close_app(self):
        self.media_player.stop()
        self.media_player.setSource(QUrl())
        QApplication.quit()
        sys.exit(0)

    def closeEvent(self, event):
        self.close_app()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    clock = DesktopClock()
    clock.show()
    sys.exit(app.exec())