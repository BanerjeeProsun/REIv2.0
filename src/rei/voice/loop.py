import asyncio
import numpy as np
from typing import Callable

from rei.voice.capture import AudioCapture
from rei.voice.vad import VoiceActivityDetector
from rei.voice.stt import SpeechToText
from rei.voice.aec import EchoCanceller
from rei.core.cancellation import CancelToken


class VoiceLoop:
    """Manages the voice input pipeline (Capture -> VAD -> STT -> turn runner).

    Speech output is owned by the shared Speaker (rei.voice.speaker), which
    marks the same EchoCanceller for voice, typed and greeting replies.
    """

    def __init__(
        self,
        capture: AudioCapture,
        vad: VoiceActivityDetector,
        stt: SpeechToText,
        aec: EchoCanceller,
        on_utterance: Callable[[str], None],
        on_volume: Callable[[float], None] = lambda v: None,
        on_transcribing: Callable[[], None] = lambda: None,
        on_discard: Callable[[], None] = lambda: None,
    ) -> None:
        self.capture = capture
        self.vad = vad
        self.stt = stt
        self.aec = aec
        self.on_utterance = on_utterance
        self.on_volume = on_volume
        self.on_transcribing = on_transcribing
        self.on_discard = on_discard
        self._running = False
        self._speech_buffer: list[np.ndarray] = []
        self._silence_frames = 0
        
        # 300ms of silence at 16kHz with 480 chunk size is roughly 10 chunks
        self.silence_threshold_chunks = int(0.3 * capture.sample_rate / capture.chunk_size)

    async def start(self) -> None:
        self._running = True
        await self.capture.start()
        
        print("Voice loop started. Listening...")
        
        while self._running:
            try:
                # Get raw audio chunk from microphone
                chunk = await self.capture.get_chunk()
                
                vol = float(np.max(np.abs(chunk)))
                self.on_volume(vol)
                
                # Check AEC to avoid transcribing our own TTS
                if self.aec.should_suppress():
                    self._reset_vad()
                    continue

                # Run Voice Activity Detection
                is_speech = self.vad.process_chunk(chunk)
                
                if is_speech:
                    if len(self._speech_buffer) == 0:
                        print("Speech started...")
                    self._speech_buffer.append(chunk)
                    self._silence_frames = 0
                elif len(self._speech_buffer) > 0:
                    self._silence_frames += 1
                    self._speech_buffer.append(chunk) # Include trailing silence
                    
                    if self._silence_frames >= self.silence_threshold_chunks:
                        print("Speech ended, processing...")
                        # We have reached the end of an utterance
                        await self._handle_utterance()
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Voice loop error: {e}")
                
        await self.capture.stop()

    def stop(self) -> None:
        self._running = False

    def _reset_vad(self) -> None:
        self._speech_buffer.clear()
        self._silence_frames = 0
        self.vad.reset()

    async def _handle_utterance(self) -> None:
        if not self._speech_buffer:
            return
            
        # Concatenate buffered chunks into a single 1D array
        full_audio = np.concatenate(self._speech_buffer).flatten()
        self._reset_vad()
        
        # STT
        cancel_token = CancelToken()
        try:
            print("Transcribing...")
            self.on_transcribing()
            text = await self.stt.transcribe(full_audio, cancel_token)
            if not text.strip():
                # Nothing usable was heard: return the UI to its rest state
                self.on_discard()
                return
                
            print(f"Heard: {text}")
            
            # Hand off without waiting: the turn runs in the background and the
            # mic goes straight back to listening (e.g. for a spoken "yes").
            # Rei's own speech is still ignored via the shared AEC.
            self.on_utterance(text)

        except asyncio.CancelledError:
            print("Voice turn cancelled.")
        except Exception as e:
            print(f"Failed to process utterance: {e}")
            self.on_discard()
        finally:
            self.capture.clear()
