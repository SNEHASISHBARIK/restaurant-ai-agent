import json
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
from app.database.database import SessionLocal, init_db
from app.database.models import Order

DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "seed_orders.json"

def seed_orders(db: Session) -> int:
    inserted = 0
    rows = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    for row in rows:
        if db.get(Order, row["order_id"]):
            continue
        order = Order(
            order_id=row["order_id"], customer_id=row["customer_id"],
            restaurant_name=row["restaurant_name"], items=json.dumps(row["items"]),
            total_amount=row["total_amount"], status=row["status"],
            estimated_delivery=row["estimated_delivery"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
        db.add(order); inserted += 1
    db.commit()
    return inserted

def main():
    init_db()
    db = SessionLocal()
    try:
        print(f"Inserted {seed_orders(db)} orders.")
    finally:
        db.close()

if __name__ == "__main__": main()
