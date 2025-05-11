# --------api.py------ #
from fastapi import FastAPI, HTTPException
from database import get_order  # Correct import

app = FastAPI()

@app.get("/order/{order_id}")
def read_order(order_id: str):
    order = get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order