import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import config

class Database:
    def __init__(self, db_path: str = config.DATABASE_PATH):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Keys table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_value TEXT NOT NULL,
                category_id TEXT NOT NULL,
                status TEXT DEFAULT 'available',
                user_id INTEGER,
                issued_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Purchases table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                key_id INTEGER NOT NULL,
                category_id TEXT NOT NULL,
                amount REAL NOT NULL,
                payment_id TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (key_id) REFERENCES keys(id)
            )
        """)

        conn.commit()
        conn.close()

    def add_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None):
        """Add or update user"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, created_at)
            VALUES (?, ?, ?, ?, COALESCE((SELECT created_at FROM users WHERE user_id = ?), CURRENT_TIMESTAMP))
        """, (user_id, username, first_name, last_name, user_id))

        conn.commit()
        conn.close()

    def add_keys(self, keys: List[str], category_id: str) -> int:
        """Add multiple keys to database"""
        conn = self.get_connection()
        cursor = conn.cursor()

        added_count = 0
        for key in keys:
            key = key.strip()
            if key:
                cursor.execute("""
                    INSERT INTO keys (key_value, category_id, status)
                    VALUES (?, ?, 'available')
                """, (key, category_id))
                added_count += 1

        conn.commit()
        conn.close()
        return added_count

    def get_available_keys_count(self, category_id: str) -> int:
        """Get count of available keys for category"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM keys
            WHERE category_id = ? AND status = 'available'
        """, (category_id,))
        count = cursor.fetchone()[0]

        conn.close()
        return count

    def get_all_categories_count(self) -> Dict[str, int]:
        """Get available keys count for all categories"""
        conn = self.get_connection()
        cursor = conn.cursor()

        counts = {}
        for cat_id in config.CATEGORIES:
            cursor.execute("""
                SELECT COUNT(*) FROM keys
                WHERE category_id = ? AND status = 'available'
            """, (cat_id,))
            counts[cat_id] = cursor.fetchone()[0]

        conn.close()
        return counts

    def get_available_key(self, category_id: str) -> Optional[Dict]:
        """Get one available key from category"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, key_value FROM keys
            WHERE category_id = ? AND status = 'available'
            LIMIT 1
        """, (category_id,))
        result = cursor.fetchone()

        conn.close()

        if result:
            return {"id": result[0], "key_value": result[1]}
        return None

    def issue_key(self, key_id: int, user_id: int):
        """Mark key as issued to user"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE keys
            SET status = 'issued', user_id = ?, issued_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id, key_id))

        conn.commit()
        conn.close()

    def get_user_keys(self, user_id: int) -> List[Dict]:
        """Get all keys issued to user"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT k.key_value, k.category_id, k.issued_at
            FROM keys k
            WHERE k.user_id = ? AND k.status = 'issued'
            ORDER BY k.issued_at DESC
        """, (user_id,))

        keys = []
        for row in cursor.fetchall():
            category_name = config.CATEGORIES.get(row[1], {}).get("name", row[1])
            keys.append({
                "key_value": row[0],
                "category_id": row[1],
                "category_name": category_name,
                "issued_at": row[2]
            })

        conn.close()
        return keys

    def create_purchase(self, user_id: int, key_id: int, category_id: str, amount: float, payment_id: str = None) -> int:
        """Create purchase record"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO purchases (user_id, key_id, category_id, amount, payment_id, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
        """, (user_id, key_id, category_id, amount, payment_id))

        purchase_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return purchase_id

    def complete_purchase(self, purchase_id: int):
        """Mark purchase as completed"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE purchases
            SET status = 'completed', completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (purchase_id,))

        conn.commit()
        conn.close()

    def get_purchase_by_payment_id(self, payment_id: str) -> Optional[Dict]:
        """Get purchase by payment ID"""
        conn = self.get_connection()
        cursor = cursor = conn.cursor()

        cursor.execute("""
            SELECT id, user_id, key_id, category_id, amount, status
            FROM purchases
            WHERE payment_id = ?
        """, (payment_id,))
        result = cursor.fetchone()

        conn.close()

        if result:
            return {
                "id": result[0],
                "user_id": result[1],
                "key_id": result[2],
                "category_id": result[3],
                "amount": result[4],
                "status": result[5]
            }
        return None

    def get_admin_stats(self) -> Dict:
        """Get statistics for admin panel"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Total keys by category
        cursor.execute("""
            SELECT category_id, COUNT(*) FROM keys GROUP BY category_id
        """)
        total_keys = {row[0]: row[1] for row in cursor.fetchall()}

        # Available keys by category
        cursor.execute("""
            SELECT category_id, COUNT(*) FROM keys WHERE status = 'available' GROUP BY category_id
        """)
        available_keys = {row[0]: row[1] for row in cursor.fetchall()}

        # Total users
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        # Total purchases
        cursor.execute("SELECT COUNT(*) FROM purchases WHERE status = 'completed'")
        total_purchases = cursor.fetchone()[0]

        # Total revenue
        cursor.execute("SELECT SUM(amount) FROM purchases WHERE status = 'completed'")
        total_revenue = cursor.fetchone()[0] or 0

        conn.close()

        return {
            "total_keys": total_keys,
            "available_keys": available_keys,
            "total_users": total_users,
            "total_purchases": total_purchases,
            "total_revenue": total_revenue
        }

    def get_all_keys_by_category(self, category_id: str, status: str = None) -> List[Dict]:
        """Get all keys in a category, optionally filtered by status"""
        conn = self.get_connection()
        cursor = conn.cursor()

        if status:
            cursor.execute("""
                SELECT id, key_value, status, created_at
                FROM keys
                WHERE category_id = ? AND status = ?
                ORDER BY created_at DESC
            """, (category_id, status))
        else:
            cursor.execute("""
                SELECT id, key_value, status, created_at
                FROM keys
                WHERE category_id = ?
                ORDER BY created_at DESC
            """, (category_id,))

        keys = []
        for row in cursor.fetchall():
            keys.append({
                "id": row[0],
                "key_value": row[1],
                "status": row[2],
                "created_at": row[3]
            })

        conn.close()
        return keys

    def delete_key_by_id(self, key_id: int) -> bool:
        """Delete a key by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM keys WHERE id = ?", (key_id,))
        deleted = cursor.rowcount > 0

        conn.commit()
        conn.close()
        return deleted

    def delete_keys_by_category(self, category_id: str, status: str = None) -> int:
        """Delete all keys in a category, optionally filtered by status"""
        conn = self.get_connection()
        cursor = conn.cursor()

        if status:
            cursor.execute("DELETE FROM keys WHERE category_id = ? AND status = ?", (category_id, status))
        else:
            cursor.execute("DELETE FROM keys WHERE category_id = ?", (category_id,))

        deleted_count = cursor.rowcount

        conn.commit()
        conn.close()
        return deleted_count

    def search_key_by_value(self, key_value: str) -> Optional[Dict]:
        """Search for a key by its value"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, key_value, category_id, status, created_at
            FROM keys
            WHERE key_value = ?
        """, (key_value,))
        result = cursor.fetchone()

        conn.close()

        if result:
            return {
                "id": result[0],
                "key_value": result[1],
                "category_id": result[2],
                "status": result[3],
                "created_at": result[4]
            }
        return None
