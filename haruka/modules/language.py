from haruka.modules.sql.translation import switch_to_locale, prev_locale
from haruka.modules.translations.strings import tld
from telegram.ext import CommandHandler
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from haruka import dispatcher
from haruka.modules.translations.list_locale import list_locales
from haruka.modules.helper_funcs.chat_status import user_admin
from telegram.ext import CallbackQueryHandler
import re

from haruka.modules.connection import connected


@user_admin
def locale(bot, update, args):
    chat = update.effective_chat
    if len(args) > 0:
        locale = args[0].lower()
        if locale in list_locales:
            if locale in ('en', 'ru', 'ua', 'es', 'tr', 'id'):
                switch_to_locale(chat.id, locale)
                update.message.reply_text(tld(chat.id, 'Sprache zu {} geändert!').format(list_locales[locale]))
            else:
                update.message.reply_text("{} ist noch keine unterstützte Sprache!".format(list_locales[locale]))
        else:
            update.message.reply_text("Ist das eine Sprache? Gib den ISO code an!")
    else:
        LANGUAGE = prev_locale(chat.id)
        if LANGUAGE:
            locale = LANGUAGE.locale_name
            native_lang = list_locales[locale]
            update.message.reply_text("Die aktuelle Spracheinstellung ist: *{}*".format(native_lang), parse_mode = ParseMode.MARKDOWN)
        else:
            update.message.reply_text("Die aktuelle Sprache für diesen Chat ist *Deutsch*", parse_mode=ParseMode.MARKDOWN)

@user_admin
def locale_button(bot, update):
    chat = update.effective_chat
    user = update.effective_user  # type: Optional[User]
    query = update.callback_query
    lang_match = re.findall(r"en|ru|ua|es|tr|id", query.data)
    if lang_match:
        if lang_match[0]:
            switch_to_locale(chat.id, lang_match[0])
            query.answer(text="Sprache geändert!")
        else:
            query.answer(text="Fehler!", show_alert=True)

    try:
        LANGUAGE = prev_locale(chat.id)
        locale = LANGUAGE.locale_name
        curr_lang = list_locales[locale]
    except:
        curr_lang = "English"

    text = "*Sprache auswählen* \n"
    text += "Nutzer-Sprache: `{}`".format(curr_lang)

    conn = connected(bot, update, chat, user.id, need_admin=False)

    if not conn == False:
        try:
            chatlng = prev_locale(conn).locale_name
            chatlng = list_locales[chatlng]
            text += "\nDie Sprache des verbundenen Chats : `{}`".format(chatlng)
        except:
            chatlng = "English"

    text += "*\n\nWähle die zu nutzende Sprache aus:*"

    query.message.reply_text(text, parse_mode=ParseMode.MARKDOWN,
                                            reply_markup=InlineKeyboardMarkup([[
                                            InlineKeyboardButton("Englisch 🇺🇸", callback_data="set_lang_en")]] + [[
                                            InlineKeyboardButton("Russisch 🇷🇺", callback_data="set_lang_ru"),
                                            InlineKeyboardButton("Ukrainisch 🇺🇦", callback_data="set_lang_ua")]] + [[
                                            InlineKeyboardButton("Spanisch 🇪🇸", callback_data="set_lang_es"),
                                            InlineKeyboardButton("Türkish 🇹🇷", callback_data="set_lang_tr")]] + [[
                                            InlineKeyboardButton("Indonesisch 🇮🇩", callback_data="set_lang_id")]] + [[
                                            InlineKeyboardButton("⬅️ Zurück", callback_data="bot_start")]]))

    print(lang_match)
    query.message.delete()
    bot.answer_callback_query(query.id)


LOCALE_HANDLER = CommandHandler(["set_locale", "locale", "lang", "setlang"], locale, pass_args=True)
locale_handler = CallbackQueryHandler(locale_button, pattern="chng_lang")
set_locale_handler = CallbackQueryHandler(locale_button, pattern=r"set_lang_")

dispatcher.add_handler(LOCALE_HANDLER)
dispatcher.add_handler(locale_handler)
dispatcher.add_handler(set_locale_handler)
