from fastapi import FastAPI, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from .database import init_db, SessionLocal, Invoice, Customer # Fixed imports
from .services import seed_data, get_overdue_invoices, send_whatsapp_message, get_db, get_recent_deliveries, create_alert, check_unresponsive
from .agent import run_ai_workflow, generate_delivery_message
import uvicorn

app = FastAPI(title="Payment Reminder System")

@app.on_event("startup")
def on_startup():
    init_db()
    db = SessionLocal()
    seed_data(db)
    db.close()

@app.get("/")
def read_root():
    return {"message": "Payment Reminder System Backend is Running"}

@app.post("/trigger-reminders")
def trigger_reminders(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    overdue_invoices = get_overdue_invoices(db)
    results = []
    
    for inv in overdue_invoices:
        # Determine message and tone
        msg_content, tone = run_ai_workflow(inv, inv.customer)
        
        # Check specific conditions for Alerts
        if tone == "Formal Escalation":
            create_alert(db, "Critical Overdue", f"Customer {inv.customer.name} has reached critical overdue status on Invoice #{inv.id}")
        
        if check_unresponsive(db, inv.customer.id):
             create_alert(db, "Unresponsive Client", f"Customer {inv.customer.name} is unresponsive to multiple reminders.")

        # Send message (mock)
        send_whatsapp_message(db, inv.customer.id, inv.id, msg_content, tone, ref_type="Invoice")
        
        results.append({
            "customer": inv.customer.name,
            "type": "Invoice Reminder",
            "detail": f"Inv #{inv.id}",
            "status": "Sent"
        })

    # 2. Check Delivery Updates
    recent_deliveries = get_recent_deliveries(db)
    for order in recent_deliveries:
        msg = generate_delivery_message(order.customer.name, order.id, order.delivery_date)
        send_whatsapp_message(db, order.customer.id, order.id, msg, "Delivery Update", ref_type="Order")
        
        results.append({
            "customer": order.customer.name,
            "type": "Delivery Update",
            "detail": f"Order #{order.id}",
            "status": "Sent"
        })
        
    return {"count": len(results), "details": results}

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
