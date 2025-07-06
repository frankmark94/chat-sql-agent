#!/usr/bin/env python3
"""
Create a sample SQLite database for testing the Chat-with-SQL Agent.
This generates a realistic e-commerce database with customers, products, orders, and reviews.
"""

import json
import random
import sqlite3
from datetime import datetime, timedelta

import pandas as pd
from faker import Faker

# Initialize Faker for generating realistic data
fake = Faker()
Faker.seed(42)  # For reproducible data
random.seed(42)


def create_sample_database(db_path="sample_ecommerce.db"):
    """Create a comprehensive sample e-commerce database."""

    print("🚀 Creating sample e-commerce database...")

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Drop existing tables if they exist
    tables = ["order_items", "reviews", "orders", "products", "categories", "customers"]
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")

    # Create tables
    print("📊 Creating tables...")

    # Categories table
    cursor.execute(
        """
    CREATE TABLE categories (
        category_id INTEGER PRIMARY KEY,
        category_name TEXT NOT NULL,
        description TEXT,
        created_at DATE DEFAULT CURRENT_DATE
    )
    """
    )

    # Customers table
    cursor.execute(
        """
    CREATE TABLE customers (
        customer_id INTEGER PRIMARY KEY,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        date_of_birth DATE,
        gender TEXT CHECK(gender IN ('M', 'F', 'Other')),
        country TEXT,
        state TEXT,
        city TEXT,
        postal_code TEXT,
        registration_date DATE DEFAULT CURRENT_DATE,
        last_login_date DATE,
        is_active BOOLEAN DEFAULT 1,
        customer_segment TEXT CHECK(customer_segment IN ('Bronze', 'Silver', 'Gold', 'Platinum'))
    )
    """
    )

    # Products table
    cursor.execute(
        """
    CREATE TABLE products (
        product_id INTEGER PRIMARY KEY,
        product_name TEXT NOT NULL,
        category_id INTEGER,
        brand TEXT,
        price DECIMAL(10,2) NOT NULL,
        cost DECIMAL(10,2),
        stock_quantity INTEGER DEFAULT 0,
        weight_kg DECIMAL(5,2),
        dimensions TEXT,
        color TEXT,
        size TEXT,
        description TEXT,
        rating DECIMAL(3,2) DEFAULT 0,
        review_count INTEGER DEFAULT 0,
        is_featured BOOLEAN DEFAULT 0,
        is_active BOOLEAN DEFAULT 1,
        created_at DATE DEFAULT CURRENT_DATE,
        FOREIGN KEY (category_id) REFERENCES categories (category_id)
    )
    """
    )

    # Orders table
    cursor.execute(
        """
    CREATE TABLE orders (
        order_id INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL,
        order_date DATE NOT NULL,
        order_status TEXT CHECK(order_status IN ('Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled', 'Returned')),
        payment_method TEXT CHECK(payment_method IN ('Credit Card', 'Debit Card', 'PayPal', 'Bank Transfer', 'Cash on Delivery')),
        shipping_address TEXT,
        billing_address TEXT,
        subtotal DECIMAL(10,2),
        tax_amount DECIMAL(10,2),
        shipping_cost DECIMAL(10,2),
        discount_amount DECIMAL(10,2) DEFAULT 0,
        total_amount DECIMAL(10,2),
        shipped_date DATE,
        delivered_date DATE,
        tracking_number TEXT,
        notes TEXT,
        FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
    )
    """
    )

    # Order items table
    cursor.execute(
        """
    CREATE TABLE order_items (
        order_item_id INTEGER PRIMARY KEY,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price DECIMAL(10,2) NOT NULL,
        discount_percent DECIMAL(5,2) DEFAULT 0,
        line_total DECIMAL(10,2),
        FOREIGN KEY (order_id) REFERENCES orders (order_id),
        FOREIGN KEY (product_id) REFERENCES products (product_id)
    )
    """
    )

    # Reviews table
    cursor.execute(
        """
    CREATE TABLE reviews (
        review_id INTEGER PRIMARY KEY,
        product_id INTEGER NOT NULL,
        customer_id INTEGER NOT NULL,
        order_id INTEGER,
        rating INTEGER CHECK(rating BETWEEN 1 AND 5),
        review_title TEXT,
        review_text TEXT,
        review_date DATE DEFAULT CURRENT_DATE,
        is_verified_purchase BOOLEAN DEFAULT 0,
        helpful_votes INTEGER DEFAULT 0,
        FOREIGN KEY (product_id) REFERENCES products (product_id),
        FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
        FOREIGN KEY (order_id) REFERENCES orders (order_id)
    )
    """
    )

    print("✅ Tables created successfully!")

    # Insert sample data
    print("📝 Inserting sample data...")

    # Categories
    categories_data = [
        (1, "Electronics", "Electronic devices and gadgets"),
        (2, "Clothing", "Fashion and apparel"),
        (3, "Home & Garden", "Home improvement and garden supplies"),
        (4, "Sports & Outdoors", "Sports equipment and outdoor gear"),
        (5, "Books", "Books and educational materials"),
        (6, "Beauty & Health", "Beauty products and health supplements"),
        (7, "Toys & Games", "Toys and entertainment"),
        (8, "Automotive", "Car parts and accessories"),
        (9, "Food & Beverages", "Food items and drinks"),
        (10, "Office Supplies", "Office and business supplies"),
    ]

    cursor.executemany(
        'INSERT INTO categories VALUES (?, ?, ?, DATE("now"))', categories_data
    )

    # Customers (500 customers)
    print("👥 Generating customers...")
    customers_data = []
    segments = ["Bronze", "Silver", "Gold", "Platinum"]

    for i in range(1, 501):
        first_name = fake.first_name()
        last_name = fake.last_name()
        email = f"{first_name.lower()}.{last_name.lower()}{i}@{fake.domain_name()}"
        registration_date = fake.date_between(start_date="-2y", end_date="today")
        last_login = fake.date_between(start_date=registration_date, end_date="today")

        customers_data.append(
            (
                i,
                first_name,
                last_name,
                email,
                fake.phone_number(),
                fake.date_of_birth(minimum_age=18, maximum_age=80),
                random.choice(["M", "F", "Other"]),
                fake.country(),
                fake.state(),
                fake.city(),
                fake.postcode(),
                registration_date,
                last_login,
                random.choice([0, 1]) if random.random() < 0.95 else 0,  # 95% active
                random.choice(segments),
            )
        )

    cursor.executemany(
        """INSERT INTO customers VALUES 
        (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        customers_data,
    )

    # Products (200 products)
    print("📦 Generating products...")
    products_data = []
    brands = [
        "Apple",
        "Samsung",
        "Nike",
        "Adidas",
        "Sony",
        "LG",
        "Dell",
        "HP",
        "Canon",
        "Nikon",
    ]
    colors = ["Black", "White", "Red", "Blue", "Green", "Silver", "Gold", "Gray"]
    sizes = ["XS", "S", "M", "L", "XL", "XXL", "One Size"]

    for i in range(1, 201):
        category_id = random.randint(1, 10)
        brand = random.choice(brands)
        price = round(random.uniform(10, 2000), 2)
        cost = round(price * random.uniform(0.3, 0.7), 2)  # Cost is 30-70% of price
        stock = random.randint(0, 500)
        rating = round(random.uniform(1, 5), 1)
        review_count = random.randint(0, 1000)

        products_data.append(
            (
                i,
                fake.catch_phrase(),
                category_id,
                brand,
                price,
                cost,
                stock,
                round(random.uniform(0.1, 50), 2),  # weight
                f"{random.randint(10, 50)}x{random.randint(10, 50)}x{random.randint(5, 30)}cm",
                random.choice(colors),
                random.choice(sizes),
                fake.text(max_nb_chars=200),
                rating,
                review_count,
                1 if random.random() < 0.2 else 0,  # 20% featured
                1 if random.random() < 0.95 else 0,  # 95% active
                fake.date_between(start_date="-1y", end_date="today"),
            )
        )

    cursor.executemany(
        """INSERT INTO products VALUES 
        (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        products_data,
    )

    # Orders (1000 orders)
    print("🛒 Generating orders...")
    orders_data = []
    statuses = [
        "Pending",
        "Processing",
        "Shipped",
        "Delivered",
        "Cancelled",
        "Returned",
    ]
    payment_methods = [
        "Credit Card",
        "Debit Card",
        "PayPal",
        "Bank Transfer",
        "Cash on Delivery",
    ]

    for i in range(1, 1001):
        customer_id = random.randint(1, 500)
        order_date = fake.date_between(start_date="-1y", end_date="today")
        status = random.choice(statuses)

        # Determine shipped and delivered dates based on status
        shipped_date = None
        delivered_date = None
        tracking_number = None

        if status in ["Shipped", "Delivered"]:
            shipped_date = order_date + timedelta(days=random.randint(1, 3))
            tracking_number = f"TRK{random.randint(100000, 999999)}"

        if status == "Delivered":
            delivered_date = shipped_date + timedelta(days=random.randint(1, 7))

        subtotal = round(random.uniform(20, 500), 2)
        tax_rate = 0.08  # 8% tax
        tax_amount = round(subtotal * tax_rate, 2)
        shipping_cost = round(random.uniform(5, 25), 2)
        discount = (
            round(random.uniform(0, subtotal * 0.2), 2) if random.random() < 0.3 else 0
        )
        total = subtotal + tax_amount + shipping_cost - discount

        orders_data.append(
            (
                i,
                customer_id,
                order_date,
                status,
                random.choice(payment_methods),
                fake.address(),
                fake.address(),
                subtotal,
                tax_amount,
                shipping_cost,
                discount,
                total,
                shipped_date,
                delivered_date,
                tracking_number,
                fake.text(max_nb_chars=100) if random.random() < 0.1 else None,
            )
        )

    cursor.executemany(
        """INSERT INTO orders VALUES 
        (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        orders_data,
    )

    # Order Items (2000 order items)
    print("📋 Generating order items...")
    order_items_data = []

    for i in range(1, 2001):
        order_id = random.randint(1, 1000)
        product_id = random.randint(1, 200)
        quantity = random.randint(1, 5)

        # Get product price
        cursor.execute("SELECT price FROM products WHERE product_id = ?", (product_id,))
        unit_price = cursor.fetchone()[0]

        discount_percent = random.uniform(0, 20) if random.random() < 0.2 else 0
        line_total = round(unit_price * quantity * (1 - discount_percent / 100), 2)

        order_items_data.append(
            (
                i,
                order_id,
                product_id,
                quantity,
                unit_price,
                discount_percent,
                line_total,
            )
        )

    cursor.executemany(
        """INSERT INTO order_items VALUES 
        (?, ?, ?, ?, ?, ?, ?)""",
        order_items_data,
    )

    # Reviews (800 reviews)
    print("⭐ Generating reviews...")
    reviews_data = []

    for i in range(1, 801):
        product_id = random.randint(1, 200)
        customer_id = random.randint(1, 500)
        order_id = random.randint(1, 1000) if random.random() < 0.8 else None
        rating = random.choices([1, 2, 3, 4, 5], weights=[5, 10, 15, 35, 35])[0]

        review_titles = [
            "Great product!",
            "Love it!",
            "Excellent quality",
            "Good value",
            "Not what I expected",
            "Amazing!",
            "Perfect",
            "Disappointed",
            "Highly recommend",
            "Outstanding",
            "Poor quality",
            "Fantastic",
        ]

        reviews_data.append(
            (
                i,
                product_id,
                customer_id,
                order_id,
                rating,
                random.choice(review_titles),
                fake.text(max_nb_chars=300),
                fake.date_between(start_date="-1y", end_date="today"),
                1 if order_id else 0,  # Verified if linked to order
                random.randint(0, 50),
            )
        )

    cursor.executemany(
        """INSERT INTO reviews VALUES 
        (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        reviews_data,
    )

    # Create indexes for better query performance
    print("🚀 Creating indexes...")
    indexes = [
        "CREATE INDEX idx_customers_email ON customers(email)",
        "CREATE INDEX idx_customers_segment ON customers(customer_segment)",
        "CREATE INDEX idx_products_category ON products(category_id)",
        "CREATE INDEX idx_products_price ON products(price)",
        "CREATE INDEX idx_orders_customer ON orders(customer_id)",
        "CREATE INDEX idx_orders_date ON orders(order_date)",
        "CREATE INDEX idx_orders_status ON orders(order_status)",
        "CREATE INDEX idx_order_items_order ON order_items(order_id)",
        "CREATE INDEX idx_order_items_product ON order_items(product_id)",
        "CREATE INDEX idx_reviews_product ON reviews(product_id)",
        "CREATE INDEX idx_reviews_customer ON reviews(customer_id)",
    ]

    for index in indexes:
        cursor.execute(index)

    # Commit changes
    conn.commit()

    # Print summary statistics
    print("\n📊 Database Summary:")
    print("=" * 50)

    summary_queries = [
        ("Total Customers", "SELECT COUNT(*) FROM customers"),
        ("Total Products", "SELECT COUNT(*) FROM products"),
        ("Total Orders", "SELECT COUNT(*) FROM orders"),
        ("Total Order Items", "SELECT COUNT(*) FROM order_items"),
        ("Total Reviews", "SELECT COUNT(*) FROM reviews"),
        (
            "Total Revenue",
            "SELECT ROUND(SUM(total_amount), 2) FROM orders WHERE order_status = 'Delivered'",
        ),
        ("Average Order Value", "SELECT ROUND(AVG(total_amount), 2) FROM orders"),
        (
            "Top Category by Products",
            """
            SELECT c.category_name, COUNT(p.product_id) as product_count 
            FROM categories c 
            LEFT JOIN products p ON c.category_id = p.category_id 
            GROUP BY c.category_name 
            ORDER BY product_count DESC 
            LIMIT 1
        """,
        ),
    ]

    for description, query in summary_queries:
        cursor.execute(query)
        result = cursor.fetchone()[0]
        if description == "Top Category by Products":
            cursor.execute(query)
            result = cursor.fetchone()
            print(f"{description}: {result[0]} ({result[1]} products)")
        else:
            print(f"{description}: {result}")

    conn.close()

    print(f"\n🎉 Sample database created successfully: {db_path}")
    print("\n💡 Example queries you can try:")
    print("• 'How many customers do we have?'")
    print("• 'What are the top 5 products by revenue?'")
    print("• 'Show me monthly sales trends'")
    print("• 'Which customers haven't ordered in the last 30 days?'")
    print("• 'What's the average rating for Electronics products?'")
    print("• 'Show me the top 10 customers by total spending'")

    return db_path


if __name__ == "__main__":
    try:
        # Install faker if not available
        import faker
    except ImportError:
        print("Installing faker package...")
        import subprocess

        subprocess.check_call(["pip", "install", "faker"])
        from faker import Faker

    db_path = create_sample_database()
    print(f"\n✅ Ready to use! Upload {db_path} to your Chat-with-SQL Agent.")
