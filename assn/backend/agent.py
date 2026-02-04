import datetime

def determine_tone(days_overdue: int, relationship_score: int) -> str:
    if days_overdue <= 3:
        return "Friendly"
    elif days_overdue <= 7:
        return "Firm"
    else:
        return "Formal Escalation"

def generate_message_content(customer_name: str, invoice_amount: float, due_date: datetime.date, tone: str) -> str:
    # In a real scenario, this would call OpenAI API with a prompt.
    # We will simulate the output with templates.
    
    date_str = due_date.strftime("%Y-%m-%d")
    
    if tone == "Friendly":
        return (f"Hi {customer_name}, just a friendly reminder that invoice for ${invoice_amount} was due on {date_str}. "
                f"We appreciate your business!")
    elif tone == "Firm":
        return (f"Hello {customer_name}. We haven't received payment for invoice of ${invoice_amount} (due {date_str}). "
                f"Please settle this at your earliest convenience to avoid service interruption.")
    else: # Formal Escalation
        return (f"URGENT: Payment for invoice ${invoice_amount} is significantly overdue ({date_str}). "
                f"Immediate payment is required. Please contact finance immediately.")

def generate_delivery_message(customer_name: str, order_id: int, delivery_date: datetime.date) -> str:
    date_str = delivery_date.strftime("%Y-%m-%d")
    return (f"Hi {customer_name}, your order #{order_id} was delivered on {date_str}. "
            f"We hope everything arrived in perfect condition. Please let us know if you have any feedback!")

def run_ai_workflow(invoice, customer):
    days_overdue = (datetime.date.today() - invoice.due_date).days
    tone = determine_tone(days_overdue, customer.relationship_score)
    message = generate_message_content(customer.name, invoice.amount, invoice.due_date, tone)
    return message, tone
