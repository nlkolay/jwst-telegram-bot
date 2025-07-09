import sqlite3

DATABASE_NAME = "subscriptions.db"

def init_db():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            user_id INTEGER PRIMARY KEY,
            frequency TEXT DEFAULT 'daily'
        )
    """)
    conn.commit()
    conn.close()

def subscribe_user(user_id: int, frequency: str = 'daily'):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO subscriptions (user_id, frequency) VALUES (?, ?)", (user_id, frequency))
    conn.commit()
    conn.close()

def unsubscribe_user(user_id: int):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM subscriptions WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def get_subscribed_users():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, frequency FROM subscriptions")
    users = cursor.fetchall()
    conn.close()
    return users

if __name__ == '__main__':
    init_db()
    print("Database initialized.")
