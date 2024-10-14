import time
import os
import smtplib
from email.mime.text import MIMEText
import sqlite3

# Create the database and logs table if they don't exist
def initialize_database():
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

class RansomwareMonitor:
    def __init__(self, watch_directory):
        self.watch_directory = watch_directory
        self.file_info = {}
        self.db_connection = sqlite3.connect('logs.db')
        self.create_table()

    def create_table(self):
        with self.db_connection:
            self.db_connection.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    message TEXT
                )
            ''')

    def get_logs(self):
        try:
            conn = sqlite3.connect('logs.db')
            cursor = conn.cursor()
            cursor.execute("SELECT timestamp, message FROM logs ORDER BY id DESC")
            logs = cursor.fetchall()
        except sqlite3.OperationalError as e:
            print(f"OperationalError: {e}")
            logs = []
        finally:
            conn.close()
        return logs

    def send_email_notification(self, subject, message):
        sender = 'your_email@example.com'  # Replace with your email
        receiver = 'recipient_email@example.com'  # Replace with recipient email
        password = 'your_email_password'  # Replace with your email password

        msg = MIMEText(message)
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = receiver

        try:
            with smtplib.SMTP('smtp.example.com', 587) as server:  # Replace with your SMTP server
                server.starttls()
                server.login(sender, password)
                server.sendmail(sender, receiver, msg.as_string())
        except Exception as e:
            print(f"Failed to send email: {e}")

    def run(self):
        print("Starting the monitor...")
        while True:
            self.check_file_activity()
            time.sleep(5)

    def check_file_activity(self):
        for file_name in os.listdir(self.watch_directory):
            file_path = os.path.join(self.watch_directory, file_name)
            if os.path.isfile(file_path):
                self.check_file(file_path)

    def check_file(self, file_path):
        # Get current file info
        current_info = os.stat(file_path)
        current_size = current_info.st_size
        current_mtime = current_info.st_mtime

        # Check if the file is already in the monitored list
        if file_path in self.file_info:
            # Compare with previous info
            previous_size, previous_mtime = self.file_info[file_path]
            if current_size != previous_size or current_mtime != previous_mtime:
                self.log(f"File modified: {file_path}")
                self.send_notification(f"File modified: {file_path}")
                self.send_email_notification("Suspicious Activity Detected", f"File modified: {file_path}")

        # Update the file info
        self.file_info[file_path] = (current_size, current_mtime)

    def log(self, message):
        timestamp = time.ctime()
        print(message)
        with self.db_connection:
            self.db_connection.execute("INSERT INTO logs (timestamp, message) VALUES (?, ?)", (timestamp, message))

    def send_notification(self, message):
        # Email notification implementation (optional)
        pass  # You can implement the notification method here if needed

if __name__ == "__main__":
    initialize_database()  # Initialize the database and create table
    watch_directory = "path_to_watch"  # Replace with your directory to monitor
    monitor = RansomwareMonitor(watch_directory)
    monitor.run()
