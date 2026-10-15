# A-Eye Track 3: Assistive Mobile Client (Flutter Android)

Track 3 is the user-facing assistive **Flutter mobile application (Android primary)** for visually impaired users. It continuously samples camera frames, communicates with the **Track 2 scene reasoning engine** via a dedicated Python bridge, and provides immediate **automatic speech** and **tactile haptic feedback**.

---

## 1. What Track 3 Does

- **Voice-First Navigation Aid**: Eliminates manual button taps, visual dashboards, and screen reliance. Once started, assistance runs autonomously in the background.
- **Continuous Frame Sampling**: Captures upright camera frames at a controlled, non-saturating interval (default 750 ms) without lagging the UI.
- **Zero-Pileup Scheduling**: Buffers the latest frame and drops stale frames while backend inference is in-flight, preventing queuing delays.
- **Autonomous Speech & Haptics**: Automatically announces potential hazards (`ALERT`), directional landmarks (`GUIDANCE`), and changes, accompanied by priority-based vibrations.
- **Anti-Spam & Deduplication**: Intelligently suppresses repetitive chatter (e.g. "chair, chair, chair") while allowing urgent high-priority alerts to interrupt lower-priority speech immediately.

---

## 2. System Architecture

```
┌────────────────────────┐
│  Android Phone Camera  │
└───────────┬────────────┘
            │  Live preview stream (hardware ISP)
            ▼
┌────────────────────────┐
│    FrameScheduler      │  Ticking at 500–1000 ms; drops stale frames when inferring
└───────────┬────────────┘
            │  Multipart JPEG POST /process-frames
            ▼
┌────────────────────────┐
│  Track 2 Python Bridge │  FastAPI HTTP service (track2_bridge/) on port 5000
└───────────┬────────────┘
            │  Direct Python imports (FrameBatch, Track2Pipeline)
            ▼
┌────────────────────────┐
│    Track 2 Pipeline    │  VLM (MockVLM or GeminiVLM) -> Spatial -> Context -> Decision
└───────────┬────────────┘
            │  Returns strongly typed Track2Result JSON
            ▼
┌────────────────────────┐
│ AssistanceOutputPolicy │  Deduplication, cooldowns, priority escalation, safety wording
└──────┬──────────┬──────┘
       │          │
       ▼          ▼
┌────────────┐ ┌─────────────┐
│  TTS Voice │ │   Haptics   │
│  (en-IN)   │ │ (Vibration) │
└────────────┘ └─────────────┘
```

---

## 3. Track 2 Integration Contract

Track 3 strictly honors Track 2 as the source of truth for all scene understanding and never reinterprets spatial reasoning:
- **`Track2Result`**: Received via HTTP JSON. Contains `frame_id`, `timestamp_ms`, `decision`, `perception`, `spatial`, `context`, and `summary`.
- **`decision.category`**:
  - `ALERT`: Potential obstacle or hazard requiring user awareness. Spoken automatically; triggers strong vibration.
  - `GUIDANCE`: Relevant directional landmark or corridor object. Spoken automatically; triggers medium vibration.
  - `INFO`: Background scene context. Spoken only when material changes occur.
  - `NONE`: Silent.
- **`decision.priority`**: `HIGH`, `MEDIUM`, `LOW`. High-priority alerts outrank and interrupt lower-priority active speech.
- **Context Persistence**: The Python bridge initializes `Track2Pipeline` once, allowing Track 2's `ContextReasoner` to maintain temporal persistence across sequential frames in a session. Track 3 calls `POST /session/reset` whenever an assistance session begins.

---

## 4. Required Software & Prerequisites

Before running Track 3, verify the following are installed:
- **Flutter SDK**: 3.38+ / 3.47+ (Dart 3.10+ / 3.13+)
- **Python**: 3.11+
- **Android SDK & Command-Line Tools**: API level 21+ (Android 5.0+) with Android Studio or SDK Platform-Tools
- **Java Development Kit**: JDK 17 or JDK 21

---

## 5. Setup & Configuration

### A. Python Backend & Bridge Setup
Install Python dependencies and start the bridge:
```bash
# Navigate to repository root
cd C:\Source_Code\A-Eye

# Install requirements
pip install -r track2/requirements.txt
pip install fastapi uvicorn python-multipart
```

### B. VLM Modes (Mock vs Live)

#### 1. Mock Mode (Default — 100% Offline)
Runs entirely locally using Track 2's deterministic `MockVLM`. Requires no internet, no external APIs, and no API keys:
```bash
# Set environment variable (PowerShell)
$env:A_EYE_VLM_MODE="mock"

# Launch the bridge server
python -m track2_bridge
```

#### 2. Live Gemini Mode (Real Image Analysis)
Uses Google's Gemini Vision-Language Model (`gemini-3.8-flash` via `google-genai`):
1. Copy `.env.example` to `.env` in the repository root or inside `track2/`:
   ```bash
   cp .env.example .env
   ```
2. Set your Google Gemini API key:
   ```env
   A_EYE_VLM_MODE=live
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   GEMINI_MODEL=gemini-3.8-flash
   ```
3. Start the bridge:
   ```bash
   python -m track2_bridge
   ```

> [!WARNING]
> **Location of API Keys**: Never hardcode API keys in code or commit `.env` files to git. `GEMINI_API_KEY` is loaded strictly through environment variables or `track2/.env` / root `.env`.

---

## 6. Network Configuration

The backend URL is completely configurable and is never hardcoded to localhost:

| Environment | Bridge Host Setting | Flutter Backend URL Setting | Notes |
| :--- | :--- | :--- | :--- |
| **Android Emulator** | `0.0.0.0` or `127.0.0.1` | `http://10.0.2.2:5000` | `10.0.2.2` maps directly to your host machine's `127.0.0.1`. |
| **Physical Android Phone** | `0.0.0.0` | `http://<YOUR_LAN_IP>:5000` | Phone and PC must be on the same Wi-Fi network (e.g. `http://192.168.1.45:5000`). |
| **Desktop / Dev Testing** | `127.0.0.1` | `http://127.0.0.1:5000` | Local desktop testing. |

### Setting the URL in Flutter:
1. **Via In-App Settings**: Tap the Settings gear icon in the top-right corner to type or select pre-set URLs.
2. **Via Build Flag**:
   ```bash
   flutter run -d <device_id> --dart-define=BACKEND_URL=http://192.168.1.45:5000
   ```

---

## 7. How to Run the App

1. Ensure the Python bridge is running:
   ```bash
   python -m track2_bridge
   ```
2. Verify bridge health:
   ```bash
   curl http://localhost:5000/health
   ```
3. Run the Flutter Android app:
   ```bash
   cd track3_app
   flutter run -d android
   ```
   Or select your connected physical device from `flutter devices`.

---

## 8. How to Test

### Run Flutter Unit & Integration Tests (16 Tests):
```bash
cd track3_app
flutter test
```
Tests cover:
- Track2Result JSON deserialization
- AssistanceCategory & PriorityLevel parsing
- Speech deduplication and cooldown enforcement
- Urgent alert interrupt behavior
- Haptic vibration mappings
- Frame scheduler non-overlapping inference and stale frame dropping
- Duplicate frame prevention (unique frame IDs and timestamps)
- Backend error and timeout handling (400, 502, network failure)
- Session lifecycle state transitions
- Dynamic configuration parsing and mutators

### Run Python Track 2 & Bridge Tests (49 Tests):
```bash
cd C:\Source_Code\A-Eye
pytest track2/tests/ track2_bridge/tests/ -v
```

---

## 9. Key Technical Policies

### Frame Scheduling (Section 5)
- **Controlled Rate**: Samples at 500–1000 ms intervals.
- **Mutex Guard**: If an HTTP request is in-flight when the timer ticks, the frame is dropped immediately to prevent server overload or latency backlog.
- **Format**: JPEGs are encoded with upright orientation (`img.bakeOrientation`) and scaled to 720px max width in a background isolate to maintain 60fps UI responsiveness.

### Automatic Speech & Deduplication (Section 6)
- **Zero-Touch Audio**: Voice output starts automatically on detection; no manual "Speak" button.
- **Anti-Spam Cooldowns**: Alerts have a 3s cooldown; guidance has a 5s cooldown; info has an 8s cooldown.
- **Preemption**: An incoming `HIGH` priority alert immediately stops any active speech and delivers the urgent alert.

### Tactile Haptics (Section 6)
- High alerts trigger double-pulse high-intensity vibrations.
- Guidance triggers a single medium vibration pulse.
- Info triggers a subtle click.
- Debounced with a 1200ms minimum cooldown to prevent annoying buzzing.

---

## 10. Manual Steps Requiring User Action

> [!IMPORTANT]
> The following steps cannot be performed autonomously by an AI agent and must be completed by the developer/user:
> 1. **Installing Android Studio / SDK**: If not already present, install Android Studio and the Android SDK command-line tools.
> 2. **Accepting Android SDK Licenses**: Run `flutter doctor --android-licenses` in a terminal and press `y` to accept all SDK licenses.
> 3. **Obtaining Gemini API Key**: Visit [Google AI Studio](https://aistudio.google.com/app/apikey) to generate an API key for live mode.
> 4. **Enabling Android USB Debugging**: On physical phones, enable Developer Options and turn on "USB Debugging".
> 5. **Granting Camera Permissions**: When launching the app for the first time, grant the runtime camera permission when prompted by Android.

---

## 11. Safety & Privacy Notice

> [!CAUTION]
> **Safety Limitations**:
> A-Eye is an experimental assistive aid. It does **NOT** guarantee obstacle detection or safe navigation. It must never replace trained mobility techniques, a white cane, or a guide dog. The system never declares a pathway "safe to walk".
>
> **Privacy Consideration**:
> Camera frames captured by this application are transmitted over the local network to the Python bridge server. In live mode, frames are transmitted to Google Gemini for scene understanding. Do not point the camera at sensitive or confidential information.
