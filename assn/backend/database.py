from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime

Base = declarative_base()

class Customer(Base):
    __tablename__ = 'customers'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    phone = Column(String)
    email = Column(String)
    relationship_score = Column(Integer, default=50) # 0-100

class Invoice(Base):
    __tablename__ = 'invoices'
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey('customers.id'))
    amount = Column(Float)
    due_date = Column(Date)
    status = Column(String, default="Unpaid") # Unpaid, Paid, Overdue
    
    customer = relationship("Customer")

class CommunicationLog(Base):
    __tablename__ = 'communication_logs'
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey('customers.id'))
    invoice_id = Column(Integer, ForeignKey('invoices.id'))
    timestamp = Column(Date, default=datetime.date.today)
    message_type = Column(String) # Reminder, Escalation, Feedback
    content = Column(String)
    status = Column(String) # Sent, Failed, Read

    customer = relationship("Customer")
    customer = relationship("Customer")
    invoice = relationship("Invoice")

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey('customers.id'))
    status = Column(String, default="Processing") # Processing, Shipped, Delivered
    delivery_date = Column(Date)
    
    customer = relationship("Customer")

class Alert(Base):
    __tablename__ = 'alerts'
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String) # Overdue, Unresponsive, Delayed
    message = Column(String)
    is_resolved = Column(Integer, default=0) # 0=Active, 1=Resolved
    timestamp = Column(Date, default=datetime.date.today)

DATABASE_URL = "sqlite:///./crm.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
