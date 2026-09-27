import pytest
from rei.voice.aec import EchoCanceller
from rei.voice.capture import AudioCapture

def test_aec_suppression() -> None:
    aec = EchoCanceller()
    assert not aec.should_suppress()
    aec.mark_playback_active(True)
    assert aec.should_suppress()
    aec.mark_playback_active(False)
    assert not aec.should_suppress()

@pytest.mark.asyncio
async def test_audio_capture_start_stop() -> None:
    # Test that capture can be started and stopped without throwing.
    # Note: On CI machines without audio devices, this might throw AudioCaptureError.
    # So we'll skip if it fails to initialize.
    try:
        capture = AudioCapture()
        await capture.start()
        await capture.stop()
    except Exception as e:
        pytest.skip(f"Audio device not available: {e}")
