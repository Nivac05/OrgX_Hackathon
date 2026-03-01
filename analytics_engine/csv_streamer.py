import pandas as pd
import requests
import time
import sys
import os

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "Dataset", "synthetic_bot_dataset.csv")
API_URL = "http://localhost:8082/event"
SPEEDUP = 5000  # Even faster for immediate results

def stream_csv():
    if not os.path.exists(CSV_PATH):
        print(f"❌ Error: CSV not found at {CSV_PATH}")
        return

    print(f"🚀 Loading dataset from {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH, nrows=5000) # Stream first 5000 events for a quick blast
    
    # Sort by timestamp to ensure chronological streaming
    df = df.sort_values('timestamp')
    
    print(f"📈 Ready to stream {len(df)} events at {SPEEDUP}x speed.")
    
    last_ts = None
    count = 0
    
    try:
        for idx, row in df.iterrows():
            curr_ts = row['timestamp']
            
            if last_ts is not None:
                delta = curr_ts - last_ts
                if delta > 0:
                    wait = delta / SPEEDUP
                    if wait < 0.01: # Avoid too many tiny sleeps
                        pass
                    else:
                        time.sleep(min(wait, 0.5))
            
            # Prepare payload
            payload = {
                "user_id": f"u_dataset_{row['user_id']}",
                "event_type": row['action_type']
            }
            
            try:
                # Use a very short timeout to keep things moving
                requests.post(API_URL, json=payload, timeout=0.1)
                count += 1
                if count % 10 == 0:
                    print(f"✅ Ingested {count} events... (Latest: {payload['user_id']})", end='\r')
                    sys.stdout.flush()
            except Exception:
                # Ignore failures (backend might be busy)
                pass
            
            last_ts = curr_ts
            
    except KeyboardInterrupt:
        print("\n🛑 Streaming stopped by user.")
    
    print(f"\n🏁 Quick-fire burst complete. Total events sent: {count}")

if __name__ == "__main__":
    stream_csv()
