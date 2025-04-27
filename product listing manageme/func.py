import sqlite3
import pathlib
import csv

BASE_DIR = pathlib.Path(__file__).resolve().parent
DB_PATH  = BASE_DIR / "nittanybusiness.db"
CAT_CSV  = BASE_DIR / "data" / "Categories.csv"

def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def get_categories():

    categories = []
    with CAT_CSV.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            categories.append(row["category_name"])
    return categories

def publish_product(category, product_name, title, desc, qty, price):
    sql = """
    INSERT INTO Product_Listings
      (Seller_Email, Category, Product_Name, Product_Title,
       Product_Description, Quantity, Product_Price, Status)
    VALUES (?, ?, ?, ?, ?, ?, ?, 1);
    """
    with get_conn() as conn:
        # Seller_Email is always NULL now
        conn.execute(sql, (None, category, product_name, title, desc, qty, price))
        conn.commit()

def get_active_listings():
    sql = """
    SELECT Listing_ID, Category, Product_Name, Product_Title,
           Product_Description, Quantity, Product_Price, Status
      FROM Product_Listings
     ORDER BY Listing_ID DESC;
    """
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(sql).fetchall()]

def get_listing(listing_id):
    sql = "SELECT * FROM Product_Listings WHERE Listing_ID = ?;"
    with get_conn() as conn:
        row = conn.execute(sql, (listing_id,)).fetchone()
    return dict(row) if row else None

def edit_listing(listing_id, category=None, product_name=None,
                 title=None, desc=None, qty=None, price=None):
    updates, params = [], []
    if category     is not None: updates.append("Category = ?");            params.append(category)
    if product_name is not None: updates.append("Product_Name = ?");        params.append(product_name)
    if title        is not None: updates.append("Product_Title = ?");       params.append(title)
    if desc         is not None: updates.append("Product_Description = ?"); params.append(desc)
    if qty          is not None: updates.append("Quantity = ?");            params.append(qty)
    if price        is not None: updates.append("Product_Price = ?");       params.append(price)
    if not updates:
        return
    sql = f"UPDATE Product_Listings SET {', '.join(updates)} WHERE Listing_ID = ?;"
    params.append(listing_id)
    with get_conn() as conn:
        conn.execute(sql, params)
        conn.commit()

def update_quantity(listing_id, qty):
    sql = "UPDATE Product_Listings SET Quantity = ? WHERE Listing_ID = ?;"
    with get_conn() as conn:
        conn.execute(sql, (qty, listing_id))
        conn.commit()

def toggle_status(listing_id):
    sql = """
    UPDATE Product_Listings
       SET Status = CASE
         WHEN Status = 1 THEN 0
         WHEN Status = 0 THEN 1
         ELSE Status
       END
     WHERE Listing_ID = ?;
    """
    with get_conn() as conn:
        conn.execute(sql, (listing_id,))
        conn.commit()

def delete_listing(listing_id):
    sql = "DELETE FROM Product_Listings WHERE Listing_ID = ?;"
    with get_conn() as conn:
        conn.execute(sql, (listing_id,))
        conn.commit()
