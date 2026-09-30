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

def create_orchestrator(ui: 'ReiUI', registry: Any, store: Any, policy_config_model: Any, grant_key: bytes) -> Orchestrator:
    policy_config = policy_config_model.model_dump()
    policy_engine = PolicyEngine(registry, policy_config, grant_key)

    # Phase P4: Local Formatter -> Cloud Planner, with local fallback
    from rei.models.nim_planner import CloudAssistedPlanner
    from rei.models.local_planner import LocalPlanner
    from rei.models.router import ModelRouter
    from rei.egress.gate import EgressGate

    egress_gate = EgressGate(policy_config_model, PrivacyMode.CLOUD_ASSISTED)

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

    from rei.confirm.broker import ConfirmationBroker, UIClientWired
    orchestrator = Orchestrator(
        model=active_model,
        registry=registry,
        policy_engine=policy_engine,
        parser=IntentParser(),
        prompt_builder=PromptBuilder(store=store),
        confirmation_broker=ConfirmationBroker(UIClientWired(ui.backend)),
        executor=Executor(registry, GrantVerifier(registry, grant_key)),
    )
    orchestrator.egress_gate = egress_gate  # type: ignore[attr-defined]
    return orchestrator


async def start_voice_loop(ui: 'ReiUI', aec: EchoCanceller, run_turn: Any) -> None:
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

    def on_utterance(text: str) -> Awaitable[None]:
        return run_turn(text, Origin.USER_VOICE)  # type: ignore[no-any-return]

    loop = VoiceLoop(
        capture, vad, stt, aec,
        on_utterance=on_utterance,
        on_volume=ui.update_volume,
        on_transcribing=lambda: ui.set_state("processing"),
        on_discard=ui.set_rest_state,
    )
    ui.mic_active = True
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

    ui = ReiUI()
    ui.set_context(store, registry, policy_config_model.model_dump())
    ui.show()

    orchestrator = create_orchestrator(ui, registry, store, policy_config_model, grant_key)

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

    def get_current_privacy_mode() -> PrivacyMode:
        return PrivacyMode.CLOUD_ASSISTED if ui.backend.privacyModeText == "Cloud Assisted" else PrivacyMode.LOCAL_ONLY

    turn_lock = asyncio.Lock()
    background_tasks: set[asyncio.Task[None]] = set()

    def spawn(coro: Any) -> None:
        task = asyncio.ensure_future(coro)
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)

    async def run_turn(text: str, origin: Origin, *, show_user: bool = True) -> None:
        """The single path for voice, typed and greeting turns:
        processing -> reply in chat -> speaking -> rest state, always."""
        text = text.strip()
        if not text:
            return
        # Barge-in: a new request interrupts whatever Rei is saying
        speaker.stop()
        if show_user:
            ui.add_message(text, True)
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
                result = await orchestrator.process_turn(text, ctx, CancelToken())
                ui.add_message(result.reply, False)
                await speaker.say(result.reply, on_start=lambda: ui.set_state("speaking"))
            except asyncio.CancelledError:
                raise
            except Exception as e:
                print(f"Turn failed: {e}")
                ui.add_message("Sorry, something went wrong while handling that.", False)
            finally:
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
        # locally before it is shown and spoken.
        spawn(run_turn(
            f"Greet me warmly by name in one or two sentences. "
            f"My name is {name}; I mainly use you for {purpose}.",
            Origin.USER_TYPED,
            show_user=False,
        ))

    ui.backend.onboardingCompleted.connect(on_setup)

    def on_privacy_toggle() -> None:
        if ui.backend.privacyModeText == "Cloud Assisted":
            ui.backend.privacyModeText = "Local Only"
        else:
            ui.backend.privacyModeText = "Cloud Assisted"

        orchestrator.egress_gate.current_mode = get_current_privacy_mode()  # type: ignore[attr-defined]

    ui.backend.privacyModeToggled.connect(on_privacy_toggle)

    # Set initial egress gate mode
    orchestrator.egress_gate.current_mode = get_current_privacy_mode()  # type: ignore[attr-defined]

    def on_text_message(text: str) -> None:
        spawn(run_turn(text, Origin.USER_TYPED))

    ui.backend.textMessageReceived.connect(on_text_message)

    # Start voice loop in background
    voice_task = loop.create_task(start_voice_loop(ui, aec, run_turn))
    app.aboutToQuit.connect(voice_task.cancel)

    with loop:
        loop.run_forever()

if __name__ == "__main__":
    main()
