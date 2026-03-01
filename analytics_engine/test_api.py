import requests
import json

BASE = "http://localhost:8082"

# Send 5 rapid_click events from the same bot user
print("=== Sending events ===")
for i in range(5):
    r = requests.post(f"{BASE}/event", json={"user_id": "u_test_bot_9000", "event_type": "rapid_click"})
    print(f"  Event {i+1}: {r.json()}")

# Also send a normal user
r = requests.post(f"{BASE}/event", json={"user_id": "u_legit_user", "event_type": "page_view"})
print(f"  Normal user: {r.json()}")

print("\n=== Metrics ===")
print(requests.get(f"{BASE}/metrics").json())

print("\n=== Suspicious ===")
print(requests.get(f"{BASE}/suspicious").json())

print("\n=== User Profile ===")
print(requests.get(f"{BASE}/user/u_test_bot_9000").json())
