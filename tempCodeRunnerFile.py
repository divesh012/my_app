
    import pymysql

try:
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="yourpassword",
        database="register"
    )
    print("Connected to MySQL successfully!")
    conn.close()
except Exception as e:
    print("Error:", e)
