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
def dashboard(request: Request):
    conn = get_db_conn()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM Hubs")
        hubs = cursor.fetchall()

        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "hubs": hubs
            }
        )
    finally:
        cursor.close()
        conn.close()

@app.post("/checkout")
def checkout(member_id: int = Form(...), serial_num: str = Form(...)):
    conn = get_db_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Rentals (MemberID, SerialNum, StartTime) VALUES (%s, %s, NOW())", (member_id, serial_num))
        cursor.execute("UPDATE Bikes SET Status = 'In-Use', HubID = NULL WHERE SerialNum = %s", (serial_num,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()
    return RedirectResponse(url="/", status_code=303)
