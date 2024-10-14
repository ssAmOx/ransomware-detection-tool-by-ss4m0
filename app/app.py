from flask import Flask, render_template, request, jsonify, logging
import os
import sqlite3
from datetime import datetime

app = Flask(__name__)


# Function to create the logs table if it doesn't exist
def create_logs_table():
    conn = sqlite3.connect('logs.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        message TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

# Function to add test logs
def add_test_logs():
    conn = sqlite3.connect('logs.db')
    cursor = conn.cursor()
    for i in range(20):
        cursor.execute("INSERT INTO logs (message) VALUES (?)", (f"Test log message {i+1}",))
    conn.commit()
    conn.close()

@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("query", "")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    page = request.args.get("page", 1, type=int)
    per_page = 10

    conn = sqlite3.connect('logs.db')
    cursor = conn.cursor()

    # Build the SQL query dynamically based on filters
    sql_query = "SELECT COUNT(*) FROM logs WHERE 1=1"
    sql_count = "SELECT * FROM logs WHERE 1=1"

    params = []
    if query:
        query = f"%{query}%"
        sql_query += " AND message LIKE ?"
        sql_count += " AND message LIKE ?"
        params.append(query)

    if start_date:
        sql_query += " AND timestamp >= ?"
        sql_count += " AND timestamp >= ?"
        params.append(start_date)

    if end_date:
        sql_query += " AND timestamp <= ?"
        sql_count += " AND timestamp <= ?"
        params.append(end_date)

    cursor.execute(sql_query, params)
    total_logs = cursor.fetchone()[0]

    sql_count += " LIMIT ? OFFSET ?"
    params.append(per_page)
    params.append((page - 1) * per_page)

    cursor.execute(sql_count, params)
    logs = cursor.fetchall()
    conn.close()

    return render_template("index.html", logs=logs, page=page, total_logs=total_logs, query=request.args.get("query", ""))

@app.route('/')
def index():
    logs = get_logs(limit=10)  # Get initial 10 logs
    total_logs = get_total_logs()  # Function to get the total count of logs
    return render_template('index.html', logs=logs, page=1, total_logs=total_logs)

def get_logs(limit=10, offset=0):
    try:
        conn = sqlite3.connect('logs.db')
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp, message FROM logs ORDER BY id DESC LIMIT ? OFFSET ?", (limit, offset))
        logs = cursor.fetchall()
    except sqlite3.OperationalError as e:
        print(f"OperationalError: {e}")
        logs = []  # Return an empty list if there’s an error
    finally:
        conn.close()
    return logs

def get_total_logs():
    try:
        conn = sqlite3.connect('logs.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM logs")
        count = cursor.fetchone()[0]
    except sqlite3.OperationalError as e:
        print(f"OperationalError: {e}")
        count = 0
    finally:
        conn.close()
    return count

if __name__ == "__main__":
    create_logs_table()  # Ensure the table is created
    add_test_logs()  # Add the test logs
    app.run(debug=True)
