import os
import traceback
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

print("TEMPLATES TYPE:", type(templates))
print("WORKING DIR:", os.getcwd())

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
        # This replaces your "Active Rentals" query
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

@app.post("/customer")
def add_customer(
    customer_id: int = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(None),
    email: str = Form(None),
    phone: str = Form(None)
):
    conn = get_db_conn()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            INSERT INTO CUSTOMER 
            (CUSTOMER_ID, CUSTOMER_FNAME, CUSTOMER_LNAME, CUSTOMER_EMAIL, CUSTOMER_PHONE)
            VALUES (%s, %s, %s, %s, %s)
        """, (customer_id, first_name, last_name, email, phone))

        conn.commit()
    except Exception as e:
        conn.rollback()
        print(e)
    finally:
        cursor.close()
        conn.close()

    return RedirectResponse(url="/", status_code=303)

@app.get("/test")
def test():
    return {"status": "working"}



@app.post("/checkout")
def add_checkout(
    checkout_id: int = Form(...),
    checkout_total_price: int = Form(...),
    cashier_id: int = Form(...),
    customer_id: int = Form(...),
    purchases_id: int = Form(...),
    product_id: int = Form(...),
    purchases_quantity: int = Form(...)
):
    # Connection
    conn = get_db_conn()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Create checkout record
        cursor.execute("""
          INSERT INTO CHECKOUT
          (CHECKOUT_ID, CHECKOUT_TOTAL_PRICE, CHECKOUT_DATE, CASHIER_ID, CUSTOMER_ID)
            VALUES (%s, %s, CURDATE(), %s, %s)
        """, (checkout_id, checkout_total_price, cashier_id, customer_id))

    # Purchase record
    cursor.execute("""
    INSERT INTO PURCHASES
    (PURCHASES_ID, PURCHASES_QUANTITY, PRODUCT_ID, CHECKOUT_ID)
    VALUES (%s, %s, %s, %s)
     """, (purchases_id, purchases_quantity, product_id, checkout_id))

#Update product stock
cursor.execute("""
    UPDATE PRODUCT
    SET PRODUCT_STOCK = PRODUCT_STOCK - %s
    WHERE PRODUCT_ID = %s
    """, (purchases_quantity, product_id))

conn.commit()

# exception will catch errors, connrollback undoes the database changes

execpt Exception as e:
conn.rollback()
print("Checkout error:", e)
finally: 
cursor.close()
conn.close()

return RedirectResponse(url="/", status_code=303)

# Read
@app.get("/checkouts")
def view_checkouts():
    conn = get_db_conn()
    cursor = conn.cursor(dictionary=True)
try:
    # Read checkout records 
    cursor.execute("""
        SELECT * FROM CHECKOUT
        ORDER BY CHECKOUT_DATE DESC
    """)
    checkouts = cursor.fetchall()
    return checkouts

except Exception as e:
    print("Read error:", e)
    return {"error": str(e)}
    
finally:
    cursor.close()
    conn.close()
    
    


            

    
          
        
            
    
