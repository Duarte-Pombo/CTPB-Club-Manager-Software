import sqlite3

def setup_database(db_name="CTPB.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON;")

    # USERS ---------------------------------------
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        card_id TEXT UNIQUE NOT NULL,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT UNIQUE,
        phone TEXT,
        nif TEXT UNIQUE,
        membership_type TEXT CHECK(membership_type IN ('admin', 'atleta', 'sócio', 'atleta e sócio')),
        monthly_fee REAL DEFAULT 0.0,
        current_balance REAL DEFAULT 0.0,
        is_active BOOLEAN DEFAULT 1,
        join_date DATE DEFAULT CURRENT_DATE
    )
    ''')

    # PAYMENT TYPES ---------------------------------
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS payment_types (
        type_id INTEGER PRIMARY KEY AUTOINCREMENT,
        type_name TEXT UNIQUE NOT NULL
    )
    ''')

    # TRANSACTIONS -----------------------------------
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        type_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        notes TEXT,
        FOREIGN KEY (user_id) REFERENCES users (user_id),
        FOREIGN KEY (type_id) REFERENCES payment_types (type_id)
    )
    ''')

    # MONTHLY FEES ------------------------------------
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS monthly_fees (
        fee_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        month INTEGER NOT NULL,
        year INTEGER NOT NULL,
        amount_due REAL NOT NULL,
        is_paid BOOLEAN DEFAULT 0,
        paid_date DATE,
        due_date DATE,
        UNIQUE(user_id, month, year),
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    ''')

    # AUDIT LOGS ----------------------------------------
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS audit_logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        user_id INTEGER,
        action TEXT NOT NULL,
        details TEXT,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    ''')

    conn.commit()
    conn.close()
    print("database initialized successfully")

if __name__ == "__main__":
    setup_database()
