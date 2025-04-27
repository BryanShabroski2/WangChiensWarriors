import sqlite3
import pathlib

BASE_DIR = pathlib.Path(__file__).parent
DB_PATH  = BASE_DIR / "nittanybusiness.db"
conn     = sqlite3.connect(DB_PATH)
cur      = conn.cursor()

# ─── Drop and recreate Product_Listings without NOT NULL on Seller_Email ───
cur.executescript("""
DROP TABLE IF EXISTS Product_Listings;

CREATE TABLE Product_Listings (
    Listing_ID          INTEGER PRIMARY KEY AUTOINCREMENT,
    Seller_Email        TEXT,                -- now nullable
    Category            TEXT    NOT NULL,
    Product_Name        TEXT    NOT NULL,
    Product_Title       TEXT    NOT NULL,
    Product_Description TEXT    NOT NULL,
    Quantity            INTEGER NOT NULL CHECK (Quantity >= 0),
    Product_Price       REAL    NOT NULL CHECK (Product_Price >= 0),
    Status              INTEGER NOT NULL DEFAULT 1
);
""")

# ─── Index ────────────────────────────────────────────────────────────────
cur.execute("CREATE INDEX IF NOT EXISTS idx_listing_status ON Product_Listings(Status);")

# ─── Triggers ─────────────────────────────────────────────────────────────
# Quantity = 0 → Status = 2 (Sold)
cur.execute("""
CREATE TRIGGER IF NOT EXISTS trg_set_sold
AFTER UPDATE OF Quantity ON Product_Listings
FOR EACH ROW
WHEN NEW.Quantity = 0
BEGIN
    UPDATE Product_Listings
       SET Status = 2
     WHERE Listing_ID = NEW.Listing_ID;
END;
""")

# Quantity > 0 → Status = 1 (Active)
cur.execute("""
CREATE TRIGGER IF NOT EXISTS trg_set_active
AFTER UPDATE OF Quantity ON Product_Listings
FOR EACH ROW
WHEN NEW.Quantity > 0
BEGIN
    UPDATE Product_Listings
       SET Status = 1
     WHERE Listing_ID = NEW.Listing_ID;
END;
""")

conn.commit()
conn.close()
print("✅ Database, table and triggers initialized (Seller_Email is now optional).")
