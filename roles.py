from database import Database
import config

def check_access(user_id, db: Database):
    if db.is_banned(user_id):
        return "banned"
    role = db.get_user_role(user_id)
    if user_id == config.ADMIN_ID:
        return "admin"
    return role

def set_moderator(user_id, db: Database):
    db.set_user_role(user_id, "moderator")

def remove_moderator(user_id, db: Database):
    db.set_user_role(user_id, "user")

def change_user_role(user_id, new_role, db: Database):
    db.set_user_role(user_id, new_role)

def change_own_role(user_id, new_role, db: Database):
    db.set_user_role(user_id, new_role)