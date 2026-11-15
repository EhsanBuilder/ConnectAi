import sqlite3
import os
import shutil
from datetime import datetime
import bcrypt

# =========================================================
# DATABASE CONFIG
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DB_PATH = os.path.join(
    BASE_DIR,
    "contacts.db"
)

BACKUP_DIR = os.path.join(
    BASE_DIR,
    "database_backups"
)


DATABASE_VERSION = 1



# =========================================================
# TIME ENGINE
# =========================================================

def now():

    return datetime.now().isoformat(
        timespec="seconds"
    )



def today():

    return datetime.now().date().isoformat()



# =========================================================
# CONNECTION ENGINE
# =========================================================

def get_connection():

    conn = sqlite3.connect(
        DB_PATH,
        timeout=30,
        check_same_thread=False
    )


    conn.row_factory = sqlite3.Row


    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    conn.execute(
        "PRAGMA journal_mode = WAL"
    )

    conn.execute(
        "PRAGMA synchronous = NORMAL"
    )


    return conn




# =========================================================
# BACKUP SYSTEM
# =========================================================

def backup_database():

    try:

        os.makedirs(
            BACKUP_DIR,
            exist_ok=True
        )


        filename = (
            "backup_"
            +
            datetime.now().strftime(
                "%Y%m%d_%H%M%S"
            )
            +
            ".db"
        )


        path = os.path.join(
            BACKUP_DIR,
            filename
        )


        shutil.copy2(
            DB_PATH,
            path
        )


        return path


    except Exception:

        return None





# =========================================================
# CONTACTS SYSTEM
# =========================================================

def create_contacts(cursor):

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contacts (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            workspace_id INTEGER NOT NULL,

            name TEXT NOT NULL,

            email TEXT DEFAULT '',

            phone TEXT DEFAULT '',

            note TEXT DEFAULT '',

            followup TEXT DEFAULT '',

            budget INTEGER DEFAULT 0,

            vip INTEGER DEFAULT 0,

            contact_type TEXT DEFAULT 'شخصی',

            deleted INTEGER DEFAULT 0,

            created_at TEXT NOT NULL,

            updated_at TEXT,

            FOREIGN KEY(user_id)
                REFERENCES users(id)
                ON DELETE CASCADE,

            FOREIGN KEY(workspace_id)
                REFERENCES workspaces(id)
                ON DELETE CASCADE
        )
    """)
    # =========================================================
# ADD CONTACT
# =========================================================

def add_contact(
    user_id,
    workspace_id,
    name,
    email="",
    phone="",
    note="",
    followup="",
    budget=0,
    vip=0,
    contact_type="شخصی"
):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            INSERT INTO contacts
            (
                user_id,
                workspace_id,
                name,
                email,
                phone,
                note,
                followup,
                budget,
                vip,
                contact_type,
                created_at
            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,

            (
                user_id,
                workspace_id,
                name,
                email,
                phone,
                note,
                followup,
                budget,
                vip,
                contact_type,
                now()
            )
        )

        conn.commit()

        return cursor.lastrowid

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()
# =========================================================
# DATABASE INIT
# =========================================================

def init_db():

    conn = get_connection()

    cursor = conn.cursor()


    create_users(cursor)

    create_workspaces(cursor)

    create_user_settings(cursor)

    create_activity_logs(cursor)

    create_contacts(cursor)

    create_database_info(cursor)


    create_indexes(cursor)


    conn.commit()

    conn.close()





# =========================================================
# USERS
# =========================================================

def create_users(cursor):

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS users (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT NOT NULL,

        email TEXT UNIQUE NOT NULL,

        password_hash TEXT NOT NULL,

        username TEXT DEFAULT '',

        avatar TEXT DEFAULT '',

        phone TEXT DEFAULT '',

        plan TEXT DEFAULT 'free',

        role TEXT DEFAULT 'owner',

        is_active INTEGER DEFAULT 1,

        last_login TEXT,

        created_at TEXT NOT NULL

    )

    """)
    # =========================================================
# CREATE USER
# =========================================================

def create_user(name, email, password):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE email = ?
            """,
            (email,)
        )

        existing_user = cursor.fetchone()

        if existing_user:
            return None

        password_hash = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        cursor.execute(
            """
            INSERT INTO users
            (
                name,
                email,
                password_hash,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                name,
                email,
                password_hash,
                now()
            )
        )

        conn.commit()

        return cursor.lastrowid

    except Exception:
        conn.rollback()
        raise

    finally:
     conn.close()



def login_user(email, password):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE email = ? AND is_active = 1
            """,
            (email,)
        )

        user = cursor.fetchone()

        if not user:
            return None

        if not bcrypt.checkpw(
            password.encode("utf-8"),
            user["password_hash"].encode("utf-8")
        ):
            return None

        cursor.execute(
            """
            UPDATE users
            SET last_login = ?
            WHERE id = ?
            """,
            (now(), user["id"])
        )

        conn.commit()
        return user

    finally:
        conn.close()


def get_or_create_google_user(name, email):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            """,
            (email,)
        )

        user = cursor.fetchone()

        if user:
            return user

        password_hash = bcrypt.hashpw(
            os.urandom(32),
            bcrypt.gensalt()
        ).decode("utf-8")

        cursor.execute(
            """
            INSERT INTO users
            (
                name,
                email,
                password_hash,
                last_login,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, email, password_hash, now(), now())
        )

        conn.commit()
        user_id = cursor.lastrowid

        cursor.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        )

        return cursor.fetchone()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()





    
def update_user_avatar(user_id, avatar_path):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            UPDATE users
            SET avatar = ?
            WHERE id = ?
            """,
            (
                avatar_path,
                user_id
            )
        )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()





# =========================================================
# WORKSPACE SYSTEM
# =========================================================

def create_workspaces(cursor):

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS workspaces (

        id INTEGER PRIMARY KEY AUTOINCREMENT,


        user_id INTEGER NOT NULL,


        name TEXT NOT NULL,


        description TEXT DEFAULT '',


        business_type TEXT DEFAULT '',


        currency TEXT DEFAULT 'IRR',


        created_at TEXT NOT NULL,


        FOREIGN KEY(user_id)

        REFERENCES users(id)

        ON DELETE CASCADE

    )

    """)
def get_or_create_default_workspace(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        # اول ببین این کاربر از قبل اتاق داره یا نه
        cursor.execute(
            """
            SELECT id
            FROM workspaces
            WHERE user_id = ?
            ORDER BY id ASC
            LIMIT 1
            """,
            (user_id,)
        )

        existing = cursor.fetchone()

        if existing:
            return existing["id"]

        # اتاق نداشت، یکی بساز
        cursor.execute(
            """
            INSERT INTO workspaces
            (
                user_id,
                name,
                created_at
            )
            VALUES (?, ?, ?)
            """,
            (
                user_id,
                "Workspace اصلی",
                now()
            )
        )

        conn.commit()

        return cursor.lastrowid

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()
        # =========================================================
# ACTIVITY LOGS (WRITE)
# =========================================================

def log_activity(user_id, workspace_id, action, description=""):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            INSERT INTO activity_logs
            (user_id, workspace_id, action, description, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, workspace_id, action, description, now())
        )

        conn.commit()

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()





# =========================================================
# USER SETTINGS
# =========================================================

def create_user_settings(cursor):

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS user_settings (

        id INTEGER PRIMARY KEY AUTOINCREMENT,


        user_id INTEGER UNIQUE NOT NULL,


        language TEXT DEFAULT 'fa',


        theme TEXT DEFAULT 'light',


        notifications INTEGER DEFAULT 1,


        ai_enabled INTEGER DEFAULT 1,


        created_at TEXT NOT NULL,


        FOREIGN KEY(user_id)

        REFERENCES users(id)

        ON DELETE CASCADE

    )

    """)






# =========================================================
# ACTIVITY LOG
# =========================================================

def create_activity_logs(cursor):

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS activity_logs (

        id INTEGER PRIMARY KEY AUTOINCREMENT,


        user_id INTEGER NOT NULL,


        workspace_id INTEGER,


        action TEXT NOT NULL,


        description TEXT DEFAULT '',


        created_at TEXT NOT NULL,


        FOREIGN KEY(user_id)

        REFERENCES users(id)

        ON DELETE CASCADE


    )

    """)







# =========================================================
# DATABASE INFO
# =========================================================

def create_database_info(cursor):

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS database_info (

        id INTEGER PRIMARY KEY,


        version INTEGER NOT NULL,


        updated_at TEXT NOT NULL

    )

    """)


    cursor.execute("""

    INSERT OR IGNORE INTO database_info

    (
        id,
        version,
        updated_at
    )

    VALUES

    (
        1,
        ?,
        ?
    )

    """,
    (
        DATABASE_VERSION,
        now()
    ))




# =========================================================
# INDEXES
# =========================================================

def create_indexes(cursor):


    indexes = [

        """
        CREATE INDEX IF NOT EXISTS
        idx_users_email

        ON users(email)
        """,


        """
        CREATE INDEX IF NOT EXISTS
        idx_workspace_user

        ON workspaces(user_id)
        """,


        """
        CREATE INDEX IF NOT EXISTS
        idx_activity_user

        ON activity_logs(user_id)
        """

    ]


    for index in indexes:

        cursor.execute(index)# =========================================================
# FINANCE CORE SYSTEM
# Professional Accounting Engine
# =========================================================



# =========================================================
# ACCOUNTS
# =========================================================

def create_finance_accounts(cursor):

    cursor.execute("""
    
    CREATE TABLE IF NOT EXISTS finance_accounts (

        id INTEGER PRIMARY KEY AUTOINCREMENT,


        user_id INTEGER NOT NULL,


        workspace_id INTEGER NOT NULL,


        name TEXT NOT NULL,


        account_type TEXT NOT NULL,
        -- cash
        -- bank
        -- wallet


        balance INTEGER DEFAULT 0,


        currency TEXT DEFAULT 'IRR',


        description TEXT DEFAULT '',


        created_at TEXT NOT NULL,


        FOREIGN KEY(user_id)

        REFERENCES users(id)

        ON DELETE CASCADE,


        FOREIGN KEY(workspace_id)

        REFERENCES workspaces(id)

        ON DELETE CASCADE

    )

    """)






# =========================================================
# FINANCIAL CATEGORIES
# =========================================================

def create_finance_categories(cursor):

    cursor.execute("""
    
    CREATE TABLE IF NOT EXISTS finance_categories (

        id INTEGER PRIMARY KEY AUTOINCREMENT,


        workspace_id INTEGER NOT NULL,


        name TEXT NOT NULL,


        category_type TEXT NOT NULL,
        -- income
        -- expense


        icon TEXT DEFAULT '',


        created_at TEXT NOT NULL,


        FOREIGN KEY(workspace_id)

        REFERENCES workspaces(id)

        ON DELETE CASCADE

    )

    """)







# =========================================================
# MAIN TRANSACTIONS
# =========================================================

def create_finance_transactions(cursor):

    cursor.execute("""
    
    CREATE TABLE IF NOT EXISTS finance_transactions (

        id INTEGER PRIMARY KEY AUTOINCREMENT,


        user_id INTEGER NOT NULL,


        workspace_id INTEGER NOT NULL,


        account_id INTEGER,


        category_id INTEGER,


        transaction_type TEXT NOT NULL,
        -- income
        -- expense


        amount INTEGER NOT NULL,


        title TEXT NOT NULL,


        description TEXT DEFAULT '',


        contact_id INTEGER,


        transaction_date TEXT NOT NULL,


        created_at TEXT NOT NULL,


        status TEXT DEFAULT 'completed',



        FOREIGN KEY(user_id)

        REFERENCES users(id)

        ON DELETE CASCADE,


        FOREIGN KEY(workspace_id)

        REFERENCES workspaces(id)

        ON DELETE CASCADE,


        FOREIGN KEY(account_id)

        REFERENCES finance_accounts(id)

        ON DELETE SET NULL,


        FOREIGN KEY(category_id)

        REFERENCES finance_categories(id)

        ON DELETE SET NULL

    )

    """)






# =========================================================
# DOUBLE ENTRY LEDGER
# دفتر کل حسابداری
# =========================================================

def create_finance_ledger(cursor):

    cursor.execute("""
    
    CREATE TABLE IF NOT EXISTS finance_ledger (

        id INTEGER PRIMARY KEY AUTOINCREMENT,


        transaction_id INTEGER NOT NULL,


        account_id INTEGER NOT NULL,


        debit INTEGER DEFAULT 0,


        credit INTEGER DEFAULT 0,


        created_at TEXT NOT NULL,


        FOREIGN KEY(transaction_id)

        REFERENCES finance_transactions(id)

        ON DELETE CASCADE,


        FOREIGN KEY(account_id)

        REFERENCES finance_accounts(id)

        ON DELETE CASCADE

    )

    """)







# =========================================================
# INVOICES
# =========================================================

def create_invoices(cursor):

    cursor.execute("""
    
    CREATE TABLE IF NOT EXISTS invoices (

        id INTEGER PRIMARY KEY AUTOINCREMENT,


        user_id INTEGER NOT NULL,


        workspace_id INTEGER NOT NULL,


        contact_id INTEGER,


        invoice_number TEXT UNIQUE NOT NULL,


        status TEXT DEFAULT 'draft',
        -- draft
        -- sent
        -- paid
        -- cancelled


        subtotal INTEGER DEFAULT 0,


        discount INTEGER DEFAULT 0,


        tax INTEGER DEFAULT 0,


        total INTEGER DEFAULT 0,


        paid_amount INTEGER DEFAULT 0,


        due_amount INTEGER DEFAULT 0,


        issue_date TEXT NOT NULL,


        due_date TEXT,


        note TEXT DEFAULT '',


        created_at TEXT NOT NULL,


        FOREIGN KEY(user_id)

        REFERENCES users(id)

        ON DELETE CASCADE,


        FOREIGN KEY(workspace_id)

        REFERENCES workspaces(id)

        ON DELETE CASCADE

    )

    """)







# =========================================================
# INVOICE ITEMS
# =========================================================

def create_invoice_items(cursor):

    cursor.execute("""
    
    CREATE TABLE IF NOT EXISTS invoice_items (

        id INTEGER PRIMARY KEY AUTOINCREMENT,


        invoice_id INTEGER NOT NULL,


        title TEXT NOT NULL,


        quantity INTEGER DEFAULT 1,


        unit_price INTEGER DEFAULT 0,


        total_price INTEGER DEFAULT 0,


        FOREIGN KEY(invoice_id)

        REFERENCES invoices(id)

        ON DELETE CASCADE

    )

    """)







# =========================================================
# PAYMENTS
# =========================================================

def create_payments(cursor):

    cursor.execute("""
    
    CREATE TABLE IF NOT EXISTS payments (

        id INTEGER PRIMARY KEY AUTOINCREMENT,


        invoice_id INTEGER NOT NULL,


        amount INTEGER NOT NULL,


        payment_method TEXT DEFAULT '',
        -- cash
        -- card
        -- bank


        payment_date TEXT NOT NULL,


        created_at TEXT NOT NULL,


        FOREIGN KEY(invoice_id)

        REFERENCES invoices(id)

        ON DELETE CASCADE

    )

    """)







# =========================================================
# DEBTS / RECEIVABLES
# =========================================================

def create_finance_debts(cursor):

    cursor.execute("""
    
    CREATE TABLE IF NOT EXISTS finance_debts (

        id INTEGER PRIMARY KEY AUTOINCREMENT,


        user_id INTEGER NOT NULL,


        workspace_id INTEGER NOT NULL,


        contact_id INTEGER,


        debt_type TEXT NOT NULL,
        -- payable
        -- receivable


        amount INTEGER NOT NULL,


        paid_amount INTEGER DEFAULT 0,


        status TEXT DEFAULT 'open',


        due_date TEXT,


        description TEXT DEFAULT '',


        created_at TEXT NOT NULL,


        FOREIGN KEY(user_id)

        REFERENCES users(id)

        ON DELETE CASCADE,


        FOREIGN KEY(workspace_id)

        REFERENCES workspaces(id)

        ON DELETE CASCADE

    )

    """)
def init_finance_tables():

    conn = get_connection()
    cursor = conn.cursor()

    create_finance_accounts(cursor)
    create_finance_categories(cursor)
    create_finance_transactions(cursor)
    create_finance_ledger(cursor)
    create_invoices(cursor)
    create_invoice_items(cursor)
    create_payments(cursor)
    create_finance_debts(cursor)

    conn.commit()
    conn.close()

    create_finance_accounts(cursor)
    create_finance_categories(cursor)
    create_finance_transactions(cursor)
    create_finance_ledger(cursor)
    create_invoices(cursor)
    create_invoice_items(cursor)
    create_payments(cursor)
    create_finance_debts(cursor)

    conn.commit()
    conn.close()
# =========================================================
# FINANCE CORE SYSTEM
# Professional Accounting Engine
# =========================================================



# =========================================================
# ACCOUNTS
# =========================================================

def create_finance_accounts(cursor):

    cursor.execute("""
    
    CREATE TABLE IF NOT EXISTS finance_accounts (

        id INTEGER PRIMARY KEY AUTOINCREMENT,


        user_id INTEGER NOT NULL,


        workspace_id INTEGER NOT NULL,


        name TEXT NOT NULL,


        account_type TEXT NOT NULL,
        -- cash
        -- bank
        -- wallet


        balance INTEGER DEFAULT 0,


        currency TEXT DEFAULT 'IRR',


        description TEXT DEFAULT '',


        created_at TEXT NOT NULL,


        FOREIGN KEY(user_id)

        REFERENCES users(id)

        ON DELETE CASCADE,


        FOREIGN KEY(workspace_id)

        REFERENCES workspaces(id)

        ON DELETE CASCADE

    )

    """)






# =========================================================
# FINANCIAL CATEGORIES
# =========================================================

def create_finance_categories(cursor):

    cursor.execute("""
    
    CREATE TABLE IF NOT EXISTS finance_categories (

        id INTEGER PRIMARY KEY AUTOINCREMENT,


        workspace_id INTEGER NOT NULL,


        name TEXT NOT NULL,


        category_type TEXT NOT NULL,
        -- income
        -- expense


        icon TEXT DEFAULT '',


        created_at TEXT NOT NULL,


        FOREIGN KEY(workspace_id)

        REFERENCES workspaces(id)

        ON DELETE CASCADE

    )

    """)







# =========================================================
# MAIN TRANSACTIONS
# =========================================================








# =========================================================
# DOUBLE ENTRY LEDGER
# دفتر کل حسابداری
# =========================================================

def create_finance_ledger(cursor):

    cursor.execute("""
    
    CREATE TABLE IF NOT EXISTS finance_ledger (

        id INTEGER PRIMARY KEY AUTOINCREMENT,


        transaction_id INTEGER NOT NULL,


        account_id INTEGER NOT NULL,


        debit INTEGER DEFAULT 0,


        credit INTEGER DEFAULT 0,


        created_at TEXT NOT NULL,


        FOREIGN KEY(transaction_id)

        REFERENCES finance_transactions(id)

        ON DELETE CASCADE,


        FOREIGN KEY(account_id)

        REFERENCES finance_accounts(id)

        ON DELETE CASCADE

    )

    """)







# =========================================================
# INVOICES
# =========================================================

def create_invoices(cursor):

    cursor.execute("""
    
    CREATE TABLE IF NOT EXISTS invoices (

        id INTEGER PRIMARY KEY AUTOINCREMENT,


        user_id INTEGER NOT NULL,


        workspace_id INTEGER NOT NULL,


        contact_id INTEGER,


        invoice_number TEXT UNIQUE NOT NULL,


        status TEXT DEFAULT 'draft',
        -- draft
        -- sent
        -- paid
        -- cancelled


        subtotal INTEGER DEFAULT 0,


        discount INTEGER DEFAULT 0,


        tax INTEGER DEFAULT 0,


        total INTEGER DEFAULT 0,


        paid_amount INTEGER DEFAULT 0,


        due_amount INTEGER DEFAULT 0,


        issue_date TEXT NOT NULL,


        due_date TEXT,


        note TEXT DEFAULT '',


        created_at TEXT NOT NULL,


        FOREIGN KEY(user_id)

        REFERENCES users(id)

        ON DELETE CASCADE,


        FOREIGN KEY(workspace_id)

        REFERENCES workspaces(id)

        ON DELETE CASCADE

    )

    """)







# =========================================================
# INVOICE ITEMS
# =========================================================

def create_invoice_items(cursor):

    cursor.execute("""
    
    CREATE TABLE IF NOT EXISTS invoice_items (

        id INTEGER PRIMARY KEY AUTOINCREMENT,


        invoice_id INTEGER NOT NULL,


        title TEXT NOT NULL,


        quantity INTEGER DEFAULT 1,


        unit_price INTEGER DEFAULT 0,


        total_price INTEGER DEFAULT 0,


        FOREIGN KEY(invoice_id)

        REFERENCES invoices(id)

        ON DELETE CASCADE

    )

    """)







# =========================================================
# PAYMENTS
# =========================================================

def create_payments(cursor):

    cursor.execute("""
    
    CREATE TABLE IF NOT EXISTS payments (

        id INTEGER PRIMARY KEY AUTOINCREMENT,


        invoice_id INTEGER NOT NULL,


        amount INTEGER NOT NULL,


        payment_method TEXT DEFAULT '',
        -- cash
        -- card
        -- bank


        payment_date TEXT NOT NULL,


        created_at TEXT NOT NULL,


        FOREIGN KEY(invoice_id)

        REFERENCES invoices(id)

        ON DELETE CASCADE

    )

    """)







# =========================================================
# DEBTS / RECEIVABLES
# =========================================================

def create_finance_debts(cursor):

    cursor.execute("""
    
    CREATE TABLE IF NOT EXISTS finance_debts (

        id INTEGER PRIMARY KEY AUTOINCREMENT,


        user_id INTEGER NOT NULL,


        workspace_id INTEGER NOT NULL,


        contact_id INTEGER,


        debt_type TEXT NOT NULL,
        -- payable
        -- receivable


        amount INTEGER NOT NULL,


        paid_amount INTEGER DEFAULT 0,


        status TEXT DEFAULT 'open',


        due_date TEXT,


        description TEXT DEFAULT '',


        created_at TEXT NOT NULL,


        FOREIGN KEY(user_id)

        REFERENCES users(id)

        ON DELETE CASCADE,


        FOREIGN KEY(workspace_id)

        REFERENCES workspaces(id)

        ON DELETE CASCADE

    )

    """)


# =========================================================
# DASHBOARD STATISTICS
# =========================================================

def get_dashboard_stats(user_id, workspace_id):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        stats = {}

        # Total contacts
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM contacts
            WHERE user_id = ?
            AND workspace_id = ?
            AND deleted = 0
            """,
            (
                user_id,
                workspace_id
            )
        )

        stats["total"] = cursor.fetchone()[0]


        # VIP contacts
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM contacts
            WHERE user_id = ?
            AND workspace_id = ?
            AND vip = 1
            AND deleted = 0
            """,
            (
                user_id,
                workspace_id
            )
        )

        stats["vip"] = cursor.fetchone()[0]


        # Business contacts
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM contacts
            WHERE user_id = ?
            AND workspace_id = ?
            AND contact_type = 'work'
            AND deleted = 0
            """,
            (
                user_id,
                workspace_id
            )
        )

        stats["work"] = cursor.fetchone()[0]


        # Contacts added today
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM contacts
            WHERE user_id = ?
            AND workspace_id = ?
            AND deleted = 0
            AND DATE(created_at) = DATE('now', 'localtime')
            """,
            (
                user_id,
                workspace_id
            )
        )

        stats["today"] = cursor.fetchone()[0]


        # Overdue follow-ups
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM contacts
            WHERE user_id = ?
            AND workspace_id = ?
            AND deleted = 0
            AND followup IS NOT NULL
            AND followup != ''
            AND DATE(followup) < DATE('now', 'localtime')
            """,
            (
                user_id,
                workspace_id
            )
        )

        stats["late"] = cursor.fetchone()[0]


        return stats


    except Exception as e:

        print(
            f"Dashboard stats error: {e}"
        )

        return {
            "total": 0,
            "vip": 0,
            "work": 0,
            "today": 0,
            "late": 0
        }


    finally:

        conn.close()
        # =========================================================
# GET CONTACTS
# =========================================================

def get_contacts(user_id, workspace_id, search=""):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        if search:

            cursor.execute(
                """
                SELECT *
                FROM contacts

                WHERE user_id = ?
                AND workspace_id = ?
                AND deleted = 0

                AND (
                    name LIKE ?
                    OR phone LIKE ?
                    OR email LIKE ?
                )

                ORDER BY created_at DESC
                """,

                (
                    user_id,
                    workspace_id,
                    f"%{search}%",
                    f"%{search}%",
                    f"%{search}%"
                )
            )

        else:

            cursor.execute(
                """
                SELECT *
                FROM contacts

                WHERE user_id = ?
                AND workspace_id = ?
                AND deleted = 0

                ORDER BY created_at DESC
                """,

                (
                    user_id,
                    workspace_id
                )
            )

        return cursor.fetchall()

    finally:

        conn.close()
        # =========================================================
# GET ONE CONTACT
# =========================================================

def get_contact(contact_id, user_id, workspace_id):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            SELECT *
            FROM contacts

            WHERE id = ?
            AND user_id = ?
            AND workspace_id = ?
            AND deleted = 0
            """,
            (
                contact_id,
                user_id,
                workspace_id
            )
        )

        return cursor.fetchone()

    finally:

        conn.close()
        # =========================================================
# UPDATE CONTACT
# =========================================================

def update_contact(
    contact_id,
    user_id,
    workspace_id,
    name,
    email="",
    phone="",
    note="",
    followup="",
    budget=0,
    vip=0,
    contact_type="شخصی"
):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            UPDATE contacts

            SET
                name = ?,
                email = ?,
                phone = ?,
                note = ?,
                followup = ?,
                budget = ?,
                vip = ?,
                contact_type = ?,
                updated_at = ?

            WHERE id = ?
            AND user_id = ?
            AND workspace_id = ?
            AND deleted = 0
            """,

            (
                name,
                email,
                phone,
                note,
                followup,
                budget,
                vip,
                contact_type,
                now(),

                contact_id,
                user_id,
                workspace_id
            )
        )

        conn.commit()

        return cursor.rowcount

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()
        # =========================================================
# DELETE CONTACT
# =========================================================

def delete_contact(contact_id, user_id, workspace_id):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            UPDATE contacts

            SET
                deleted = 1,
                updated_at = ?

            WHERE id = ?
            AND user_id = ?
            AND workspace_id = ?
            AND deleted = 0
            """,

            (
                now(),
                contact_id,
                user_id,
                workspace_id
            )
        )

        conn.commit()

        return cursor.rowcount

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()

def add_finance_transaction(
    user_id,
    workspace_id,
    transaction_type,
    amount,
    title,
    category_id=None,
    description=None,
    transaction_date=None,
    account_id=None,
    contact_id=None
):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO finance_transactions (
                user_id,
                workspace_id,
                account_id,
                category_id,
                transaction_type,
                amount,
                title,
                description,
                contact_id,
                transaction_date,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                workspace_id,
                account_id,
                category_id,
                transaction_type,
                amount,
                title,
                description or "",
                contact_id,
                transaction_date or today(),
                now()
            )
        )

        conn.commit()
        return cursor.lastrowid

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

    
def get_or_create_finance_category(workspace_id, name):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id FROM finance_categories
            WHERE workspace_id = ?
            AND name = ?
            AND category_type = 'income'
            """,
            (workspace_id, name.strip())
        )

        category = cursor.fetchone()

        if category:
            return category["id"]

        cursor.execute(
            """
            INSERT INTO finance_categories
            (workspace_id, name, category_type, created_at)
            VALUES (?, ?, 'income', ?)
            """,
            (workspace_id, name.strip(), now())
        )

        conn.commit()
        return cursor.lastrowid

    finally:
        conn.close()

def check_finance_columns():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(finance_transactions)")

    columns = cursor.fetchall()

    conn.close()

    return columns
    
# =========================================================
# ACTIVITY LOGS (READ)
# =========================================================

def get_activity_logs(user_id, workspace_id, limit=50):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            SELECT id, action, description, created_at
            FROM activity_logs

            WHERE user_id = ?
            AND (workspace_id = ? OR workspace_id IS NULL)

            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, workspace_id, limit)
        )

        return [
            {
                "id": row["id"],
                "action": row["action"],
                "details": row["description"],
                "created_at": row["created_at"],
            }
            for row in cursor.fetchall()
        ]

    finally:

        conn.close()


# =========================================================
# UPDATE USER NAME
# =========================================================

def update_user_name(user_id, name):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            "UPDATE users SET name = ? WHERE id = ?",
            (name, user_id)
        )

        conn.commit()

    except Exception:

        conn.rollback()
        raise

    finally:


        

        conn.close()
        # =========================================================
# ACTIVITY LOGS (WRITE)
# =========================================================

def log_activity(user_id, workspace_id, action, description=""):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            INSERT INTO activity_logs
            (user_id, workspace_id, action, description, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, workspace_id, action, description, now())
        )

        conn.commit()

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()