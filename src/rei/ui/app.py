from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QHBoxLayout
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QMouseEvent, QPainter, QColor, QPen

class WaveformWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setFixedHeight(40)
        self.volume = 0.0
        self.target_volume = 0.0
        
        # Smooth animation timer
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._animate)
        self.anim_timer.start(16) # ~60fps
        
    def set_volume(self, vol: float) -> None:
        # Scale volume up for visual effect, cap at 1.0
        self.target_volume = min(1.0, vol * 5.0)
        
    def _animate(self) -> None:
        # Smooth interpolation
        self.volume += (self.target_volume - self.volume) * 0.3
        self.update()
        
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        y = height / 2
        
        # Base line
        pen = QPen(QColor(0, 255, 204, 100)) # #00FFCC with alpha
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawLine(0, int(y), width, int(y))
        
        # Glowing pulse in the center
        amp = max(4.0, self.volume * height)
        
        painter.setBrush(QColor(0, 255, 204, 200))
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Draw 3 circles for a cool effect
        painter.drawEllipse(int(width/2 - amp/2), int(y - amp/2), int(amp), int(amp))
        
        amp2 = amp * 0.6
        painter.setBrush(QColor(255, 255, 255, 255))
        painter.drawEllipse(int(width/2 - amp2/2), int(y - amp2/2), int(amp2), int(amp2))

class ReiUI(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Rei v2.0")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(320, 120)
        
        # Center on screen
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 340, 40)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Background container for styling
        self.bg_container = QWidget()
        self.bg_container.setStyleSheet(
            "background-color: rgba(15, 15, 20, 230); "
            "border: 1px solid rgba(0, 255, 204, 50); "
            "border-radius: 12px;"
        )
        self.bg_layout = QVBoxLayout(self.bg_container)
        self.main_layout.addWidget(self.bg_container)
        
        # Waveform
        self.waveform = WaveformWidget()
        self.bg_layout.addWidget(self.waveform)
        
        # Status Text
        self.status_label = QLabel("Rei: Offline")
        self.status_label.setStyleSheet(
            "color: #E0E0E0; font-family: 'Segoe UI', sans-serif; font-size: 13px;"
        )
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bg_layout.addWidget(self.status_label)
        
    def set_status(self, status: str) -> None:
        self.status_label.setText(status)
        
    def update_volume(self, vol: float) -> None:
        self.waveform.set_volume(vol)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        QApplication.quit()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPos() - self.drag_pos)
            event.accept()
