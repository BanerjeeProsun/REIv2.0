import sys
import math
from typing import Literal
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QPainterPath

UIState = Literal["idle", "listening", "processing", "speaking"]

class OrbWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setFixedSize(160, 160)
        self.state: UIState = "idle"
        
        self.pulse_phase = 0.0
        self.spin_angle = 0.0
        self.volume = 0.0
        self.target_volume = 0.0
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(16)
        
    def set_state(self, state: UIState) -> None:
        self.state = state
        
    def set_volume(self, vol: float) -> None:
        self.target_volume = min(1.0, vol * 5.0)
        
    def _animate(self) -> None:
        self.pulse_phase += 0.05
        if self.pulse_phase > math.pi * 2:
            self.pulse_phase -= math.pi * 2
            
        self.spin_angle += 5.0
        if self.spin_angle >= 360:
            self.spin_angle -= 360
            
        self.volume += (self.target_volume - self.volume) * 0.2
        self.update()
        
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center = QPointF(self.width() / 2, self.height() / 2)
        base_radius = 40.0
        
        accent_color = QColor(229, 192, 123) # Gold/Beige #E5C07B
        
        if self.state == "idle":
            pen = QPen(accent_color, 2)
            painter.setPen(pen)
            painter.drawEllipse(center, base_radius, base_radius)
            
        elif self.state == "listening":
            # Inner circle
            pen = QPen(accent_color, 2)
            painter.setPen(pen)
            painter.drawEllipse(center, base_radius, base_radius)
            
            # Pulsing rings
            for i in range(1, 4):
                phase = (self.pulse_phase + i * 2.0) % (math.pi * 2)
                scale = (phase / (math.pi * 2))
                alpha = int(255 * (1.0 - scale) * 0.3)
                
                r = base_radius + (scale * 30.0)
                
                ring_color = QColor(accent_color)
                ring_color.setAlpha(alpha)
                painter.setPen(QPen(ring_color, 1))
                painter.drawEllipse(center, r, r)
                
        elif self.state == "processing":
            pen = QPen(accent_color, 2)
            painter.setPen(pen)
            
            # Spinning arc
            span_angle = int(120 * 16) # 120 degrees
            start_angle = int(-self.spin_angle * 16)
            
            rect = QRectF(center.x() - base_radius, center.y() - base_radius, base_radius * 2, base_radius * 2)
            painter.drawArc(rect, start_angle, span_angle)
            
            # Dimmed full circle
            dim_color = QColor(accent_color)
            dim_color.setAlpha(30)
            painter.setPen(QPen(dim_color, 1))
            painter.drawEllipse(center, base_radius, base_radius)
            
        elif self.state == "speaking":
            # Glow effect based on volume
            glow_radius = base_radius + (self.volume * 15.0)
            
            glow_color = QColor(accent_color)
            glow_color.setAlpha(int(100 * self.volume))
            
            painter.setBrush(glow_color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(center, glow_radius, glow_radius)
            
            # Core circle
            pen = QPen(accent_color, 2)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(center, base_radius, base_radius)


class ReiUI(QMainWindow):
    """Implementation of UI-02: Floating 'orb' mode for voice."""
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Rei")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(300, 350)
        
        # Center on right side of screen
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 320, 40)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Dark Background Panel
        self.bg_panel = QWidget()
        self.bg_panel.setStyleSheet(
            "background-color: #0B0B0C; "
            "border: 1px solid rgba(229, 192, 123, 0.2); "
            "border-radius: 12px;"
        )
        self.bg_layout = QVBoxLayout(self.bg_panel)
        self.bg_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.bg_panel)
        
        # Top Header (App Name + Window controls placeholder)
        self.header_label = QLabel("Rei")
        self.header_label.setStyleSheet("color: rgba(255, 255, 255, 0.5); font-family: 'Segoe UI'; font-size: 12px;")
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        header_container = QWidget()
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(15, 10, 15, 0)
        header_layout.addWidget(self.header_label)
        self.bg_layout.addWidget(header_container)
        
        # Orb Widget
        self.orb = OrbWidget()
        self.bg_layout.addWidget(self.orb, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Status Text
        self.status_label = QLabel("How can I help you?")
        self.status_label.setStyleSheet("color: #FFFFFF; font-family: 'Segoe UI'; font-size: 14px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bg_layout.addWidget(self.status_label)
        
        # Add some padding at the bottom
        self.bg_layout.addSpacing(40)
        
        self.set_state("idle")
        
    def set_state(self, state: UIState) -> None:
        self.orb.set_state(state)
        if state == "idle":
            self.status_label.setText("How can I help you?")
        elif state == "listening":
            self.status_label.setText("Listening...")
        elif state == "processing":
            self.status_label.setText("Thinking...")
        elif state == "speaking":
            self.status_label.setText("Speaking...")
            
    def set_status(self, status: str) -> None:
        """Legacy support for orchestrator passing raw strings."""
        if "Listening" in status:
            self.set_state("listening")
        elif "Transcribing" in status or "Routing" in status:
            self.set_state("processing")
        elif "Speaking" in status:
            self.set_state("speaking")
        else:
            self.set_state("idle")
            
    def update_volume(self, vol: float) -> None:
        self.orb.set_volume(vol)
        
    def mouseDoubleClickEvent(self, event) -> None:
        QApplication.quit()
