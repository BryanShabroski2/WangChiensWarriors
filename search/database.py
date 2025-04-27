import sqlite3, csv, pathlib

BASE_DIR = pathlib.Path(__file__).resolve().parent
DB_PATH  = BASE_DIR / "nittanybusiness.db"
DATA_DIR = BASE_DIR / "data"

conn = sqlite3.connect(str(DB_PATH))
cur  = conn.cursor()

cur.executescript("""
DROP TABLE IF EXISTS Product_Listings;
DROP TABLE IF EXISTS Sellers;
DROP TABLE IF EXISTS Address;
DROP TABLE IF EXISTS Zipcode_Info;

CREATE TABLE Product_Listings (
    Listing_ID          INTEGER PRIMARY KEY,
    Product_Title       TEXT,
    Product_Name        TEXT,
    Product_Description TEXT,
    Category            TEXT,
    Product_Price       REAL,
    Quantity            INTEGER,
    Seller_Email        TEXT,
    Status              INTEGER
);

CREATE TABLE Sellers (
    email                 TEXT PRIMARY KEY,
    business_name         TEXT,
    Business_Address_ID   TEXT,
    bank_routing_number   TEXT,
    bank_account_number   TEXT,
    balance               REAL
);

-- Address now matches your CSV columns exactly
CREATE TABLE Address (
    address_id  TEXT PRIMARY KEY,
    zipcode     TEXT,
    street_num  TEXT,
    street_name TEXT
);

CREATE TABLE Zipcode_Info (
    zipcode TEXT PRIMARY KEY,
    city    TEXT,
    state   TEXT
);
""")

# indices, triggers ... (unchanged) -------------------------
cur.execute("CREATE INDEX idx_pl_title   ON Product_Listings(Product_Title);")
cur.execute("CREATE INDEX idx_pl_desc    ON Product_Listings(Product_Description);")
cur.execute("CREATE INDEX idx_pl_cat     ON Product_Listings(Category);")

cur.executescript("""
CREATE TRIGGER IF NOT EXISTS trg_set_sold
AFTER UPDATE OF Quantity ON Product_Listings
FOR EACH ROW
WHEN NEW.Quantity = 0 AND OLD.Quantity <> 0
BEGIN
  UPDATE Product_Listings SET Status = 2 WHERE Listing_ID = NEW.Listing_ID;
END;

CREATE TRIGGER IF NOT EXISTS trg_set_active
AFTER UPDATE OF Quantity ON Product_Listings
FOR EACH ROW
WHEN NEW.Quantity > 0 AND OLD.Quantity = 0
BEGIN
  UPDATE Product_Listings SET Status = 1 WHERE Listing_ID = NEW.Listing_ID;
END;
""")

# helper  ----------------------------------------------------
def import_csv(path: pathlib.Path, table: str, price_col: str | None = None):
    with path.open(newline="", encoding="utf-8") as f:
        reader  = csv.reader(f)
        header  = next(reader)
        ph      = ",".join("?" * len(header))
        sql     = f"INSERT OR IGNORE INTO {table}({','.join(header)}) VALUES({ph})"
        rows    = []
        if price_col and price_col in header:
            idx = header.index(price_col)
            for r in reader:
                r[idx] = float(r[idx].replace("$", "").replace(",", "").strip())
                rows.append(r)
        else:
            rows = list(reader)
        cur.executemany(sql, rows)
        conn.commit()

# import
import_csv(DATA_DIR / "Product_Listings.csv", "Product_Listings", price_col="Product_Price")
import_csv(DATA_DIR / "Sellers.csv",           "Sellers")
import_csv(DATA_DIR / "Address.csv",           "Address")
import_csv(DATA_DIR / "Zipcode_Info.csv",      "Zipcode_Info")

conn.close()
print("✅ database rebuilt with updated Address columns")
