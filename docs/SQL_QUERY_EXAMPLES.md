# SQL Query Examples for Enhanced Agent

## Toy & Game Sales Analysis

### ✅ **Correct Query Pattern**

For the request: *"Give me a line chart of the toys and game sales in the past 6 months"*

The agent should generate:

```sql
SELECT 
    strftime('%Y-%m', o.order_date) as month,
    SUM(oi.line_total) as total_sales
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
JOIN products p ON oi.product_id = p.product_id
JOIN categories c ON p.category_id = c.category_id
WHERE c.category_name = 'Toys & Games'
  AND o.order_date >= DATE('now', '-6 months')
GROUP BY strftime('%Y-%m', o.order_date)
ORDER BY month
```

### 🔧 **Key Improvements Made**

1. **Enhanced Prompt Template**: Added comprehensive database schema understanding
2. **Proper Table Relationships**: Agent now knows to join order_items → orders → products → categories
3. **SQLite Date Functions**: Uses `DATE('now', '-6 months')` instead of MySQL syntax
4. **Category Filtering**: Correctly identifies 'Toys & Games' category
5. **Time Grouping**: Uses `strftime('%Y-%m', order_date)` for monthly grouping

### 📊 **Expected Data Output**

```
month     | total_sales
----------|------------
2025-01   | 54935.99
2025-02   | 53258.73
2025-03   | 38947.83
2025-04   | 50005.30
2025-05   | 36858.10
```

### 🎯 **Visualization Integration**

After getting the data, the agent should call:
```
create_database_visualization|line|Toys & Games Sales (Last 6 Months)|month|total_sales
```

## Database Schema Reference

### Tables and Relationships
```
categories (category_id, category_name)
    ↓ (1:many)
products (product_id, category_id, price, created_at)
    ↓ (1:many)
order_items (order_item_id, order_id, product_id, quantity, unit_price, line_total)
    ↓ (many:1)
orders (order_id, customer_id, order_date, total_amount)
```

### Sales Data Location
- **Sales amounts**: `order_items.line_total`
- **Sales dates**: `orders.order_date`
- **Product categories**: `categories.category_name`

### Common Patterns

#### Category Sales
```sql
SELECT c.category_name, SUM(oi.line_total) as total_sales
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
JOIN products p ON oi.product_id = p.product_id
JOIN categories c ON p.category_id = c.category_id
GROUP BY c.category_name
ORDER BY total_sales DESC
```

#### Time-based Sales
```sql
SELECT 
    DATE(o.order_date) as sale_date,
    SUM(oi.line_total) as daily_sales
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_date >= DATE('now', '-30 days')
GROUP BY DATE(o.order_date)
ORDER BY sale_date
```

#### Product Performance
```sql
SELECT 
    p.product_name,
    SUM(oi.quantity) as units_sold,
    SUM(oi.line_total) as revenue
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
GROUP BY p.product_id, p.product_name
ORDER BY revenue DESC
LIMIT 10
```