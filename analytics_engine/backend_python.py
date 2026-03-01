import json
import math
import threading
import sys
import random
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from collections import deque
from datetime import datetime, timedelta
import os
import urllib.request
import urllib.error

# --- PATHS ---
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "logistic_regression_model.json")
WAL_PATH = os.path.join(os.path.dirname(__file__), "events_wal.log")
PORT = 8082
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyC6bpkCdPdQaESgX0MREC4ZQ3upJDGjTcM")

class State:
    def __init__(self):
        self.event_count = 0
        self.last_probability = 0.0
        self.recent_events = deque(maxlen=5)
        self.is_suspicious = False
        self.event_timestamps = deque(maxlen=50)
        self.lock = threading.Lock()

class BackendBrain:
    def __init__(self):
        print(f"[BOOT] Loading model from {MODEL_PATH}")
        sys.stdout.flush()
        try:
            with open(MODEL_PATH, 'r') as f:
                self.model = json.load(f)
            self.feature_names = self.model.get('feature_order', [])
            self.weights = self.model.get('weights', [])
            self.bias = self.model.get('bias', 0)
            print(f"[BOOT] Model loaded: {len(self.weights)} weights, bias={self.bias:.4f}")
        except Exception as e:
            print(f"[ERROR] Failed to load model: {e}")
            self.feature_names = []
            self.weights = []
            self.bias = 0

        self.kv_store = {}
        self.wal_lock = threading.Lock()
        self.replay_wal()
        sys.stdout.flush()

    def replay_wal(self):
        if not os.path.exists(WAL_PATH):
            print("[BOOT] No WAL file found, starting fresh.")
            return
        count = 0
        try:
            with open(WAL_PATH, 'r') as f:
                for line in f:
                    if line.strip():
                        entry = json.loads(line)
                        self._apply_state(entry['user_id'], entry['event_type'], entry['probability'])
                        count += 1
            print(f"[BOOT] Replayed {count} WAL entries. Tracking {len(self.kv_store)} users.")
        except Exception as e:
            print(f"[ERROR] WAL replay: {e}")

    def sigmoid(self, x):
        try:
            return 1.0 / (1.0 + math.exp(-x))
        except OverflowError:
            return 0.0 if x < 0 else 1.0

    def get_probability(self, user_id, events):
        """Simple inference: count event types, map to feature vector, dot product with weights."""
        counts = {}
        for ev in events:
            counts[ev] = counts.get(ev, 0) + 1

        z = self.bias
        for i, fname in enumerate(self.feature_names):
            if i < len(self.weights):
                z += self.weights[i] * counts.get(fname, 0)

        return self.sigmoid(z)

    def _apply_state(self, user_id, event_type, prob):
        if user_id not in self.kv_store:
            self.kv_store[user_id] = State()
        state = self.kv_store[user_id]
        with state.lock:
            state.event_count += 1
            state.last_probability = prob
            state.recent_events.append(event_type)
            state.is_suspicious = prob > 0.8
            state.event_timestamps.append(time.time())

    def ingest_event(self, user_id, event_type):
        if user_id not in self.kv_store:
            self.kv_store[user_id] = State()
        state = self.kv_store[user_id]
        events = list(state.recent_events) + [event_type]
        prob = self.get_probability(user_id, events)
        self._apply_state(user_id, event_type, prob)

        # WAL append
        with self.wal_lock:
            try:
                with open(WAL_PATH, 'a') as f:
                    f.write(json.dumps({'user_id': user_id, 'event_type': event_type, 'probability': prob}) + "\n")
            except Exception as e:
                print(f"[ERROR] WAL write: {e}")

        return prob

    def get_timing_regularity(self, user_id):
        """Compute timing regularity: std dev of inter-event intervals. Low std = bot-like."""
        state = self.kv_store.get(user_id)
        if not state or len(state.event_timestamps) < 3:
            return {'regularity_score': 0.5, 'avg_interval_ms': 0, 'std_dev_ms': 0, 'verdict': 'insufficient_data'}
        ts = list(state.event_timestamps)
        intervals = [ts[i+1] - ts[i] for i in range(len(ts)-1)]
        avg = sum(intervals) / len(intervals) if intervals else 1
        var = sum((x - avg)**2 for x in intervals) / len(intervals) if intervals else 0
        std = math.sqrt(var)
        cv = std / avg if avg > 0 else 0  # coefficient of variation
        regularity = max(0, 1.0 - cv)  # high regularity = bot-like
        verdict = 'bot_like' if regularity > 0.85 else ('suspicious' if regularity > 0.65 else 'organic')
        return {
            'regularity_score': round(regularity, 3),
            'avg_interval_ms': round(avg * 1000, 1),
            'std_dev_ms': round(std * 1000, 1),
            'verdict': verdict
        }

    def get_engagement_bursts(self, user_id):
        """Detect engagement bursts: rapid-fire events in short windows."""
        state = self.kv_store.get(user_id)
        if not state or len(state.event_timestamps) < 2:
            return {'burst_count': 0, 'max_burst_size': 0, 'burst_score': 0.0}
        ts = sorted(state.event_timestamps)
        bursts = []
        current_burst = [ts[0]]
        for i in range(1, len(ts)):
            if ts[i] - ts[i-1] < 1.0:  # events within 1 second
                current_burst.append(ts[i])
            else:
                if len(current_burst) >= 3:
                    bursts.append(len(current_burst))
                current_burst = [ts[i]]
        if len(current_burst) >= 3:
            bursts.append(len(current_burst))
        max_burst = max(bursts) if bursts else 0
        burst_score = min(1.0, len(bursts) * 0.2 + max_burst * 0.1)
        return {
            'burst_count': len(bursts),
            'max_burst_size': max_burst,
            'burst_score': round(burst_score, 3)
        }

    def get_network_patterns(self):
        """Compute network interaction patterns: users with similar event patterns."""
        users = {}
        for uid, state in self.kv_store.items():
            events = list(state.recent_events)
            users[uid] = {
                'event_count': state.event_count,
                'probability': round(state.last_probability, 3),
                'recent_events': events,
                'is_suspicious': state.is_suspicious
            }
        # Detect coordinated behavior: users with identical event sequences
        coordinated_groups = []
        checked = set()
        uids = list(users.keys())
        for i in range(len(uids)):
            if uids[i] in checked:
                continue
            group = [uids[i]]
            for j in range(i+1, len(uids)):
                if uids[j] in checked:
                    continue
                if users[uids[i]]['recent_events'] == users[uids[j]]['recent_events'] and len(users[uids[i]]['recent_events']) >= 2:
                    group.append(uids[j])
                    checked.add(uids[j])
            if len(group) > 1:
                coordinated_groups.append(group)
                checked.add(uids[i])
        return {
            'total_users': len(users),
            'users': users,
            'coordinated_groups': coordinated_groups,
            'coordination_detected': len(coordinated_groups) > 0
        }

    def get_linguistic_consistency(self, user_id):
        """Simulate linguistic consistency analysis based on event pattern diversity."""
        state = self.kv_store.get(user_id)
        if not state:
            return {'consistency_score': 0.5, 'unique_patterns': 0, 'verdict': 'unknown'}
        events = list(state.recent_events)
        unique = len(set(events))
        total = len(events) if events else 1
        diversity = unique / total
        # Low diversity = repetitive = bot-like
        consistency = 1.0 - diversity
        verdict = 'bot_like' if consistency > 0.8 else ('suspicious' if consistency > 0.5 else 'organic')
        return {
            'consistency_score': round(consistency, 3),
            'unique_patterns': unique,
            'total_patterns': total,
            'diversity_ratio': round(diversity, 3),
            'verdict': verdict
        }

    def get_full_analytics(self):
        """Aggregate all behavioural indicators into a comprehensive analytics response."""
        total_users = len(self.kv_store)
        suspicious_users = [uid for uid, s in self.kv_store.items() if s.is_suspicious]
        
        # Calculate authenticity score: % of non-suspicious users
        authenticity = round((1.0 - len(suspicious_users) / max(total_users, 1)) * 100, 1)
        
        # Per-user behavioural analysis
        user_analysis = {}
        for uid in self.kv_store:
            timing = self.get_timing_regularity(uid)
            bursts = self.get_engagement_bursts(uid)
            linguistic = self.get_linguistic_consistency(uid)
            state = self.kv_store[uid]
            
            # Composite behavioural score
            bot_indicators = 0
            if timing['verdict'] in ('bot_like', 'suspicious'): bot_indicators += 1
            if bursts['burst_score'] > 0.5: bot_indicators += 1
            if linguistic['verdict'] in ('bot_like', 'suspicious'): bot_indicators += 1
            if state.last_probability > 0.7: bot_indicators += 1
            
            user_analysis[uid] = {
                'bot_probability': round(state.last_probability, 3),
                'event_count': state.event_count,
                'timing': timing,
                'engagement_bursts': bursts,
                'linguistic': linguistic,
                'bot_indicators': bot_indicators,
                'indicator_max': 4,
                'classification': 'bot' if bot_indicators >= 3 else ('suspicious' if bot_indicators >= 2 else 'organic')
            }
        
        return {
            'authenticity_score': authenticity,
            'total_users': total_users,
            'suspicious_count': len(suspicious_users),
            'suspicious_users': suspicious_users,
            'working_threads': 4,
            'user_analysis': user_analysis,
            'indicators': {
                'timing_regularity': 'Measures inter-event timing variance. Low variance = bot-like repetition.',
                'engagement_bursts': 'Detects rapid-fire event clusters within 1-second windows.',
                'network_patterns': 'Identifies users with identical event sequences (coordinated activity).',
                'linguistic_consistency': 'Measures event pattern diversity. Low diversity = repetitive bot behaviour.'
            }
        }

    def get_gemini_explanation(self, user_id):
        """Call Gemini API to generate a behavioural anomaly explanation."""
        state = self.kv_store.get(user_id)
        if not state:
            return {'explanation': 'No data available for this user.', 'source': 'fallback'}

        timing = self.get_timing_regularity(user_id)
        bursts = self.get_engagement_bursts(user_id)
        linguistic = self.get_linguistic_consistency(user_id)

        context = f"""Analyze this user's behavioural data for signs of fake engagement:
- User ID: {user_id}
- Event count: {state.event_count}
- Bot probability (LR model): {state.last_probability:.3f}
- Recent events: {list(state.recent_events)}
- Timing regularity score: {timing['regularity_score']} (1.0 = perfectly regular/bot-like)
- Timing verdict: {timing['verdict']}
- Average interval between events: {timing['avg_interval_ms']}ms
- Engagement burst count: {bursts['burst_count']}, max burst size: {bursts['max_burst_size']}
- Burst score: {bursts['burst_score']}
- Linguistic consistency: {linguistic['consistency_score']} (high = repetitive/bot-like)
- Event diversity ratio: {linguistic['diversity_ratio']}

Provide a concise 2-3 sentence behavioural anomaly explanation. State whether this is likely a bot or organic user, and cite the specific indicators."""

        if not GEMINI_API_KEY:
            # Fallback: generate a rule-based explanation
            return self._generate_fallback_explanation(user_id, state, timing, bursts, linguistic)

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
            payload = json.dumps({
                "contents": [{"parts": [{"text": context}]}],
                "generationConfig": {"maxOutputTokens": 200, "temperature": 0.3}
            }).encode()
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read())
                text = result['candidates'][0]['content']['parts'][0]['text']
                return {'explanation': text.strip(), 'source': 'gemini'}
        except Exception as e:
            print(f"[GEMINI] Error: {e}")
            return self._generate_fallback_explanation(user_id, state, timing, bursts, linguistic)

    def _generate_fallback_explanation(self, user_id, state, timing, bursts, linguistic):
        """Rule-based fallback when Gemini API is unavailable."""
        indicators = []
        if state.last_probability > 0.8:
            indicators.append(f"high bot probability ({state.last_probability:.0%})")
        if timing['verdict'] == 'bot_like':
            indicators.append(f"highly regular timing (regularity: {timing['regularity_score']:.2f})")
        elif timing['verdict'] == 'suspicious':
            indicators.append(f"suspiciously regular timing")
        if bursts['burst_score'] > 0.5:
            indicators.append(f"{bursts['burst_count']} engagement bursts detected")
        if linguistic['verdict'] == 'bot_like':
            indicators.append(f"repetitive event patterns (diversity: {linguistic['diversity_ratio']:.0%})")

        if not indicators:
            explanation = f"User {user_id} shows organic engagement patterns. No anomalies detected across timing, burst, or linguistic indicators."
            classification = "organic"
        elif len(indicators) >= 3:
            explanation = f"User {user_id} exhibits strong bot-like behaviour: {', '.join(indicators)}. Multiple converging indicators suggest automated or coordinated fake engagement."
            classification = "bot"
        else:
            explanation = f"User {user_id} shows suspicious patterns: {', '.join(indicators)}. Further monitoring recommended."
            classification = "suspicious"

        return {'explanation': explanation, 'classification': classification, 'source': 'rule_engine', 'indicators': indicators}

brain = BackendBrain()

class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json_response(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        try:
            if self.path == '/event':
                length = int(self.headers.get('Content-Length', 0))
                body = json.loads(self.rfile.read(length))
                uid = body.get('user_id', 'anon')
                ev = body.get('event_type', 'click')
                prob = brain.ingest_event(uid, ev)
                print(f"[EVENT] {uid} -> {ev} => prob={prob:.4f}")
                sys.stdout.flush()
                self._json_response({'status': 'success', 'bot_probability': prob})
            else:
                self._json_response({'error': 'not found'}, 404)
        except Exception as e:
            print(f"[ERROR] POST: {e}")
            sys.stdout.flush()
            self._json_response({'error': str(e)}, 500)

    def do_GET(self):
        try:
            if self.path == '/metrics':
                self._json_response({
                    'total_users': len(brain.kv_store),
                    'working_threads': 4
                })
            elif self.path == '/suspicious':
                bad = [uid for uid, s in brain.kv_store.items() if s.is_suspicious]
                self._json_response({'suspicious_count': len(bad), 'users': bad})
            elif self.path == '/analytics':
                self._json_response(brain.get_full_analytics())
            elif self.path == '/network':
                self._json_response(brain.get_network_patterns())
            elif self.path.startswith('/explain/'):
                uid = self.path.split('/')[-1]
                self._json_response(brain.get_gemini_explanation(uid))
            elif self.path.startswith('/timing/'):
                uid = self.path.split('/')[-1]
                self._json_response(brain.get_timing_regularity(uid))
            elif self.path.startswith('/user/'):
                uid = self.path.split('/')[-1]
                s = brain.kv_store.get(uid)
                if s:
                    self._json_response({
                        'user_id': uid,
                        'event_count': s.event_count,
                        'last_probability': s.last_probability,
                        'is_suspicious': s.is_suspicious
                    })
                else:
                    self._json_response({'user_id': uid, 'event_count': 0, 'last_probability': 0, 'is_suspicious': False})
            else:
                self._json_response({'error': 'not found'}, 404)
        except Exception as e:
            print(f"[ERROR] GET: {e}")
            sys.stdout.flush()

    def log_message(self, format, *args):
        pass  # Silence default HTTP logs

from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

print(f"[BOOT] Analytics Engine listening on http://localhost:{PORT}")
if GEMINI_API_KEY:
    print(f"[BOOT] Gemini API key detected — AI explanations enabled")
else:
    print(f"[BOOT] No Gemini API key — using rule-based explanations (set GEMINI_API_KEY env var)")
sys.stdout.flush()
ThreadedHTTPServer(('0.0.0.0', PORT), Handler).serve_forever()

