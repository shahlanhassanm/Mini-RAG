import datetime
from sqlalchemy.orm import Session
from .database import Customer, Invoice, CommunicationLog, SessionLocal, Order, Alert
import random

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- CRM Service ---

def seed_data(db: Session):
    # Check if data exists
    if db.query(Customer).first():
        return

    # Seed Customers
    c1 = Customer(name="TechSolutions Inc.", phone="+1234567890", email="contact@techsolutions.com", relationship_score=80)
    c2 = Customer(name="Global Traders", phone="+0987654321", email="accounts@globaltraders.com", relationship_score=40)
    db.add_all([c1, c2])
    db.commit()

    # Seed Invoices
    today = datetime.date.today()
    i1 = Invoice(customer_id=c1.id, amount=1500.00, due_date=today - datetime.timedelta(days=2), status="Overdue")
    i2 = Invoice(customer_id=c2.id, amount=5000.00, due_date=today - datetime.timedelta(days=10), status="Overdue")
    i3 = Invoice(customer_id=c1.id, amount=300.00, due_date=today + datetime.timedelta(days=5), status="Unpaid")
    db.add_all([i1, i2, i3])
    db.commit()

    # Seed Orders
    o1 = Order(customer_id=c1.id, status="Delivered", delivery_date=today - datetime.timedelta(days=1))
    o2 = Order(customer_id=c2.id, status="Shipped", delivery_date=today + datetime.timedelta(days=2))
    db.add_all([o1, o2])
    db.commit()

def get_overdue_invoices(db: Session):
    return db.query(Invoice).filter(Invoice.status == "Overdue").all()

def get_recent_deliveries(db: Session):
    # Orders delivered in last 3 days
    cutoff = datetime.date.today() - datetime.timedelta(days=3)
    return db.query(Order).filter(Order.status == "Delivered", Order.delivery_date >= cutoff).all()

def create_alert(db: Session, type: str, message: str):
    # Check duplicate
    existing = db.query(Alert).filter(Alert.message == message, Alert.is_resolved == 0).first()
    if not existing:
        alert = Alert(type=type, message=message)
        db.add(alert)
        db.commit()

def check_unresponsive(db: Session, customer_id: int):
    # Check if last 2 messages were reminders and no payment
    # Simplification for demo: just check total sent reminders count for this customer > 2
    count = db.query(CommunicationLog).filter(
        CommunicationLog.customer_id == customer_id, 
        CommunicationLog.message_type.in_(["Friendly", "Firm", "Formal Escalation"])
    ).count()
    if count >= 3:
        return True
    return False

def mark_invoice_paid(db: Session, invoice_id: int):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if invoice:
        invoice.status = "Paid"
        db.commit()

# --- WhatsApp Service (Mock) ---

def send_whatsapp_message(db: Session, customer_id: int, ref_id: int, message_content: str, message_type: str, ref_type: str = "Invoice"):
    print(f"--- [WhatsApp Mock] Sending to Customer {customer_id} ({message_type}) ---")
    print(message_content)
    print("-------------------------------------------------------")
    
    # Log the communication
    # Log the communication
    log = CommunicationLog(
        customer_id=customer_id,
        timestamp=datetime.date.today(),
        message_type=message_type,
        content=message_content,
        status="Sent"
    )
    # Reuse invoice_id column for generic reference ID for simplicity in this hacky ORM usage, 
    # or just leave null if it's an Order. Ideally we'd have `order_id` in log.
    if ref_type == 'Invoice':
        log.invoice_id = ref_id
    
    db.add(log)
    db.commit()
    return True
