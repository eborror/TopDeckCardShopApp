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

def generate_id(cursor, table_name, column_name):
    query = f"SELECT MAX({column_name}) AS max_id FROM {table_name}"
    cursor.execute(query)

    row = cursor.fetchone()

    if row is None or row["max_id"] is None:
        return 1

    return row["max_id"] + 1

@app.get("/")
def dashboard(request: Request):
    conn = get_db_conn()
    cursor = conn.cursor(dictionary=True)

    try:
        # LEFT PANEL: current stock
        cursor.execute("""
            SELECT PRODUCT_ID, PRODUCT_NAME, PRODUCT_PRICELISTED, PRODUCT_STOCK
            FROM PRODUCT
            ORDER BY PRODUCT_NAME
        """)
        products = cursor.fetchall()

        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={
                "products": products
            }
        )

    finally:
        cursor.close()
        conn.close()

@app.post("/update_stock")
def update_stock(
    product_id: int = Form(...),
    quantity: int = Form(...)
):
    conn = get_db_conn()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE PRODUCT
            SET PRODUCT_STOCK = PRODUCT_STOCK + %s
            WHERE PRODUCT_ID = %s
        """, (quantity, product_id))

        conn.commit()

    except Exception as e:
        conn.rollback()
        print("Stock update error:", e)

    finally:
        cursor.close()
        conn.close()

    return RedirectResponse(url="/", status_code=303)

@app.post("/add_product")
def add_product(
    product_name: str = Form(...),
    buy_price: float = Form(...),
    listed_price: float = Form(...),
    stock: int = Form(...)
):
    conn = get_db_conn()
    cursor = conn.cursor(dictionary=True)

    try:
        # generate new ID
        product_id = generate_id(cursor, "PRODUCT", "PRODUCT_ID")

        cursor.execute("""
            INSERT INTO PRODUCT
            (PRODUCT_ID, PRODUCT_NAME, PRODUCT_PRICEBOUGHT, PRODUCT_PRICELISTED, PRODUCT_STOCK)
            VALUES (%s, %s, %s, %s, %s)
        """, (product_id, product_name, buy_price, listed_price, stock))

        conn.commit()

    except Exception as e:
        conn.rollback()
        print("Add product error:", e)

    finally:
        cursor.close()
        conn.close()

    return RedirectResponse(url="/admin", status_code=303)

# This Page will have the form to process a sale and show dropdowns for customers, products, and cashiers
@app.get("/interaction")
def interactionHandler(request: Request):
    conn = get_db_conn()
    cursor = conn.cursor(dictionary=True)

    try:
        # Fetch data for dropdowns
        cursor.execute("SELECT * FROM CUSTOMER")
        customers = cursor.fetchall()

        cursor.execute("""
            SELECT PRODUCT_ID, PRODUCT_NAME, PRODUCT_PRICELISTED, PRODUCT_STOCK 
            FROM PRODUCT
        """)
        products = cursor.fetchall()

        # Join Cashier with Customer to get the names
        cursor.execute("""
            SELECT CA.CASHIER_ID, CU.CUSTOMER_FNAME, CU.CUSTOMER_LNAME 
            FROM CASHIER CA 
            JOIN CUSTOMER CU ON CA.CUSTOMER_ID = CU.CUSTOMER_ID
        """)
        cashiers = cursor.fetchall()

        # Transaction history
        cursor.execute("""
            SELECT 
                C.CHECKOUT_ID,
                C.CHECKOUT_TOTAL_PRICE,
                C.CHECKOUT_DATE,
                CU.CUSTOMER_FNAME,
                CU.CUSTOMER_LNAME,
                P.PRODUCT_NAME,
                PU.PURCHASES_QUANTITY
            FROM CHECKOUT C
            JOIN CUSTOMER CU ON C.CUSTOMER_ID = CU.CUSTOMER_ID
            JOIN PURCHASES PU ON C.CHECKOUT_ID = PU.CHECKOUT_ID
            JOIN PRODUCT P ON PU.PRODUCT_ID = P.PRODUCT_ID
            ORDER BY C.CHECKOUT_DATE DESC, C.CHECKOUT_ID DESC
            LIMIT 50
        """)
        history = cursor.fetchall()

        return templates.TemplateResponse(
            request=request,
            name="interactionHandler.html",
            context={
                "customers": customers,
                "products": products,
                "cashiers": cashiers,
                "history": history
            }
        )

    finally:
        cursor.close()
        conn.close()

# This page processes the form submission from the interaction page, inserting
#  into CHECKOUT and PURCHASES, and updating PRODUCT stock
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

        # 2. Calculate total
        if total_price is None:
            total = price * quantity
        else:
            total = total_price

        # 3. Generate new IDs
        checkout_id = generate_id(cursor, "CHECKOUT", "CHECKOUT_ID")

        purchases_id = generate_id(cursor, "PURCHASES", "PURCHASES_ID")

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

@app.get("/admin")
def admin_page(request: Request):
    conn = get_db_conn()
    cursor = conn.cursor(dictionary=True)

    try:
        # show existing customers/managers
        cursor.execute("SELECT * FROM CUSTOMER")
        customers = cursor.fetchall()

        cursor.execute("SELECT * FROM MANAGER")
        managers = cursor.fetchall()

        cursor.execute("SELECT PRODUCT_ID, PRODUCT_NAME, PRODUCT_STOCK FROM PRODUCT")
        products = cursor.fetchall()
        
        return templates.TemplateResponse(
            request=request,
            name="admin.html",
            context={
                "customers": customers,
                "managers": managers
            }
        )

    finally:
        cursor.close()
        conn.close()

@app.post("/add_manager")
def add_manager(
    customer_id: int = Form(...),
    wage: float = Form(...),
    hours: int = Form(...),
    location_id: int = Form(...)
):
    conn = get_db_conn()
    cursor = conn.cursor(dictionary=True)

    manager_id = generate_id(cursor, "MANAGER", "MANAGER_ID")

    try:
        cursor.execute("""
            INSERT INTO MANAGER
            (MANAGER_ID, MANAGER_WAGE, MANAGER_HOURSWORKED, CUSTOMER_ID, LOCATION_ID)
            VALUES (%s, %s, %s, %s, %s)
        """, (manager_id, wage, hours, customer_id, location_id))

        conn.commit()

    except Exception as e:
        conn.rollback()
        print("Add manager error:", e)

    finally:
        cursor.close()
        conn.close()

    return RedirectResponse(url="/admin", status_code=303)

@app.post("/remove_manager")
def remove_manager(manager_id: int = Form(...)):
    conn = get_db_conn()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            DELETE FROM MANAGER
            WHERE MANAGER_ID = %s
        """, (manager_id,))

        conn.commit()

    except Exception as e:
        conn.rollback()
        print("Remove manager error:", e)

    finally:
        cursor.close()
        conn.close()

    return RedirectResponse(url="/admin", status_code=303)
#Add customer

@app.post("/add_customer")
def add_customer(
    first_name: str = Form(...),
    last_name: str = Form(None),
    email: str = Form(None),
    phone: str = Form(None)
):
    conn = get_db_conn()
    cursor = conn.cursor(dictionary=True)

    try:
        customer_id = generate_id(cursor, "CUSTOMER", "CUSTOMER_ID")

        cursor.execute("""
            INSERT INTO CUSTOMER 
            (CUSTOMER_ID, CUSTOMER_FNAME, CUSTOMER_LNAME, CUSTOMER_EMAIL, CUSTOMER_PHONE)
            VALUES (%s, %s, %s, %s, %s)
        """, (customer_id, first_name, last_name, email, phone))

        conn.commit()
    except Exception as e:
        conn.rollback()
        print("Add customer error:", e)
    finally:
        cursor.close()
        conn.close()

    return RedirectResponse(url="/admin", status_code=303)
# Delete customer record

@app.post("/remove_customer")
def remove_customer(customer_id: int = Form(...)):
    conn = get_db_conn()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            DELETE FROM CUSTOMER
            WHERE CUSTOMER_ID = %s
        """, (customer_id,))
        

        conn.commit()
        return {"message": "Customer removed successfully"}

    except Exception as e:
        conn.rollback()
        print("Remove customer error:", e)
        return {"error": str(e)}

    finally:
        cursor.close()
        conn.close()




@app.get("/test")
def test():
    return {"status": "working"}
