from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QHBoxLayout
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QMouseEvent, QPainter, QColor, QPen



class ReiUI(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Rei v2.0")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(250, 40)
        
        # Center on screen
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 270, 20)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Status Text
        self.status_label = QLabel("Rei: Offline")
        self.status_label.setStyleSheet(
            "color: #FFFFFF; font-family: 'Consolas', monospace; font-size: 11px; "
            "background-color: rgba(0, 0, 0, 180); padding: 8px; border-radius: 4px;"
        )
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.status_label)
        
    def set_status(self, status: str) -> None:
        self.status_label.setText(status)
        
    def update_volume(self, vol: float) -> None:
        # Volume visualization removed per user request
        pass

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
