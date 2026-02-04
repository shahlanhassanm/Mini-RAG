import sys
import os

# Ensure we can import from backend
sys.path.append(os.getcwd())

from backend.database import init_db, SessionLocal, Alert, CommunicationLog
from backend.services import seed_data
from backend.main import trigger_reminders
from fastapi import BackgroundTasks

def test_system():
    print("1. Initializing Database...")
    init_db()
    
    db = SessionLocal()
    print("2. Seeding Data...")
    seed_data(db)
    
    print("3. Running Trigger Logic...")
    # Mocking background tasks
    bg = BackgroundTasks()
    
    # We can't easily call the API function directly because of Dependency Injection, 
    # but we can import the logic or just instantiate the deps manually. 
    # Actually, trigger_reminders takes db as dependency, we can pass it.
    
    result = trigger_reminders(bg, db)
    print(f"Result: {result}")
    
    print("\n4. Verifying Alerts...")
    alerts = db.query(Alert).all()
    for a in alerts:
        print(f"ALARM --> Type: {a.type} | Msg: {a.message}")
        
    print("\n5. Verifying Logs (WhatsApp Messages)...")
    logs = db.query(CommunicationLog).all()
    for l in logs:
        print(f"MSG --> To: Customer {l.customer_id} | Type: {l.message_type} | Content: {l.content[:50]}...")
        
    if len(alerts) > 0 and len(logs) > 0:
        print("\nSUCCESS: System generated alerts and messages as expected.")
    else:
        print("\nFAILURE: No alerts or messages generated.")

if __name__ == "__main__":
    test_system()
