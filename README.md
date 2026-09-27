# Rei v2.0

Rei v2.0 is a local-first, privacy-obsessed AI operating layer for Windows. It acts as a hyper-fast intelligent bridge between your voice and your operating system. Built completely from scratch with a strict security architecture, Rei guarantees that **model output is an intent, never an execution**. 

Rei processes audio natively, thinks using a quantized local model, and executes typed capabilities securely—all without requiring an active internet connection or relying on a fragile cloud infrastructure.

## 🚀 Current Features & Architecture

* **The Core Orchestrator (8-Stage Pipeline):** Every request passes through a strict, side-effect-free parsing pipeline. The LLM cannot execute code; it can only propose strongly-typed JSON intents that are verified against a capability registry and a deterministic Policy Engine.
* **Hybrid Intelligence (`ModelRouter`):** Features a seamless dynamic fallback router. Rei attempts to use a Cloud-assisted NIM model (Llama 3.2 11B) for complex logic, but if the API fails, times out, or loses internet connection, the thought is instantly routed to a lightweight `Llama 3.2 1B Instruct` GGUF model running entirely locally via `llama-cpp-python`.
* **Hardware-Accelerated Voice Engine:**
  * **STT:** `faster-whisper` running natively on the GPU. Includes dynamic CUDA injection (automatically discovers NVIDIA cuBLAS libraries in the python environment to avoid system PATH pollution) and rigorous hallucination filtering.
  * **TTS:** `kokoro-onnx` for lightning-fast, ultra-natural local speech synthesis.
  * **VAD:** `webrtcvad` configured for highly aggressive noise-gating to prevent continuous transcription loops from background static.
* **Figma-Perfect QML UI:** A world-class, hardware-accelerated frontend built with **PySide6 and QML (Qt Quick)**. It perfectly replicates the sleek, minimalist vector aesthetics of the original Figma reference, featuring a massive dark-mode control center and a floating, animated Voice Orb that pulses to audio waveforms.
* **Zero-Password Secure Memory:** A persistent SQLite `MemoryStore` for user preferences and context, cryptographically secured at rest using **Windows DPAPI**. The database is intrinsically locked to the user's OS login, rendering it unreadable to external threats without requiring a master password.
* **Core Capabilities:** Full OS-level integrations for locking the workstation, managing power states, directly injecting keystrokes into active windows (`system.type_text`), scaling global audio volume (`pycaw`), and downloading files.

## 🗺️ Roadmap & Future Plans

As we push towards the ultimate goal of a frictionless, invisible OS layer, the following milestones are planned:

### 1. Headless Background Integrations (Zero-Click Capabilities)
We will expand the Capability Registry to interact with third-party cloud services headlessly, bypassing the need for a web browser entirely:
* **YouTube Music & Spotify:** Integrations via `ytmusicapi` and `spotipy` to allow Rei to securely authenticate and stream music through the OS mixer in the background.
* **Gmail Integration:** Utilizing `google-api-python-client` with OAuth2 tokens (safely stored in the DPAPI memory vault) to read, summarize, and draft emails silently.

### 2. Deep OS Integration & UX
* **System Tray & Global Hotkeys:** Minimizing the UI to a lightweight system tray background process. The floating Orb will trigger instantly over any application via a global hook (e.g., `Ctrl + Space`).
* **Vector Iconography:** Dropping in a full SVG library (like Lucide or Phosphor) to complete the QML UI's transition to a pixel-perfect modern application.

### 3. Advanced Hardening (Phase P3)
* **Sandboxed Capability Host:** Segregating the Executor from the main Orchestrator into a dedicated, low-privilege subprocess to guarantee that rogue capabilities cannot compromise the core pipeline.
* **Egress Broker & Firewall:** Enforcing stringent firewall rules so that only designated, sanitized HTTP clients can connect to the internet, strictly prohibiting unauthorized model callbacks.

## 🛠️ Technology Stack

Rei is built on the absolute bleeding edge of local AI technologies:
* **Frontend:** PySide6, Qt Quick / QML
* **Backend:** Python 3.12 (uv package manager), asyncio, Pydantic
* **AI & Inference:** llama-cpp-python, faster-whisper, kokoro-onnx
* **Security:** Windows DPAPI, strict JSON schema validation, Typed Intents

## 📦 Getting Started

*(Development requires Windows 11, `uv`, and an NVIDIA GPU).*

```bash
# Clone the repository
git clone https://github.com/BanerjeeProsun/REIv2.0.git

# Run Rei (uv will automatically sync the virtual environment and lockfile)
uv run python -m rei.main
```
