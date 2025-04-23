import logging
import random forgor
import string
import os
from telebot import TeleBot, types
from config import BOT_TOKEN, MEDIA_PATH
from database import Database
from keyboards import *
from languages import get_text
from roles import check_access, set_moderator, remove_moderator, change_user_role, change_own_role

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

bot = TeleBot(BOT_TOKEN)
db = Database("university_bot.db")
user_states = {}
user_context = {}

def update_user_data(bot, db, user_id, message_or_call):
    user = message_or_call.from_user if hasattr(message_or_call, 'from_user') else message_or_call.message.from_user
    db.update_user_info(user_id, tag=f"@{user.username}" if user.username else None, 
                        full_name=f"{user.first_name} {user.last_name or ''}".strip())
    language = db.get_user_language(user_id)
    if not language:
        bot.send_message(message_or_call.chat.id if hasattr(message_or_call, 'chat') else message_or_call.message.chat.id, 
                         get_text("ru", "start_message"), reply_markup=language_keyboard())
        return False
    role = db.get_user_role(user_id)
    if not role:
        db.set_user_role(user_id, "user")
    return True

def send_content(chat_id, content):
    for item in content:
        if isinstance(item, dict) and "text" in item and "media" in item:
            if item["media"].startswith("photo:"):
                bot.send_photo(chat_id, open(f"{MEDIA_PATH}/images/{item['media'][6:]}", "rb"), caption=item["text"])
            elif item["media"].startswith("video:"):
                bot.send_video(chat_id, open(f"{MEDIA_PATH}/videos/{item['media'][6:]}", "rb"), caption=item["text"])
            elif item["media"].startswith("document:"):
                bot.send_document(chat_id, open(f"{MEDIA_PATH}/documents/{item['media'][9:]}", "rb"), caption=item["text"])
        elif isinstance(item, str):
            if item.startswith("photo:"):
                bot.send_photo(chat_id, open(f"{MEDIA_PATH}/images/{item[6:]}", "rb"))
            elif item.startswith("video:"):
                bot.send_video(chat_id, open(f"{MEDIA_PATH}/videos/{item[6:]}", "rb"))
            elif item.startswith("document:"):
                bot.send_document(chat_id, open(f"{MEDIA_PATH}/documents/{item['media'][9:]}", "rb"))
            else:
                bot.send_message(chat."
                else:
                bot.send_message(chat_id, item)

def generate_callback(name):
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"custom_{name.lower().replace(' ', '_')}_{random_suffix}"

def notify_moderators_and_admins(bot, question, username):
    moderators_and_admins = db.get_moderators_and_admins()
    for user_id in moderators_and_admins:
        try:
            bot.send_message(user_id, f"Новый вопрос от @{username}:\n{question}")
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление {user_id}: {e}")

def notify_user(bot, user_id, message):
    try:
        bot.send_message(user_id, message)
    except Exception as e:
        logger.error(f"Не удалось отправить уведомление {user_id}: {e}")

def notify_admins(bot, moderator_id, message):
    admins = db.get_admins()
    for admin_id in admins:
        try:
            moderator_tag = db.get_user_info(moderator_id)[2] or "Неизвестный"
            bot.send_message(admin_id, f"Сообщение от модератора {moderator_tag} (ID: {moderator_id}):\n{message}", 
                             reply_markup=types.InlineKeyboardMarkup().add(
                                 types.InlineKeyboardButton("Ответить", callback_data=f"reply_to_moderator_{moderator_id}")
                             ))
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление админу {admin_id}: {e}")

def register_handlers(bot: TeleBot, db: Database):
    @bot.message_handler(commands=['start'])
    def start(message):
        user_id = message.from_user.id
        if not update_user_data(bot, db, user_id, message):
            return
        access = check_access(user_id, db)
        if access == "banned":
            language = db.get_user_language(user_id) or "ru"
            bot.send_message(message.chat.id, get_text(language, "banned"))
            return
        language = db.get_user_language(user_id)
        custom_buttons, _ = db.get_custom_buttons()
        bot.send_message(message.chat.id, get_text(language, "main_menu"), 
                         reply_markup=main_menu_keyboard(language, access, custom_buttons))

    @bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
    def set_language(call):
        language = call.data.split("_")[1]
        user_id = call.from_user.id
        db.set_user_language(user_id, language)
        if not update_user_data(bot, db, user_id, call):
            return
        access = check_access(user_id, db)
        if access == "banned":
            bot.send_message(call.message.chat.id, get_text(language, "banned"))
            return
        custom_buttons, _ = db.get_custom_buttons()
        bot.send_message(call.message.chat.id, get_text(language, "main_menu"), 
                         reply_markup=main_menu_keyboard(language, access, custom_buttons))
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)

    @bot.callback_query_handler(func=lambda call: True)
    def callback_handler(call):
        user_id = call.from_user.id
        if not update_user_data(bot, db, user_id, call):
            return
        if not db.can_perform_action(user_id):
            language = db.get_user_language(user_id) or "ru"
            bot.send_message(call.message.chat.id, "Подождите 2 секунды перед следующим действием!")
            bot.answer_callback_query(call.id)
            return
        access = check_access(user_id, db)
        if access == "banned":
            language = db.get_user_language(user_id) or "ru"
            bot.send_message(call.message.chat.id, get_text(language, "banned"))
            return
        language = db.get_user_language(user_id)
        custom_buttons, custom_contents = db.get_custom_buttons()

        if call.data == "back_to_main":
            bot.send_message(call.message.chat.id, get_text(language, "main_menu"), 
                             reply_markup=main_menu_keyboard(language, access, custom_buttons))
        elif call.data == "about_college":
            bot.send_message(call.message.chat.id, "О колледже:", reply_markup=about_college_keyboard(language))
        elif call.data == "college_info":
            bot.send_message(call.message.chat.id, "Красноярский колледж радиоэлектроники и информационных технологий\nАдрес: пр. Свободный, 67", 
                             reply_markup=types.InlineKeyboardMarkup().add(back_button(language)))
        elif call.data == "college_media":
            bot.send_message(call.message.chat.id, "Медиа о колледже скоро будет добавлено!", 
                             reply_markup=types.InlineKeyboardMarkup().add(back_button(language)))
        elif call.data == "working_hours":
            schedule = db.get_schedule()
            bot.send_message(call.message.chat.id, "\n".join(schedule), reply_markup=types.InlineKeyboardMarkup().add(back_button(language)))
        elif call.data == "contacts":
            contacts = db.get_contacts()
            bot.send_message(call.message.chat.id, "\n".join(contacts), reply_markup=types.InlineKeyboardMarkup().add(back_button(language)))
        elif call.data == "specialties":
            bot.send_message(call.message.chat.id, "Выберите тип обучения:", reply_markup=specialties_keyboard(language))
        elif call.data == "budget_learning":
            specialties = db.get_specialties()
            budget_specs = [f"{spec[1]} (Бюджетных мест: {spec[3]}) - {spec[2]}" for spec in specialties if spec[3] > 0]
            bot.send_message(call.message.chat.id, "\n\n".join(budget_specs) if budget_specs else "Нет бюджетных мест.", 
                             reply_markup=types.InlineKeyboardMarkup().add(back_button(language)))
        elif call.data == "paid_learning":
            specialties = db.get_specialties()
            paid_specs = [f"{spec[1]} (Платных мест: {spec[4]}) - {spec[2]}" for spec in specialties if spec[4] > 0]
            bot.send_message(call.message.chat.id, "\n\n".join(paid_specs) if paid_specs else "Нет платных мест.", 
                             reply_markup=types.InlineKeyboardMarkup().add(back_button(language)))
        elif call.data == "documents":
            documents = db.get_documents()
            bot.send_message(call.message.chat.id, "\n".join(documents), reply_markup=types.InlineKeyboardMarkup().add(back_button(language)))
        elif call.data == "rules":
            bot.send_message(call.message.chat.id, "Правила приёма: https://kraskrit.ru/priemnaya-komissiya/", 
                             reply_markup=types.InlineKeyboardMarkup().add(back_button(language)))
        elif call.data == "faq":
            categories = db.get_faq_categories(language)
            bot.send_message(call.message.chat.id, "Вопросы и ответы:", reply_markup=faq_keyboard(language, categories))
        elif call.data.startswith("faq_category_"):
            category_id = int(call.data.split("_")[-1])
            faq_items = db.get_faq(language, category_id=category_id)
            bot.send_message(call.message.chat.id, f"Вопросы в категории:", 
                             reply_markup=faq_category_keyboard(faq_items, language, category_id, access))
        elif call.data == "my_questions":
            faq_items = db.get_faq(language, user_id=user_id)
            bot.send_message(call.message.chat.id, "Ваши вопросы:", 
                             reply_markup=faq_category_keyboard(faq_items, language, None, access))
        elif call.data.startswith("faq_view_"):
            faq_id = int(call.data.split("_")[-1])
            faq_items = db.get_faq(language)
            for item in faq_items:
                if item[0] == faq_id:
                    response = f"❓ {item[4]}\n✅ {item[5]}" if item[5] else f"❓ {item[4]}\nОтвета пока нет"
                    bot.send_message(call.message.chat.id, response, reply_markup=types.InlineKeyboardMarkup().add(back_button(language)))
                    break
        elif call.data == "ask_faq_question":
            if not db.can_ask_question(user_id):
                bot.send_message(call.message.chat.id, "Вы можете задавать вопрос не чаще, чем раз в 15 минут!")
                return
            categories = db.get_faq_categories(language)
            if not categories:
                bot.send_message(call.message.chat.id, "Нет доступных категорий. Обратитесь к администратору.")
                return
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            for cat_id, name in categories:
                keyboard.add(types.InlineKeyboardButton(text=name, callback_data=f"select_category_{cat_id}"))
            bot.send_message(call.message.chat.id, "Выберите категорию для вопроса:", reply_markup=keyboard)
        elif call.data.startswith("select_category_"):
            category_id = int(call.data.split("_")[-1])
            user_states[user_id] = {"state": "waiting_for_faq_question", "category_id": category_id}
            bot.send_message(call.message.chat.id, "Введите ваш вопрос:")
        elif call.data.startswith("answer_faq_") and access in ["moderator", "admin"]:
            faq_id = int(call.data.split("_")[-1])
            user_states[user_id] = {"state": "answering_faq", "faq_id": faq_id}
            bot.send_message(call.message.chat.id, "Введите ответ на вопрос:")
        elif call.data.startswith("delete_faq_") and access in ["moderator", "admin"]:
            faq_id = int(call.data.split("_")[-1])
            faq_info = db.get_faq_by_id(faq_id)
            if faq_info:
                user_id_to_notify, question = faq_info
                db.delete_faq(faq_id)
                notify_user(bot, user_id_to_notify, f"Ваш вопрос '{question}' был удалён модератором.")
            category_id = None
            if "category_id" in user_context.get(user_id, {}):
                category_id = user_context[user_id]["category_id"]
            faq_items = db.get_faq(language, category_id=category_id) if category_id else db.get_faq(language, user_id=user_id)
            bot.send_message(call.message.chat.id, "Вопрос удалён!", 
                             reply_markup=faq_category_keyboard(faq_items, language, category_id, access))
        elif call.data == "leave_review":
            if db.can_leave_review(user_id):
                bot.send_message(call.message.chat.id, "Введите ваш отзыв:")
                user_states[user_id] = "waiting_for_review"
            else:
                bot.send_message(call.message.chat.id, "Вы можете оставить отзыв раз в день!")
        elif call.data == "view_reviews":
            reviews = db.get_reviews()
            bot.send_message(call.message.chat.id, "\n".join([f"{i+1}. {r[2]}" for i, r in enumerate(reviews)]) or "Нет отзывов", 
                             reply_markup=types.InlineKeyboardMarkup().add(back_button(language)))
        elif call.data == "moderator_menu" and access in ["moderator", "admin"]:
            bot.send_message(call.message.chat.id, get_text(language, "moderator_menu"), reply_markup=moderator_menu_keyboard(language))
        elif call.data == "admin_menu" and access == "admin":
            bot.send_message(call.message.chat.id, get_text(language, "admin_menu"), reply_markup=admin_menu_keyboard(language))
        elif call.data == "users_and_moderators" and access in ["moderator", "admin"]:
            users = db.get_all_users()
            bot.send_message(call.message.chat.id, "Список пользователей и модераторов:", 
                             reply_markup=users_and_moderators_keyboard(users, language))
        elif call.data.startswith("user_info_") and access in ["moderator", "admin"]:
            target_id = int(call.data.split("_")[-1])
            user_info = db.get_user_info(target_id)
            if user_info:
                user_id, role, tag, full_name, lang, is_banned = user_info
                info_text = (
                    f"ID: {user_id}\n"
                    f"Тег: {tag or 'Не указан'}\n"
                    f"Имя: {full_name or 'Не указано'}\n"
                    f"Роль: {role}\n"
                    f"Язык: {lang}\n"
                    f"Забанен: {'Да' if is_banned else 'Нет'}"
                )
                bot.send_message(call.message.chat.id, info_text, reply_markup=types.InlineKeyboardMarkup().add(back_button(language)))
            else:
                bot.send_message(call.message.chat.id, "Пользователь не найден!", 
                                 reply_markup=types.InlineKeyboardMarkup().add(back_button(language)))
        elif call.data == "ban_user" and access == "admin":
            bot.send_message(call.message.chat.id, "Введите ID пользователя для бана:")
            user_states[user_id] = "waiting_for_ban"
        elif call.data == "unban_user" and access == "admin":
            bot.send_message(call.message.chat.id, "Введите ID пользователя для разбана:")
            user_states[user_id] = "waiting_for_unban"
        elif call.data == "add_moderator" and access == "admin":
            bot.send_message(call.message.chat.id, "Введите ID или тег (@username) пользователя для назначения модератором:")
            user_states[user_id] = "waiting_for_add_moderator"
        elif call.data == "remove_moderator" and access == "admin":
            bot.send_message(call.message.chat.id, "Введите ID модератора для удаления:")
            user_states[user_id] = "waiting_for_remove_moderator"
        elif call.data == "change_user_role" and access == "admin":
            bot.send_message(call.message.chat.id, "Введите ID пользователя для изменения роли:")
            user_states[user_id] = "waiting_for_change_user_role"
        elif call.data == "change_own_role" and access in ["moderator", "admin"]:
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            keyboard.add(types.InlineKeyboardButton("Пользователь", callback_data="set_own_role_user"))
            keyboard.add(types.InlineKeyboardButton("Модератор", callback_data="set_own_role_moderator"))
            if access == "admin":
                keyboard.add(types.InlineKeyboardButton("Администратор", callback_data="set_own_role_admin"))
            bot.send_message(call.message.chat.id, "Выберите новую роль:", reply_markup=keyboard)
        elif call.data in ["set_own_role_user", "set_own_role_moderator", "set_own_role_admin"]:
            new_role = {"set_own_role_user": "user", "set_own_role_moderator": "moderator", "set_own_role_admin": "admin"}[call.data]
            change_own_role(user_id, new_role, db)
            bot.send_message(call.message.chat.id, f"Ваша роль изменена на {new_role}!", 
                             reply_markup=main_menu_keyboard(language, new_role, custom_buttons))
        elif call.data.startswith("set_role_") and access == "admin":
            parts = call.data.split("_")
            target_id = int(parts[2])
            new_role = parts[3]
            change_user_role(target_id, new_role, db)
            bot.send_message(call.message.chat.id, f"Роль пользователя с ID {target_id} изменена на {new_role}!", 
                             reply_markup=admin_menu_keyboard(language))
        elif call.data == "edit_content" and access in ["moderator", "admin"]:
            bot.send_message(call.message.chat.id, "Редактировать контент:", reply_markup=edit_content_keyboard(language, custom_buttons))
        elif call.data == "edit_working_hours" and access in ["moderator", "admin"]:
            bot.send_message(call.message.chat.id, "Введите новый график работы (каждый пункт с новой строки):")
            user_states[user_id] = "edit_working_hours"
        elif call.data == "edit_contacts" and access in ["moderator", "admin"]:
            bot.send_message(call.message.chat.id, "Введите новые контакты (каждый пункт с новой строки):")
            user_states[user_id] = "edit_contacts"
        elif call.data == "edit_documents" and access in ["moderator", "admin"]:
            bot.send_message(call.message.chat.id, "Введите новый список документов (каждый пункт с новой строки):")
            user_states[user_id] = "edit_documents"
        elif call.data == "add_custom_button" and access in ["moderator", "admin"]:
            bot.send_message(call.message.chat.id, "Введите название новой кнопки:")
            user_states[user_id] = "waiting_for_custom_button_name"
        elif call.data.startswith("edit_") and access in ["moderator", "admin"]:
            callback = call.data[5:]
            bot.send_message(call.message.chat.id, f"Введите содержимое для кнопки (текст, фото, видео, документ):")
            user_states[user_id] = {"state": "editing_custom_content", "callback": callback, "content": []}
        elif call.data.startswith("delete_") and access in ["moderator", "admin"]:
            callback = call.data[7:]
            db.delete_custom_button(callback)
            custom_buttons, _ = db.get_custom_buttons()
            bot.send_message(call.message.chat.id, "Кнопка удалена!", reply_markup=edit_content_keyboard(language, custom_buttons))
        elif call.data == "add_faq_category" and access in ["moderator", "admin"]:
            bot.send_message(call.message.chat.id, "Введите название новой категории FAQ:")
            user_states[user_id] = "waiting_for_faq_category"
        elif call.data in custom_contents:
            send_content(call.message.chat.id, custom_contents[call.data])
            if access in ["moderator", "admin"]:
                bot.send_message(call.message.chat.id, "Вернуться:", reply_markup=types.InlineKeyboardMarkup().add(back_button(language)))
        elif call.data == "finish_content" and access in ["moderator", "admin"]:
            if isinstance(user_states.get(user_id), dict) and "content" in user_states[user_id]:
                state = user_states[user_id]
                if state["state"] == "adding_custom_content":
                    db.add_custom_button(state["name"], state["callback"], state["content"])
                    custom_buttons, _ = db.get_custom_buttons()
                    bot.send_message(call.message.chat.id, "Кнопка добавлена!", reply_markup=edit_content_keyboard(language, custom_buttons))
                elif state["state"] == "editing_custom_content":
                    db.update_custom_button(state["callback"], state["content"])
                    bot.send_message(call.message.chat.id, "Содержимое обновлено!", reply_markup=edit_content_keyboard(language, custom_buttons))
                user_states.pop(user_id)
        elif call.data == "continue_content" and access in ["moderator", "admin"]:
            if isinstance(user_states.get(user_id), dict):
                bot.send_message(call.message.chat.id, "Продолжайте вводить содержимое (текст, фото, видео, документ):")
        elif call.data == "change_language":
            bot.send_message(call.message.chat.id, get_text(language, "change_language"), reply_markup=language_keyboard())
        elif call.data == "message_to_admin" and access == "moderator":
            bot.send_message(call.message.chat.id, "Введите сообщение для администратора:")
            user_states[user_id] = "waiting_for_message_to_admin"
        elif call.data.startswith("reply_to_moderator_") and access == "admin":
            moderator_id = int(call.data.split("_")[-1])
            user_states[user_id] = {"state": "replying_to_moderator", "moderator_id": moderator_id}
            bot.send_message(call.message.chat.id, "Введите ответ модератору:")

        bot.answer_callback_query(call.id)

    @bot.message_handler(content_types=['text'])
    def handle_text(message):
        user_id = message.from_user.id
        if not update_user_data(bot, db, user_id, message):
            return
        if not db.can_perform_action(user_id):
            language = db.get_user_language(user_id) or "ru"
            bot.send_message(message.chat.id, "Подождите 2 секунды перед следующим действием!")
            return
        language = db.get_user_language(user_id)
        state = user_states.get(user_id)
        access = check_access(user_id, db)
        custom_buttons, _ = db.get_custom_buttons()

        if isinstance(state, dict):
            if state["state"] == "waiting_for_faq_question":
                category_id = state["category_id"]
                db.add_faq_question(user_id, message.from_user.username or "unknown", category_id, message.text, language)
                notify_moderators_and_admins(bot, message.text, message.from_user.username or "unknown")
                bot.send_message(message.chat.id, "Вопрос отправлен модераторам!", 
                                 reply_markup=main_menu_keyboard(language, access, custom_buttons))
                user_states.pop(user_id)
            elif state["state"] == "answering_faq" and access in ["moderator", "admin"]:
                faq_id = state["faq_id"]
                faq_info = db.get_faq_by_id(faq_id)
                if faq_info:
                    user_id_to_notify, question = faq_info
                    db.answer_faq(faq_id, message.text)
                    notify_user(bot, user_id_to_notify, f"На ваш вопрос '{question}' добавлен ответ:\n{message.text}")
                bot.send_message(message.chat.id, "Ответ сохранён!", 
                                 reply_markup=moderator_menu_keyboard(language) if access == "moderator" else admin_menu_keyboard(language))
                user_states.pop(user_id)
            elif state["state"] == "waiting_for_message_to_admin" and access == "moderator":
                notify_admins(bot, user_id, message.text)
                bot.send_message(message.chat.id, "Сообщение отправлено администратору!", 
                                 reply_markup=moderator_menu_keyboard(language))
                user_states.pop(user_id)
            elif state["state"] == "replying_to_moderator" and access == "admin":
                moderator_id = state["moderator_id"]
                notify_user(bot, moderator_id, f"Ответ от администратора:\n{message.text}")
                bot.send_message(message.chat.id, "Ответ отправлен модератору!", reply_markup=admin_menu_keyboard(language))
                user_states.pop(user_id)
            elif state["state"] in ["editing_custom_content", "adding_custom_content"] and access in ["moderator", "admin"]:
                state["content"].append(message.text)
                bot.send_message(message.chat.id, "Закончили ввод?", reply_markup=finish_or_continue_keyboard(language))
        elif isinstance(state, str):
            if state == "waiting_for_review":
                db.add_review(user_id, message.text)
                bot.send_message(message.chat.id, "Отзыв сохранён!", reply_markup=main_menu_keyboard(language, access, custom_buttons))
                user_states.pop(user_id)
            elif state == "waiting_for_ban" and access == "admin":
                try:
                    target_id = int(message.text)
                    db.ban_user(target_id)
                    bot.send_message(message.chat.id, "Пользователь забанен!", reply_markup=admin_menu_keyboard(language))
                except ValueError:
                    bot.send_message(message.chat.id, "Некорректный ID!")
                user_states.pop(user_id)
            elif state == "waiting_for_unban" and access == "admin":
                try:
                    target_id = int(message.text)
                    db.unban_user(target_id)
                    bot.send_message(message.chat.id, "Пользователь разбанен!", reply_markup=admin_menu_keyboard(language))
                except ValueError:
                    bot.send_message(message.chat.id, "Некорректный ID!")
                user_states.pop(user_id)
            elif state == "waiting_for_add_moderator" and access == "admin":
                input_text = message.text.strip()
                if input_text.startswith("@"):
                    user = db.get_user_by_tag(input_text)
                    if user:
                        target_id = user[0]
                        set_moderator(target_id, db)
                        bot.send_message(message.chat.id, f"Пользователь {input_text} назначен модератором!", 
                                         reply_markup=admin_menu_keyboard(language))
                    else:
                        bot.send_message(message.chat.id, "Пользователь с таким тегом не найден! Убедитесь, что он взаимодействовал с ботом.")
                else:
                    try:
                        target_id = int(input_text)
                        set_moderator(target_id, db)
                        bot.send_message(message.chat.id, "Модератор добавлен!", reply_markup=admin_menu_keyboard(language))
                    except ValueError:
                        bot.send_message(message.chat.id, "Некорректный ID или тег!")
                user_states.pop(user_id)
            elif state == "waiting_for_remove_moderator" and access == "admin":
                try:
                    target_id = int(message.text)
                    remove_moderator(target_id, db)
                    bot.send_message(message.chat.id, "Модератор удалён!", reply_markup=admin_menu_keyboard(language))
                except ValueError:
                    bot.send_message(message.chat.id, "Некорректный ID!")
                user_states.pop(user_id)
            elif state == "waiting_for_change_user_role" and access == "admin":
                try:
                    target_id = int(message.text)
                    if db.get_user_info(target_id):
                        keyboard = types.InlineKeyboardMarkup(row_width=1)
                        keyboard.add(types.InlineKeyboardButton("Пользователь", callback_data=f"set_role_{target_id}_user"))
                        keyboard.add(types.InlineKeyboardButton("Модератор", callback_data=f"set_role_{target_id}_moderator"))
                        keyboard.add(types.InlineKeyboardButton("Администратор", callback_data=f"set_role_{target_id}_admin"))
                        bot.send_message(message.chat.id, "Выберите роль:", reply_markup=keyboard)
                    else:
                        bot.send_message(message.chat.id, "Пользователь с таким ID не найден!")
                except ValueError:
                    bot.send_message(message.chat.id, "Некорректный ID!")
                user_states.pop(user_id)
            elif state == "edit_working_hours" and access in ["moderator", "admin"]:
                if message.text:
                    db.update_schedule(message.text)
                    bot.send_message(message.chat.id, "График обновлён!", 
                                     reply_markup=moderator_menu_keyboard(language) if access == "moderator" else admin_menu_keyboard(language))
                else:
                    bot.send_message(message.chat.id, "Пожалуйста, введите текст графика!")
                user_states.pop(user_id)
            elif state == "edit_contacts" and access in ["moderator", "admin"]:
                if message.text:
                    db.update_contacts(message.text)
                    bot.send_message(message.chat.id, "Контакты обновлены!", 
                                     reply_markup=moderator_menu_keyboard(language) if access == "moderator" else admin_menu_keyboard(language))
                else:
                    bot.send_message(message.chat.id, "Пожалуйста, введите текст контактов!")
                user_states.pop(user_id)
            elif state == "edit_documents" and access in ["moderator", "admin"]:
                if message.text:
                    db.update_documents(message.text)
                    bot.send_message(message.chat.id, "Документы обновлены!", 
                                     reply_markup=moderator_menu_keyboard(language) if access == "moderator" else admin_menu_keyboard(language))
                else:
                    bot.send_message(message.chat.id, "Пожалуйста, введите текст документов!")
                user_states.pop(user_id)
            elif state == "waiting_for_custom_button_name" and access in ["moderator", "admin"]:
                callback = generate_callback(message.text)
                user_states[user_id] = {"state": "adding_custom_content", "name": message.text, "callback": callback, "content": []}
                bot.send_message(message.chat.id, "Введите содержимое (текст, фото, видео, документ):")
            elif state == "waiting_for_faq_category" and access in ["moderator", "admin"]:
                db.add_faq_category(message.text, language)
                bot.send_message(message.chat.id, "Категория добавлена!", 
                                 reply_markup=moderator_menu_keyboard(language) if access == "moderator" else admin_menu_keyboard(language))
                user_states.pop(user_id)

    @bot.message_handler(content_types=['photo', 'video', 'document'])
    def handle_media(message):
        user_id = message.from_user.id
        if not update_user_data(bot, db, user_id, message):
            return
        if not db.can_perform_action(user_id):
            language = db.get_user_language(user_id) or "ru"
            bot.send_message(message.chat.id, "Подождите 2 секунды перед следующим действием!")
            return
        language = db.get_user_language(user_id)
        state = user_states.get(user_id)
        access = check_access(user_id, db)

        if isinstance(state, dict) and (state["state"] == "editing_custom_content" or state["state"] == "adding_custom_content"):
            if message.content_type == "photo":
                file_id = message.photo[-1].file_id ape
                file_path = bot.get_file(file_id).file_path
                downloaded_file = bot.download_file(file_path)
                file_name = f"image_{file_id}.jpg"
                with open(f"{MEDIA_PATH}/images/{file_name}", "wb") as f:
                    f.write(downloaded_file)
                if state["content"] and isinstance(state["content"][-1], str) and not state["content"][-1].startswith(("photo:", "video:", "document:")):
                    state["content"][-1] = {"text": state["content"][-1], "media": f"photo:{file_name}"}
                else:
                    state["content"].append(f"photo:{file_name}")
            elif message.content_type == "video":
                file_id = message.video.file_id
                file_path = bot.get_file(file_id).file_path
                downloaded_file = bot.download_file(file_path)
                file_name = f"video_{file_id}.mp4"
                with open(f"{MEDIA_PATH}/videos/{file_name}", "wb") as f:
                    f.write(downloaded_file)
                if state["content"] and isinstance(state["content"][-1], str) and not state["content"][-1].startswith(("photo:", "video:", "document:")):
                    state["content"][-1] = {"text": state["content"][-1], "media": f"video:{file_name}"}
                else:
                    state["content"].append(f"video:{file_name}")
            elif message.content_type == "document":
                file_id = message.document.file_id
                file_path = bot.get_file(file_id).file_path
                downloaded_file = bot.download_file(file_path)
                file_name = f"doc_{file_id}"
                with open(f"{MEDIA_PATH}/documents/{file_name}", "wb") as f:
                    f.write(downloaded_file)
                if state["content"] and isinstance(state["content"][-1], str) and not state["content"][-1].startswith(("photo:", "video:", "document:")):
                    state["content"][-1] = {"text": state["content"][-1], "media": f"document:{file_name}"}
                else:
                    state["content"].append(f"document:{file_name}")
            bot.send_message(message.chat.id, "Закончили ввод?", reply_markup=finish_or_continue_keyboard(language))
            user_states[user_id] = state
        elif state in ["edit_working_hours", "edit_contacts", "edit_documents"]:
            bot.send_message(message.chat.id, "Пожалуйста, отправьте текстовое сообщение, а не медиа!")