import os
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from mysql.connector import pooling
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="TopDeck Card Shop App")
templates = Jinja2Templates(directory="templates")
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
def home(request: Request):
    conn = get_db_conn()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM PRODUCT")
        products = cursor.fetchall()

        return {"products": products}

    except Exception as e:
        return {"error": str(e)}

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
    cursor = conn.cursor()

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