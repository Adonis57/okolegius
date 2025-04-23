from telebot import types
from languages import TEXT

def language_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"))
    keyboard.add(types.InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en"))
    keyboard.add(types.InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="lang_uz"))
    keyboard.add(types.InlineKeyboardButton(text="🇰🇬 Кыргызча", callback_data="lang_ky"))
    keyboard.add(types.InlineKeyboardButton(text="🇹🇯 Тоҷикӣ", callback_data="lang_tg"))
    return keyboard

def main_menu_keyboard(language, role, custom_buttons):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton(text="🏫 " + TEXT[language]["about_college"], callback_data="about_college"))
    keyboard.add(types.InlineKeyboardButton(text="⏱️ " + TEXT[language]["working_hours"], callback_data="working_hours"))
    keyboard.add(types.InlineKeyboardButton(text="📞 " + TEXT[language]["contacts"], callback_data="contacts"))
    keyboard.add(types.InlineKeyboardButton(text="📚 " + TEXT[language]["specialties"], callback_data="specialties"))
    keyboard.add(types.InlineKeyboardButton(text="📝 " + TEXT[language]["documents"], callback_data="documents"))
    keyboard.add(types.InlineKeyboardButton(text="📜 " + TEXT[language]["rules"], callback_data="rules"))
    keyboard.add(types.InlineKeyboardButton(text="❓ " + TEXT[language]["faq"], callback_data="faq"))
    keyboard.add(types.InlineKeyboardButton(text="✍️ " + TEXT[language]["leave_review"], callback_data="leave_review"))
    keyboard.add(types.InlineKeyboardButton(text="📋 " + TEXT[language]["view_reviews"], callback_data="view_reviews"))
    keyboard.add(types.InlineKeyboardButton(text=TEXT[language]["show_map"], url="https://adonis57.github.io/okolegius/college_map.html"))
    for name, callback in custom_buttons.items():
        keyboard.add(types.InlineKeyboardButton(text=name, callback_data=callback))
    if role == "moderator":
        keyboard.add(types.InlineKeyboardButton(text="🛠️ " + TEXT[language]["moderator_menu"], callback_data="moderator_menu"))
    elif role == "admin":
        keyboard.add(types.InlineKeyboardButton(text="👑 " + TEXT[language]["admin_menu"], callback_data="admin_menu"))
    keyboard.add(types.InlineKeyboardButton(text=TEXT[language]["change_language"], callback_data="change_language"))
    return keyboard

def about_college_keyboard(language):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton(text="ℹ️ О колледже", callback_data="college_info"))
    keyboard.add(types.InlineKeyboardButton(text="📸 Фото и видео", callback_data="college_media"))
    keyboard.add(back_button(language))
    return keyboard

def specialties_keyboard(language):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton(text="💰 " + TEXT[language]["budget_learning"], callback_data="budget_learning"))
    keyboard.add(types.InlineKeyboardButton(text="💸 " + TEXT[language]["paid_learning"], callback_data="paid_learning"))
    keyboard.add(back_button(language))
    return keyboard

def faq_keyboard(language, categories):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton(text="📩 Задать вопрос", callback_data="ask_faq_question"))
    keyboard.add(types.InlineKeyboardButton(text="📋 Мои вопросы", callback_data="my_questions"))
    for cat_id, name in categories:
        keyboard.add(types.InlineKeyboardButton(text=f"❓ {name}", callback_data=f"faq_category_{cat_id}"))
    keyboard.add(back_button(language))
    return keyboard

def faq_category_keyboard(faq_items, language, category_id, access):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    if not faq_items:
        keyboard.add(types.InlineKeyboardButton(text="Нет вопросов", callback_data="noop"))
    else:
        for i, (faq_id, user_id, username, _, question, answer) in enumerate(faq_items, 1):
            text = f"{i}. {question} (@{username or 'unknown'})" + (" ✅" if answer else " ❓")
            keyboard.add(types.InlineKeyboardButton(text=text, callback_data=f"faq_view_{faq_id}"))
            if access in ["moderator", "admin"]:
                keyboard.add(types.InlineKeyboardButton(text=f"✏️ Ответить {i}", callback_data=f"answer_faq_{faq_id}"))
                keyboard.add(types.InlineKeyboardButton(text=f"🗑️ Удалить {i}", callback_data=f"delete_faq_{faq_id}"))
    keyboard.add(back_button(language))
    return keyboard

def moderator_menu_keyboard(language):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton(text="✏️ " + TEXT[language]["edit_content"], callback_data="edit_content"))
    keyboard.add(types.InlineKeyboardButton(text="❓ " + TEXT[language]["faq"], callback_data="faq"))
    keyboard.add(types.InlineKeyboardButton(text="➕ Добавить категорию FAQ", callback_data="add_faq_category"))
    keyboard.add(types.InlineKeyboardButton(text="📩 Написать администратору", callback_data="message_to_admin"))
    keyboard.add(types.InlineKeyboardButton(text="🔄 " + TEXT[language]["change_own_role"], callback_data="change_own_role"))
    keyboard.add(back_button(language))
    return keyboard

def admin_menu_keyboard(language):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton(text="👥 Пользователи и модераторы", callback_data="users_and_moderators"))
    keyboard.add(types.InlineKeyboardButton(text="🚫 " + TEXT[language]["ban_user"], callback_data="ban_user"))
    keyboard.add(types.InlineKeyboardButton(text="✅ " + TEXT[language]["unban_user"], callback_data="unban_user"))
    keyboard.add(types.InlineKeyboardButton(text="➕ " + TEXT[language]["add_moderator"], callback_data="add_moderator"))
    keyboard.add(types.InlineKeyboardButton(text="➖ " + TEXT[language]["remove_moderator"], callback_data="remove_moderator"))
    keyboard.add(types.InlineKeyboardButton(text="✏️ " + TEXT[language]["edit_content"], callback_data="edit_content"))
    keyboard.add(types.InlineKeyboardButton(text="❓ " + TEXT[language]["faq"], callback_data="faq"))
    keyboard.add(types.InlineKeyboardButton(text="➕ Добавить категорию FAQ", callback_data="add_faq_category"))
    keyboard.add(types.InlineKeyboardButton(text="🔄 " + TEXT[language]["change_user_role"], callback_data="change_user_role"))
    keyboard.add(types.InlineKeyboardButton(text="🔄 " + TEXT[language]["change_own_role"], callback_data="change_own_role"))
    keyboard.add(back_button(language))
    return keyboard

def edit_content_keyboard(language, custom_buttons):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton(text="⏱️ " + TEXT[language]["working_hours"], callback_data="edit_working_hours"))
    keyboard.add(types.InlineKeyboardButton(text="📞 " + TEXT[language]["contacts"], callback_data="edit_contacts"))
    keyboard.add(types.InlineKeyboardButton(text="📝 " + TEXT[language]["documents"], callback_data="edit_documents"))
    keyboard.add(types.InlineKeyboardButton(text="➕ Добавить кнопку", callback_data="add_custom_button"))
    for name, callback in custom_buttons.items():
        keyboard.add(types.InlineKeyboardButton(text=f"✏️ {name}", callback_data=f"edit_{callback}"))
        keyboard.add(types.InlineKeyboardButton(text=f"🗑️ Удалить {name}", callback_data=f"delete_{callback}"))
    keyboard.add(back_button(language))
    return keyboard

def users_and_moderators_keyboard(users, language):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for user_id, role, tag, full_name in users:
        text = f"{tag or user_id} ({role}) - {full_name or 'Нет имени'}"
        keyboard.add(types.InlineKeyboardButton(text=text, callback_data=f"user_info_{user_id}"))
    keyboard.add(back_button(language))
    return keyboard

def back_button(language):
    return types.InlineKeyboardButton(text="🔙 " + TEXT[language]["back"], callback_data="back_to_main")

def finish_or_continue_keyboard(language):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("✅ Закончить", callback_data="finish_content"),
        types.InlineKeyboardButton("➕ Продолжить", callback_data="continue_content")
    )
    return keyboard