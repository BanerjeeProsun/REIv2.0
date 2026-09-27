# Rei v2.0

Rei v2.0 is a local-first, privacy-obsessed AI operating layer for Windows. It acts as a hyper-fast intelligent bridge between your voice and your operating system. Built completely from scratch with a strict security architecture, Rei guarantees that model output is an intent, never an execution. 

Rei processes audio natively, thinks using a quantized local model, and executes typed capabilities securely, all without requiring an active internet connection or relying on a fragile cloud infrastructure.

## Deep Architectural Overview

The architecture of Rei v2.0 is designed around strict trust boundaries and explicit control flow. It ensures that arbitrary AI hallucinations cannot compromise the operating system.

### 1. The 8-Stage Execution Pipeline
Every user request or worker trigger goes through a deterministic, side-effect-free pipeline.
* Capture: Voice input is transcribed via local STT to a UserUtterance.
* Propose: The LLM processes the prompt and outputs a JSON intent proposal.
* Parse: The raw JSON is validated against strict Pydantic schemas. Invalid output halts the process.
* Decide: The Policy Engine evaluates the intent against security rules and issues a PolicyDecision (ALLOW, CONFIRM, DENY).
* Confirm: If required by policy, a UI dialog halts execution until the user manually approves the action.
* Grant: The Policy Engine mints a cryptographically bound, single-use GrantToken.
* Execute: The Capability Host validates the GrantToken and executes the typed python function.
* Report: The result is audited and spoken back to the user via TTS.

### 2. Hybrid Intelligence Routing
Rei utilizes a ModelRouter to ensure maximum resilience and speed.
* Cloud-Assisted Mode: Rei first attempts to route complex queries to a cloud NIM model (e.g., Llama 3.2 11B). A strict 5-second deadline is enforced.
* Seamless Local Fallback: If the cloud API fails, times out, or loses network connection, the ModelRouter instantly intercepts the error and routes the prompt to a local Llama 3.2 1B Instruct GGUF model. This guarantees that Rei never goes completely offline.

### 3. Hardware-Accelerated Voice Engine
The voice pipeline is fully local and runs concurrently to maintain low latency.
* Speech-to-Text: Powered by faster-whisper on the GPU. The engine uses a dynamic CUDA injector that automatically discovers NVIDIA cuBLAS libraries in the Python environment, preventing system PATH pollution. Strict hallucination filtering removes ghost transcriptions caused by static.
* Voice Activity Detection: WebRTC VAD is deployed with maximum aggressiveness (level 3) to prevent background noise from triggering continuous transcription loops.
* Text-to-Speech: Uses kokoro-onnx for ultra-low latency, highly natural speech synthesis.

### 4. Zero-Password Secure Memory
Rei possesses long-term memory via a persistent SQLite database. To ensure total privacy, the database is encrypted at rest using the Windows Data Protection API (DPAPI).
* The encryption key is cryptographically bound to the user's active Windows logon session.
* External processes or unauthorized users cannot decrypt the memory store, even if they steal the physical database file.
* This allows Rei to safely store sensitive OAuth tokens and personal preferences without requiring a master password.

### 5. Hardware-Accelerated QML Frontend
The UI has been entirely decoupled from legacy QWidgets. It is built using PySide6 and QML (Qt Quick).
* Fluid Vector Rendering: The interface mathematically scales and animates at 60fps using the GPU, perfectly translating the minimalist vector aesthetics of modern design systems.
* Concurrent Windows: A large dark-mode control center manages capabilities and memory, while a floating, borderless Voice Orb pulses to audio waveforms on the desktop.

## Roadmap and Future Integrations

As the core architecture is now complete, development will focus on deep headless integrations.

### 1. Headless Background Integrations
Rei will interact with third-party cloud services headlessly, completely bypassing the web browser:
* Media Integrations: Implementing ytmusicapi (YouTube Music) and spotipy (Spotify) to allow Rei to securely authenticate and stream music directly through the OS audio mixer.
* Communication: Utilizing the google-api-python-client with OAuth2 tokens (safely stored in the DPAPI vault) to read, summarize, and draft Gmail messages silently.

### 2. Deep OS Integration and UX
* System Tray and Global Hotkeys: Moving the UI to a lightweight background process. The floating Orb will trigger instantly over any active application via a global hook.
* Vector Iconography: Integrating a full SVG library (such as Lucide or Phosphor) into the QML interface to replace placeholder typography.

### 3. Advanced Hardening
* Sandboxed Capability Host: Segregating the executor logic into a dedicated, low-privilege subprocess to guarantee that rogue capabilities cannot compromise the core orchestrator pipeline.
* Egress Broker Firewall: Enforcing stringent network rules so that only designated, sanitized HTTP clients can connect to the internet, strictly prohibiting unauthorized model callbacks.

## Getting Started

Note: Development requires Windows 11, the uv package manager, and an NVIDIA GPU.

```bash
# Clone the repository
git clone https://github.com/BanerjeeProsun/REIv2.0.git

# Run Rei
uv run python -m rei.main
```
