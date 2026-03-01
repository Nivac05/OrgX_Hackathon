# 🌌 WpDev: Behavioural Intelligence Engine

> **Precision Reimagined.** A high-performance, real-time analytics suite designed to distinguish organic human interaction from synthetic bot behaviour using multi-vector forensic indicators.

---

## 🚀 The Propulsion Sequence (Landing)
The experience begins with a high-fidelity, 120-frame scroll-linked animation. As the user descends into the engine, the system's core architecture is revealed through dynamic text beats and seamless transitions from form to function.

## 📊 Detailed Component Analysis

### 1. Authenticity Score (Integrity Gauge)
Displays the global percentage of human vs. synthetic traffic. It serves as the primary health index for the platform, where a dip below 75% indicates a coordinated automated assault.

### 2. Timing Regularity Analysis
Detects sub-millisecond mathematical repetition. Humans exhibit natural "temporal entropy" (irregular pauses), while bots are defined by their precise, repetitive cadence.

### 3. Engagement Bursts
Identifies actions per second (APS). Humans physically cannot sustain high-density action clusters (e.g., 50 actions/sec), making this a definitive signal for script-based automation.

### 4. Linguistic Consistency & Entropy
Evaluates the diversity of user actions. A human explores a variety of interactions (Scroll, Click, Hover, Fill), whereas bots often focus on a single exhaustive path.

### 5. Local Heuristics Forensic Audit
A browser-side neural reasoning module that synthesizes raw telemetry vectors into a human-readable forensic report. No external API is required, ensuring zero-latency auditing.

---

## 🏎️ Tech Stack Rationale: Why Multi-Threading?

We utilize a **POSIX-style Thread Pool** (in C++) and a **Multi-threaded Handler** (in Python) because:
- **Zero Ingestion Lag:** High-volume telemetry (thousands of events/sec) would choke a single-threaded server. Our architecture processes events in parallel.
- **Concurrent KV-Store:** We use an in-memory Key-Value store with bucket-level locking, allowing O(1) state lookups without blocking the main event loop.
- **Resource Isolation:** Heavy AI forensic audits are offloaded to sister threads, keeping the live data metrics smooth and responsive.

## 🤖 Model Selection: The Power of Logistic Regression (LR)

While Deep Learning models like LSTMs are powerful, **Logistic Regression (LR)** is the optimal choice for this specific behavioural challenge because:
1. **Nano-second Latency:** LR inference is mathematically lightweight, allowing us to flag a bot *before* its second request even hits the server.
2. **Deterministic Explainability:** Unlike "black box" neural networks, LR provides clear feature weights, allowing us to explain *exactly* why a user was flagged (e.g., "Flagged due to low Timing Entropy").
3. **Probabilistic Output:** Using the Sigmoid function, LR provides a 0-1 probability scale, which maps perfectly to our **Authenticity Score** and risk buckets.

---

## 🛠️ Getting Started

### 1. Requirements
- Node.js 18+
- Python 3.10+
- `requests`, `pandas` python libraries

### 2. Launch Sequence
```bash
# Terminal 1: Start the Analytics Engine
cd analytics_engine
python backend_python.py

# Terminal 2: Stream the Dataset (High-Speed Simulation)
python analytics_engine/csv_streamer.py

# Terminal 3: Launch the Intelligence UI
cd wpdev
npm install && npm run dev
```

---

**Built for HackBA 2026**
*"Measuring humanity in a digital world."*
