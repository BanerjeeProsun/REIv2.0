from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt

from PySide6.QtGui import QMouseEvent

class ReiUI(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Rei v2.0")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(300, 100)
        
        # Center on screen
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 320, 20)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Glowing Orb (Text placeholder for now)
        self.status_label = QLabel("Rei: Listening...")
        self.status_label.setStyleSheet(
            "color: #00FFCC; font-size: 16px; font-weight: bold; "
            "background-color: rgba(10, 10, 10, 200); padding: 15px; border-radius: 10px;"
        )
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.status_label)
        
    def set_status(self, status: str) -> None:
        self.status_label.setText(status)

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
