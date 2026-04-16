import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def init_db():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS")
        )
        cursor = conn.cursor()
        
        # Create Database
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {os.getenv('DB_NAME')}")
        cursor.execute(f"USE {os.getenv('DB_NAME')}")

        # Create User
        cursor.execute(f"CREATE USER IF NOT EXISTS 'manager_mark'@'localhost' IDENTIFIED BY '{os.getenv('DB_PASS')}'")
        cursor.execute(f"GRANT ALL PRIVILEGES ON {os.getenv('DB_NAME')}.* TO 'manager_mark'@'localhost'")
        cursor.execute("FLUSH PRIVILEGES")

        # Create Tables
        tables = {
            "CUSTOMER": """
                CREATE TABLE IF NOT EXISTS CUSTOMER(
                    CUSTOMER_ID INT PRIMARY KEY,
                    CUSTOMER_FNAME VARCHAR(45) NOT NULL,
                    CUSTOMER_LNAME VARCHAR(45),
                    CUSTOMER_EMAIL VARCHAR(45),
                    CUSTOMER_PHONE VARCHAR(45)
                )
            """,

            "LOCATION": """
                CREATE TABLE IF NOT EXISTS LOCATION(
                    LOCATION_ID INT PRIMARY KEY,
                    LOCATION_ADDRESS VARCHAR(45)
                )
            """,

            "PRODUCT": """
                CREATE TABLE IF NOT EXISTS PRODUCT(
                    PRODUCT_ID INT PRIMARY KEY,
                    PRODUCT_NAME VARCHAR(45),
                    PRODUCT_PRICEBOUGHT DECIMAL(5,2),
                    PRODUCT_PRICELISTED DECIMAL(5,2),
                    PRODUCT_STOCK INT
                )
            """,

            "CASHIER": """
                CREATE TABLE IF NOT EXISTS CASHIER(
                    CASHIER_ID INT PRIMARY KEY,
                    CASHIER_WAGE DECIMAL(5,2),
                    CASHIER_HOURSWORKED INT,
                    CUSTOMER_ID INT,
                    LOCATION_ID INT,
                    FOREIGN KEY (CUSTOMER_ID) REFERENCES CUSTOMER(CUSTOMER_ID),
                    FOREIGN KEY (LOCATION_ID) REFERENCES LOCATION(LOCATION_ID)
                )
            """,

            "MANAGER": """
                CREATE TABLE IF NOT EXISTS MANAGER(
                    MANAGER_ID INT PRIMARY KEY,
                    MANAGER_WAGE DECIMAL(5,2),
                    MANAGER_HOURSWORKED INT,
                    CUSTOMER_ID INT,
                    LOCATION_ID INT,
                    FOREIGN KEY (CUSTOMER_ID) REFERENCES CUSTOMER(CUSTOMER_ID),
                    FOREIGN KEY (LOCATION_ID) REFERENCES LOCATION(LOCATION_ID)
                )
            """,

            "CHECKOUT": """
                CREATE TABLE IF NOT EXISTS CHECKOUT(
                    CHECKOUT_ID INT PRIMARY KEY,
                    CHECKOUT_TOTAL_PRICE INT,
                    CHECKOUT_DATE DATE,
                    CASHIER_ID INT,
                    CUSTOMER_ID INT,
                    FOREIGN KEY (CUSTOMER_ID) REFERENCES CUSTOMER(CUSTOMER_ID),
                    FOREIGN KEY (CASHIER_ID) REFERENCES CASHIER(CASHIER_ID)
                )
            """,

            "PURCHASES": """
                CREATE TABLE IF NOT EXISTS PURCHASES(
                    PURCHASES_ID INT PRIMARY KEY,
                    PURCHASES_QUANTITY INT,
                    PRODUCT_ID INT,
                    CHECKOUT_ID INT,
                    FOREIGN KEY (PRODUCT_ID) REFERENCES PRODUCT(PRODUCT_ID),
                    FOREIGN KEY (CHECKOUT_ID) REFERENCES CHECKOUT(CHECKOUT_ID)
                )
            """
        }

        for name, ddl in tables.items():
            cursor.execute(ddl)
            print(f"Table '{name}' verified.")
        
        conn.commit()
        print("--- Database Setup Complete ---")
    except Exception as e:
        print(f"DB Error: {e}")

    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == '__main__':
    init_db()
