| column | suggested_name | description | issues |
|--------|---------------|-------------|--------|
| customer_id | customer_id | Unique identifier for each customer | None |
| order_id | order_id | Unique identifier for each order | None |
| item | product | Name of the item purchased | None |
| count | quantity | Number of items purchased in an order | None |
| total_price | total_order_price | Total price of the items in an order | Mixed types (should be float or decimal) |
| recorded_date | order_date | Date when the order was recorded | None |
| ship_date | shipment_date | Date when the order was shipped | None |
| subscription_status | subscription_level | Status of the customer's subscription (e.g., Elite, Basic, etc.) | None |