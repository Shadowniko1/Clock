import sys
import os
import random
import ctypes
from PyQt6.QtCore import Qt, QTimer, QTime, QUrl, QPropertyAnimation, QRect
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QPainterPath, QPen
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtWidgets import QApplication, QLabel, QHBoxLayout, QSlider, QPushButton, QWidget, QVBoxLayout

# ─── ROBUST PATH HELPER FOR SEAMLESS EMBEDDING ─────────────────────────────
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


class CozyDesktopClock(QWidget):
    def __init__(self):
        super().__init__()

        # Borderless, smooth desktop integration
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowMinMaxButtonsHint
        )
        
        # Anti-bleed corner masking configurations
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        
        # Dimensions
        self.base_width = 360
        self.expanded_width = 540  
        self.normal_height = 160
        self.resize(self.base_width, self.normal_height)
        self.setMinimumSize(320, 110)
        
        # Apply the absolute bulletproof dual-layer icon fix
        self.apply_my_icon()
        self.setWindowTitle("Cozy Desktop Clock")
        self.setMouseTracking(True)

        # State Variables
        self.match_active = False    
        self.glow_active = True      # Warm Hearth Glow
        self.menu_expanded = False

        # Cozy Palette Definition (Warm, earthy, coffee-shop tones)
        self.cozy_palette = [
            QColor(36, 27, 24),    # Dark Espresso
            QColor(46, 31, 26),    # Warm Walnut
            QColor(54, 34, 27),    # Burnt Terracotta
            QColor(41, 29, 31),    # Dusty Plum
            QColor(33, 30, 26)     # Soft Charcoal Wood
        ]
        self.bg_color = random.choice(self.cozy_palette)
        self.color_switch_counter = 0

        # Master Horizontal Layout
        self.master_layout = QHBoxLayout(self)
        self.master_layout.setContentsMargins(0, 0, 0, 0)
        self.master_layout.setSpacing(0)

        # ─── 1. SIDE PANEL WIDGET (LEFT SIDE) ────────────────────────────────
        self.side_menu = QWidget(self)
        self.side_menu.setObjectName("SideMenu")
        self.side_menu.setFixedWidth(180)
        self.side_menu.setStyleSheet("""
            QWidget #SideMenu {
                background-color: #1a1513;
                border-top-left-radius: 16px;
                border-bottom-left-radius: 16px;
            }
        """)
        self.side_layout = QVBoxLayout(self.side_menu)
        self.side_layout.setContentsMargins(15, 20, 15, 20)
        self.side_layout.setSpacing(12)
        self.side_layout.addStretch()

        self.setup_match_btn = QPushButton("Setup Match: OFF", self.side_menu)
        self.setup_match_btn.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.side_layout.addWidget(self.setup_match_btn)

        self.glow_btn = QPushButton("Glow: OFF", self.side_menu)
        self.glow_btn.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.side_layout.addWidget(self.glow_btn)
        
        self.side_layout.addStretch()

        self.setup_match_btn.clicked.connect(self.toggle_setup_match)
        self.glow_btn.clicked.connect(self.toggle_glow)

        self.refresh_button_styles()
        self.master_layout.addWidget(self.side_menu)
        self.side_menu.hide()

        # ─── 2. MAIN CLOCK CONTAINER WIDGET (RIGHT SIDE) ───────────────────────
        self.main_container = QWidget(self)
        self.main_container.setObjectName("MainContainer")
        self.main_container.setMouseTracking(True)
        
        self.main_layout = QVBoxLayout(self.main_container)
        self.main_layout.setContentsMargins(15, 12, 15, 12)
        self.main_layout.setSpacing(6)

        # Top Control Buttons Row
        self.top_row_widget = QWidget(self.main_container)
        self.top_row_layout = QHBoxLayout(self.top_row_widget)
        self.top_row_layout.setContentsMargins(5, 0, 5, 0)
        self.top_row_layout.setSpacing(6)
        
        self.menu_button = QPushButton("←", self.main_container)
        self.menu_button.setFixedSize(24, 24)
        self.menu_button.setStyleSheet("""
            QPushButton { 
                background: rgba(255, 240, 230, 0.06); 
                color: #c7b8b0; 
                border-radius: 12px; 
                border: none; 
                font-size: 10pt;
            }
            QPushButton:hover { background: rgba(255, 240, 230, 0.12); color: #fbf7f5; }
        """)
        self.menu_button.clicked.connect(self.toggle_side_menu)
        self.top_row_layout.addWidget(self.menu_button)
        
        self.top_row_layout.addStretch()
        
        self.minimize_button = QPushButton("–", self.main_container)
        self.minimize_button.setFixedSize(24, 24)
        self.minimize_button.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.minimize_button.setStyleSheet("""
            QPushButton { background: rgba(255, 240, 230, 0.06); color: #c7b8b0; border-radius: 12px; border: none; }
            QPushButton:hover { background: rgba(255, 240, 230, 0.12); color: #fbf7f5; }
        """)
        self.minimize_button.clicked.connect(self.animate_minimize)
        self.top_row_layout.addWidget(self.minimize_button)

        self.close_button = QPushButton("×", self.main_container)
        self.close_button.setFixedSize(24, 24)
        self.close_button.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.close_button.setStyleSheet("""
            QPushButton { background: rgba(255, 240, 230, 0.06); color: #c7b8b0; border-radius: 12px; border: none; }
            QPushButton:hover { background: #8c3f3f; color: white; }
        """)
        self.close_button.clicked.connect(self.close_app)
        self.top_row_layout.addWidget(self.close_button)
        self.main_layout.addWidget(self.top_row_widget)

        # Time Display Label - Swapped to a soft, elegant Serif font
        self.label = QLabel(self.main_container)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        clock_font = QFont("Georgia", 44, QFont.Weight.Medium)
        self.label.setFont(clock_font)
        self.label.setStyleSheet("color: #f7f1ed; background: transparent; letter-spacing: 1px;")
        self.main_layout.addWidget(self.label)

        # Bottom Music Pill Layout Container
        self.controller_widget = QWidget(self.main_container)
        self.controller_widget.setObjectName("ControllerPill")
        self.controller_widget.setStyleSheet("""
            QWidget #ControllerPill {
                background-color: rgba(20, 15, 12, 0.5);
                border-radius: 20px;
            }
        """)
        self.control_layout = QHBoxLayout(self.controller_widget)
        self.control_layout.setContentsMargins(15, 5, 15, 5)
        self.control_layout.setSpacing(10)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal, self.main_container)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 4px; background: rgba(255, 255, 255, 0.1); border-radius: 2px; }
            QSlider::sub-page:horizontal { background: #dfb28d; border-radius: 2px; }
            QSlider::handle:horizontal { background: #f7f1ed; width: 10px; height: 10px; margin: -3px 0; border-radius: 5px; }
        """)
        self.volume_slider.valueChanged.connect(self.change_volume)
        self.control_layout.addWidget(self.volume_slider, stretch=1)

        self.play_button = QPushButton("⏸", self.main_container)
        self.play_button.setFixedSize(30, 30)
        self.play_button.setStyleSheet("""
            QPushButton { 
                background: #dfb28d; 
                color: #241714; 
                border-radius: 15px; 
                border: none; 
                font-size: 11pt;
            }
            QPushButton:hover { background: #ebd2be; }
        """)
        self.play_button.clicked.connect(self.toggle_audio)
        self.control_layout.addWidget(self.play_button)
        self.main_layout.addWidget(self.controller_widget)

        self.master_layout.addWidget(self.main_container)

        self.top_row_widget.setVisible(False)
        self.controller_widget.setVisible(False)

        # Engine Mechanics
        self._drag_position = None
        self.border_margin = 10
        self.is_minimizing = False

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)

        # Media Player Audio Setup
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setSource(QUrl.fromLocalFile(resource_path("lofi_music.mp3")))
        self.media_player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.5) 
        self.media_player.setLoops(QMediaPlayer.Loops.Infinite)
        self.media_player.play()

        self.update_clock()

    def refresh_button_styles(self):
        off_style = "background: #2e2521; color: #a3938b; border: 1px solid #40342f; border-radius: 6px; padding: 8px 4px; font-weight: bold;"
        on_style = "background: #3b2f25; color: #dfb28d; border: 1px solid #b38562; border-radius: 6px; padding: 8px 4px; font-weight: bold;"
        
        glow_on_style = """
            QPushButton {
                background: #3d2c20; 
                color: #f7cb99; 
                border: 1px solid #e09f5e;
                border-radius: 6px; 
                padding: 8px 4px;
                font-weight: bold;
            }
        """

        if self.match_active:
            self.setup_match_btn.setText("Setup Match: ON")
            self.setup_match_btn.setStyleSheet(on_style)
        else:
            self.setup_match_btn.setText("Setup Match: OFF")
            self.setup_match_btn.setStyleSheet(off_style)

        if self.glow_active:
            self.glow_btn.setText("Glow: ON")
            self.glow_btn.setStyleSheet(glow_on_style)
        else:
            self.glow_btn.setText("Glow: OFF")
            self.glow_btn.setStyleSheet(off_style)

    def toggle_side_menu(self):
        self.menu_expanded = not self.menu_expanded
        geom = self.geometry()
        if self.menu_expanded:
            self.menu_button.setText("→")
            self.setGeometry(geom.x() - 180, geom.y(), self.expanded_width, self.normal_height)
            self.side_menu.show()
        else:
            self.menu_button.setText("←")
            self.side_menu.hide()
            self.setGeometry(geom.x() + 180, geom.y(), self.base_width, self.normal_height)

    def toggle_setup_match(self):
        self.match_active = not self.match_active
        self.refresh_button_styles()
        self.update() 

    def toggle_glow(self):
        self.glow_active = not self.glow_active
        self.refresh_button_styles()
        self.update() 

    # ─── PAINT ENGINE: SOFT HEARTH AMBIENT GLOW ───────────────────────────
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        p.fillRect(self.rect(), Qt.GlobalColor.transparent)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        
        rect = self.main_container.geometry()
        x = float(rect.x())
        y = float(rect.y())
        w = float(rect.width())
        h = float(rect.height())
        radius = 16.0
        
        path = QPainterPath()
        
        if self.menu_expanded:
            path.moveTo(x, y)
            path.lineTo(x + w - radius, y)
            path.quadTo(x + w, y, x + w, y + radius)
            path.lineTo(x + w, y + h - radius)
            path.quadTo(x + w, y + h, x + w - radius, y + h)
            path.lineTo(x, y + h)
            path.closeSubpath()
        else:
            path.addRoundedRect(x, y, w, h, radius, radius)

        if self.match_active:
            p.setBrush(QColor(23, 19, 17, 160))  # Muted glass look
        else:
            p.setBrush(self.bg_color)  
            
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPath(path)

        # Warm Soft Amber Fireplace/Hearth Glow Layout
        if self.glow_active:
            p.setBrush(Qt.BrushStyle.NoBrush)
            
            # Ultra-wide scattered environmental warmth
            glow_pen3 = QPen(QColor(240, 160, 90, 25))
            glow_pen3.setWidthF(9.0)
            p.setPen(glow_pen3)
            p.drawPath(path)
            
            # Inner amber radiance
            glow_pen2 = QPen(QColor(223, 178, 141, 95))
            glow_pen2.setWidthF(4.0)
            p.setPen(glow_pen2)
            p.drawPath(path)
            
            # Subtle core rim light
            glow_pen1 = QPen(QColor(247, 241, 237, 140))
            glow_pen1.setWidthF(1.0)
            p.setPen(glow_pen1)
            p.drawPath(path)

    # ─── NATIVE MECHANICS & WINDOW EVENTS ──────────────────────────────────
    def animate_minimize(self):
        if self.is_minimizing: return
        self.is_minimizing = True
        if self.menu_expanded:
            self.toggle_side_menu()

        self.saved_geometry = self.geometry()
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(220) 
        self.anim.setStartValue(self.saved_geometry)
        
        target_rect = QRect(
            self.saved_geometry.x() + int(self.saved_geometry.width() / 2) - 25,
            self.saved_geometry.y() + self.saved_geometry.height(),
            50, 0
        )
        self.anim.setEndValue(target_rect)
        self.anim.finished.connect(self.finalize_minimize)
        self.anim.start()

    def finalize_minimize(self):
        self.showMinimized()
        self.setGeometry(self.saved_geometry)
        self.is_minimizing = False

    def changeEvent(self, event):
        if event.type() == event.Type.WindowStateChange:
            if not self.isMinimized() and hasattr(self, 'saved_geometry'):
                self.setGeometry(self.saved_geometry)
        super().changeEvent(event)

    def apply_my_icon(self):
        icon_path = resource_path("app_icon.ico")
        if os.path.exists(icon_path):
            app_icon = QIcon(icon_path)
            self.setWindowIcon(app_icon)
            QApplication.setWindowIcon(app_icon)

    def update_clock(self):
        if not self.is_minimizing:
            self.label.setText(QTime.currentTime().toString("hh:mm:ss"))
            
            # Slower background color evolution (only changes every 12 seconds instead of every second)
            if not self.match_active:
                self.color_switch_counter += 1
                if self.color_switch_counter >= 12:
                    self.bg_color = random.choice(self.cozy_palette)
                    self.color_switch_counter = 0
                    
            self.update() 

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
    if sys.platform == "win32":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("lofi.desktop.clock.standalone.cozy")
        except Exception:
            pass

    app = QApplication(sys.argv)
    clock = CozyDesktopClock()
    clock.show()
    sys.exit(app.exec())
