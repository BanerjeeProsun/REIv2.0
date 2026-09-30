import sys
from pathlib import Path
from PySide6.QtCore import QObject, Signal, Property, Slot
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

class ReiBackend(QObject):
    statusChanged = Signal()
    volumeChanged = Signal()
    stateChanged = Signal()
    messageAdded = Signal(str, bool)
    confirmationRequested = Signal(str, str, str) # title, message, intent_id
    textMessageReceived = Signal(str)

    def __init__(self):
        super().__init__()
        self._status = "How can I help you?"
        self._volume = 0.0
        self._state = "idle"
        self.response_callback = None

    @Slot(str, bool)
    def sendConfirmationResponse(self, intent_id: str, approved: bool):
        if self.response_callback:
            self.response_callback(intent_id, approved)

    @Slot(str)
    def sendTextMessage(self, text: str):
        self.textMessageReceived.emit(text)

    onboardingCompleted = Signal(str, str)
    @Slot(str, str)
    def completeOnboarding(self, name: str, purpose: str):
        self.onboardingCompleted.emit(name, purpose)

    needsSetupChanged = Signal()
    @Property(bool, notify=needsSetupChanged)
    def needsSetup(self):
        return getattr(self, '_needs_setup', False)

    @needsSetup.setter
    def needsSetup(self, val):
        self._needs_setup = val
        self.needsSetupChanged.emit()

    @Property(str, notify=statusChanged)
    def status(self):
        return self._status

    @status.setter
    def status(self, val):
        if self._status != val:
            self._status = val
            self.statusChanged.emit()

    @Property(float, notify=volumeChanged)
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, val):
        if self._volume != val:
            self._volume = val
            self.volumeChanged.emit()

    @Property(str, notify=stateChanged)
    def state(self):
        return self._state

    @state.setter
    def state(self, val):
        if self._state != val:
            self._state = val
            self.stateChanged.emit()

    privacyModeChanged = Signal()
    privacyModeToggled = Signal()

    @Slot()
    def togglePrivacyMode(self):
        self.privacyModeToggled.emit()

    @Property(str, notify=privacyModeChanged)
    def privacyModeText(self):
        return getattr(self, '_privacy_mode', "Local Only")

    @privacyModeText.setter
    def privacyModeText(self, val):
        self._privacy_mode = val
        self.privacyModeChanged.emit()


class ReiUI:
    """QML-based implementation of the UI Reference."""
    def __init__(self) -> None:
        self.backend = ReiBackend()
        self.engine = QQmlApplicationEngine()
        
        # Expose backend to QML
        self.engine.rootContext().setContextProperty("backend", self.backend)
        
        qml_file = Path(__file__).parent / "qml" / "Main.qml"
        self.engine.load(str(qml_file))
        
        if not self.engine.rootObjects():
            print("CRITICAL: Failed to load QML UI.")
            sys.exit(-1)
            
        # Initial greeting
        self.backend.messageAdded.emit("Hello! I am Rei. I am running entirely locally on your hardware. How can I assist you today?", False)

    def set_context(self, store, registry, policy_config):
        from rei.ui.models import MemoryModel, CapabilityModel
        self.memory_model = MemoryModel(store)
        self.capability_model = CapabilityModel(registry)
        
        self.engine.rootContext().setContextProperty("memoryModel", self.memory_model)
        self.engine.rootContext().setContextProperty("capabilityModel", self.capability_model)
        
        # Determine privacy mode
        mode = policy_config.get("defaults", {}).get("privacy_mode", "local_only")
        self.backend.privacyModeText = "Cloud Assisted" if mode == "cloud_assisted" else "Local Only"

        # Check if onboarding is needed
        profile = store.read("user_profile")
        if not profile:
            self.backend.needsSetup = True

    def show(self) -> None:
        # QML Windows handle their own visibility (visible: true)
        pass

    def set_status(self, status: str) -> None:
        if "Heard: " in status:
            msg = status.replace("Heard: ", "")
            self.backend.messageAdded.emit(msg, True)
            self.backend.state = "processing"
            self.backend.status = "Thinking..."
        elif "Listening" in status:
            self.backend.state = "listening"
            self.backend.status = "Listening..."
        elif "Transcribing" in status or "Routing" in status:
            self.backend.state = "processing"
            self.backend.status = "Thinking..."
        elif "Speaking" in status:
            self.backend.state = "speaking"
            self.backend.status = "Speaking..."
            msg = status.replace("Speaking: ", "")
            self.backend.messageAdded.emit(msg, False)
        else:
            self.backend.state = "idle"
            self.backend.status = "How can I help you?"
            
    def update_volume(self, vol: float) -> None:
        self.backend.volume = min(1.0, vol * 5.0)

    def close(self):
        QApplication.quit()
