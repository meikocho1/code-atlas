CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'new'
);

CREATE TABLE order_items (
    id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id),
    unit_price_cents INTEGER NOT NULL,
    quantity INTEGER NOT NULL
);
