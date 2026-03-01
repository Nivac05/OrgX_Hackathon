# WpDev Behavioural Analytics — Implementation Plan

> **Status: ✅ COMPLETE & SHIFTED TO PORT 8082**

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Unified Next.js App (localhost:3000)            │
│                                                  │
│  ┌─────────────────────────────────────────────┐ │
│  │ PART 1: Scroll Animation (500vh sticky)     │ │
│  │  - 120-frame canvas sequence                │ │
│  │  - 6 text beats (giant bold white)          │ │
│  │  - Side panels, vignette, progress bar      │ │
│  └─────────────────────────────────────────────┘ │
│                    ↓ seamless scroll ↓           │
│  ┌─────────────────────────────────────────────┐ │
│  │ PART 2: Analytics Dashboard                 │ │
│  │  - Multi-threaded rendering                 │ │
│  │  - Local Heuristics Audit Engine            │ │
│  │  - Live charts (Recharts)                   │ │
│  └─────────────────────────────────────────────┘ │
└───────────────────────┬─────────────────────────┘
                        │ REST API (fetch)
                        ▼
┌─────────────────────────────────────────────────┐
│  Python Backend (localhost:8082)                  │
│  Upgraded: Multi-threaded ThreadingMixIn         │
│  - POST /event → LR inference + WAL append       │
│  - GET /analytics → Behavioural aggregates       │
│  - GET /metrics → Performance counters           │
└─────────────────────────────────────────────────┘
```

---

## 🔬 Component Deep-Dive & Indicators

### 1. Authenticity Score (Main Gauge)
*   **What it does:** Displays the global percentage of human-to-synthetic traffic based on active user sessions.
*   **What it indicates:** Platform integrity. A score below 75% triggers a "High Risk" state, suggesting a coordinated bot attack or massive scraping event.

### 2. Timing Regularity (Vector Analysis)
*   **What it does:** Calculates the variance (standard deviation) between event timestamps for a specific identity.
*   **What it indicates:** **Repetition vs. Entropy.** Humans are erratic; their timing follows a "long-tail" distribution. Scripts are precise; if intervals are suspiciously consistent (e.g., exactly 200ms +/- 5ms), it's flagged as `BOT_LIKE`.

### 3. Engagement Bursts (Sub-Second Cluster)
*   **What it does:** Monitors the volume of actions within a sliding 1-second window.
*   **What it indicates:** **Mechanical Speed.** Humans average 1-3 actions per second. Bots can sustain 50-100. High burst scores indicate automated form filling or rapid-fire "liking" scripts.

### 4. Linguistic Consistency (Entropy Metric)
*   **What it does:** Measures the diversity of event types (Clicks, Hovers, FormFills, Scrolls).
*   **What it indicates:** **Browsing Intent.** A human explores a page with varied actions. A bot often focuses on a single task (e.g., only clicking "Like"). Low diversity + High volume = Automated intent.

### 5. Heatmap (Indicator Grid)
*   **What it does:** Visualizes the number of "Bot Indicators" (out of 4) triggered by a user.
*   **What it indicates:** **Convergence of Evidence.** A user might trigger a "Timing" flag accidentally (e.g., refreshing), but when Timing, Burst, and Pattern flags all light up red simultaneously, the bot probability approaches 99.9%.

### 6. Local Heuristics Audit (Forensic Panel)
*   **What it does:** Synthesizes raw vectors into a human-readable forensic report locally in the browser.
*   **What it indicates:** **The "Why" behind the verdict.** It explains the mathematical reasoning (e.g., "Interaction cadence deviates from organic human baselines") without needing an external LLM.

---

## ✅ Final System Specifications

| Feature | Specification | Result |
|---|---|---|
| **Backend Port** | 8082 | Avoids zombie process conflicts on 8081 |
| **Concurrency** | ThreadingMixIn | Non-blocking ingestion + analytics |
| **Model** | Logistic Regression | σ(w·x + b) calibrated for synthetic datasets |
| **Animation** | Pure Canvas | 120 FPS buttery smooth scroll rendering |
| **Forensics** | Local Engine | Instant audits with zero API latency/cost |

---

## 🛠️ Performance & Maintenance

*   **WAL Logging:** Every event is written to `events_wal.log` before processing, ensuring state can be recovered after a crash.
*   **Memory Management:** User states are stored in a `KVStore` with `deque` buffers, preventing memory leaks on high-volume streams.
*   **Streaming Speed:** The demo streamer is set to **5000x real-time**, allowing you to observe hours of traffic patterns in seconds.

---

## 🏃 Start Instructions

1.  **Kill all previous tasks (Critical):** `taskkill /F /IM python.exe /T`
2.  **Start Engine:** `python analytics_engine/backend_python.py`
3.  **Start Stream:** `python analytics_engine/csv_streamer.py`
4.  **View Dashboard:** Navigate to `localhost:3000` and scroll to the bottom.
