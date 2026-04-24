import os
import traceback
from fastapi import responses
from fastapi.responses import HTMLResponse
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from mysql.connector import pooling
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="TopDeck Card Shop App")
templates = Jinja2Templates(directory="./templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Connection Pool Initialization (Size 10)
db_pool = pooling.MySQLConnectionPool(
    pool_name="topDeck_pool",
    pool_size=10,
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    database=os.getenv("DB_NAME")
)

def get_db_conn():
    return db_pool.get_connection()

@app.get("/")
def dashboard(request: Request):
    conn = get_db_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        # 1. Fetch all products (to show inventory/stock status)
        cursor.execute("SELECT * FROM PRODUCT")
        products = cursor.fetchall()
        
        # 2. Joined Query for Recent Checkouts
        query = """
            SELECT 
                C.CHECKOUT_ID, 
                CU.CUSTOMER_FNAME, 
                CU.CUSTOMER_LNAME, 
                C.CHECKOUT_TOTAL_PRICE, 
                C.CHECKOUT_DATE 
            FROM CHECKOUT C 
            JOIN CUSTOMER CU ON C.CUSTOMER_ID = CU.CUSTOMER_ID 
            ORDER BY C.CHECKOUT_DATE DESC 
            LIMIT 10
        """
        cursor.execute(query)
        recent_checkouts = cursor.fetchall()

        return templates.TemplateResponse(
            request=request, 
            name="dashboard.html", 
            context={"products": products, "recent_checkouts": recent_checkouts}
        )
    finally:
        cursor.close()
        conn.close()

# It will be the main page for handling interactions (sales, inventory updates, etc.)
@app.get("/interaction")
def interactionHandler(request: Request):
    conn = get_db_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        # Fetch data for dropdowns
        cursor.execute("SELECT * FROM CUSTOMER")
        customers = cursor.fetchall()

        cursor.execute("SELECT PRODUCT_ID, PRODUCT_NAME, PRODUCT_PRICELISTED, PRODUCT_STOCK FROM PRODUCT")
        products = cursor.fetchall()

        # Join Cashier with Customer to get the names
        cursor.execute("""
            SELECT CA.CASHIER_ID, CU.CUSTOMER_FNAME, CU.CUSTOMER_LNAME 
            FROM CASHIER CA 
            JOIN CUSTOMER CU ON CA.CUSTOMER_ID = CU.CUSTOMER_ID
        """)
        cashiers = cursor.fetchall()

        return templates.TemplateResponse(
            request=request, 
            name="interactionHandler.html", 
            context={
                "customers": customers, 
                "products": products, 
                "cashiers": cashiers
            }
        )
    finally:
        cursor.close()
        conn.close()

@app.post("/process_sale")
def process_sale(
    cashier_id: int = Form(...),
    customer_id: int = Form(...),
    product_id: int = Form(...),
    quantity: int = Form(...),
    total_price: float = Form(None)
):
    conn = get_db_conn()
    cursor = conn.cursor(dictionary=True)

    try:
        # 1. Get product price
        cursor.execute("""
            SELECT PRODUCT_PRICELISTED, PRODUCT_STOCK
            FROM PRODUCT
            WHERE PRODUCT_ID = %s
        """, (product_id,))
        product = cursor.fetchone()

        if not product:
            raise Exception("Product not found")

        if product["PRODUCT_STOCK"] < quantity:
            raise Exception("Not enough stock")

        price = float(product["PRODUCT_PRICELISTED"])

        # 2. Calculate total (unless overridden)
        if total_price is None:
            total = price * quantity
        else:
            total = total_price

        # 3. Generate new IDs (basic approach)
        cursor.execute("SELECT MAX(CHECKOUT_ID) AS max_id FROM CHECKOUT")
        checkout_id = (cursor.fetchone()["max_id"] or 0) + 1

        cursor.execute("SELECT MAX(PURCHASES_ID) AS max_id FROM PURCHASES")
        purchases_id = (cursor.fetchone()["max_id"] or 0) + 1

        # 4. Insert checkout
        cursor.execute("""
            INSERT INTO CHECKOUT
            (CHECKOUT_ID, CHECKOUT_TOTAL_PRICE, CHECKOUT_DATE, CASHIER_ID, CUSTOMER_ID)
            VALUES (%s, %s, CURDATE(), %s, %s)
        """, (checkout_id, total, cashier_id, customer_id))

        # 5. Insert purchase
        cursor.execute("""
            INSERT INTO PURCHASES
            (PURCHASES_ID, PURCHASES_QUANTITY, PRODUCT_ID, CHECKOUT_ID)
            VALUES (%s, %s, %s, %s)
        """, (purchases_id, quantity, product_id, checkout_id))

        # 6. Update stock
        cursor.execute("""
            UPDATE PRODUCT
            SET PRODUCT_STOCK = PRODUCT_STOCK - %s
            WHERE PRODUCT_ID = %s
        """, (quantity, product_id))

        conn.commit()

    except Exception as e:
        conn.rollback()
        print("=== TRANSACTION ERROR ===")
        print(e)
        import traceback
        traceback.print_exc()

    finally:
        cursor.close()
        conn.close()

    return RedirectResponse(url="/interaction", status_code=303)

@app.get("/test")
def test():
    return {"status": "working"}