import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "nova_assist.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"

random.seed(42)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create tables
with open(SCHEMA_PATH, "r", encoding="utf-8") as file:
    cursor.executescript(file.read())

# Clear existing data
cursor.executescript("""
DELETE FROM tool_call_log;
DELETE FROM messages;
DELETE FROM escalations;
DELETE FROM conversations;
DELETE FROM return_requests;
DELETE FROM order_items;
DELETE FROM orders;
DELETE FROM products;
DELETE FROM customers;
""")

now = datetime.now()

# -------------------------
# CUSTOMERS - 40
# -------------------------

first_names = [
    "Rahul", "Aisha", "Arjun", "Priya", "Rohan",
    "Sneha", "Vikram", "Neha", "Aditya", "Sara",
    "Karan", "Ananya", "Imran", "Meera", "Yash",
    "Zoya", "Aman", "Isha", "Kabir", "Diya"
]

last_names = [
    "Sharma", "Khan", "Reddy", "Patel", "Singh",
    "Verma", "Rao", "Gupta", "Malik", "Das"
]

cities = ["Hyderabad", "Bengaluru", "Mumbai", "Delhi", "Chennai"]

customers = []

for i in range(1, 41):
    name = f"{first_names[(i - 1) % len(first_names)]} {last_names[(i - 1) % len(last_names)]}"
    email = f"customer{i}@example.com"
    phone = f"987654{1000 + i}"
    city = cities[(i - 1) % len(cities)]
    created_at = (now - timedelta(days=random.randint(30, 700))).isoformat()

    customers.append(
        (i, name, email, phone, city, created_at)
    )

cursor.executemany("""
INSERT INTO customers
(customer_id, full_name, email, phone, city, created_at)
VALUES (?, ?, ?, ?, ?, ?)
""", customers)

# -------------------------
# PRODUCTS - 60
# -------------------------

product_names = [
    "Wireless Headphones",
    "Bluetooth Speaker",
    "Smart Watch",
    "Gaming Mouse",
    "Mechanical Keyboard",
    "USB-C Cable",
    "Laptop Stand",
    "Power Bank",
    "Wireless Charger",
    "Webcam",
    "Phone Case",
    "Smartphone",
    "Laptop",
    "Tablet",
    "Monitor",
    "Keyboard",
    "Mouse Pad",
    "Earbuds",
    "Fitness Band",
    "Backpack"
]

categories = [
    "Electronics",
    "Accessories",
    "Computers",
    "Mobile",
    "Gaming"
]

products = []

for i in range(1, 61):
    name = f"{product_names[(i - 1) % len(product_names)]} {i}"
    category = categories[(i - 1) % len(categories)]
    description = f"High-quality {category.lower()} product for everyday use."
    price = round(random.uniform(299, 75000), 2)

    # Required stock bands:
    # 0 = Out of stock
    # 1-5 = Low stock
    # 6+ = In stock
    if i <= 5:
        stock = 0
    elif i <= 10:
        stock = random.randint(1, 5)
    else:
        stock = random.randint(6, 100)

    is_returnable = 0 if i in [5, 15, 25, 35, 45, 55] else 1

    products.append(
        (
            i,
            name,
            category,
            description,
            price,
            stock,
            is_returnable
        )
    )

cursor.executemany("""
INSERT INTO products
(product_id, name, category, description, price, stock_quantity, is_returnable)
VALUES (?, ?, ?, ?, ?, ?, ?)
""", products)

# -------------------------
# ORDERS - 200
# -------------------------

statuses = [
    "PLACED",
    "SHIPPED",
    "OUT_FOR_DELIVERY",
    "DELIVERED",
    "CANCELLED"
]

orders = []

for order_id in range(1, 201):
    customer_id = random.randint(1, 40)
    order_date = now - timedelta(days=random.randint(1, 180))
    status = random.choice(statuses)

    total_amount = round(random.uniform(500, 50000), 2)

    expected_delivery = None
    delivered_on = None
    courier_name = None
    tracking_ref = None

    if status != "CANCELLED":
        expected_delivery = (
            order_date + timedelta(days=random.randint(2, 7))
        ).isoformat()

        courier_name = random.choice([
            "Delhivery",
            "BlueDart",
            "DTDC",
            "Ecom Express"
        ])

        tracking_ref = f"TRK{order_id:06d}"

    if status == "DELIVERED":
        delivered_on = (
            order_date + timedelta(days=random.randint(2, 7))
        ).isoformat()

    shipping_city = cities[(customer_id - 1) % len(cities)]

    orders.append(
        (
            order_id,
            customer_id,
            order_date.isoformat(),
            status,
            total_amount,
            expected_delivery,
            delivered_on,
            courier_name,
            tracking_ref,
            shipping_city
        )
    )

cursor.executemany("""
INSERT INTO orders
(order_id, customer_id, order_date, status, total_amount,
 expected_delivery, delivered_on, courier_name,
 tracking_ref, shipping_city)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", orders)

# -------------------------
# ORDER ITEMS - 450
# -------------------------

order_items = []
item_id = 1

for order_id in range(1, 201):
    item_count = 1 if order_id <= 150 else 2

    for _ in range(item_count):
        product_id = random.randint(1, 60)
        quantity = random.randint(1, 3)

        price = cursor.execute(
            "SELECT price FROM products WHERE product_id = ?",
            (product_id,)
        ).fetchone()[0]

        order_items.append(
            (
                item_id,
                order_id,
                product_id,
                quantity,
                price
            )
        )

        item_id += 1

# Add 50 more items to reach 450
while len(order_items) < 450:
    order_id = random.randint(1, 200)
    product_id = random.randint(1, 60)
    quantity = random.randint(1, 3)

    price = cursor.execute(
        "SELECT price FROM products WHERE product_id = ?",
        (product_id,)
    ).fetchone()[0]

    order_items.append(
        (
            item_id,
            order_id,
            product_id,
            quantity,
            price
        )
    )

    item_id += 1

cursor.executemany("""
INSERT INTO order_items
(order_item_id, order_id, product_id, quantity, unit_price)
VALUES (?, ?, ?, ?, ?)
""", order_items)

# -------------------------
# RETURN REQUESTS - 20
# -------------------------

return_statuses = [
    "REQUESTED",
    "UNDER_REVIEW",
    "APPROVED",
    "REJECTED",
    "COMPLETED"
]

reasons = [
    "Damaged product",
    "Wrong product received",
    "Product not as expected",
    "Changed my mind",
    "Product is defective"
]

return_requests = []

for return_id in range(1, 21):
    order_id = random.randint(1, 200)
    reason = random.choice(reasons)
    status = random.choice(return_statuses)

    requested_at = (
        now - timedelta(days=random.randint(1, 30))
    ).isoformat()

    resolution_note = (
        "Return request processed."
        if status in ["APPROVED", "REJECTED", "COMPLETED"]
        else None
    )

    return_requests.append(
        (
            return_id,
            order_id,
            reason,
            status,
            requested_at,
            resolution_note
        )
    )

cursor.executemany("""
INSERT INTO return_requests
(return_id, order_id, reason, status, requested_at, resolution_note)
VALUES (?, ?, ?, ?, ?, ?)
""", return_requests)

conn.commit()

# -------------------------
# VERIFY DATA
# -------------------------

tables = [
    "customers",
    "products",
    "orders",
    "order_items",
    "return_requests"
]

print("\nNOVA-ASSIST DATABASE READY\n")

for table in tables:
    count = cursor.execute(
        f"SELECT COUNT(*) FROM {table}"
    ).fetchone()[0]

    print(f"{table}: {count}")

conn.close()

print("\nSeed completed successfully!")