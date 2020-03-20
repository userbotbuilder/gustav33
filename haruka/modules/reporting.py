import html
from typing import Optional, List
import re
from telegram import Message, Chat, Update, Bot, User, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest, Unauthorized
from telegram.ext import CommandHandler, RegexHandler, run_async, Filters, CallbackQueryHandler
from telegram.utils.helpers import mention_html

from haruka import dispatcher, LOGGER
from haruka.modules.helper_funcs.chat_status import user_not_admin, user_admin
from haruka.modules.log_channel import loggable
from haruka.modules.sql import reporting_sql as sql

REPORT_GROUP = 5


@run_async
@user_admin
def report_setting(bot: Bot, update: Update, args: List[str]):
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message  # type: Optional[Message]

    if chat.type == chat.PRIVATE:
        if len(args) >= 1:
            if args[0] in ("yes", "on"):
                sql.set_user_setting(chat.id, True)
                msg.reply_text("Das Melden von Nachrichten ist nun aktiviert! Wenn ein Nutzer eine Nachricht meldet, bekommt jeder Admin eine Benachrichtigung.")

            elif args[0] in ("no", "off"):
                sql.set_user_setting(chat.id, False)
                msg.reply_text("Das Melden von Nachrichten ist nun deaktiviert! /report und @admin sind nun nutzlos.")
        else:
            msg.reply_text("Deine aktuelle Einstellung zum Melden von Nachrichten ist: `{}`".format(sql.user_should_report(chat.id)),
                           parse_mode=ParseMode.MARKDOWN)

    else:
        if len(args) >= 1:
            if args[0] in ("yes", "on"):
                sql.set_chat_setting(chat.id, True)
                msg.reply_text("Das Melden von Nachrichten ist nun aktiviert! Die admins werden nun informiert, wenn ein Nutzer mit /report "
                               "oder @admin auf eine Nachricht eines anderen Users antwortet.")

            elif args[0] in ("no", "off"):
                sql.set_chat_setting(chat.id, False)
                msg.reply_text("Das Melden von Nachrichten ist nun deaktiviert! /report und @admin sind nun nutzlos.")
        else:
            msg.reply_text("Die aktuelle Einstellungen für diesen Chat ist: `{}`".format(sql.chat_should_report(chat.id)),
                           parse_mode=ParseMode.MARKDOWN)


@run_async
@user_not_admin
@loggable
def report(bot: Bot, update: Update) -> str:
    message = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]

    if chat and message.reply_to_message and sql.chat_should_report(chat.id):
        reported_user = message.reply_to_message.from_user  # type: Optional[User]
        chat_name = chat.title or chat.first or chat.username
        admin_list = chat.get_administrators()

        #if reported_user == "483808054":
        #    continue
       # 
        #if user.id == "435606081":
        #    continue

        if chat.username and chat.type == Chat.SUPERGROUP:
            msg = "<b>{}:</b>" \
                  "\n<b>Gemeldeter Nutzer:</b> {} (<code>{}</code>)" \
                  "\n<b>Gemeldet von:</b> {} (<code>{}</code>)".format(html.escape(chat.title),
                                                                      mention_html(
                                                                          reported_user.id,
                                                                          reported_user.first_name),
                                                                      reported_user.id,
                                                                      mention_html(user.id,
                                                                                   user.first_name),
                                                                      user.id)
            link = "\n<b>Link:</b> " \
                   "<a href=\"http://telegram.me/{}/{}\">hier tippen</a>".format(chat.username, message.message_id)

            should_forward = True
            keyboard = [
                [InlineKeyboardButton(u"➡ Nachricht schreiben", url="https://t.me/{}/{}".format(chat.username, str(
                    message.reply_to_message.message_id)))],
                [InlineKeyboardButton(u"⚠ Kicken",
                                      callback_data="report_{}=kick={}={}".format(chat.id, reported_user.id,
                                                                                  reported_user.first_name)),
                 InlineKeyboardButton(u"⛔️ Bannen",
                                      callback_data="report_{}=banned={}={}".format(chat.id, reported_user.id,
                                                                                    reported_user.first_name))],
                [InlineKeyboardButton(u"❎ Nachricht löschen",
                                      callback_data="report_{}=delete={}={}".format(chat.id, reported_user.id,
                                                                                    message.reply_to_message.message_id))]]
            reply_markup = InlineKeyboardMarkup(keyboard)

        else:
            msg = "{} Ruft die Admins im Chat \"{}\"!".format(mention_html(user.id, user.first_name),
                                                               html.escape(chat_name))
            link = ""
            should_forward = True

        for admin in admin_list:
            if admin.user.is_bot:  # can't message bots
                continue

            if sql.user_should_report(admin.user.id):
                try:
                    if not chat.type == Chat.SUPERGROUP:
                        bot.send_message(admin.user.id, msg + link, parse_mode=ParseMode.HTML)

                        if should_forward:
                            message.reply_to_message.forward(admin.user.id)

                            if len(message.text.split()) > 1:  # If user is giving a reason, send his message too
                                message.forward(admin.user.id)

                    if not chat.username:
                        bot.send_message(admin.user.id, msg + link, parse_mode=ParseMode.HTML)

                        if should_forward:
                            message.reply_to_message.forward(admin.user.id)

                            if len(message.text.split()) > 1:  # If user is giving a reason, send his message too
                                message.forward(admin.user.id)

                    if chat.username and chat.type == Chat.SUPERGROUP:
                        bot.send_message(admin.user.id, msg + link, parse_mode=ParseMode.HTML, reply_markup=reply_markup)

                        if should_forward:
                            message.reply_to_message.forward(admin.user.id)

                            if len(message.text.split()) > 1:  # If user is giving a reason, send his message too
                                message.forward(admin.user.id)

                except Unauthorized:
                    pass
                except BadRequest as excp:  # TODO: cleanup exceptions
                    LOGGER.exception("Exception while reporting user")

        message.reply_to_message.reply_text("{} hat die Nachricht den Admins gemeldet.".
                                            format(mention_html(user.id, user.first_name)),
                                            parse_mode=ParseMode.HTML)
        return msg

    return ""


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(bot, update, chat, chatP, user):
    return "Dieser Chat ist so eingerichtet, dass Nutzer andere Nutzer mit /report und @admin melden können: `{}`".format(
        sql.chat_should_report(chat.id))


def __user_settings__(bot, update, user):
    if sql.user_should_report(user.id) == True:
        text = "Du Empfängst Meldungen von Chats, in denen du Admin bist."
        keyboard = [[InlineKeyboardButton(text="Meldungen abschalten", callback_data="panel_reporting_U_disable")]]
    else:
        text = "Du Empfängst *keine* Meldungen von Chats, in denen du Admin bist."
        keyboard = [[InlineKeyboardButton(text="Meldungen aktivieren", callback_data="panel_reporting_U_enable")]]

    return text, keyboard

    
def control_panel_user(bot, update):
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat
    query = update.callback_query
    enable = re.match(r"panel_reporting_U_enable", query.data)
    disable = re.match(r"panel_reporting_U_disable", query.data)

    query.message.delete()

    if enable:
        sql.set_user_setting(chat.id, True)
        text = "Du wirst nun per PN informiert!"
    else:
        sql.set_user_setting(chat.id, False)
        text = "Du wirst keine Meldungen per PN erhalten!"

    keyboard = [[InlineKeyboardButton(text="⬅️ Zurück", callback_data="cntrl_panel_U(1)")]]

    update.effective_message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)


def buttons(bot: Bot, update):
    query = update.callback_query
    splitter = query.data.replace("report_", "").split("=")
    chat = update.effective_chat
    if splitter[1] == "kick":
        try:
            bot.kickChatMember(splitter[0], splitter[2])
            bot.unbanChatMember(splitter[0], splitter[2])
            query.answer("✅ Gekickt")
            return ""
        except Exception as err:
            query.answer("❎ Fehler beim Kicken")
            bot.sendMessage(text="Fehler: {}".format(err),
                            chat_id=query.message.chat_id,
                            parse_mode=ParseMode.HTML)
    elif splitter[1] == "banned":
        try:
            bot.kickChatMember(splitter[0], splitter[2])
            query.answer("✅ Verbannt")
            return ""
        except Exception as err:
            bot.sendMessage(text="Fehler: {}".format(err),
                            chat_id=query.message.chat_id,
                            parse_mode=ParseMode.HTML)
            query.answer("❎ Fehler beim verbannen")
    elif splitter[1] == "delete":
        try:
            bot.deleteMessage(splitter[0], splitter[3])
            query.answer("✅ Nachricht gelöscht")
            return ""
        except Exception as err:
            bot.sendMessage(text="Fehler: {}".format(err),
                                  chat_id=query.message.chat_id,
                                  parse_mode=ParseMode.HTML)
            query.answer("❎ Fehler beim Löschen der Nachricht!")


__mod_name__ = "Melden von Nutzern"

__help__ = """
 - /report <Grund>: Auf eine Nachricht antworten, um sie den Admins zu melden.
 - @admin: Auf eine Nachricht antworten, um sie den Admins zu melden.
Info: Diese Befehle sind natürlich nicht für Gruppenadmins verfügbar

*Nur für Admins:*
 - /reports <on/off>: Die Einstellung zum Melden von Nachrichten verändern oder den aktuellen Status einsehen.
 - Per PN wird deine aktuelle Einstellung gezeigt.
 - Im Chat wird die aktuelle Einstellung der Gruppe angezeigt.
"""

REPORT_HANDLER = CommandHandler("report", report, filters=Filters.group)
SETTING_HANDLER = CommandHandler("reports", report_setting, pass_args=True)
ADMIN_REPORT_HANDLER = RegexHandler("(?i)@admin(s)?", report)

cntrl_panel_user_callback_handler = CallbackQueryHandler(control_panel_user, pattern=r"panel_reporting_U")
report_button_user_handler = CallbackQueryHandler(buttons, pattern=r"report_")
dispatcher.add_handler(cntrl_panel_user_callback_handler)
dispatcher.add_handler(report_button_user_handler)

dispatcher.add_handler(REPORT_HANDLER, REPORT_GROUP)
dispatcher.add_handler(ADMIN_REPORT_HANDLER, REPORT_GROUP)
dispatcher.add_handler(SETTING_HANDLER)
