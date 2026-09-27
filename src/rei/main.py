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
from rei.models.nim_planner import CloudAssistedPlanner
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
from rei.models.adapter import ModelAdapter

load_dotenv()

def create_orchestrator() -> Orchestrator:
    grant_key = secrets.token_bytes(32)
    registry = CapabilityRegistry()
    register_builtin(registry)

    from rei.memory.db import MemoryStore
    from rei.capabilities.builtin.memory import set_memory_store
    
    app_data = Path(os.getenv("APPDATA", ".")) / "Rei"
    store = MemoryStore(app_data / "rei.db")
    set_memory_store(store)
    
    policy_config = {
        "version": "2026.09.1",
        "defaults": {"safe_mode": False},
        "disabled": {"capabilities": []},
        "preauthorise": {"allowed": ["apps.open", "media.set_volume", "web.open_url", "memory.remember", "system.type_text"]},
    }

    policy_engine = PolicyEngine(registry, policy_config, grant_key)
    
    # Phase P4: Multi-Model Intelligence with Fallback
    from rei.models.nim_planner import CloudAssistedPlanner
    from rei.models.local_planner import LocalPlanner
    from rei.models.router import ModelRouter
    
    try:
        cloud_model = CloudAssistedPlanner("meta/llama-3.2-11b-vision-instruct")
    except Exception as e:
        print(f"Failed to load NIM Planner: {e}")
        cloud_model = None

    model_path = Path("models/Llama-3.2-1B-Instruct-Q4_K_M.gguf")
    try:
        local_model = LocalPlanner(model_path, n_ctx=4096)
    except Exception as e:
        print(f"Failed to load Local Planner: {e}")
        local_model = None

    active_model = ModelRouter(cloud_model=cloud_model, local_model=local_model)

    return Orchestrator(
        model=active_model,
        registry=registry,
        policy_engine=policy_engine,
        parser=IntentParser(),
        prompt_builder=PromptBuilder(store=store),
        confirmation_broker=ConfirmationBroker(UIClientMock()),
        executor=Executor(registry, GrantVerifier(registry, grant_key)),
    )


async def start_voice_loop(orchestrator: Orchestrator, ui: ReiUI) -> None:
    try:
        capture = AudioCapture()
        vad = VoiceActivityDetector(Path("models/silero_vad.onnx"), threshold=0.3)
        stt = SpeechToText()
        tts = TextToSpeech(Path("models/kokoro-v0_19.onnx"))
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
            privacy_mode=PrivacyMode.CLOUD_ASSISTED,
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

    loop = VoiceLoop(capture, vad, stt, tts, aec, handle_utterance, on_volume=handle_volume)
    await loop.start()


def main() -> None:
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    ui = ReiUI()
    ui.show()

    orchestrator = create_orchestrator()

    # Start voice loop in background
    voice_task = loop.create_task(start_voice_loop(orchestrator, ui))
    app.aboutToQuit.connect(voice_task.cancel)

    with loop:
        loop.run_forever()

if __name__ == "__main__":
    main()
