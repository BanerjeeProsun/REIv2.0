import asyncio
import sys
import os
import secrets
from pathlib import Path

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
from rei.confirm.broker import ConfirmationBroker, UIClientMock
from rei.core.executor import Executor
from rei.host.verify import GrantVerifier

from rei.voice.capture import AudioCapture
from rei.voice.vad import VoiceActivityDetector
from rei.voice.stt import SpeechToText
from rei.voice.tts import TextToSpeech
from rei.voice.aec import EchoCanceller
from rei.voice.loop import VoiceLoop
from rei.core.cancellation import CancelToken

load_dotenv()

def create_orchestrator(ui: 'ReiUI', registry, store, policy_config_model, grant_key: bytes) -> Orchestrator:
    policy_config = policy_config_model.model_dump()
    policy_engine = PolicyEngine(registry, policy_config, grant_key)
    
    # Phase P4: Multi-Model Intelligence with Fallback
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
    orchestrator.egress_gate = egress_gate
    return orchestrator


async def start_voice_loop(orchestrator: Orchestrator, ui: 'ReiUI', tts) -> None:
    try:
        capture = AudioCapture()
        vad = VoiceActivityDetector(threshold=3)
        stt = SpeechToText()
        aec = EchoCanceller()
    except Exception as e:
        ui.set_status(f"Voice Error: {e}")
        return

    async def handle_utterance(text: str) -> str:
        ui.set_status("Rei: Thinking...")
        ctx = PolicyContext(
            session_id="voice-session",
            turn_id=f"turn-{secrets.token_hex(4)}",
            origin=Origin.USER_VOICE,
            privacy_mode=PrivacyMode.CLOUD_ASSISTED if ui.backend.privacyModeText == "Cloud Assisted" else PrivacyMode.LOCAL_ONLY,
            taint=frozenset(),
            settings={},
            recent=None,
        )
        token = CancelToken()
        result = await orchestrator.process_turn(text, ctx, token)
        ui.set_status("Rei: Listening...")
        return result.reply

    def handle_volume(vol: float) -> None:
        ui.update_volume(vol)

    loop = VoiceLoop(capture, vad, stt, tts, aec, handle_utterance, on_volume=handle_volume, on_status=ui.set_status)
    await loop.start()


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
    store = MemoryStore(app_data / "rei.db")
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
        from rei.voice.tts import TextToSpeech
        loader = ModelLoader("models.lock")
        tts_model = loader.verify_and_get_path(Path("models"), "kokoro-v0_19.onnx")
        # Ensure voices.bin is handled internally by TTS class
        tts = TextToSpeech(tts_model)
    except Exception as e:
        print(f"Failed to load global TTS: {e}")
        tts = TextToSpeech(None) # Fallback to pyttsx3

    async def speak_text(text: str):
        from rei.core.cancellation import CancelToken
        ui.set_status(f"Speaking: {text}")
        try:
            await tts.speak(text, CancelToken())
        except Exception as e:
            print(f"TTS output failed: {e}")
        finally:
            ui.set_status("How can I help you?")
            ui.backend.state = "idle"

    def on_setup(name: str, purpose: str):
        from rei.policy.context import PolicyContext
        from rei.policy.schemas import Origin, PrivacyMode
        from rei.capabilities.spec import DataClass
        import time

        ctx = PolicyContext(
            session_id="setup",
            turn_id="setup-1",
            origin=Origin.SYSTEM,
            privacy_mode=PrivacyMode.LOCAL_ONLY,
            taint=frozenset(),
            settings={},
            recent=None
        )
        
        store.write(
            memory_id="user_profile",
            content={"name": name, "purpose": purpose},
            kind="UserProfile",
            data_class=DataClass.C0,
            created_at=int(time.time()),
            ctx=ctx
        )
        ui.backend.needsSetup = False
        
        # Trigger greeting
        ui.backend.messageAdded.emit(f"Setup complete. Generating greeting...", False)
        async def generate_greeting():
            ui.set_status("Rei: Thinking...")
            from rei.core.cancellation import CancelToken
            import secrets
            ctx_greet = PolicyContext(
                session_id="ui-session",
                turn_id=f"turn-{secrets.token_hex(4)}",
                origin=Origin.USER_TYPED,
                privacy_mode=PrivacyMode.CLOUD_ASSISTED,
                taint=frozenset(),
                settings={},
                recent=None,
            )
            result = await orchestrator.process_turn(f"Please greet me. My name is {name} and my purpose is {purpose}. Keep it brief and friendly.", ctx_greet, CancelToken())
            await speak_text(result.reply)
            
        asyncio.create_task(generate_greeting())

    ui.backend.onboardingCompleted.connect(on_setup)

    def on_privacy_toggle():
        if ui.backend.privacyModeText == "Cloud Assisted":
            ui.backend.privacyModeText = "Local Only"
        else:
            ui.backend.privacyModeText = "Cloud Assisted"
            
        orchestrator.egress_gate.current_mode = get_current_privacy_mode()

    ui.backend.privacyModeToggled.connect(on_privacy_toggle)

    def get_current_privacy_mode():
        from rei.policy.schemas import PrivacyMode
        return PrivacyMode.CLOUD_ASSISTED if ui.backend.privacyModeText == "Cloud Assisted" else PrivacyMode.LOCAL_ONLY

    # Set initial egress gate mode
    orchestrator.egress_gate.current_mode = get_current_privacy_mode()

    def on_text_message(text: str) -> None:
        ui.backend.messageAdded.emit(text, True)
        async def process_typed() -> None:
            ui.set_status("Rei: Thinking...")
            from rei.policy.context import PolicyContext
            from rei.policy.schemas import Origin
            from rei.core.cancellation import CancelToken
            import secrets
            ctx = PolicyContext(
                session_id="ui-session",
                turn_id=f"turn-{secrets.token_hex(4)}",
                origin=Origin.USER_TYPED,
                privacy_mode=get_current_privacy_mode(),
                taint=frozenset(),
                settings={},
                recent=None,
            )
            token = CancelToken()
            result = await orchestrator.process_turn(text, ctx, token)
            await speak_text(result.reply)
        asyncio.create_task(process_typed())
        
    ui.backend.textMessageReceived.connect(on_text_message)

    # Start voice loop in background
    voice_task = loop.create_task(start_voice_loop(orchestrator, ui, tts))
    app.aboutToQuit.connect(voice_task.cancel)

    with loop:
        loop.run_forever()

if __name__ == "__main__":
    main()
