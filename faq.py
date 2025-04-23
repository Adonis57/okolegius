from telebot import types
from languages import get_text

def create_faq_keyboard(categories, language):
    return keyboards.faq_keyboard(language, categories)

def create_faq_category_keyboard(faq_items, language, category_id, access):
    return keyboards.faq_category_keyboard(faq_items, language, category_id, access)