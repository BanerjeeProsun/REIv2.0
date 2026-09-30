import asyncio
import sys
import os
import secrets
import time
from pathlib import Path
from typing import Any, Awaitable

from PySide6.QtWidgets import QApplication
from qasync import QEventLoop # type: ignore
from dotenv import load_dotenv

from rei.ui.app import ReiUI
from rei.core.orchestrator import Orchestrator
from rei.intents.parser import IntentParser
from rei.core.prompt_builder import PromptBuilder
from rei.policy.engine import PolicyEngine
from rei.policy.context import PolicyContext
from rei.policy.schemas import Origin, PrivacyMode
from rei.capabilities.registry import CapabilityRegistry
from rei.capabilities.builtin import register_builtin
from rei.core.executor import Executor
from rei.host.verify import GrantVerifier

from rei.voice.capture import AudioCapture
from rei.voice.vad import VoiceActivityDetector
from rei.voice.stt import SpeechToText
from rei.voice.tts import TextToSpeech
from rei.voice.aec import EchoCanceller
from rei.voice.loop import VoiceLoop
from rei.voice.speaker import Speaker
from rei.core.cancellation import CancelToken

load_dotenv()

# The Windows console defaults to a legacy code page; printing a transcript or
# reply with characters outside it raised UnicodeEncodeError and silently
# discarded the whole voice turn. Never let logging break the pipeline.
for _stream in (sys.stdout, sys.stderr):
    if _stream is not None and hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

def create_orchestrator(ui: 'ReiUI', registry: Any, store: Any, policy_config_model: Any, grant_key: bytes,
                        ui_client: Any, egress_gate: Any) -> Orchestrator:
    policy_config = policy_config_model.model_dump()
    policy_engine = PolicyEngine(registry, policy_config, grant_key)

    # Phase P4: Local Formatter -> Cloud Planner, with local fallback
    from rei.models.nim_planner import CloudAssistedPlanner
    from rei.models.local_planner import LocalPlanner
    from rei.models.router import ModelRouter

    try:
        cloud_model = CloudAssistedPlanner(egress_gate, "meta/llama-3.2-11b-vision-instruct")
    except Exception as e:
        print(f"Failed to load NIM Planner: {e}")
        cloud_model = None

    from rei.models.loader import ModelLoader
    model_loader = ModelLoader("models.lock")

    try:
        model_path = model_loader.verify_and_get_path(Path("models"), "Llama-3.2-1B-Instruct-Q4_K_M.gguf")
        local_model = LocalPlanner(model_path, n_ctx=4096)
    except Exception as e:
        print(f"Failed to load Local Planner: {e}")
        local_model = None

    active_model = ModelRouter(cloud_model=cloud_model, local_model=local_model)

    from rei.confirm.broker import ConfirmationBroker
    orchestrator = Orchestrator(
        model=active_model,
        registry=registry,
        policy_engine=policy_engine,
        parser=IntentParser(),
        prompt_builder=PromptBuilder(store=store),
        confirmation_broker=ConfirmationBroker(ui_client),
        executor=Executor(registry, GrantVerifier(registry, grant_key)),
    )
    orchestrator.egress_gate = egress_gate  # type: ignore[attr-defined]
    return orchestrator


async def start_voice_loop(ui: 'ReiUI', aec: EchoCanceller, route_input: Any, busy: Any) -> None:
    try:
        capture = AudioCapture()
        vad = VoiceActivityDetector(threshold=3)
        # Whisper takes seconds to load; do it off the UI thread so the window
        # stays responsive (typing works) while voice is still starting up.
        ui.set_status("Loading voice...")
        stt = await asyncio.get_running_loop().run_in_executor(None, SpeechToText)
    except Exception as e:
        ui.set_status(f"Voice Error: {e}")
        return

    def on_utterance(text: str) -> None:
        # Non-blocking: the mic keeps listening while the turn runs, so a
        # spoken "yes" can answer a confirmation mid-turn
        route_input(text, Origin.USER_VOICE)

    # Only touch the UI state when no turn owns it (a turn may be speaking/listening)
    loop = VoiceLoop(
        capture, vad, stt, aec,
        on_utterance=on_utterance,
        on_volume=ui.update_volume,
        on_transcribing=lambda: None if busy() else ui.set_state("processing"),
        on_discard=lambda: None if busy() else ui.set_rest_state(),
    )
    ui.mic_active = True
    if not busy():  # a turn (e.g. the greeting) may already own the UI state
        ui.set_rest_state()
    try:
        await loop.start()
    except asyncio.CancelledError:
        raise
    except Exception as e:
        print(f"Voice loop stopped: {e}")
        ui.mic_active = False
        ui.set_rest_state()
        ui.set_status(f"Voice Error: {e}")


def main() -> None:
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    grant_key = secrets.token_bytes(32)
    registry = CapabilityRegistry()
    register_builtin(registry)

    from rei.memory.store import MemoryStore
    from rei.capabilities.builtin.memory import set_memory_store
    app_data = Path(os.getenv("APPDATA", ".")) / "Rei"
    # First run on a fresh machine: sqlite cannot create the folder itself
    app_data.mkdir(parents=True, exist_ok=True)
    store = MemoryStore(str(app_data / "rei.db"))
    set_memory_store(store)

    from rei.policy.config import load_policy_config
    from rei.egress.socket_guard import install_socket_guard
    install_socket_guard()

    policy_config_model = load_policy_config("src/rei/policy/policy.toml")

    # One egress gate for everything that talks to the network. Connectors add
    # only the hosts of services the user has connected.
    from rei.egress.gate import EgressGate
    from rei.connectors import ConnectorManager
    from rei.connectors.email import EmailConnector
    from rei.config.secrets import SecretManager
    egress_gate = EgressGate(policy_config_model, PrivacyMode.LOCAL_ONLY)

    # Music: an in-app player (YouTube via yt-dlp) and Spotify, behind one "music.play"
    from rei.connectors.music import MusicHub
    from rei.connectors.youtube import YouTubeConnector
    from rei.connectors.spotify import SpotifyConnector
    from rei.egress.stream import open_audio
    from rei.voice.player import MusicPlayer
    from rei.capabilities.builtin.media import set_media_controller
    now_playing_listeners: list[Any] = []

    def on_player_change() -> None:
        # The player reports from audio/decoder threads; hop to the UI thread
        for fn in now_playing_listeners:
            loop.call_soon_threadsafe(fn)

    player = MusicPlayer(
        opener=lambda url, headers: open_audio(egress_gate, url, headers),
        on_change=on_player_change,
    )
    music = MusicHub()
    connectors = ConnectorManager(registry, app_data / "connectors.json", [
        EmailConnector(egress_gate, SecretManager()),
        YouTubeConnector(egress_gate, music, player),
        SpotifyConnector(egress_gate, SecretManager(), music),
    ])
    set_media_controller(music.control)
    egress_gate.connector_hosts = connectors.hosts
    connectors.load()

    ui = ReiUI()
    ui.set_context(store, registry, policy_config_model.model_dump(), connectors=connectors)
    ui.show()

    # Initialize TTS
    try:
        from rei.models.loader import ModelLoader
        loader = ModelLoader("models.lock")
        tts_model = loader.verify_and_get_path(Path("models"), "kokoro-v0_19.onnx")
        # Ensure voices.bin is handled internally by TTS class
        tts = TextToSpeech(tts_model)
    except Exception as e:
        print(f"Failed to load global TTS: {e}")
        tts = TextToSpeech(None) # Fallback to pyttsx3

    # One echo canceller and one speaker shared by every path, so the mic
    # ignores Rei's voice no matter what triggered the reply.
    aec = EchoCanceller()
    speaker = Speaker(tts, aec, on_level=ui.update_output_level)

    # Voice (or click) confirmation: Rei reads the action back and listens
    from rei.confirm.broker import UIClientWired
    from rei.confirm.voice import VoiceConfirmer
    confirmer = VoiceConfirmer()

    def describe(intent: Any) -> str:
        try:
            phrase = registry.get_spec(intent.capability).confirm_template.format(**intent.args)
        except Exception:
            phrase = intent.capability
        return phrase if len(phrase) <= 140 else phrase[:137] + "..."

    def on_listen(listening: bool) -> None:
        if listening:
            ui.set_state("listening", 'Say "confirm" or "no"...' if confirmer.strict else 'Say "yes" or "no"...')
        else:
            ui.set_state("processing")

    defaults = policy_config_model.defaults
    ui_client = UIClientWired(
        ui.backend,
        confirmer=confirmer,
        say=lambda text: speaker.say(text, on_start=lambda: ui.set_state("speaking")),
        describe=describe,
        mic_active=lambda: ui.mic_active,
        on_listen=on_listen,
        voice_window_s=float(defaults.voice_confirm_window_s),
        click_window_s=float(defaults.confirm_timeout_s),
    )
    orchestrator = create_orchestrator(ui, registry, store, policy_config_model, grant_key, ui_client, egress_gate)

    MODES = {
        "Local Only": PrivacyMode.LOCAL_ONLY,
        "Local + Connectors": PrivacyMode.LOCAL_PLUS_WEB,
        "Cloud Assisted": PrivacyMode.CLOUD_ASSISTED,
    }

    def get_current_privacy_mode() -> PrivacyMode:
        return MODES.get(ui.backend.privacyModeText, PrivacyMode.LOCAL_ONLY)

    turn_lock = asyncio.Lock()
    background_tasks: set[asyncio.Task[None]] = set()

    def spawn(coro: Any) -> None:
        task = asyncio.ensure_future(coro)
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)

    active_turns = {"n": 0}

    def busy() -> bool:
        return active_turns["n"] > 0 or confirmer.pending

    from rei.voice.wake import strip_wake_word

    def route_input(text: str, origin: Origin) -> None:
        """Every utterance or typed message enters here. While Rei is waiting
        for a confirmation, the input answers it instead of starting a turn."""
        text = text.strip()
        if not text:
            return
        if origin == Origin.USER_VOICE and player.active and not player.paused and not confirmer.pending:
            command = strip_wake_word(text)
            if command is None:
                return  # probably the song, not the user
            text = command
        if confirmer.pending:
            if confirmer.offer(text):
                ui.add_message(text, True)
            # Anything else is ignored until the question is answered or expires
            return
        spawn(run_turn(text, origin))

    async def run_turn(text: str, origin: Origin, *, show_user: bool = True, allow_actions: bool = True) -> None:
        """The single path for voice, typed and greeting turns:
        processing -> reply in chat -> speaking -> rest state, always."""
        text = text.strip()
        if not text:
            return
        # Barge-in: a new request interrupts whatever Rei is saying
        speaker.stop()
        if show_user:
            ui.add_message(text, True)
        active_turns["n"] += 1
        player.duck(True)  # music goes quiet while Rei listens/thinks/speaks
        async with turn_lock:
            ui.set_state("processing")
            try:
                ctx = PolicyContext(
                    session_id="voice-session" if origin == Origin.USER_VOICE else "ui-session",
                    turn_id=f"turn-{secrets.token_hex(4)}",
                    origin=origin,
                    privacy_mode=get_current_privacy_mode(),
                    taint=frozenset(),
                    settings={},
                    recent=None,
                )
                result = await orchestrator.process_turn(text, ctx, CancelToken(), allow_actions=allow_actions)
                update_now_playing()  # e.g. Spotify started playing on another device
                ui.add_message(result.reply, False)
                await speaker.say(result.reply, on_start=lambda: ui.set_state("speaking"))
            except asyncio.CancelledError:
                raise
            except Exception as e:
                print(f"Turn failed: {e}")
                ui.add_message("Sorry, something went wrong while handling that.", False)
            finally:
                active_turns["n"] -= 1
                if active_turns["n"] == 0:
                    player.duck(False)
                ui.set_rest_state()

    def on_setup(name: str, purpose: str) -> None:
        from rei.capabilities.spec import DataClass

        ctx = PolicyContext(
            session_id="setup",
            turn_id="setup-1",
            origin=Origin.SYSTEM,
            privacy_mode=PrivacyMode.LOCAL_ONLY,
            taint=frozenset(),
            settings={},
            recent=None
        )
        try:
            store.write(
                memory_id="user_profile",
                content={"name": name, "purpose": purpose},
                kind="UserProfile",
                data_class=DataClass.C0,
                created_at=int(time.time()),
                ctx=ctx
            )
        except Exception as e:
            print(f"Failed to save profile: {e}")
        ui.backend.needsSetup = False

        # Personalised greeting through the full pipeline. In Cloud Assisted
        # mode the name leaves the device only as [USER_NAME] and is restored
        # locally before it is shown and spoken. It is purely conversational:
        # no capabilities are offered, so it can never type or run anything.
        spawn(run_turn(
            f"Greet me warmly by name in one or two sentences. "
            f"My name is {name}; I mainly use you for {purpose}.",
            Origin.USER_TYPED,
            show_user=False,
            allow_actions=False,
        ))

    ui.backend.onboardingCompleted.connect(on_setup)

    def set_privacy_mode(name: str) -> None:
        if name not in MODES:
            return
        ui.backend.privacyModeText = name
        egress_gate.current_mode = MODES[name]

    def on_privacy_toggle() -> None:
        # Cycle Local Only -> Local + Connectors -> Cloud Assisted
        names = list(MODES)
        current = names.index(ui.backend.privacyModeText) if ui.backend.privacyModeText in names else 0
        set_privacy_mode(names[(current + 1) % len(names)])

    ui.backend.privacyModeToggled.connect(on_privacy_toggle)
    ui.backend.privacyModeSelected.connect(set_privacy_mode)

    def refresh_models() -> None:
        ui.connector_model.refresh()
        ui.capability_model.refresh()

    async def connect_connector(cid: str, params_json: str) -> None:
        import json
        from rei.connectors import ConnectorError
        try:
            params = json.loads(params_json) if params_json else {}
            await asyncio.to_thread(connectors.connect, cid, {k: str(v) for k, v in params.items()})
            ok, message = True, "Connected."
        except ConnectorError as e:
            ok, message = False, str(e)
        except Exception as e:
            ok, message = False, f"Couldn't connect: {e}"
        refresh_models()
        ui.backend.connectorResult.emit(cid, ok, message)

    async def disconnect_connector(cid: str) -> None:
        try:
            await asyncio.to_thread(connectors.disconnect, cid)
        except Exception as e:
            print(f"[Connectors] disconnect failed: {e}")
        refresh_models()
        ui.backend.connectorResult.emit(cid, True, "Disconnected.")

    def update_now_playing() -> None:
        if player.active:
            ui.backend.set_now_playing(player.title, player.paused, "youtube")
        elif music.current == "spotify" and music.now_playing:
            ui.backend.set_now_playing(music.now_playing, False, "spotify")
        else:
            ui.backend.set_now_playing("", False, "")

    now_playing_listeners.append(update_now_playing)

    async def player_command(command: str) -> None:
        action = {"toggle": "pause" if not player.paused else "play", "stop": "stop", "next": "next"}.get(command)
        if music.current == "spotify" and command == "toggle":
            action = "pause"
        if action:
            try:
                await asyncio.to_thread(music.control, action)
            except Exception as e:
                print(f"[music] {command} failed: {e}")
        update_now_playing()

    ui.backend.playerCommand.connect(lambda command: spawn(player_command(command)))
    ui.backend.connectRequested.connect(lambda cid, params: spawn(connect_connector(cid, params)))
    ui.backend.disconnectRequested.connect(lambda cid: spawn(disconnect_connector(cid)))

    # Set initial egress gate mode
    egress_gate.current_mode = get_current_privacy_mode()

    def on_text_message(text: str) -> None:
        # Typing "yes" also answers a pending confirmation
        route_input(text, Origin.USER_TYPED)

    ui.backend.textMessageReceived.connect(on_text_message)

    # Start voice loop in background
    voice_task = loop.create_task(start_voice_loop(ui, aec, route_input, busy))
    app.aboutToQuit.connect(voice_task.cancel)

    with loop:
        loop.run_forever()

if __name__ == "__main__":
    main()
