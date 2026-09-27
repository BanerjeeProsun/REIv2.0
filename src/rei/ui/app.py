import sys
import math
from typing import Literal
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QStackedWidget, QLineEdit, QScrollArea, QFrame,
    QGridLayout, QCheckBox, QComboBox, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF, QSize
from PySide6.QtGui import QPainter, QColor, QPen, QFont

UIState = Literal["idle", "listening", "processing", "speaking"]

# --- COMPACT ORB WIDGET ---

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
        accent_color = QColor(229, 192, 123)
        
        if self.state == "idle":
            painter.setPen(QPen(accent_color, 2))
            painter.drawEllipse(center, base_radius, base_radius)
        elif self.state == "listening":
            painter.setPen(QPen(accent_color, 2))
            painter.drawEllipse(center, base_radius, base_radius)
            for i in range(1, 4):
                phase = (self.pulse_phase + i * 2.0) % (math.pi * 2)
                scale = (phase / (math.pi * 2))
                alpha = int(255 * (1.0 - scale) * 0.3)
                r = base_radius + (scale * 30.0)
                rc = QColor(accent_color)
                rc.setAlpha(alpha)
                painter.setPen(QPen(rc, 1))
                painter.drawEllipse(center, r, r)
        elif self.state == "processing":
            painter.setPen(QPen(accent_color, 2))
            span_angle = int(120 * 16)
            start_angle = int(-self.spin_angle * 16)
            rect = QRectF(center.x() - base_radius, center.y() - base_radius, base_radius * 2, base_radius * 2)
            painter.drawArc(rect, start_angle, span_angle)
            dim_color = QColor(accent_color)
            dim_color.setAlpha(30)
            painter.setPen(QPen(dim_color, 1))
            painter.drawEllipse(center, base_radius, base_radius)
        elif self.state == "speaking":
            glow_radius = base_radius + (self.volume * 15.0)
            glow_color = QColor(accent_color)
            glow_color.setAlpha(int(100 * self.volume))
            painter.setBrush(glow_color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(center, glow_radius, glow_radius)
            painter.setPen(QPen(accent_color, 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(center, base_radius, base_radius)

class CompactOrbWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(250, 300)
        
        layout = QVBoxLayout(self)
        self.bg = QFrame()
        self.bg.setStyleSheet("background-color: #0B0B0C; border: 1px solid rgba(229,192,123,0.2); border-radius: 12px;")
        bg_layout = QVBoxLayout(self.bg)
        
        self.orb = OrbWidget()
        bg_layout.addWidget(self.orb, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.status = QLabel("How can I help you?")
        self.status.setStyleSheet("color: white; font-family: 'Segoe UI'; font-size: 14px;")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bg_layout.addWidget(self.status)
        
        layout.addWidget(self.bg)

# --- FULL APP PAGES ---

class ChatPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background: transparent; border: none;")
        
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.chat_container)
        
        layout.addWidget(self.scroll)
        
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Talk or type...")
        self.input_box.setStyleSheet(
            "background-color: rgba(255,255,255,0.05); color: white; border: 1px solid rgba(255,255,255,0.1); "
            "border-radius: 20px; padding: 10px 15px; font-size: 14px;"
        )
        layout.addWidget(self.input_box)
        
    def add_message(self, text: str, is_user: bool = False):
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        if is_user:
            lbl.setStyleSheet("color: white; background: rgba(229,192,123,0.1); padding: 10px; border-radius: 8px;")
            self.chat_layout.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignRight)
        else:
            lbl.setStyleSheet("color: rgba(255,255,255,0.8); background: rgba(255,255,255,0.05); padding: 10px; border-radius: 8px;")
            self.chat_layout.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignLeft)

class CapabilitiesPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        title = QLabel("Capabilities")
        title.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        layout.addWidget(title)
        
        grid = QGridLayout()
        caps = [
            ("Filesystem", "Read, search, create, move, delete files."),
            ("Applications", "Open, close, control applications."),
            ("Browser", "Web search, open links, retrieve content."),
            ("System", "System information and utilities."),
            ("Media", "Play, pause, control media.")
        ]
        
        for i, (name, desc) in enumerate(caps):
            frame = QFrame()
            frame.setStyleSheet("background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px;")
            fl = QVBoxLayout(frame)
            nl = QLabel(name)
            nl.setStyleSheet("color: #E5C07B; font-weight: bold;")
            dl = QLabel(desc)
            dl.setStyleSheet("color: rgba(255,255,255,0.6);")
            fl.addWidget(nl)
            fl.addWidget(dl)
            grid.addWidget(frame, i // 2, i % 2)
            
        layout.addLayout(grid)
        layout.addStretch()

class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        title = QLabel("Settings")
        title.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        layout.addWidget(title)
        
        grid = QGridLayout()
        
        # Privacy Mode
        pm_frame = QFrame()
        pm_layout = QVBoxLayout(pm_frame)
        pm_layout.addWidget(QLabel("<span style='color: white; font-weight: bold;'>Privacy Mode</span>"))
        
        rad1 = QCheckBox("Local Only")
        rad1.setChecked(True)
        rad1.setStyleSheet("color: white;")
        rad2 = QCheckBox("Cloud Assisted")
        rad2.setStyleSheet("color: white;")
        pm_layout.addWidget(rad1)
        pm_layout.addWidget(rad2)
        grid.addWidget(pm_frame, 0, 0)
        
        # Models
        mod_frame = QFrame()
        mod_layout = QVBoxLayout(mod_frame)
        mod_layout.addWidget(QLabel("<span style='color: white; font-weight: bold;'>Models</span>"))
        
        cmb1 = QComboBox()
        cmb1.addItems(["Llama-3.2-1B-Instruct-Q4_K_M.gguf", "phi-3-mini"])
        mod_layout.addWidget(cmb1)
        grid.addWidget(mod_frame, 0, 1)
        
        layout.addLayout(grid)
        layout.addStretch()

# --- MAIN APP WINDOW ---

class ReiUI(QMainWindow):
    """Full implementation of the Rei UI Reference."""
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Rei v2.0")
        self.setMinimumSize(900, 600)
        self.setStyleSheet("background-color: #0B0B0C; color: white;")
        
        self.central = QWidget()
        self.setCentralWidget(self.central)
        
        self.main_layout = QHBoxLayout(self.central)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(220)
        self.sidebar.setStyleSheet("background-color: #121214; border-right: 1px solid rgba(255,255,255,0.05);")
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(10, 20, 10, 20)
        
        self.logo = QLabel("Rei")
        self.logo.setStyleSheet("color: #E5C07B; font-size: 24px; font-weight: bold; margin-left: 10px; margin-bottom: 20px;")
        self.sidebar_layout.addWidget(self.logo)
        
        self.nav_buttons = {}
        nav_items = ["Chat", "Activity", "Memory", "Capabilities", "Settings"]
        for i, item in enumerate(nav_items):
            btn = QPushButton(item)
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left; padding: 10px 15px; background: transparent; 
                    border: none; border-radius: 8px; color: rgba(255,255,255,0.7); font-size: 14px;
                }
                QPushButton:hover { background: rgba(255,255,255,0.05); color: white; }
                QPushButton:checked { background: rgba(229,192,123,0.1); color: #E5C07B; font-weight: bold; }
            """)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, idx=i: self.switch_page(idx))
            self.sidebar_layout.addWidget(btn)
            self.nav_buttons[i] = btn
            
        self.sidebar_layout.addStretch()
        self.main_layout.addWidget(self.sidebar)
        
        # Stacked Widget (Pages)
        self.pages = QStackedWidget()
        self.pages.setStyleSheet("background-color: #0B0B0C;")
        
        self.chat_page = ChatPage()
        self.activity_page = QWidget() # Placeholder
        self.memory_page = QWidget() # Placeholder
        self.caps_page = CapabilitiesPage()
        self.settings_page = SettingsPage()
        
        self.pages.addWidget(self.chat_page)
        self.pages.addWidget(self.activity_page)
        self.pages.addWidget(self.memory_page)
        self.pages.addWidget(self.caps_page)
        self.pages.addWidget(self.settings_page)
        
        self.main_layout.addWidget(self.pages)
        
        # Orb Overlay
        self.compact_orb = CompactOrbWindow()
        
        # Init state
        self.switch_page(0)
        self.chat_page.add_message("Hello! I am Rei. I am running entirely locally on your hardware. How can I assist you today?")
        
    def switch_page(self, index: int):
        self.pages.setCurrentIndex(index)
        for i, btn in self.nav_buttons.items():
            btn.setChecked(i == index)
            
            
    def set_status(self, status: str) -> None:
        if "Heard: " in status:
            self.chat_page.add_message(status.replace("Heard: ", ""), is_user=True)
            self.compact_orb.orb.set_state("processing")
            self.compact_orb.status.setText("Thinking...")
        elif "Listening" in status:
            self.compact_orb.orb.set_state("listening")
            self.compact_orb.status.setText("Listening...")
        elif "Transcribing" in status or "Routing" in status:
            self.compact_orb.orb.set_state("processing")
            self.compact_orb.status.setText("Thinking...")
        elif "Speaking" in status:
            self.compact_orb.orb.set_state("speaking")
            self.compact_orb.status.setText("Speaking...")
            self.chat_page.add_message(status.replace("Speaking: ", ""))
        else:
            self.compact_orb.orb.set_state("idle")
            self.compact_orb.status.setText("How can I help you?")
            
    def update_volume(self, vol: float) -> None:
        self.compact_orb.orb.set_volume(vol)
        
    def showEvent(self, event):
        super().showEvent(event)
        # Position compact orb in top right of screen
        screen = QApplication.primaryScreen().geometry()
        self.compact_orb.move(screen.width() - 270, 40)
        self.compact_orb.show()
        
    def closeEvent(self, event):
        self.compact_orb.close()
        super().closeEvent(event)
