import html
import re
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, MessageHandler, Filters, run_async

import haruka.modules.sql.blacklist_sql as sql
from haruka import dispatcher, LOGGER
from haruka.modules.disable import DisableAbleCommandHandler
from haruka.modules.helper_funcs.chat_status import user_admin, user_not_admin
from haruka.modules.helper_funcs.extraction import extract_text
from haruka.modules.helper_funcs.misc import split_message

from haruka.modules.connection import connected

from haruka.modules.translations.strings import tld

BLACKLIST_GROUP = 11


@run_async
def blacklist(bot: Bot, update: Update, args: List[str]):
    msg = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    
    conn = connected(bot, update, chat, user.id, need_admin=False)
    if not conn == False:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if chat.type == "private":
            exit(1)
        else:
            chat_id = update.effective_chat.id
            chat_name = chat.title
    
    filter_list = tld(chat.id, "<b>Aktuell geblockte Wörter in {}:</b>\n").format(chat_name)

    all_blacklisted = sql.get_chat_blacklist(chat_id)

    if len(args) > 0 and args[0].lower() == 'copy':
        for trigger in all_blacklisted:
            filter_list += "<code>{}</code>\n".format(html.escape(trigger))
    else:
        for trigger in all_blacklisted:
            filter_list += " • <code>{}</code>\n".format(html.escape(trigger))

    split_text = split_message(filter_list)
    for text in split_text:
        if filter_list == tld(chat.id, "<b>Aktuell geblockte Wörter in {}:</b>\n").format(chat_name): #We need to translate
            msg.reply_text(tld(chat.id, "Es sind aktuell keine Wörter in der Gruppe <b>{}</b> gesperrt!").format(chat_name), parse_mode=ParseMode.HTML)
            return
        msg.reply_text(text, parse_mode=ParseMode.HTML)


@run_async
@user_admin
def add_blacklist(bot: Bot, update: Update):
    msg = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    words = msg.text.split(None, 1)

    conn = connected(bot, update, chat, user.id)
    if not conn == False:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            exit(1)
        else:
            chat_name = chat.title

    if len(words) > 1:
        text = words[1]
        to_blacklist = list(set(trigger.strip() for trigger in text.split("\n") if trigger.strip()))
        for trigger in to_blacklist:
            sql.add_to_blacklist(chat_id, trigger.lower())

        if len(to_blacklist) == 1:
            msg.reply_text(tld(chat.id, "Ich habe <code>{}</code> zu der Blacklist im Chat <b>{}</b> hinzugefügt!").format(html.escape(to_blacklist[0]), chat_name),
                           parse_mode=ParseMode.HTML)

        else:
            msg.reply_text(tld(chat.id, 
             "Ich habe <code>{}</code> zu der Blacklist im Chat <b>{}</b> hinzugefügt!").format(len(to_blacklist)), chat_name, parse_mode=ParseMode.HTML)

    else:
        msg.reply_text(tld(chat.id, "Sag mir, welche wörter du zur Blacklist hinzufügen möchtest."))


@run_async
@user_admin
def unblacklist(bot: Bot, update: Update):
    msg = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    words = msg.text.split(None, 1)

    conn = connected(bot, update, chat, user.id)
    if not conn == False:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            exit(1)
        else:
            chat_name = chat.title

    if len(words) > 1:
        text = words[1]
        to_unblacklist = list(set(trigger.strip() for trigger in text.split("\n") if trigger.strip()))
        successful = 0
        for trigger in to_unblacklist:
            success = sql.rm_from_blacklist(chat_id, trigger.lower())
            if success:
                successful += 1

        if len(to_unblacklist) == 1:
            if successful:
                msg.reply_text(tld(chat.id, "Ich habe <code>{}</code> von der Blacklist im Chat <b>{}</b> entfernt!").format(html.escape(to_unblacklist[0]), chat_name),
                               parse_mode=ParseMode.HTML)
            else:
                msg.reply_text(tld(chat.id, "Das ist kein geblocktes Wort!"))

        elif successful == len(to_unblacklist):
            msg.reply_text(tld(chat.id, 
                "Ich habe Blacklists entfernt. Es sind <code>{}</code>. Sie sind entfernt aus dem Chat <b>{}</b>!").format(
                    successful, chat_name), parse_mode=ParseMode.HTML)

        elif not successful:
            msg.reply_text(tld(chat.id, 
                "Keines dieser Wörter war geblockt, also habe ich sie nicht entfernt.").format(
                    successful, len(to_unblacklist) - successful), parse_mode=ParseMode.HTML)

        else:
            msg.reply_text(tld(chat.id, 
                "Ich habde <code>{}</code> Wörter aus der Blacklist im Chat <b>{}</b> entfernt! {} existierten nicht, "
                "also habe ich die nicht entfernt.").format(successful, chat_name, len(to_unblacklist) - successful),
                parse_mode=ParseMode.HTML)
    else:
        msg.reply_text(tld(chat.id, "Welches Wort möchtest du von der Blacklist entfernen?"))


@run_async
@user_not_admin
def del_blacklist(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    message = update.effective_message  # type: Optional[Message]
    to_match = extract_text(message)
    if not to_match:
        return

    chat_filters = sql.get_chat_blacklist(chat.id)
    for trigger in chat_filters:
        pattern = r"( |^|[^\w])" + re.escape(trigger) + r"( |$|[^\w])"
        if re.search(pattern, to_match, flags=re.IGNORECASE):
            try:
                message.delete()
            except BadRequest as excp:
                if excp.message == "Message to delete not found":
                    pass
                else:
                    LOGGER.exception("Ich konnte die Blacklist-Nachricht nicht löschen.")
            break


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(bot, update, chat, chatP, user):
    blacklisted = sql.num_blacklist_chat_filters(chat.id)
    return "Es gibt {} Wörter auf der Blacklist.".format(blacklisted)


def __stats__():
    return "{} blacklist-Einträge, in {} Chats.".format(sql.num_blacklist_filters(),
                                                            sql.num_blacklist_filter_chats())

def __import_data__(chat_id, data):
    # set chat blacklist
    blacklist = data.get('blacklist', {})
    for trigger in blacklist:
        sql.add_to_blacklist(chat_id, trigger)


__mod_name__ = "Wort-Blacklists"

__help__ = """
Mit dieser Funktion können Wörter hinzugefügt werden, bei deren Erwähnung im Chat eine Aktion ausgelöst wird.
 - /addblacklist <blacklist trigger> <blacklist reason>: Setzt ein Wort auf die Blacklist. Sätze mit Anführungszeichen einklammern.
 - /unblacklist <blacklist trigger>: Das entsprechende Wort von der Blacklist runternehmen.
 - /blacklist: Alle aktiven Wörter/Sätze auf der Blacklist anzeigen lassen.


/addblacklist "die Admins spinnen" Respektiere die Admins!
Das würde jede Nachricht löschen, die  'die Admins spinnen' enthält.
Falls du den alternativen Blacklist-Modus verwendest, Wird das Schreiben dieser Nachricht mit einem Kick, Ban oder einer Verwarnung bestraft.
"""

BLACKLIST_HANDLER = DisableAbleCommandHandler("blacklist", blacklist, pass_args=True, admin_ok=True)
ADD_BLACKLIST_HANDLER = CommandHandler("addblacklist", add_blacklist)
UNBLACKLIST_HANDLER = CommandHandler(["unblacklist", "rmblacklist"], unblacklist)
BLACKLIST_DEL_HANDLER = MessageHandler(
    (Filters.text | Filters.command | Filters.sticker | Filters.photo) & Filters.group, del_blacklist, edited_updates=True)

dispatcher.add_handler(BLACKLIST_HANDLER)
dispatcher.add_handler(ADD_BLACKLIST_HANDLER)
dispatcher.add_handler(UNBLACKLIST_HANDLER)
dispatcher.add_handler(BLACKLIST_DEL_HANDLER, group=BLACKLIST_GROUP)
