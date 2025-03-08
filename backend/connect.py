import psycopg2

try:
    conn = psycopg2.connect(
        dbname="schema",
        user="postgres",
        password="postgres",
        host="localhost",
        port="5432"
    )
    print("Connecting with PostgreSQL")
    
    cur = conn.cursor()
    cur.execute("SELECT version();")
    print(cur.fetchone())

    cur.close()
    conn.close()

except Exception as e:
    print(f"Connection error: {e}")