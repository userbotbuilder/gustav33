import html
import re
from typing import Optional, List

import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, User, CallbackQuery
from telegram import Message, Chat, Update, Bot
from telegram.error import BadRequest
from telegram.ext import CommandHandler, run_async, DispatcherHandlerStop, MessageHandler, Filters, CallbackQueryHandler
from telegram.utils.helpers import mention_html

from haruka import dispatcher, BAN_STICKER
from haruka.modules.disable import DisableAbleCommandHandler
from haruka.modules.helper_funcs.chat_status import is_user_admin, bot_admin, user_admin_no_reply, user_admin, \
    can_restrict
from haruka.modules.helper_funcs.extraction import extract_text, extract_user_and_text, extract_user
from haruka.modules.helper_funcs.filters import CustomFilters
from haruka.modules.helper_funcs.misc import split_message
from haruka.modules.helper_funcs.string_handling import split_quotes
from haruka.modules.log_channel import loggable
from haruka.modules.sql import warns_sql as sql

WARN_HANDLER_GROUP = 9
CURRENT_WARNING_FILTER_STRING = "<b>Aktuelle Filter in diesem Chat, die zu einer Verwarnung führen:</b>\n"


# Not async
def warn(user: User, chat: Chat, reason: str, message: Message, warner: User = None) -> str:
    if is_user_admin(chat, user.id):
        message.reply_text("Ich verwarne keinen Admin!")
        return ""

    if warner:
        warner_tag = mention_html(warner.id, warner.first_name)
    else:
        warner_tag = "Automated warn filter."

    limit, soft_warn = sql.get_warn_setting(chat.id)
    num_warns, reasons = sql.warn_user(user.id, chat.id, reason)
    if num_warns >= limit:
        sql.reset_warns(user.id, chat.id)
        if soft_warn:  # kick
            chat.unban_member(user.id)
            reply = "So, das war's, mein lieber! {} Verwarnungen, {} wurde gekickt!".format(limit, mention_html(user.id, user.first_name))

        else:  # ban
            chat.kick_member(user.id)
            reply = "So, das war's, mein lieber! Hausverbot! {} Verwarnungen, {} wurde verbannt!".format(limit, mention_html(user.id, user.first_name))

        for warn_reason in reasons:
            reply += "\n - {}".format(html.escape(warn_reason))

        keyboard = []
        log_reason = "<b>{}:</b>" \
                     "\n#WARN_BAN" \
                     "\n<b>Admin:</b> {}" \
                     "\n<b>User:</b> {} (<code>{}</code>)" \
                     "\n<b>Reason:</b> {}"\
                     "\n<b>Counts:</b> <code>{}/{}</code>".format(html.escape(chat.title),
                                                                  warner_tag,
                                                                  mention_html(user.id, user.first_name),
                                                                  user.id, reason, num_warns, limit)

    else:
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Verwarnung entfernen (Nur Admins)", callback_data="rm_warn({})".format(user.id))]])

        reply = "Ohje, schon Scheiße gebaut! Der liebe User {} <b>wurde verwarnt!</b>\nDieser Nutzer hat aktuell {} von {} Verwarnungen.".format(mention_html(user.id, user.first_name), num_warns,
                                                             limit)
        if reason:
            reply += "\nGrund für die Verwarnung:\n<code>{}</code>".format(html.escape(reason))

        log_reason = "<b>{}:</b>" \
                     "\n#WARN" \
                     "\n<b>Admin:</b> {}" \
                     "\n<b>User:</b> {} (<code>{}</code>)" \
                     "\n<b>Reason:</b> {}"\
                     "\n<b>Counts:</b> <code>{}/{}</code>".format(html.escape(chat.title),
                                                                  warner_tag,
                                                                  mention_html(user.id, user.first_name),
                                                                  user.id, reason, num_warns, limit)

    try:
        message.reply_text(reply, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text(reply, reply_markup=keyboard, parse_mode=ParseMode.HTML, quote=False)
        else:
            raise
    return log_reason


@run_async
@bot_admin
@loggable
def button(bot: Bot, update: Update) -> str:
    query = update.callback_query  # type: Optional[CallbackQuery]
    user = update.effective_user  # type: Optional[User]
    match = re.match(r"rm_warn\((.+?)\)", query.data)
    if match:
        user_id = match.group(1)
        chat = update.effective_chat  # type: Optional[Chat]
        if not is_user_admin(chat, int(user.id)):
            query.answer(text="Du darfst diese Verwarnung nicht entfernen, das können nur Admins!", show_alert=True)
            return ""
        res = sql.remove_warn(user_id, chat.id)
        if res:
            update.effective_message.edit_text(
                "~ Verwarnung entfernt vom Admin {}.".format(mention_html(user.id, user.first_name)),
                parse_mode=ParseMode.HTML)
            user_member = chat.get_member(user_id)
            return "<b>{}:</b>" \
                   "\n#UNWARN" \
                   "\n<b>Admin:</b> {}" \
                   "\n<b>User:</b> {} (<code>{}</code>)".format(html.escape(chat.title),
                                                                mention_html(user.id, user.first_name),
                                                                mention_html(user_member.user.id, user_member.user.first_name),
                                                                user_member.user.id)
        else:
            update.effective_message.edit_text(
                "Der Nutzer hat bereits keine Verwarnungen.".format(mention_html(user.id, user.first_name)),
                parse_mode=ParseMode.HTML)

    return ""


@run_async
@user_admin
@bot_admin
@loggable
def remove_warns(bot: Bot, update: Update, args: List[str]) -> str:
    message = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]

    user_id = extract_user(message, args)

    if user_id:
        sql.remove_warn(user_id, chat.id)
        message.reply_text("Die letzte Verwarnung wurde entfernt!")
        warned = chat.get_member(user_id).user
        return "<b>{}:</b>" \
               "\n#UNWARN" \
               "\n<b>• Admin:</b> {}" \
               "\n<b>• User:</b> {}" \
               "\n<b>• ID:</b> <code>{}</code>".format(html.escape(chat.title),
                                                       mention_html(user.id, user.first_name),
                                                       mention_html(warned.id, warned.first_name),
                                                       warned.id)
    else:
        message.reply_text("Kein Nutzer wurde angegeben!")
    return ""

@run_async
@user_admin
@can_restrict
@loggable
def warn_user(bot: Bot, update: Update, args: List[str]) -> str:
    message = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    warner = update.effective_user  # type: Optional[User]

    user_id, reason = extract_user_and_text(message, args)

    if user_id:
        if message.reply_to_message and message.reply_to_message.from_user.id == user_id:
            return warn(message.reply_to_message.from_user, chat, reason, message.reply_to_message, warner)
        else:
            return warn(chat.get_member(user_id).user, chat, reason, message, warner)
    else:
        message.reply_text("Kein Nutzer wurde angegeben!")
    return ""


@run_async
@user_admin
@bot_admin
@loggable
def reset_warns(bot: Bot, update: Update, args: List[str]) -> str:
    message = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]

    user_id = extract_user(message, args)

    if user_id:
        sql.reset_warns(user_id, chat.id)
        message.reply_text("Verwarnungen wurden zurückgesetzt!")
        warned = chat.get_member(user_id).user
        return "<b>{}:</b>" \
               "\n#RESETWARNS" \
               "\n<b>Admin:</b> {}" \
               "\n<b>User:</b> {} (<code>{}</code>)".format(html.escape(chat.title),
                                                            mention_html(user.id, user.first_name),
                                                            mention_html(warned.id, warned.first_name),
                                                            warned.id)
    else:
        message.reply_text("Kein Nutzer wurde angegeben!")
    return ""


@run_async
def warns(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    user_id = extract_user(message, args) or update.effective_user.id
    result = sql.get_warns(user_id, chat.id)

    if result and result[0] != 0:
        num_warns, reasons = result
        limit, soft_warn = sql.get_warn_setting(chat.id)

        if reasons:
            text = "Dieser Nutzer hat {} von {} Verwarnungen, aus den folgenden Gründen:".format(num_warns, limit)
            for reason in reasons:
                text += "\n - {}".format(reason)

            msgs = split_message(text)
            for msg in msgs:
                update.effective_message.reply_text(msg)
        else:
            update.effective_message.reply_text(
                "Der Nutzer hat {} von {} Verwarnungen, aber für keine wurde ein Grund angegeben.".format(num_warns, limit))
    else:
        update.effective_message.reply_text("Dieser Nutzer hat keine Verwarnungen kassiert!")


# Dispatcher handler stop - do not async
@user_admin
def add_warn_filter(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message  # type: Optional[Message]

    args = msg.text.split(None, 1)  # use python's maxsplit to separate Cmd, keyword, and reply_text

    if len(args) < 2:
        return

    extracted = split_quotes(args[1])

    if len(extracted) >= 2:
        # set trigger -> lower, so as to avoid adding duplicate filters with different cases
        keyword = extracted[0].lower()
        content = extracted[1]

    else:
        return

    # Note: perhaps handlers can be removed somehow using sql.get_chat_filters
    for handler in dispatcher.handlers.get(WARN_HANDLER_GROUP, []):
        if handler.filters == (keyword, chat.id):
            dispatcher.remove_handler(handler, WARN_HANDLER_GROUP)

    sql.add_warn_filter(chat.id, keyword, content)

    update.effective_message.reply_text("Warn-Handler für '{}' hinzugefügt!".format(keyword))
    raise DispatcherHandlerStop


@user_admin
def remove_warn_filter(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message  # type: Optional[Message]

    args = msg.text.split(None, 1)  # use python's maxsplit to separate Cmd, keyword, and reply_text

    if len(args) < 2:
        return

    extracted = split_quotes(args[1])

    if len(extracted) < 1:
        return

    to_remove = extracted[0]

    chat_filters = sql.get_chat_warn_triggers(chat.id)

    if not chat_filters:
        msg.reply_text("Hier sind keine Warn-Filter aktiv!")
        return

    for filt in chat_filters:
        if filt == to_remove:
            sql.remove_warn_filter(chat.id, to_remove)
            msg.reply_text("Yeah, dafür werden die Nutzer nicht mehr verwarnt.")
            raise DispatcherHandlerStop

    msg.reply_text("Das ist kein aktueller Warnfilter- führe /warnfilters aus, um eine Liste zu erhalten.")


@run_async
def list_warn_filters(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    all_handlers = sql.get_chat_warn_triggers(chat.id)

    if not all_handlers:
        update.effective_message.reply_text("Hier sind keine Warn-Filter aktiv!")
        return

    filter_list = CURRENT_WARNING_FILTER_STRING
    for keyword in all_handlers:
        entry = " - {}\n".format(html.escape(keyword))
        if len(entry) + len(filter_list) > telegram.MAX_MESSAGE_LENGTH:
            update.effective_message.reply_text(filter_list, parse_mode=ParseMode.HTML)
            filter_list = entry
        else:
            filter_list += entry

    if not filter_list == CURRENT_WARNING_FILTER_STRING:
        update.effective_message.reply_text(filter_list, parse_mode=ParseMode.HTML)


@run_async
@loggable
def reply_filter(bot: Bot, update: Update) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    message = update.effective_message  # type: Optional[Message]

    chat_warn_filters = sql.get_chat_warn_triggers(chat.id)
    to_match = extract_text(message)
    if not to_match:
        return ""

    for keyword in chat_warn_filters:
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, to_match, flags=re.IGNORECASE):
            user = update.effective_user  # type: Optional[User]
            warn_filter = sql.get_warn_filter(chat.id, keyword)
            return warn(user, chat, warn_filter.reply, message)
    return ""


@run_async
@user_admin
@loggable
def set_warn_limit(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]

    if args:
        if args[0].isdigit():
            if int(args[0]) < 3:
                msg.reply_text("Das Minimum-Warnlimit ist 3!")
            else:
                sql.set_warn_limit(chat.id, int(args[0]))
                msg.reply_text("Das Warnlimit wurde auf {} geupdated".format(args[0]))
                return "<b>{}:</b>" \
                       "\n#SET_WARN_LIMIT" \
                       "\n<b>Admin:</b> {}" \
                       "\nSet the warn limit to <code>{}</code>".format(html.escape(chat.title),
                                                                        mention_html(user.id, user.first_name), args[0])
        else:
            msg.reply_text("Gib nen User als Argument an!")
    else:
        limit, soft_warn = sql.get_warn_setting(chat.id)

        msg.reply_text("Das aktuelle Warnlimit ist {}".format(limit))
    return ""


@run_async
@user_admin
def set_warn_strength(bot: Bot, update: Update, args: List[str]):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]

    if args:
        if args[0].lower() in ("on", "yes"):
            sql.set_warn_strength(chat.id, False)
            msg.reply_text("Zu viele Verwarnungen enden nun in 'nem Ban!")
            return "<b>{}:</b>\n" \
                   "<b>Admin:</b> {}\n" \
                   "Has enabled strong warns. Users will be banned.".format(html.escape(chat.title),
                                                                            mention_html(user.id, user.first_name))

        elif args[0].lower() in ("off", "no"):
            sql.set_warn_strength(chat.id, True)
            msg.reply_text("Zu viele Verwarnungen führen nun zu 'nem Kick! Nutzer können danach wieder beitreten.")
            return "<b>{}:</b>\n" \
                   "<b>Admin:</b> {}\n" \
                   "Has disabled strong warns. Users will only be kicked.".format(html.escape(chat.title),
                                                                                  mention_html(user.id,
                                                                                               user.first_name))

        else:
            msg.reply_text("Ich verstehe nur on/yes/no/off!")
    else:
        limit, soft_warn = sql.get_warn_setting(chat.id)
        if soft_warn:
            msg.reply_text("Verwarnungen sind aktuell so gesetzt, dass ich Nutzer *kicke* , wenn sie die Limits überschreiten.",
                           parse_mode=ParseMode.MARKDOWN)
        else:
            msg.reply_text("Verwarnungen sind aktuell so gesetzt, dass ich Nutzer *verbanne* , wenn sie die Limits überschreiten.",
                           parse_mode=ParseMode.MARKDOWN)
    return ""


def __stats__():
    return "{} overall warns, across {} chats.\n" \
           "{} warn filters, across {} chats.".format(sql.num_warns(), sql.num_warn_chats(),
                                                      sql.num_warn_filters(), sql.num_warn_filter_chats())


def __import_data__(chat_id, data):
    for user_id, count in data.get('warns', {}).items():
        for x in range(int(count)):
            sql.warn_user(user_id, chat_id)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    num_warn_filters = sql.num_warn_chat_filters(chat_id)
    limit, soft_warn = sql.get_warn_setting(chat_id)
    return "Dieser Chat hat `{}` Warnfilter. Es braucht `{}` Verwarnungen, " \
           "bevor der Nutzer einen *{}* bekommt.".format(num_warn_filters, limit, "kicked" if soft_warn else "banned")


__help__ = """
 - /warns <Antwort-auf-ne-Nachricht-von-dem-Nutzer>: Liefert die Nummer und den Grund der Verwarnungen des Nutzers.
 - /warnlist: Liste aller aktuellen Warnfilter.

*Nur für Admins:*
 - /warn <userhandle>: Einen Benutzer verwarnen. Nach 3 Verwarnungen wird der Benutzer je nach Einstellung aus der Gruppe verbannt.
 - /resetwarn <userhandle>: Die Verwarnungen für einen Benutzer zurücksetzen.
 - /addwarn <keyword> <reply message>: Einen Warnfilter für ein bestimmtes Keyword setzen. Wenn du willst, dass dein Schlüsselwort ein Satz ist, schreibe es bitte so: /addwarn "boehse" Das ist ein wütender Mensch.
 - /nowarn <keyword>: einen Warnfilter stoppen
 - /warnlimit <num>: Einstellen der Warngrenze
 - /strongwarn <on/yes/off/no>: Wenn diese Option eingeschaltet ist, führt die Überschreitung des Warngrenzwertes zu einer Sperrung. Andernfalls wird der Nutzer einfach mit einem Kick bestraft.
"""

__mod_name__ = "Verwarnungen"

WARN_HANDLER = DisableAbleCommandHandler("warn", warn_user, pass_args=True, filters=Filters.group, admin_ok=True)
RESET_WARN_HANDLER = DisableAbleCommandHandler(["resetwarn", "resetwarns"], reset_warns, pass_args=True, filters=Filters.group)
CALLBACK_QUERY_HANDLER = CallbackQueryHandler(button, pattern=r"rm_warn")
MYWARNS_HANDLER = DisableAbleCommandHandler("warns", warns, pass_args=True, filters=Filters.group, admin_ok=True)
ADD_WARN_HANDLER = DisableAbleCommandHandler("addwarn", add_warn_filter, filters=Filters.group, admin_ok=True)
RM_WARN_HANDLER = DisableAbleCommandHandler(["nowarn", "stopwarn"], remove_warn_filter, filters=Filters.group, admin_ok=True)
LIST_WARN_HANDLER = DisableAbleCommandHandler(["warnlist", "warnfilters"], list_warn_filters, filters=Filters.group, admin_ok=True)
WARN_FILTER_HANDLER = MessageHandler(CustomFilters.has_text & Filters.group, reply_filter)
WARN_LIMIT_HANDLER = DisableAbleCommandHandler("warnlimit", set_warn_limit, pass_args=True, filters=Filters.group, admin_ok=True)
WARN_STRENGTH_HANDLER = CommandHandler("strongwarn", set_warn_strength, pass_args=True, filters=Filters.group, admin_ok=True)
REMOVE_WARNS_HANDLER = CommandHandler(["rmwarn", "unwarn"], remove_warns, pass_args=True, filters=Filters.group, admin_ok=True)

dispatcher.add_handler(WARN_HANDLER)
dispatcher.add_handler(CALLBACK_QUERY_HANDLER)
dispatcher.add_handler(RESET_WARN_HANDLER)
dispatcher.add_handler(MYWARNS_HANDLER)
dispatcher.add_handler(ADD_WARN_HANDLER)
dispatcher.add_handler(RM_WARN_HANDLER)
dispatcher.add_handler(LIST_WARN_HANDLER)
dispatcher.add_handler(WARN_LIMIT_HANDLER)
dispatcher.add_handler(WARN_STRENGTH_HANDLER)
dispatcher.add_handler(WARN_FILTER_HANDLER, WARN_HANDLER_GROUP)
dispatcher.add_handler(REMOVE_WARNS_HANDLER)
