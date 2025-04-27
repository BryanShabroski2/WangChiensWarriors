import sqlite3
import pathlib

BASE_DIR = pathlib.Path(__file__).resolve().parent
DB_PATH  = BASE_DIR / "nittanybusiness.db"

def get_conn():
    """打开并返回指向正确 DB 的连接"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def search_products(keywords="", min_price=None, max_price=None):
    """
    按关键词（title/description/category）和/或价格区间搜索商品。
    keywords: 空格分隔的词串；min_price/max_price: 数字字符串或空。
    """
    kws = [w for w in keywords.split() if w]
    sql = """
    SELECT
      Listing_ID,
      Product_Title,
      Product_Description,
      Category,
      Product_Price,
      Quantity,
      CASE Status
        WHEN 1 THEN 'Active'
        WHEN 0 THEN 'Inactive'
        WHEN 2 THEN 'Sold'
      END AS Availability
    FROM Product_Listings
    WHERE 1=1
    """
    params = {}

    # 关键词过滤
    for i, kw in enumerate(kws):
        key = f"kw{i}"
        sql += f" AND (Product_Title LIKE :{key} OR Product_Description LIKE :{key} OR Category LIKE :{key})"
        params[key] = f"%{kw}%"

    # 价格区间过滤
    if min_price not in (None, ""):
        sql += " AND Product_Price >= :min_price"
        params["min_price"] = float(min_price)
    if max_price not in (None, ""):
        sql += " AND Product_Price <= :max_price"
        params["max_price"] = float(max_price)

    sql += " ORDER BY Product_Price ASC;"

    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]

def get_product_detail(listing_id):
    """
    根据 Listing_ID 返回一条记录，包含四张表的所有列。
    """
    sql = """
    SELECT
      P.*,
      S.*,
      A.*,
      Z.*
    FROM Product_Listings P
    LEFT JOIN Sellers      S ON P.Seller_Email        = S.email
    LEFT JOIN Address      A ON S.Business_Address_ID = A.address_id
    LEFT JOIN Zipcode_Info Z ON A.zipcode             = Z.zipcode
    WHERE P.Listing_ID = :lid
    LIMIT 1;
    """
    with get_conn() as conn:
        row = conn.execute(sql, {"lid": listing_id}).fetchone()
    return dict(row) if row else None
