import asyncio
import sys
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

    policy_config = {
        "version": "2026.09.1",
        "defaults": {"safe_mode": False},
        "disabled": {"capabilities": []},
        "preauthorise": {"allowed": ["apps.open", "media.set_volume", "web.open_url"]},
    }

    policy_engine = PolicyEngine(registry, policy_config, grant_key)
    
    # Phase P3: Use CloudAssistedPlanner
    model: ModelAdapter
    try:
        model = CloudAssistedPlanner("meta/llama-3.1-70b-instruct")
    except Exception as e:
        print(f"Failed to load NIM Planner: {e}. Falling back to FakeModel.")
        from rei.models.fake import FakeModel
        model = FakeModel()

    return Orchestrator(
        model=model,
        registry=registry,
        policy_engine=policy_engine,
        parser=IntentParser(),
        prompt_builder=PromptBuilder(),
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

    loop = VoiceLoop(capture, vad, stt, tts, aec, handle_utterance)
    await loop.start()


def main() -> None:
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    ui = ReiUI()
    ui.show()

    orchestrator = create_orchestrator()

    # Start voice loop in background
    loop.create_task(start_voice_loop(orchestrator, ui))

    with loop:
        loop.run_forever()

if __name__ == "__main__":
    main()
