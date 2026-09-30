import sys
from pathlib import Path
from PySide6.QtCore import QObject, Signal, Property, Slot
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

class ReiBackend(QObject):
    statusChanged = Signal()
    volumeChanged = Signal()
    outputLevelChanged = Signal()
    stateChanged = Signal()
    messageAdded = Signal(str, bool)
    confirmationRequested = Signal(str, str, str) # title, message, intent_id
    confirmationHint = Signal(str, int, bool)     # spoken-answer hint, seconds to answer, strict
    confirmationClosed = Signal(str)              # intent_id answered/expired (close the popup)
    textMessageReceived = Signal(str)

    def __init__(self):
        super().__init__()
        self._status = "How can I help you?"
        self._volume = 0.0
        self._output_level = 0.0
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
        self.userName = name
        self.onboardingCompleted.emit(name, purpose)

    userNameChanged = Signal()
    @Property(str, notify=userNameChanged)
    def userName(self):
        """First name for the home greeting ("Good evening, Ada.")."""
        return getattr(self, '_user_name', "")

    @userName.setter
    def userName(self, val):
        first = (val or "").strip().split(" ")[0]
        if getattr(self, '_user_name', "") != first:
            self._user_name = first
            self.userNameChanged.emit()

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

    @Property(float, notify=outputLevelChanged)
    def outputLevel(self):
        """Amplitude (0..1) of Rei's own speech, for the orb animation."""
        return self._output_level

    @outputLevel.setter
    def outputLevel(self, val):
        if self._output_level != val:
            self._output_level = val
            self.outputLevelChanged.emit()

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
    privacyModeSelected = Signal(str)

    @Slot()
    def togglePrivacyMode(self):
        self.privacyModeToggled.emit()

    @Slot(str)
    def setPrivacyMode(self, mode: str):
        """mode: "Local Only", "Local + Connectors" or "Cloud Assisted"."""
        self.privacyModeSelected.emit(mode)

    # Connectors (Email, YouTube, Spotify...)
    connectRequested = Signal(str, str)      # connector id, JSON params
    disconnectRequested = Signal(str)        # connector id
    connectorResult = Signal(str, bool, str) # connector id, ok, message

    @Slot(str, str)
    def connectConnector(self, cid: str, params_json: str):
        self.connectRequested.emit(cid, params_json)

    @Slot(str)
    def disconnectConnector(self, cid: str):
        self.disconnectRequested.emit(cid)

    # Music now playing (sidebar mini player)
    nowPlayingChanged = Signal()
    playerCommand = Signal(str)  # "toggle" | "stop" | "next"

    @Property(str, notify=nowPlayingChanged)
    def nowPlaying(self):
        return getattr(self, "_now_playing", "")

    @Property(bool, notify=nowPlayingChanged)
    def nowPlayingPaused(self):
        return getattr(self, "_now_paused", False)

    @Property(str, notify=nowPlayingChanged)
    def nowPlayingSource(self):
        return getattr(self, "_now_source", "")

    def set_now_playing(self, title: str, paused: bool, source: str) -> None:
        self._now_playing, self._now_paused, self._now_source = title, paused, source
        self.nowPlayingChanged.emit()

    @Slot(str)
    def sendPlayerCommand(self, command: str):
        self.playerCommand.emit(command)

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
        self.mic_active = False
        # The native Windows style can't be themed (e.g. scrollbars); Basic can,
        # and every control is restyled by our own components anyway.
        from PySide6.QtQuickControls2 import QQuickStyle
        QQuickStyle.setStyle("Basic")
        self.engine = QQmlApplicationEngine()
        
        # Expose backend to QML
        self.engine.rootContext().setContextProperty("backend", self.backend)
        self._loaded = False

    def _load(self) -> None:
        """Load the QML once, after the data models are exposed, so pages never
        start with undefined memoryModel/capabilityModel references."""
        if self._loaded:
            return
        self._loaded = True
        qml_file = Path(__file__).parent / "qml" / "Main.qml"
        self.engine.load(str(qml_file))
        if not self.engine.rootObjects():
            print("CRITICAL: Failed to load QML UI.")
            sys.exit(-1)

    PRIVACY_MODES = {"local_only": "Local Only", "local_plus_web": "Local + Connectors",
                     "cloud_assisted": "Cloud Assisted"}

    def set_context(self, store, registry, policy_config, connectors=None):
        from rei.ui.models import MemoryModel, CapabilityModel, ConnectorModel
        self.memory_model = MemoryModel(store)
        self.capability_model = CapabilityModel(registry)
        self.connector_model = ConnectorModel(connectors)
        
        self.engine.rootContext().setContextProperty("memoryModel", self.memory_model)
        self.engine.rootContext().setContextProperty("capabilityModel", self.capability_model)
        self.engine.rootContext().setContextProperty("connectorModel", self.connector_model)
        
        # Determine privacy mode
        mode = str(policy_config.get("defaults", {}).get("privacy_mode", "local_only")).lower()
        self.backend.privacyModeText = self.PRIVACY_MODES.get(mode, "Local Only")

        # Check if onboarding is needed
        profile = store.read("user_profile")
        if not profile:
            self.backend.needsSetup = True
        elif isinstance(profile, dict):
            self.backend.userName = str(profile.get("name", ""))

        self._load()

    def show(self) -> None:
        # QML Windows handle their own visibility (visible: true); make sure the
        # QML is loaded even if set_context() was never called.
        self._load()

    STATE_TEXT = {
        "idle": "How can I help you?",
        "listening": "Listening...",
        "processing": "Thinking...",
        "speaking": "Speaking...",
    }

    def set_state(self, state: str, status: str | None = None) -> None:
        """Explicit UI state. Never inferred from message text."""
        if state not in self.STATE_TEXT:
            raise ValueError(f"Unknown UI state: {state}")
        # Status first, so bindings on stateChanged already see matching text
        self.backend.status = status or self.STATE_TEXT[state]
        self.backend.state = state

    def set_rest_state(self) -> None:
        """Where the UI settles between turns: listening if the mic is live."""
        self.set_state("listening" if self.mic_active else "idle")

    def add_message(self, text: str, is_user: bool) -> None:
        if text.strip():
            self.backend.messageAdded.emit(text, is_user)

    def set_status(self, status: str) -> None:
        """Free-form status line (e.g. errors) without changing the state."""
        self.backend.status = status

    def update_volume(self, vol: float) -> None:
        # Fast attack, slow decay so the listening glow doesn't flicker
        self.backend.volume = min(1.0, max(vol * 5.0, self.backend.volume * 0.85))

    def update_output_level(self, level: float) -> None:
        self.backend.outputLevel = max(0.0, min(1.0, level))

    def close(self):
        QApplication.quit()
