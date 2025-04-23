import sqlite3
import os
from datetime import datetime
from data import specialties_data, schedule_data, contacts_data, documents_data, faq_categories_data
from config import MEDIA_PATH

class Database:
    def __init__(self, db_name):
        self.db_name = db_name
        self.create_tables()
        if not os.path.exists(MEDIA_PATH):
            os.makedirs(f"{MEDIA_PATH}/images")
            os.makedirs(f"{MEDIA_PATH}/videos")
            os.makedirs(f"{MEDIA_PATH}/documents")

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def create_tables(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY, 
                language TEXT DEFAULT 'ru', 
                role TEXT DEFAULT 'user', 
                is_banned INTEGER DEFAULT 0, 
                last_action_time TEXT, 
                tag TEXT, 
                full_name TEXT,
                last_question_time TEXT  -- Добавлено для отслеживания времени последнего вопроса
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS specialties (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                name TEXT NOT NULL, 
                description TEXT, 
                budget_seats INTEGER, 
                paid_seats INTEGER
            )
        """)
        cursor.execute("CREATE TABLE IF NOT EXISTS schedule (id INTEGER PRIMARY KEY AUTOINCREMENT, description TEXT NOT NULL)")
        cursor.execute("CREATE TABLE IF NOT EXISTS contacts (id INTEGER PRIMARY KEY AUTOINCREMENT, description TEXT NOT NULL)")
        cursor.execute("CREATE TABLE IF NOT EXISTS documents (id INTEGER PRIMARY KEY AUTOINCREMENT, description TEXT NOT NULL)")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS faq_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                name TEXT NOT NULL, 
                language TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS faq (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                user_id INTEGER, 
                username TEXT, 
                category_id INTEGER, 
                question TEXT NOT NULL, 
                answer TEXT, 
                language TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS custom_buttons (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                name TEXT NOT NULL, 
                callback TEXT NOT NULL, 
                content TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                user_id INTEGER, 
                review TEXT, 
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("SELECT COUNT(*) FROM specialties")
        if cursor.fetchone()[0] == 0:
            for spec in specialties_data:
                cursor.execute("INSERT INTO specialties (name, description, budget_seats, paid_seats) VALUES (?, ?, ?, ?)", 
                               (spec["name"], spec["description"], spec["budget_seats"], spec["paid_seats"]))
        cursor.execute("SELECT COUNT(*) FROM schedule")
        if cursor.fetchone()[0] == 0:
            for sch in schedule_data:
                cursor.execute("INSERT INTO schedule (description) VALUES (?)", (sch,))
        cursor.execute("SELECT COUNT(*) FROM contacts")
        if cursor.fetchone()[0] == 0:
            for contact in contacts_data:
                cursor.execute("INSERT INTO contacts (description) VALUES (?)", (contact,))
        cursor.execute("SELECT COUNT(*) FROM documents")
        if cursor.fetchone()[0] == 0:
            for doc in documents_data:
                cursor.execute("INSERT INTO documents (description) VALUES (?)", (doc,))
        cursor.execute("SELECT COUNT(*) FROM faq_categories")
        if cursor.fetchone()[0] == 0:
            for cat in faq_categories_data:
                cursor.execute("INSERT INTO faq_categories (name, language) VALUES (?, ?)", (cat["name"], cat["language"]))

        conn.commit()
        conn.close()

    def update_user_info(self, user_id, tag=None, full_name=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO users (user_id, tag, full_name, language, role, is_banned, last_action_time, last_question_time)
            VALUES (?, ?, ?, COALESCE((SELECT language FROM users WHERE user_id = ?), 'ru'), 
                    COALESCE((SELECT role FROM users WHERE user_id = ?), 'user'), 
                    COALESCE((SELECT is_banned FROM users WHERE user_id = ?), 0), 
                    (SELECT last_action_time FROM users WHERE user_id = ?),
                    (SELECT last_question_time FROM users WHERE user_id = ?))
        """, (user_id, tag, full_name, user_id, user_id, user_id, user_id, user_id))
        conn.commit()
        conn.close()

    def get_user_language(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def set_user_language(self, user_id, language):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO users (user_id, language) VALUES (?, ?)", (user_id, language))
        conn.commit()
        conn.close()

    def get_user_role(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else "user"

    def set_user_role(self, user_id, role):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO users (user_id, role, language, tag, full_name, last_question_time)
            VALUES (?, ?, (SELECT language FROM users WHERE user_id = ?), 
                    (SELECT tag FROM users WHERE user_id = ?), 
                    (SELECT full_name FROM users WHERE user_id = ?),
                    (SELECT last_question_time FROM users WHERE user_id = ?))
        """, (user_id, role, user_id, user_id, user_id, user_id))
        conn.commit()
        conn.close()

    def is_banned(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT is_banned FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        return bool(result[0]) if result else False

    def ban_user(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()

    def unban_user(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()

    def can_perform_action(self, user_id, cooldown=2):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT last_action_time FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        if result and result[0]:
            last_time = datetime.fromisoformat(result[0])
            if (datetime.now() - last_time).total_seconds() < cooldown:
                return False
        cursor.execute("UPDATE users SET last_action_time = ? WHERE user_id = ?", (datetime.now().isoformat(), user_id))
        if cursor.rowcount == 0:
            cursor.execute("INSERT INTO users (user_id, last_action_time) VALUES (?, ?)", (user_id, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return True

    def can_ask_question(self, user_id, cooldown=900):  # 15 минут = 900 секунд
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT last_question_time FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        if result and result[0]:
            last_time = datetime.fromisoformat(result[0])
            if (datetime.now() - last_time).total_seconds() < cooldown:
                return False
        cursor.execute("UPDATE users SET last_question_time = ? WHERE user_id = ?", (datetime.now().isoformat(), user_id))
        if cursor.rowcount == 0:
            cursor.execute("INSERT INTO users (user_id, last_question_time) VALUES (?, ?)", (user_id, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return True

    def get_all_users(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, role, tag, full_name FROM users")
        result = cursor.fetchall()
        conn.close()
        return result

    def get_user_by_tag(self, tag):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, role, tag, full_name FROM users WHERE tag = ?", (tag,))
        result = cursor.fetchone()
        conn.close()
        return result

    def get_user_info(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, role, tag, full_name, language, is_banned FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result

    def get_moderators_and_admins(self):  # Новая функция для получения модераторов и админов
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE role IN ('moderator', 'admin') AND is_banned = 0")
        result = cursor.fetchall()
        conn.close()
        return [row[0] for row in result]

    def get_admins(self):  # Новая функция для получения только админов
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE role = 'admin' AND is_banned = 0")
        result = cursor.fetchall()
        conn.close()
        return [row[0] for row in result]

    def get_specialties(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM specialties")
        result = cursor.fetchall()
        conn.close()
        return result

    def get_schedule(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT description FROM schedule")
        result = cursor.fetchall()
        conn.close()
        return [r[0] for r in result]

    def update_schedule(self, new_schedule):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM schedule")
        for desc in new_schedule.split("\n"):
            if desc.strip():
                cursor.execute("INSERT INTO schedule (description) VALUES (?)", (desc.strip(),))
        conn.commit()
        conn.close()

    def get_contacts(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT description FROM contacts")
        result = cursor.fetchall()
        conn.close()
        return [r[0] for r in result]

    def update_contacts(self, new_contacts):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM contacts")
        for desc in new_contacts.split("\n"):
            if desc.strip():
                cursor.execute("INSERT INTO contacts (description) VALUES (?)", (desc.strip(),))
        conn.commit()
        conn.close()

    def get_documents(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT description FROM documents")
        result = cursor.fetchall()
        conn.close()
        return [r[0] for r in result]

    def update_documents(self, new_documents):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM documents")
        for desc in new_documents.split("\n"):
            if desc.strip():
                cursor.execute("INSERT INTO documents (description) VALUES (?)", (desc.strip(),))
        conn.commit()
        conn.close()

    def add_faq_category(self, name, language):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO faq_categories (name, language) VALUES (?, ?)", (name, language))
        conn.commit()
        conn.close()

    def get_faq_categories(self, language):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM faq_categories WHERE language = ?", (language,))
        result = cursor.fetchall()
        conn.close()
        return result

    def add_faq_question(self, user_id, username, category_id, question, language):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO faq (user_id, username, category_id, question, language) 
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, username, category_id, question, language))
        conn.commit()
        conn.close()

    def get_faq(self, language, category_id=None, user_id=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        if user_id:
            cursor.execute("""
                SELECT id, user_id, username, category_id, question, answer 
                FROM faq 
                WHERE user_id = ? AND language = ?
            """, (user_id, language))
        elif category_id:
            cursor.execute("""
                SELECT id, user_id, username, category_id, question, answer 
                FROM faq 
                WHERE category_id = ? AND language = ?
            """, (category_id, language))
        else:
            cursor.execute("""
                SELECT id, user_id, username, category_id, question, answer 
                FROM faq 
                WHERE language = ?
            """, (language,))
        result = cursor.fetchall()
        conn.close()
        return result

    def get_faq_by_id(self, faq_id):  # Новая функция для получения вопроса по ID
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, question FROM faq WHERE id = ?", (faq_id,))
        result = cursor.fetchone()
        conn.close()
        return result

    def answer_faq(self, faq_id, answer):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE faq SET answer = ? WHERE id = ?", (answer, faq_id))
        conn.commit()
        conn.close()

    def delete_faq(self, faq_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM faq WHERE id = ?", (faq_id,))
        conn.commit()
        conn.close()

    def add_custom_button(self, name, callback, content):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO custom_buttons (name, callback, content) VALUES (?, ?, ?)", (name, callback, str(content)))
        conn.commit()
        conn.close()

    def get_custom_buttons(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, callback, content FROM custom_buttons")
        result = cursor.fetchall()
        conn.close()
        buttons = {row[0]: row[1] for row in result}
        contents = {row[1]: eval(row[2]) for row in result}
        return buttons, contents

    def update_custom_button(self, callback, content):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE custom_buttons SET content = ? WHERE callback = ?", (str(content), callback))
        conn.commit()
        conn.close()

    def delete_custom_button(self, callback):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM custom_buttons WHERE callback = ?", (callback,))
        conn.commit()
        conn.close()

    def add_review(self, user_id, review):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO reviews (user_id, review) VALUES (?, ?)", (user_id, review))
        conn.commit()
        conn.close()

    def get_reviews(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, user_id, review, timestamp FROM reviews")
        result = cursor.fetchall()
        conn.close()
        return result

    def delete_review(self, review_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
        conn.commit()
        conn.close()

    def can_leave_review(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp FROM reviews WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1", (user_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            last_time = datetime.fromisoformat(result[0])
            return (datetime.now() - last_time).total_seconds() >= 86400  # 1 день
        return True